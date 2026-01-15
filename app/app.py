import logging
import sys

import qtawesome as qta
from worker import DownloadWorker
from dep_dl import DepWorker
from playlist_picker import PlaylistPickerDialog
from PySide6 import QtCore, QtGui, QtWidgets
from ui.main_window import Ui_MainWindow
from utils import *

__version__ = ""
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s (%(module)s:%(lineno)d) %(message)s",
    handlers=[
        logging.FileHandler(ROOT / "debug.log", encoding="utf-8", delay=True),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(str(ROOT / "assets" / "yt-dlp-gui.ico")))
        self.pb_add.setIcon(qta.icon("mdi6.plus"))
        self.pb_add.setIconSize(QtCore.QSize(21, 21))
        self.pb_clear.setIcon(qta.icon("mdi6.trash-can-outline"))
        self.pb_clear.setIconSize(QtCore.QSize(22, 22))
        self.pb_download.setIcon(qta.icon("mdi6.download"))
        self.pb_download.setIconSize(QtCore.QSize(22, 22))
        
        # Add playlist picker button
        self.pb_playlist = QtWidgets.QPushButton("Pick from Playlist")
        self.pb_playlist.setIcon(qta.icon("mdi6.playlist-check"))
        self.pb_playlist.setIconSize(QtCore.QSize(21, 21))
        self.pb_playlist.setToolTip("Select specific videos from a playlist URL")
        
        # Insert playlist button into the bottom layout (after spacer, before clear)
        self.horizontalLayout_2.insertWidget(1, self.pb_playlist)
        
        # Add quality selector dropdown (replaces the preset dropdown)
        self.dd_quality = QtWidgets.QComboBox()
        self.dd_quality.addItems(["Best", "1080p", "720p", "480p", "360p", "Audio Only"])
        self.dd_quality.setToolTip("Select video quality (or Audio Only for MP3)")
        self.dd_quality.setMinimumWidth(100)
        
        # Hide the preset dropdown and replace it with quality dropdown
        self.dd_preset.hide()
        
        # Replace preset dropdown with quality dropdown in the same position (row 2, column 3)
        # The grid layout already has: path_label(0), path_input(1), browse_btn(2), preset(3), add_btn(4)
        # We put quality dropdown in column 3, and move add button to column 4 (it's already there)
        self.gridLayout.addWidget(self.dd_quality, 2, 3)
        
        self.te_link.setPlaceholderText(
            "https://www.youtube.com/watch?v=hTWKbfoikeg\n"
            "https://www.youtube.com/watch?v=KQetemT1sWc\n"
            "https://www.youtube.com/watch?v=yKNxeF4KMsY"
        )

        self.tw.setColumnWidth(0, 200)
        self.te_link.setFocus()
        self.load_config()

        self.connect_ui()
        self.pb_download.setEnabled(False)
        self.show()

        self.dep_worker = DepWorker(self.config["general"]["update_ytdlp"])
        self.dep_worker.finished.connect(self.on_dep_finished)
        self.dep_worker.progress.connect(self.on_dep_progress)
        self.dep_worker.start()

        self.to_dl = {}
        self.worker = {}
        self.download_queue = []  # Queue for sequential downloads
        self.current_download_id = None  # Track currently downloading item
        self.index = 0

        self.tw.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tw.customContextMenuRequested.connect(self.open_menu)

    def connect_ui(self):
        # buttons
        self.pb_path.clicked.connect(self.button_path)
        self.pb_add.clicked.connect(self.button_add)
        self.pb_clear.clicked.connect(self.button_clear)
        self.pb_download.clicked.connect(self.button_download)
        self.pb_playlist.clicked.connect(self.button_playlist)

        # menu bar
        self.action_open_bin_folder.triggered.connect(lambda: self.open_folder(BIN_DIR))
        self.action_open_log_folder.triggered.connect(lambda: self.open_folder(ROOT))
        self.action_exit.triggered.connect(self.close)
        self.action_about.triggered.connect(self.show_about)
        self.action_clear_url_list.triggered.connect(self.te_link.clear)

    def on_dep_progress(self, status):
        self.statusBar.showMessage(status)

    def on_dep_finished(self):
        self.dep_worker.deleteLater()
        self.pb_download.setEnabled(True)
        self.statusBar.showMessage("")

    def open_folder(self, path):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(path)))

    def show_about(self):
        QtWidgets.QMessageBox.about(
            self,
            "About yt-dlp-gui",
            f'<a href="https://github.com/dsymbol/yt-dlp-gui">yt-dlp-gui</a> {__version__}<br><br>'
            "A GUI for yt-dlp written in PySide6.",
        )

    def open_menu(self, position):
        menu = QtWidgets.QMenu()

        delete_action = menu.addAction(qta.icon("mdi6.trash-can"), "Delete")
        copy_url_action = menu.addAction(qta.icon("mdi6.content-copy"), "Copy URL")
        open_folder_action = menu.addAction(qta.icon("mdi6.folder-open"), "Open Folder")

        item = self.tw.itemAt(position)

        if item:
            item_path = item.data(0, ItemRoles.PathRole)
            item_link = item.data(0, ItemRoles.LinkRole)
            action = menu.exec(self.tw.viewport().mapToGlobal(position))

            if action == delete_action:
                self.remove_item(item, 0)
            elif action == copy_url_action:
                QtWidgets.QApplication.clipboard().setText(item_link)
                logger.info(f"Copied URL to clipboard: {item_link}")
            elif action == open_folder_action:
                self.open_folder(item_path)
                logger.info(f"Opened folder: {item_path}")

    def remove_item(self, item, column):
        item_id = item.data(0, ItemRoles.IdRole)
        item_text = item.text(0)

        logger.debug(f"Removing download ({item_id}): {item_text}")

        if worker := self.worker.get(item_id):
            worker.stop()
            # If this was the current download, start next after removal
            if self.current_download_id == item_id:
                self.current_download_id = None

        # Remove from to_dl if not yet started
        self.to_dl.pop(item_id, None)
        
        # Remove from download queue if waiting
        self.download_queue = [(k, v) for k, v in self.download_queue if k != item_id]
        
        self.tw.takeTopLevelItem(
            self.tw.indexOfTopLevelItem(item)
        )  # remove and return a top-level item

    def button_path(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select a folder",
            self.le_path.text() or QtCore.QDir.homePath(),
            QtWidgets.QFileDialog.ShowDirsOnly,
        )

        if path:
            self.le_path.setText(path)

    def button_playlist(self):
        """Open playlist picker dialog to select specific videos."""
        url = self.te_link.toPlainText().strip()
        path = self.le_path.text()
        
        if not url:
            return QtWidgets.QMessageBox.information(
                self,
                "Application Message",
                "Please enter a playlist URL first."
            )
        
        if not path:
            return QtWidgets.QMessageBox.information(
                self,
                "Application Message",
                "Please select a save location first."
            )
        
        # Check if it looks like a playlist URL
        if 'list=' not in url and '/playlist' not in url:
            return QtWidgets.QMessageBox.information(
                self,
                "Application Message",
                "The URL doesn't appear to be a playlist.\n"
                "Playlist URLs usually contain 'list=' or '/playlist'."
            )
        
        # Get only the first URL if multiple are entered
        first_url = url.split('\n')[0].strip()
        
        dialog = PlaylistPickerDialog(self, first_url)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            selected_urls = dialog.selected_urls
            if selected_urls:
                # Replace the text area with selected URLs
                self.te_link.setPlainText('\n'.join(selected_urls))
                logger.info(f"Selected {len(selected_urls)} videos from playlist")

    def button_add(self):
        missing = []
        quality = self.dd_quality.currentText()
        links = self.te_link.toPlainText()
        path = self.le_path.text()

        if not links:
            missing.append("Video URL")
        if not path:
            missing.append("Save to")

        if missing:
            missing_fields = ", ".join(missing)
            return QtWidgets.QMessageBox.information(
                self,
                "Application Message",
                f"Required field{'s' if len(missing) > 1 else ''} ({missing_fields}) missing.",
            )

        self.te_link.clear()

        for link in links.split("\n"):
            link = link.strip()
            if not link:
                continue
            item = QtWidgets.QTreeWidgetItem(
                self.tw, [link, quality, "-", "", "Queued", "-", "-"]
            )
            pb = QtWidgets.QProgressBar()
            pb.setStyleSheet("QProgressBar { margin-bottom: 3px; }")
            pb.setTextVisible(False)
            self.tw.setItemWidget(item, 3, pb)
            [item.setTextAlignment(i, QtCore.Qt.AlignCenter) for i in range(1, 6)]
            item.setData(0, ItemRoles.IdRole, self.index)
            item.setData(0, ItemRoles.LinkRole, link)
            item.setData(0, ItemRoles.PathRole, path)

            self.to_dl[self.index] = DownloadWorker(
                item, self.config, link, path, quality
            )
            logger.info(f"Queued download ({self.index}) added {link}")
            self.index += 1

    def button_clear(self):
        if self.worker or self.download_queue:
            return QtWidgets.QMessageBox.critical(
                self,
                "Application Message",
                "Unable to clear list because there are active or queued downloads.\n"
                "Remove a download by right clicking on it and selecting delete.",
            )

        self.worker = {}
        self.to_dl = {}
        self.download_queue = []
        self.current_download_id = None
        self.tw.clear()

    def button_download(self):
        if self.te_link.toPlainText().strip():
            self.button_add()

        if not self.to_dl:
            return QtWidgets.QMessageBox.information(
                self,
                "Application Message",
                "Unable to download because there are no links in the list.",
            )

        # Add all pending downloads to the queue in order (by index key)
        for k in sorted(self.to_dl.keys()):
            v = self.to_dl[k]
            self.download_queue.append((k, v))
            logger.info(f"Added download ({k}) to queue")

        self.to_dl = {}
        
        # Start the first download if nothing is currently downloading
        if self.current_download_id is None:
            self.start_next_download()

    def start_next_download(self):
        """Start the next download in the queue."""
        if not self.download_queue:
            self.current_download_id = None
            logger.info("Download queue is empty, all downloads complete")
            return
        
        # Get the next item from the queue
        k, worker = self.download_queue.pop(0)
        self.current_download_id = k
        self.worker[k] = worker
        
        # Connect signals
        self.worker[k].finished.connect(self.worker[k].deleteLater)
        self.worker[k].finished.connect(self.on_download_finished)
        self.worker[k].progress.connect(self.on_dl_progress)
        
        # Start this download
        self.worker[k].start()
        logger.info(f"Started download ({k}), {len(self.download_queue)} remaining in queue")

    def on_download_finished(self, download_id):
        """Handle download completion and start the next one."""
        logger.info(f"Download ({download_id}) finished")
        self.worker.pop(download_id, None)
        
        # Start the next download in queue
        self.start_next_download()

    def load_config(self):
        config_path = ROOT / "config.toml"

        try:
            self.config = load_toml(config_path)
        except Exception:
            QtWidgets.QMessageBox.critical(
                self,
                "Application Message",
                f"Config file error.",
            )
            logger.error("Config file error.", exc_info=True)
            QtWidgets.QApplication.exit()

        update_ytdlp = self.config["general"].get("update_ytdlp")
        self.config["general"]["update_ytdlp"] = update_ytdlp if update_ytdlp else True
        
        # Load presets into dropdown (even though we're using quality selector, we need the config)
        self.dd_preset.addItems(self.config["presets"].keys())
        self.dd_preset.setCurrentIndex(self.config["general"].get("current_preset", 0))
        
        self.le_path.setText(self.config["general"]["path"])
        
        # Load quality setting
        quality_index = self.config["general"].get("current_quality", 2)  # Default to 720p
        self.dd_quality.setCurrentIndex(quality_index)

    def closeEvent(self, event):
        self.config["general"]["current_quality"] = self.dd_quality.currentIndex()
        self.config["general"]["path"] = self.le_path.text()
        save_toml(ROOT / "config.toml", self.config)
        event.accept()

    def on_dl_progress(self, item: QtWidgets.QTreeWidgetItem, emit_data):
        try:
            for data in emit_data:
                index, update = data
                if index != 3:
                    item.setText(index, update)
                else:
                    pb = self.tw.itemWidget(item, index)
                    pb.setValue(round(float(update.replace("%", ""))))
        except AttributeError:
            logger.info(f"Download ({item.data(0, ItemRoles.IdRole)}) no longer exists")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
