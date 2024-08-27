import logging
import os
import sys

from dep_dl import DownloadWindow

from PySide6 import QtCore as qtc, QtWidgets as qtw
from utils import *
from ui.app_ui import Ui_MainWindow
from version import __version__
from worker import Worker

os.environ["PATH"] += os.pathsep + str(ROOT / "bin")

init_logger(ROOT / "debug.log")
log = logging.getLogger(__name__)


class MainWindow(qtw.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.tw.setColumnWidth(0, 200)
        self.le_link.setFocus()
        self.conf()
        self.format_change(self.dd_format.currentText())
        self.statusBar.showMessage(f"Version {__version__}")

        self.form = DownloadWindow()
        self.form.finished.connect(self.form.close)
        self.form.finished.connect(self.show)

        self.to_dl = {}
        self.worker = {}
        self.index = 0

        self.tb_path.clicked.connect(self.button_path)
        self.dd_format.currentTextChanged.connect(self.format_change)
        self.pb_add.clicked.connect(self.button_add)
        self.pb_clear.clicked.connect(self.button_clear)
        self.pb_download.clicked.connect(self.button_download)
        self.tw.itemClicked.connect(self.remove_item)
        
        self.pb_save_preset.clicked.connect(self.save_preset)
        self.pb_delete_preset.clicked.connect(self.delete_preset)  # Connect the delete button to the method

    def save_preset(self):
        preset_name = self.le_preset_name.text().strip()
        if not preset_name:
            qtw.QMessageBox.warning(self, "Warning", "Preset name cannot be empty.")
            return
        
        cargs = self.le_cargs.text().strip()
        if not cargs:
            qtw.QMessageBox.warning(self, "Warning", "Custom arguments cannot be empty.")
            return
        
        # Save the new preset
        self.presets[preset_name] = cargs
        self.dd_presets.addItem(preset_name)
        self.le_preset_name.clear()
        qtw.QMessageBox.information(self, "Success", f"Preset '{preset_name}' saved successfully.")
        
        # Optionally, update the config file immediately
        self.save_config()
    
    def delete_preset(self):
        selected_preset = self.dd_presets.currentText()
        if selected_preset == "None":
            qtw.QMessageBox.warning(self, "Warning", "Cannot delete 'None' preset.")
            return
        
        ret = qtw.QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the preset '{selected_preset}'?",
            qtw.QMessageBox.Yes | qtw.QMessageBox.No,
            qtw.QMessageBox.No,
        )
        if ret == qtw.QMessageBox.Yes:
            # Remove the preset
            self.presets.pop(selected_preset, None)
            self.dd_presets.removeItem(self.dd_presets.currentIndex())
            qtw.QMessageBox.information(self, "Success", f"Preset '{selected_preset}' deleted successfully.")
            
            # Optionally, update the config file immediately
            self.save_config()

    def save_config(self):
        d = {
            "path": self.le_path.text(),
            "format": self.dd_format.currentIndex(),
            "sponsorblock": self.dd_sponsorblock.currentIndex(),
            "metadata": self.cb_metadata.isChecked(),
            "subtitles": self.cb_subtitles.isChecked(),
            "thumbnail": self.cb_thumbnail.isChecked(),
            "custom_args": self.le_cargs.text(),
            "presets": self.presets,  # Save the updated presets
            "selected_preset": self.dd_presets.currentIndex()  # Save the selected preset index
        }
        save_json(ROOT / "conf.json", d)
        
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
                log.info(f"Removing queued {item.text(0)} download with id {item.id} ")
                self.to_dl.pop(item.id)
            elif worker := self.worker.get(item.id):
                log.info(
                    f"Stopping and removing {item.text(0)} download with id {item.id}"
                )
                worker.stop()
            self.tw.takeTopLevelItem(self.tw.indexOfTopLevelItem(item))

    def button_path(self):
        path = qtw.QFileDialog.getExistingDirectory(
            self, "Select a folder", qtc.QDir.homePath(), qtw.QFileDialog.ShowDirsOnly
        )

        if path:
            self.le_path.setText(path)

    def format_change(self, fmt):
        if fmt == "mp4" or fmt == "best":
            self.cb_subtitles.setEnabled(True)
            self.cb_thumbnail.setEnabled(True)
        else:
            if fmt in ["mp3", "flac"]:
                self.cb_thumbnail.setEnabled(True)
            else:
                self.cb_thumbnail.setEnabled(False)
                self.cb_thumbnail.setChecked(False)
            self.cb_subtitles.setEnabled(False)
            self.cb_subtitles.setChecked(False)

    def button_add(self):
        (
            link,
            path,
            format_,
            cargs,
            filename,
            sponsorblock,
            metadata,
            thumbnail,
            subtitles,
        ) = [
            self.le_link.text(),
            self.le_path.text(),
            self.dd_format.currentText(),
            self.le_cargs.text(),
            self.le_filename.text(),
            self.dd_sponsorblock.currentText(),
            self.cb_metadata.isChecked(),
            self.cb_thumbnail.isChecked(),
            self.cb_subtitles.isChecked(),
        ]

        # Get selected preset
        selected_preset = self.dd_presets.currentText()
        preset_args = self.presets.get(selected_preset, "") if selected_preset != "None" else ""

        if not all([link, path, format_]):
            return qtw.QMessageBox.information(
                self,
                "Application Message",
                "Unable to add the download because some required fields are missing.\nRequired fields: Link, Path & Format.",
            )

        # Combine preset and custom args
        combined_args = f"{preset_args} {cargs}".strip()

        item = qtw.QTreeWidgetItem(
            self.tw, [link, format_, "-", "0%", "Queued", "-", "-"]
        )
        pb = qtw.QProgressBar()
        pb.setStyleSheet("QProgressBar { margin-bottom: 3px; }")
        pb.setTextVisible(False)
        pb.setValue(0)
        pb.setRange(0, 100)
        self.tw.setItemWidget(item, 3, pb)
        [item.setTextAlignment(i, qtc.Qt.AlignCenter) for i in range(1, 6)]
        item.id = self.index
        filename = filename if filename else "%(title)s.%(ext)s"
        #self.le_link.clear()
        self.to_dl[self.index] = [
            item,
            link,
            path,
            format_,
            combined_args,  # Use combined args
            filename,
            sponsorblock,
            metadata,
            thumbnail,
            subtitles,
        ]
        self.index += 1
        log.info(
            f"Queued download added: (link={link}, path={path}, format={format_}, cargs={combined_args}, "
            f"filename={filename}, sponsorblock={sponsorblock}, metadata={metadata}, thumbnail={thumbnail}, "
            f"subtitles={subtitles})"
        )

    def button_clear(self):
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
        if not self.to_dl:
            return qtw.QMessageBox.information(
                self,
                "Application Message",
                "Unable to download because there are no links in the list.",
            )

        for k, v in self.to_dl.items():
            self.worker[k] = Worker(*v)
            self.worker[k].finished.connect(self.worker[k].deleteLater)
            self.worker[k].finished.connect(lambda x: self.worker.pop(x))
            self.worker[k].progress.connect(self.update_progress)
            self.worker[k].start()

        self.to_dl = {}

    def conf(self):
        d = {
            "path": "",
            "format": 0,
            "sponsorblock": 0,
            "metadata": False,
            "subtitles": False,
            "thumbnail": False,
            "custom_args": "",
            "presets": {},  # Add presets key
            "selected_preset": 0  # Default to "None" if no preset is selected
        }
        settings = load_json(ROOT / "conf.json", d)

        self.le_path.setText(settings["path"])
        self.dd_format.setCurrentIndex(settings["format"])
        self.dd_sponsorblock.setCurrentIndex(settings["sponsorblock"])
        self.cb_metadata.setChecked(settings["metadata"])
        self.cb_subtitles.setChecked(settings["subtitles"])
        self.cb_thumbnail.setChecked(settings["thumbnail"])
        self.le_cargs.setText(settings["custom_args"])
        
        # Load presets into a dropdown menu (if using a dropdown for presets)
        self.presets = settings["presets"]
        self.dd_presets.clear()
        self.dd_presets.addItem("None")
        for preset in self.presets.keys():
            self.dd_presets.addItem(str(preset))
            
        # Convert selected_preset to string if it's an integer or non-string type
        selected_preset = settings["selected_preset"]
        
        if selected_preset != -1:
            self.dd_presets.setCurrentIndex(selected_preset)
        else:
            self.dd_presets.setCurrentIndex(0)  # Default to "None" if preset not found

    def closeEvent(self, event):
        d = {
            "path": self.le_path.text(),
            "format": self.dd_format.currentIndex(),
            "sponsorblock": self.dd_sponsorblock.currentIndex(),
            "metadata": self.cb_metadata.isChecked(),
            "subtitles": self.cb_subtitles.isChecked(),
            "thumbnail": self.cb_thumbnail.isChecked(),
            "custom_args": self.le_cargs.text(),
            "presets": self.presets,  # Preserve presets
            "selected_preset": self.dd_presets.currentIndex()  # Save the selected preset index
        }
        save_json(ROOT / "conf.json", d)
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
            log.info(f"Item {item.id} no longer exists")


if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
