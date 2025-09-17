import logging
import os
import sys

from dep_dl import DownloadWindow
from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw
from PySide6.QtGui import QIcon, QCursor
from ui.main_window import Ui_MainWindow
from utils import *
from worker import Worker

os.environ["PATH"] += os.pathsep + str(root / "bin")
__version__ = ""
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s (%(module)s:%(lineno)d) %(message)s",
    handlers=[
        logging.FileHandler(root / "debug.log", encoding="utf-8", delay=True),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class MainWindow(qtw.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon(str(root / "assets" / "yt-dlp-gui.ico")))
        self.pb_add.setIcon(QIcon(str(root / "assets" / "add.png")))
        self.pb_clear.setIcon(QIcon(str(root / "assets" / "clear.png")))
        self.pb_download.setIcon(QIcon(str(root / "assets" / "download.png")))
        self.te_link.setPlaceholderText(
            "https://www.youtube.com/watch?v=hTWKbfoikeg\n"
            "https://www.youtube.com/watch?v=KQetemT1sWc\n"
            "https://www.youtube.com/watch?v=yKNxeF4KMsY"
        )

        self.tw.setColumnWidth(0, 200)
        self.te_link.setFocus()
        # Make the downloads list act like a normal Windows list
        self.tw.setSelectionMode(qtw.QAbstractItemView.ExtendedSelection)  # Ctrl/Shift multi-select
        self.tw.setSelectionBehavior(qtw.QAbstractItemView.SelectRows)

        # Remove dangerous left-click-to-delete
        try:
            self.tw.itemClicked.disconnect(self.remove_item)
        except Exception:
            pass  # already disconnected or not connected yet

        # Right-click context menu
        self.tw.setContextMenuPolicy(qtc.Qt.CustomContextMenu)
        self.tw.customContextMenuRequested.connect(self.open_context_menu)
        self.load_config()
        self.statusBar.showMessage(__version__)

        self.form = DownloadWindow()
        self.form.finished.connect(self.form.close)
        self.form.finished.connect(self.show)

        self.to_dl = {}
        self.worker = {}
        self.index = 0

        self.pb_path.clicked.connect(self.button_path)
        self.pb_add.clicked.connect(self.button_add)
        self.pb_clear.clicked.connect(self.button_clear)
        self.pb_download.clicked.connect(self.button_download)

    def remove_item(self, item, column):
        ret = qtw.QMessageBox.question(
            self,
            "Application Message",
            f"Would you like to remove {item.text(0)} ?",
            qtw.QMessageBox.Yes | qtw.QMessageBox.No,
            qtw.QMessageBox.No,
        )
        if ret == qtw.QMessageBox.Yes:
            if self.to_dl.get(item.id):
                logger.debug(f"Removing queued download ({item.id}): {item.text(0)}")
                self.to_dl.pop(item.id)
            elif worker := self.worker.get(item.id):
                logger.info(
                    f"Stopping and removing download ({item.id}): {item.text(0)}"
                )
                worker.stop()
            self.tw.takeTopLevelItem(self.tw.indexOfTopLevelItem(item)) # remove and return a top-level item

    def button_path(self):
        path = qtw.QFileDialog.getExistingDirectory(
            self,
            "Select a folder",
            self.le_path.text() or qtc.QDir.homePath(),
            qtw.QFileDialog.ShowDirsOnly,
        )

        if path:
            self.le_path.setText(path)

    def button_add(self):
        missing = []
        preset = self.dd_preset.currentText()
        links = self.te_link.toPlainText()
        path = self.le_path.text()

        if not links:
            missing.append("Video URL")
        if not path:
            missing.append("Save to")

        if missing:
            missing_fields = ", ".join(missing)
            return qtw.QMessageBox.information(
                self,
                "Application Message",
                (
                    f"Required fields ({missing_fields}) are missing."
                    if len(missing) > 1
                    else f"Required field ({missing_fields}) is missing."
                ),
            )

        self.te_link.clear()

        for link in links.split("\n"):
            link = link.strip()
            item = qtw.QTreeWidgetItem(
                self.tw, [link, preset, "-", "", "Queued", "-", "-"]
            )
            pb = qtw.QProgressBar()
            pb.setStyleSheet("QProgressBar { margin-bottom: 3px; }")
            pb.setTextVisible(False)
            self.tw.setItemWidget(item, 3, pb)
            [item.setTextAlignment(i, qtc.Qt.AlignCenter) for i in range(1, 6)]
            item.link = link
            item.preset = preset
            item.path = path
            item.id = self.index

            self.to_dl[self.index] = Worker(item, self.config, link, path, preset)
            logger.info(f"Queue download ({item.id}) added: {self.to_dl[self.index]}")
            self.index += 1

    def button_clear(self):
        items = self.selected_items()
        if items:
            # Delete only selected items; allow this even if others are active
            self.delete_items(items)
            return

        # No selection: preserve original safeguard behavior
        if self.worker:
            return qtw.QMessageBox.critical(
                self,
                "Application Message",
                "Unable to clear list because there are active downloads in progress.\n"
                "Remove a download by clicking on it.",
            )

        self.worker = {}
        self.to_dl = {}
        self.tw.clear()

    def button_download(self):
        items = self.selected_items()
        if items:
            # Parallel fresh restarts for selection
            for it in items:
                self.restart_items([it])
            return

        # Fallback: original behavior (download all queued)
        if not self.to_dl:
            return qtw.QMessageBox.information(
                self,
                "Application Message",
                "Unable to download because there are no links in the list.",
            )

        for k, v in self.to_dl.items():
            self.worker[k] = v
            self.worker[k].finished.connect(self.worker[k].deleteLater)
            self.worker[k].finished.connect(lambda x: self.worker.pop(x))
            self.worker[k].progress.connect(self.update_progress)
            self.worker[k].start()

        self.to_dl = {}

    def load_config(self):
        config_path = root / "config.toml"

        try:
            self.config = load_toml(config_path)
        except FileNotFoundError:
            qtw.QMessageBox.critical(
                self,
                "Application Message",
                f"Config file not found at: {config_path}",
            )
            qtw.QApplication.exit()
        except toml.decoder.TomlDecodeError:
            qtw.QMessageBox.critical(
                self,
                "Application Message",
                "Config file TOML decoding failed, check the log file for more info.",
            )
            logger.error("Config file TOML decoding failed", exc_info=True)
            qtw.QApplication.exit()

        self.dd_preset.addItems(self.config["presets"].keys())
        self.dd_preset.setCurrentIndex(self.config["general"]["current_preset"])
        self.le_path.setText(self.config["general"]["path"])

    def closeEvent(self, event):
        self.config["general"]["current_preset"] = self.dd_preset.currentIndex()
        self.config["general"]["path"] = self.le_path.text()
        save_toml(root / "config.toml", self.config)
        event.accept()

    def update_progress(self, item, emit_data):
        try:
            for data in emit_data:
                index, update = data
                if index != 3:
                    item.setText(index, update)
                else:
                    pb = self.tw.itemWidget(item, index)
                    pb.setValue(round(float(update.replace("%", ""))))
        except AttributeError:
            logger.info(f"Download ({item.id}) no longer exists")

    # Selection helpers and actions
    def selected_items(self):
        # Only top-level items are used in this app
        return [it for it in self.tw.selectedItems()]

    def queue_worker_for_item(self, item, *, fresh=False):
        """
        Ensure 'item' has an active Worker and start it.
        If fresh=True, force a clean restart (no resume).
        """
        # Stop any existing worker for this item
        if (worker := self.worker.get(item.id)) is not None:
            worker.stop()

        # If item was queued but not started yet, drop the stale queue entry
        if self.to_dl.get(item.id):
            self.to_dl.pop(item.id)

        # Build a new worker for this item
        w = Worker(
            item,
            self.config,
            getattr(item, "link", item.text(0)),
            getattr(item, "path", self.le_path.text()),
            getattr(item, "preset", self.dd_preset.currentText()),
        )
        # For a "fresh" restart, inject no-resume/overwrite via per-instance extra_args
        w.extra_args = ["--no-continue", "--force-overwrites"] if fresh else []

        # Wire signals and start
        self.worker[item.id] = w
        w.finished.connect(w.deleteLater)
        w.finished.connect(lambda x=item.id: self.worker.pop(x, None))
        w.progress.connect(self.update_progress)
        # Reset UI visuals
        try:
            pb = self.tw.itemWidget(item, 3)
            if pb:
                pb.setValue(0)
        except Exception:
            pass
        item.setText(4, "Processing" if fresh else "Queued")
        w.start()

    def delete_items(self, items):
        for item in items:
            # If queued and not started
            if self.to_dl.get(item.id):
                logger.debug(f"Removing queued download ({item.id}): {item.text(0)}")
                self.to_dl.pop(item.id, None)
            # If running, stop it
            elif (worker := self.worker.get(item.id)) is not None:
                logger.info(
                    f"Stopping and removing download ({item.id}): {item.text(0)}"
                )
                worker.stop()
                # Let worker cleanup via finished hook; we still remove UI now
            # Remove row from UI
            idx = self.tw.indexOfTopLevelItem(item)
            if idx >= 0:
                self.tw.takeTopLevelItem(idx)

    def restart_items(self, items):
        for item in items:
            # Start a clean, fresh download (no resume, overwrite)
            self.queue_worker_for_item(item, fresh=True)

    def copy_urls(self, items):
        urls = []
        for item in items:
            # Prefer the stored link, fall back to column 0 if it looks like a URL
            link = getattr(item, "link", None) or item.text(0)
            urls.append(link)
        text = os.linesep.join(urls)
        qtw.QApplication.clipboard().setText(text)

    def open_context_menu(self, pos):
        # If user right-clicked on an unselected row, select it
        item = self.tw.itemAt(pos)
        if item and item not in self.tw.selectedItems():
            self.tw.clearSelection()
            item.setSelected(True)

        items = self.selected_items()
        if not items:
            return  # nothing selected

        menu = qtw.QMenu(self)

        act_delete = menu.addAction("Delete selected item(s)")
        act_restart = menu.addAction("Restart selected item(s)")
        act_copy = menu.addAction("Copy video URL(s)")

        action = menu.exec(self.tw.viewport().mapToGlobal(pos))
        if action == act_delete:
            self.delete_items(items)
        elif action == act_restart:
            self.restart_items(items)
        elif action == act_copy:
            self.copy_urls(items)


if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
