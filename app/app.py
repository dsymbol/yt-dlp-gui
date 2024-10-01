import logging
import os
import sys

from dep_dl import DownloadWindow

from PySide6 import QtCore as qtc, QtWidgets as qtw
from utils import *
from ui.app_ui import Ui_MainWindow
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
        self.tw.setColumnWidth(0, 200)
        self.le_link.setFocus()
        self.load_config()
        self.statusBar.showMessage(__version__)

        self.form = DownloadWindow()
        self.form.finished.connect(self.form.close)
        self.form.finished.connect(self.show)

        self.to_dl = {}
        self.worker = {}
        self.index = 0

        self.tb_path.clicked.connect(self.button_path)
        self.dd_format.currentTextChanged.connect(self.load_preset)
        self.pb_save_preset.clicked.connect(self.save_preset)
        self.pb_add.clicked.connect(self.button_add)
        self.pb_clear.clicked.connect(self.button_clear)
        self.pb_download.clicked.connect(self.button_download)
        self.tw.itemClicked.connect(self.remove_item)

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
            self.tw.takeTopLevelItem(self.tw.indexOfTopLevelItem(item))

    def button_path(self):
        path = qtw.QFileDialog.getExistingDirectory(
            self, "Select a folder", qtc.QDir.homePath(), qtw.QFileDialog.ShowDirsOnly
        )

        if path:
            self.le_path.setText(path)

    def button_add(self):
        missing = {}
        link = self.le_link.text()
        path = self.le_path.text()
        filename = self.le_filename.text()

        if not link:
            missing["Link"] = link
        if not self.fmt:
            missing["Format"] = self.fmt
        if "path" in self.preset and not path:
            missing["Path"] = path
        if "filename" in self.preset and not filename:
            missing["Filename"] = filename

        if not all(missing.values()):
            missing_fields = ", ".join(missing.keys())
            return qtw.QMessageBox.information(
                self,
                "Application Message",
                f"Required fields ({missing_fields}) are missing.",
            )

        item = qtw.QTreeWidgetItem(
            self.tw, [link, self.fmt, "-", "0%", "Queued", "-", "-"]
        )
        pb = qtw.QProgressBar()
        pb.setStyleSheet("QProgressBar { margin-bottom: 3px; }")
        pb.setTextVisible(False)
        self.tw.setItemWidget(item, 3, pb)
        [item.setTextAlignment(i, qtc.Qt.AlignCenter) for i in range(1, 6)]
        item.id = self.index
        self.le_link.clear()

        self.to_dl[self.index] = Worker(
            item,
            self.preset["args"],
            link,
            path,
            filename,
            self.fmt,
            self.dd_sponsorblock.currentText(),
            self.cb_metadata.isChecked(),
            self.cb_thumbnail.isChecked(),
            self.cb_subtitles.isChecked(),
        )
        logger.info(f"Queue download ({item.id}) added: {self.to_dl[self.index]}")
        self.index += 1

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

        self.dd_format.addItems(self.config["presets"].keys())
        self.dd_format.setCurrentIndex(self.config["general"]["format"])
        self.load_preset(self.dd_format.currentText())

    def save_preset(self):
        if "path" in self.preset:
            self.preset["path"] = self.le_path.text()
        if "sponsorblock" in self.preset:
            self.preset["sponsorblock"] = self.dd_sponsorblock.currentIndex()
        if "metadata" in self.preset:
            self.preset["metadata"] = self.cb_metadata.isChecked()
        if "subtitles" in self.preset:
            self.preset["subtitles"] = self.cb_subtitles.isChecked()
        if "thumbnail" in self.preset:
            self.preset["thumbnail"] = self.cb_thumbnail.isChecked()
        if "filename" in self.preset:
            self.preset["filename"] = self.le_filename.text()
        save_toml(root / "config.toml", self.config)

        qtw.QMessageBox.information(
            self,
            "Application Message",
            f"Preset for {self.fmt} saved successfully.",
        )

    def load_preset(self, fmt):
        preset = self.config["presets"].get(fmt)

        if not preset:
            self.le_path.clear()
            self.tb_path.setEnabled(False)
            self.dd_sponsorblock.setCurrentIndex(-1)
            self.dd_sponsorblock.setEnabled(False)
            self.cb_metadata.setChecked(False)
            self.cb_metadata.setEnabled(False)
            self.cb_subtitles.setChecked(False)
            self.cb_subtitles.setEnabled(False)
            self.cb_thumbnail.setChecked(False)
            self.cb_thumbnail.setEnabled(False)
            self.le_filename.clear()
            self.le_filename.setEnabled(False)
            self.le_link.setEnabled(False)
            self.gb_controls.setEnabled(False)
            return

        if not preset.get("args"):
            qtw.QMessageBox.critical(
                self,
                "Application Message",
                "The args key does not exist in the current preset and therefore it cannot be used.",
            )
            self.dd_format.setCurrentIndex(-1)
            return

        logger.debug(f"Changed format to {fmt} preset: {preset}")
        self.le_link.setEnabled(True)
        self.gb_controls.setEnabled(True)

        if "path" in preset:
            self.tb_path.setEnabled(True)
            self.le_path.setText(preset["path"])
        else:
            self.le_path.clear()
            self.tb_path.setEnabled(False)

        if "sponsorblock" in preset:
            self.dd_sponsorblock.setEnabled(True)
            self.dd_sponsorblock.setCurrentIndex(preset["sponsorblock"])
        else:
            self.dd_sponsorblock.setCurrentIndex(-1)
            self.dd_sponsorblock.setEnabled(False)

        if "metadata" in preset:
            self.cb_metadata.setEnabled(True)
            self.cb_metadata.setChecked(preset["metadata"])
        else:
            self.cb_metadata.setChecked(False)
            self.cb_metadata.setEnabled(False)

        if "subtitles" in preset:
            self.cb_subtitles.setEnabled(True)
            self.cb_subtitles.setChecked(preset["subtitles"])
        else:
            self.cb_subtitles.setChecked(False)
            self.cb_subtitles.setEnabled(False)

        if "thumbnail" in preset:
            self.cb_thumbnail.setEnabled(True)
            self.cb_thumbnail.setChecked(preset["thumbnail"])
        else:
            self.cb_thumbnail.setChecked(False)
            self.cb_thumbnail.setEnabled(False)

        if "filename" in preset:
            self.le_filename.setEnabled(True)
            self.le_filename.setText(preset["filename"])
        else:
            self.le_filename.clear()
            self.le_filename.setEnabled(False)

        self.preset = preset
        self.fmt = fmt

    def closeEvent(self, event):
        self.config["general"]["format"] = self.dd_format.currentIndex()
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


if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
