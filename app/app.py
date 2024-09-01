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

        self.settings = self.load_settings()
        self.init()

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
        self.pb_delete_preset.clicked.connect(self.delete_preset)

        self.dd_presets.currentIndexChanged.connect(self.load_preset)

    def load_settings(self):
        default_settings = {
            "path": "",
            "format": 0,
            "sponsorblock": 0,
            "metadata": False,
            "subtitles": False,
            "thumbnail": False,
            "chapters": False,
            "custom_args": "",
            "presets": {},
            "selected_preset": 0
        }
        return load_json(ROOT / "conf.json", default_settings)

    def init(self):        
        self.le_path.setText(self.settings["path"])
        self.dd_format.setCurrentIndex(self.settings["format"])
        self.dd_sponsorblock.setCurrentIndex(self.settings["sponsorblock"])
        self.cb_metadata.setChecked(self.settings["metadata"])
        self.cb_subtitles.setChecked(self.settings["subtitles"])
        self.cb_thumbnail.setChecked(self.settings["thumbnail"])
        self.le_cargs.setText(self.settings["custom_args"])
        self.cb_chapters.setChecked(self.settings["chapters"])

        self.presets = self.settings["presets"]
        self.dd_presets.clear()
        self.dd_presets.addItem("Custom")
        for preset in self.presets.keys():
            self.dd_presets.addItem(str(preset))  
        
        # Set the selected preset
        selected_preset_index = self.settings.get("selected_preset", 0)
        self.dd_presets.setCurrentIndex(selected_preset_index)   
        self.load_preset()

    def connect_signals(self):
        self.tb_path.clicked.connect(self.button_path)
        self.dd_format.currentTextChanged.connect(self.format_change)
        self.pb_add.clicked.connect(self.button_add)
        self.pb_clear.clicked.connect(self.button_clear)
        self.pb_download.clicked.connect(self.button_download)
        self.tw.itemClicked.connect(self.remove_item)

        self.pb_save_preset.clicked.connect(self.save_preset)
        self.pb_delete_preset.clicked.connect(self.delete_preset)

        self.dd_presets.currentIndexChanged.connect(self.load_preset)

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
            chapters,
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
            self.cb_chapters.isChecked(),
        ]

        if not all([link, path, format_]):
            return qtw.QMessageBox.information(
                self,
                "Application Message",
                "Unable to add the download because some required fields are missing.\nRequired fields: Link, Path & Format.",
            )

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
            cargs,
            filename,
            sponsorblock,
            metadata,
            thumbnail,
            subtitles,
            chapters,
        ]
        self.index += 1
        log.info(
            f"Queued download added: (link={link}, path={path}, format={format_}, cargs={cargs}, "
            f"filename={filename}, sponsorblock={sponsorblock}, metadata={metadata}, thumbnail={thumbnail}, "
            f"subtitles={subtitles}, chapters={chapters})"
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

    def set_preset(self, preset_name):
        index = self.dd_presets.findText(preset_name)
        if index != -1:
            self.dd_presets.setCurrentIndex(index)
        else:
            self.dd_presets.setCurrentIndex(0)  # Default to "Custom" if preset not found

    def save_preset(self):
        preset_name = self.le_preset_name.text().strip()
        
        # If no preset name is provided
        if not preset_name:
            selected_preset = self.dd_presets.currentText()
            
            # Ensure we're not overwriting "Custom"
            if selected_preset != "Custom":
                ret = qtw.QMessageBox.question(
                    self,
                    "Overwrite Preset",
                    f"No preset name provided. Do you want to overwrite the existing preset '{selected_preset}'?",
                    qtw.QMessageBox.Yes | qtw.QMessageBox.No,
                    qtw.QMessageBox.No,
                )
                
                if ret == qtw.QMessageBox.Yes:
                    preset_name = selected_preset  # Use the currently selected preset name
                else:
                    return  # Exit the function if the user doesn't want to overwrite
            else:
                qtw.QMessageBox.warning(self, "Warning", "Preset name cannot be empty.")
                return
        
        # If a new preset name is provided and already exists, warn the user
        if preset_name in self.presets and preset_name != self.dd_presets.currentText():
            qtw.QMessageBox.warning(self, "Warning", f"A preset with the name '{preset_name}' already exists. Please choose a different name.")
            return

        cargs = self.le_cargs.text().strip()
        if not cargs:
            qtw.QMessageBox.warning(self, "Warning", "Custom arguments cannot be empty.")
            return
        
        # Save the preset
        self.presets[preset_name] = cargs
        if preset_name not in self.presets:
            self.dd_presets.addItem(preset_name)  # Add to dropdown only if it's a new preset
        #self.le_preset_name.clear()
        qtw.QMessageBox.information(self, "Success", f"Preset '{preset_name}' saved successfully.")
        
        self.set_preset(preset_name)
        self.save_config()

    def delete_preset(self):
        selected_preset = self.dd_presets.currentText()
        if selected_preset == "Custom":
            qtw.QMessageBox.warning(self, "Warning", "Cannot delete 'Custom' preset.")
            return
        
        ret = qtw.QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the preset '{selected_preset}'?",
            qtw.QMessageBox.Yes | qtw.QMessageBox.No,
            qtw.QMessageBox.No,
        )
        if ret == qtw.QMessageBox.Yes:
            self.presets.pop(selected_preset, None)
            self.dd_presets.removeItem(self.dd_presets.currentIndex())
            qtw.QMessageBox.information(self, "Success", f"Preset '{selected_preset}' deleted successfully.")
            self.save_config()

    def load_preset(self):        
        selected_preset = self.dd_presets.currentText()
        if selected_preset == "Custom":
            self.le_cargs.setText(self.settings["custom_args"])
            self.pb_delete_preset.setEnabled(False)
        else:
            self.le_cargs.setText(self.presets.get(selected_preset, ""))
            self.pb_delete_preset.setEnabled(True)

    def save_config(self):
        if self.dd_presets.currentIndex() == 0:  # If "Custom" preset is selected
            custom_args = self.le_cargs.text()
        else:
            custom_args = self.settings["custom_args"]  # Preserve the existing custom_args

        settings_to_save = {
            "path": self.le_path.text(),
            "format": self.dd_format.currentIndex(),
            "sponsorblock": self.dd_sponsorblock.currentIndex(),
            "metadata": self.cb_metadata.isChecked(),
            "subtitles": self.cb_subtitles.isChecked(),
            "thumbnail": self.cb_thumbnail.isChecked(),
            "chapters": self.cb_chapters.isChecked(),
            "custom_args": custom_args,
            "presets": self.presets,
            "selected_preset": self.dd_presets.currentIndex()
        }
        save_json(ROOT / "conf.json", settings_to_save)

    def closeEvent(self, event):
        self.save_config()
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
