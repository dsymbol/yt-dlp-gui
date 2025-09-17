import logging
import os
import sys

from dep_dl import DownloadWindow
from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw
from PySide6.QtGui import QIcon
from ui.main_window import Ui_MainWindow
from utils import *
from worker import Worker, STATUS, PROGRESS

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
        self.load_config()
        self.statusBar.showMessage(__version__)

        self.form = DownloadWindow()
        self.form.finished.connect(self.form.close)
        self.form.finished.connect(self.show)
        
        # Setup preset controls after everything else is initialized
        self.setup_preset_controls()

        self.to_dl = {}
        self.worker = {}
        self.index = 0
        self.pending_restart = set()
        
        # Dynamic UI elements for preset options
        self.cb_metadata = None
        self.cb_subtitles = None
        self.cb_thumbnail = None
        self.dd_sponsorblock = None
        self.dynamic_labels = []

        self.pb_path.clicked.connect(self.button_path)
        self.pb_add.clicked.connect(self.button_add)
        self.pb_clear.clicked.connect(self.button_clear)
        self.pb_download.clicked.connect(self.button_download)
        
        # Set up context menu for downloads list
        self.tw.setContextMenuPolicy(qtc.Qt.CustomContextMenu)
        self.tw.customContextMenuRequested.connect(self.on_tw_context_menu)

    def on_tw_context_menu(self, pos):
        """Handle right-click context menu on downloads tree widget"""
        item = self.tw.itemAt(pos)
        if not item:
            return
            
        menu = qtw.QMenu(self)
        act_delete = menu.addAction("Delete")
        act_restart = menu.addAction("Restart download")
        act_copy = menu.addAction("Copy URL")
        
        # Disable restart if no link metadata available
        if not hasattr(item, 'link') or not item.link:
            act_restart.setEnabled(False)
            
        chosen = menu.exec(self.tw.viewport().mapToGlobal(pos))
        
        if chosen == act_delete:
            self.delete_item(item)
        elif chosen == act_restart:
            self.restart_item(item)
        elif chosen == act_copy:
            self.copy_item_url(item)

    def delete_item(self, item):
        """Delete an item from the downloads list"""
        if hasattr(item, 'id') and item.id is not None:
            if item.id in self.to_dl:
                logger.debug(f"Removing queued download ({item.id}): {item.text(0)}")
                self.to_dl.pop(item.id, None)
            elif item.id in self.worker:
                logger.info(f"Stopping and removing download ({item.id}): {item.text(0)}")
                self.worker[item.id].stop()
                # Remove from pending restart if it was there
                self.pending_restart.discard(item.id)
        
        # Remove item from tree
        try:
            self.tw.takeTopLevelItem(self.tw.indexOfTopLevelItem(item))
        except Exception as e:
            logger.error(f"Error removing item from tree: {e}")

    def on_worker_finished(self, item_id):
        """Handle worker finished signal"""
        self.worker.pop(item_id, None)
        
        if item_id in self.pending_restart:
            self.pending_restart.remove(item_id)
            # Find the item in the tree and restart it
            for i in range(self.tw.topLevelItemCount()):
                item = self.tw.topLevelItem(i)
                if hasattr(item, 'id') and item.id == item_id:
                    self.start_worker_for_item(item)
                    break

    def start_worker_for_item(self, item):
        """Start a worker for the given item"""
        if not hasattr(item, 'link') or not hasattr(item, 'preset') or not hasattr(item, 'path'):
            item_id = getattr(item, 'id', 'unknown')
            logger.error(f"Item {item_id} missing required metadata for restart")
            return
            
        # Get preset options from item or fall back to current UI state
        preset_options = getattr(item, 'preset_options', None)
        if preset_options is None:
            preset_options = self.get_current_preset_options()
            item.preset_options = preset_options.copy()  # Store for future restarts
            
        # Create new worker
        worker = Worker(item, self.config, item.link, item.path, item.preset, preset_options)
        self.worker[item.id] = worker
        
        # Connect signals
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(self.on_worker_finished)
        worker.progress.connect(self.update_progress)
        
        # Reset UI state
        item.setText(STATUS, "Queued")
        pb = self.tw.itemWidget(item, PROGRESS)
        if pb:
            pb.setValue(0)
        else:
            # Create progress bar if missing (for older items)
            pb = qtw.QProgressBar()
            pb.setStyleSheet("QProgressBar { margin-bottom: 3px; }")
            pb.setTextVisible(False)
            self.tw.setItemWidget(item, PROGRESS, pb)
        
        # Clear other columns
        item.setText(2, "-")  # Size
        item.setText(5, "-")  # Speed
        item.setText(6, "-")  # ETA
        
        # Start the worker
        worker.start()
        logger.info(f"Restarted download ({item.id}): {item.text(0)}")

    def restart_item(self, item):
        """Restart a download item"""
        if not hasattr(item, 'link') or not item.link:
            qtw.QMessageBox.information(
                self,
                "Application Message",
                "No URL available for this item to restart."
            )
            return
            
        if hasattr(item, 'id'):
            if item.id in self.worker:
                # Active download - mark for restart after stopping
                self.pending_restart.add(item.id)
                self.worker[item.id].stop()
                return
            elif item.id in self.to_dl:
                # Queued download - start immediately
                self.start_worker_for_item(item)
                self.to_dl.pop(item.id, None)
                return
                
        # Finished or not tracked - start fresh
        self.start_worker_for_item(item)

    def copy_item_url(self, item):
        """Copy the URL of the download item to clipboard"""
        url = None
        
        # Try to get URL from stored metadata first
        if hasattr(item, 'link') and item.link:
            url = item.link
        # Fallback to first column text if it looks like a URL
        elif item.text(0).startswith(('http://', 'https://')):
            url = item.text(0)
            
        if url:
            qtw.QApplication.clipboard().setText(url)
            self.statusBar.showMessage(f"URL copied to clipboard: {url}", 3000)
        else:
            qtw.QMessageBox.information(
                self,
                "Application Message",
                "No URL available for this item."
            )

    def setup_preset_controls(self):
        """Create dynamic UI elements for preset options"""
        self.create_preset_controls()
        
        # Connect preset dropdown change event
        self.dd_preset.currentTextChanged.connect(self.on_preset_changed)
        
        # Update controls for current preset
        current_preset = self.dd_preset.currentText()
        if current_preset:
            self.update_preset_controls(current_preset)

    def create_preset_controls(self):
        """Create the UI controls for preset options"""
        # Clean up existing controls first (only if they exist)
        if hasattr(self, 'cb_metadata') and self.cb_metadata is not None:
            self.cleanup_preset_controls()
        
        # Metadata checkbox
        self.cb_metadata = qtw.QCheckBox("Include metadata")
        self.cb_metadata.setToolTip("Include video metadata and info files")
        
        # Subtitles checkbox
        self.cb_subtitles = qtw.QCheckBox("Include subtitles")
        self.cb_subtitles.setToolTip("Download subtitles if available")
        
        # Thumbnail checkbox
        self.cb_thumbnail = qtw.QCheckBox("Include thumbnail")
        self.cb_thumbnail.setToolTip("Download video thumbnail")
        
        # SponsorBlock dropdown with label
        sb_label = qtw.QLabel("SponsorBlock:")
        sb_label.setToolTip("SponsorBlock functionality for sponsor segments")
        self.dd_sponsorblock = qtw.QComboBox()
        self.dd_sponsorblock.addItems(["Disabled", "Remove", "Mark"])
        self.dd_sponsorblock.setToolTip("0=Disabled, 1=Remove sponsor segments, 2=Mark sponsor segments")
        
        # Add to grid layout at row 1
        self.gridLayout.addWidget(self.cb_metadata, 1, 0, 1, 1)
        self.gridLayout.addWidget(self.cb_subtitles, 1, 1, 1, 1)
        self.gridLayout.addWidget(self.cb_thumbnail, 1, 2, 1, 1)
        self.gridLayout.addWidget(sb_label, 1, 3, 1, 1)
        self.gridLayout.addWidget(self.dd_sponsorblock, 1, 4, 1, 1)
        
        # Store label for cleanup
        self.dynamic_labels = [sb_label]

    def cleanup_preset_controls(self):
        """Remove existing preset controls from the layout"""
        controls = [
            getattr(self, 'cb_metadata', None),
            getattr(self, 'cb_subtitles', None), 
            getattr(self, 'cb_thumbnail', None),
            getattr(self, 'dd_sponsorblock', None)
        ]
        controls.extend(getattr(self, 'dynamic_labels', []))
        
        for control in controls:
            if control:
                control.setParent(None)
                control.deleteLater()
        
        self.cb_metadata = None
        self.cb_subtitles = None
        self.cb_thumbnail = None
        self.dd_sponsorblock = None
        self.dynamic_labels = []

    def on_preset_changed(self, preset_name):
        """Handle preset dropdown change"""
        self.update_preset_controls(preset_name)

    def update_preset_controls(self, preset_name):
        """Update control states based on selected preset"""
        if not preset_name or preset_name not in self.config["presets"]:
            # Disable all controls if preset not found
            for control in [self.cb_metadata, self.cb_subtitles, self.cb_thumbnail, self.dd_sponsorblock]:
                if control:
                    control.setEnabled(False)
            return
            
        preset = self.config["presets"][preset_name]
        
        # Update metadata checkbox
        if self.cb_metadata:
            if "metadata" in preset:
                self.cb_metadata.setEnabled(True)
                self.cb_metadata.setChecked(preset["metadata"])
            else:
                self.cb_metadata.setEnabled(False)
                self.cb_metadata.setChecked(False)
        
        # Update subtitles checkbox
        if self.cb_subtitles:
            if "subtitles" in preset:
                self.cb_subtitles.setEnabled(True)
                self.cb_subtitles.setChecked(preset["subtitles"])
            else:
                self.cb_subtitles.setEnabled(False)
                self.cb_subtitles.setChecked(False)
        
        # Update thumbnail checkbox
        if self.cb_thumbnail:
            if "thumbnail" in preset:
                self.cb_thumbnail.setEnabled(True)
                self.cb_thumbnail.setChecked(preset["thumbnail"])
            else:
                self.cb_thumbnail.setEnabled(False)
                self.cb_thumbnail.setChecked(False)
        
        # Update sponsorblock dropdown
        if self.dd_sponsorblock:
            if "sponsorblock" in preset:
                self.dd_sponsorblock.setEnabled(True)
                self.dd_sponsorblock.setCurrentIndex(preset["sponsorblock"])
            else:
                self.dd_sponsorblock.setEnabled(False)
                self.dd_sponsorblock.setCurrentIndex(0)

    def get_current_preset_options(self):
        """Get current preset options from UI controls"""
        options = {}
        
        if self.cb_metadata and self.cb_metadata.isEnabled():
            options["metadata"] = self.cb_metadata.isChecked()
            
        if self.cb_subtitles and self.cb_subtitles.isEnabled():
            options["subtitles"] = self.cb_subtitles.isChecked()
            
        if self.cb_thumbnail and self.cb_thumbnail.isEnabled():
            options["thumbnail"] = self.cb_thumbnail.isChecked()
            
        if self.dd_sponsorblock and self.dd_sponsorblock.isEnabled():
            options["sponsorblock"] = self.dd_sponsorblock.currentIndex()
            
        return options

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

        # Get current preset options from UI
        preset_options = self.get_current_preset_options()

        for link in links.split("\n"):
            link = link.strip()
            if not link:  # Skip empty lines
                continue
                
            item = qtw.QTreeWidgetItem(
                self.tw, [link, preset, "-", "", "Queued", "-", "-"]
            )
            pb = qtw.QProgressBar()
            pb.setStyleSheet("QProgressBar { margin-bottom: 3px; }")
            pb.setTextVisible(False)
            self.tw.setItemWidget(item, 3, pb)
            [item.setTextAlignment(i, qtc.Qt.AlignCenter) for i in range(1, 6)]
            item.id = self.index
            item.link = link
            item.preset = preset
            item.path = path
            item.preset_options = preset_options.copy()  # Store preset options in item

            self.to_dl[self.index] = Worker(item, self.config, link, path, preset, preset_options)
            logger.info(f"Queue download ({item.id}) added: {self.to_dl[self.index]} with options: {preset_options}")
            self.index += 1

    def button_clear(self):
        if self.worker:
            return qtw.QMessageBox.critical(
                self,
                "Application Message",
                "Unable to clear list because there are active downloads in progress.\n"
                "Remove a download by right-clicking it and choosing Delete.",
            )

        self.worker = {}
        self.to_dl = {}
        self.tw.clear()

    def button_download(self):
        if not self.to_dl:
            return qtw.QMessageBox.information(
                self,
                "Application Message",
                "Unable to download because there are no links in the list.",
            )

        for k, v in self.to_dl.items():
            self.worker[k] = v
            self.worker[k].finished.connect(self.worker[k].deleteLater)
            self.worker[k].finished.connect(self.on_worker_finished)
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
        
        # Clean up dynamic controls
        self.cleanup_preset_controls()
        
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


if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
