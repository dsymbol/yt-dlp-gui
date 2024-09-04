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

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s (%(module)s:%(lineno)d) %(message)s",
    handlers=[
        logging.FileHandler(ROOT / "debug.log", encoding="utf-8", delay=True),
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
        self.config = self.load_config()
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
                logger.debug(
                    f"Removing queued download ({item.id}): `{item.text(0)}`"
                )
                self.to_dl.pop(item.id)
            elif worker := self.worker.get(item.id):
                logger.info(
                    f"Stopping and removing download ({item.id}): `{item.text(0)}`"
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
        if fmt in ("mp4", "best"):
            self.cb_subtitles.setEnabled(True)
            self.cb_thumbnail.setEnabled(True)
        else:
            self.cb_subtitles.setEnabled(False)
            if fmt in ("mp3", "flac"):
                self.cb_thumbnail.setEnabled(True)
            else:
                self.cb_thumbnail.setEnabled(False)

    def button_add(self):
        link = self.le_link.text()
        path = self.le_path.text()
        fmt = self.dd_format.currentText()

        if not all([link, path, fmt]):
            return qtw.QMessageBox.information(
                self,
                "Application Message",
                "Unable to add the download because some required fields are missing.\nRequired fields: Link, Path & Format.",
            )

        item = qtw.QTreeWidgetItem(self.tw, [link, fmt, "-", "0%", "Queued", "-", "-"])
        pb = qtw.QProgressBar()
        pb.setStyleSheet("QProgressBar { margin-bottom: 3px; }")
        pb.setTextVisible(False)
        self.tw.setItemWidget(item, 3, pb)
        [item.setTextAlignment(i, qtc.Qt.AlignCenter) for i in range(1, 6)]
        item.id = self.index
        self.le_link.clear()
        self.to_dl[self.index] = Worker(
            item,
            link,
            path + "/" + (self.le_filename.text() or "%(title)s.%(ext)s"),
            fmt,
            self.le_cargs.text(),
            self.dd_sponsorblock.currentText(),
            self.cb_metadata.isEnabled() and self.cb_metadata.isChecked(),
            self.cb_thumbnail.isEnabled() and self.cb_thumbnail.isChecked(),
            self.cb_subtitles.isEnabled() and self.cb_subtitles.isChecked(),
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
        d = {
            "path": "",
            "format": 0,
            "sponsorblock": 0,
            "metadata": False,
            "subtitles": False,
            "thumbnail": False,
            "custom_args": "",
        }
        config = load_json(ROOT / "config.json", d)

        self.le_path.setText(config["path"])
        self.dd_format.setCurrentIndex(config["format"])
        self.dd_sponsorblock.setCurrentIndex(config["sponsorblock"])
        self.cb_metadata.setChecked(config["metadata"])
        self.cb_subtitles.setChecked(config["subtitles"])
        self.cb_thumbnail.setChecked(config["thumbnail"])
        self.le_cargs.setText(config["custom_args"])

        return config

    def closeEvent(self, event):
        self.config["path"] = self.le_path.text()
        self.config["format"] = self.dd_format.currentIndex()
        self.config["sponsorblock"] = self.dd_sponsorblock.currentIndex()
        self.config["metadata"] = self.cb_metadata.isChecked()
        self.config["subtitles"] = self.cb_subtitles.isChecked()
        self.config["thumbnail"] = self.cb_thumbnail.isChecked()
        self.config["custom_args"] = self.le_cargs.text()
        save_json(ROOT / "config.json", self.config)
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
