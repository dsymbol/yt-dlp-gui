import json
import logging
import os
import sys
from pathlib import Path

from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw

from dep_dl import DownloaderUi
from utils import init_logger
from ui.app_ui import Ui_mw_Main
from worker import Worker

os.environ['PATH'] += os.pathsep + os.path.join(os.path.dirname(__file__), "bin")

init_logger(Path(__file__).parent / 'debug.log')
log = logging.getLogger(__name__)


class MainWindow(qtw.QMainWindow, Ui_mw_Main):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.tw.setColumnWidth(0, 200)
        self.le_link.setFocus()
        self.conf()
        self.format_change(self.dd_format.currentText())

        self.form = DownloaderUi()
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
            'Application Message',
            f"Would you like to remove {item.text(0)} ?",
            qtw.QMessageBox.Yes | qtw.QMessageBox.No,
            qtw.QMessageBox.No
        )
        if ret == qtw.QMessageBox.Yes:
            if self.to_dl.get(item.id):
                log.info(f"Removing queued {item.text(0)} download with id {item.id} ")
                self.to_dl.pop(item.id)
            elif worker := self.worker.get(item.id):
                log.info(f"Stopping and removing {item.text(0)} download with id {item.id}")
                worker.stop()
            self.tw.takeTopLevelItem(self.tw.indexOfTopLevelItem(item))

    def button_path(self):
        path = qtw.QFileDialog.getExistingDirectory(self, "Select a folder", qtc.QDir.homePath(),
                                                    qtw.QFileDialog.ShowDirsOnly)

        if path:
            self.le_path.setText(path)

    def format_change(self, fmt):
        if fmt == "mp3":
            self.cb_subtitles.setEnabled(False)
            self.cb_subtitles.setChecked(False)
        elif fmt == "mp4":
            self.cb_subtitles.setEnabled(True)

    def button_add(self):
        link, path, format_, cargs, metadata, thumbnail, subtitles = [
            self.le_link.text(),
            self.le_path.text(),
            self.dd_format.currentText(),
            self.le_cargs.text(),
            self.cb_metadata.isChecked(),
            self.cb_thumbnail.isChecked(),
            self.cb_subtitles.isChecked()
        ]

        if link and path and format_:
            item = qtw.QTreeWidgetItem(self.tw, [link, format_, '-', '0%', 'Queued', '-', '-'])
            [item.setTextAlignment(i, qtc.Qt.AlignCenter) for i in range(1, 6)]
            item.id = self.index
            self.le_link.setText("")
            self.le_cargs.setText("")
            self.to_dl[self.index] = [item, link, path, format_, cargs, metadata, thumbnail, subtitles]
            self.index += 1
            log.info(f'Added download to list: {link} as {format_} to the `{path}` directory.')
        else:
            qtw.QMessageBox.information(
                self,
                'Application Message',
                "Unable to add the download because some required fields are missing."
            )

    def button_clear(self):
        if self.worker:
            return qtw.QMessageBox.critical(
                self,
                'Application Message',
                "Unable to clear list because there are active downloads in progress.\n"
                "Remove a download by clicking on it."
            )

        self.worker = {}
        self.to_dl = {}
        self.tw.clear()

    def button_download(self):
        if not self.to_dl:
            return qtw.QMessageBox.information(
                self,
                'Application Message',
                "Unable to download because there are no links in the list."
            )

        for k, v in self.to_dl.items():
            self.worker[k] = Worker(*v)
            self.worker[k].finished.connect(self.worker[k].deleteLater)
            self.worker[k].finished.connect(lambda x: self.worker.pop(x))
            self.worker[k].progress.connect(self.update_progress)
            self.worker[k].start()

        self.to_dl = {}

    def conf(self):
        file = Path(__file__).parent / 'conf.json'

        try:
            with open(file, 'r') as f:
                settings = json.load(f)
        except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
            log.exception(e)
            with open(file, 'w') as f:
                settings = {
                    "path": "",
                    "format": 0,
                    "metadata": False,
                    "subtitles": False,
                    "thumbnail": False
                }
                json.dump(settings, f, indent=4)

        self.le_path.setText(settings["path"])
        self.dd_format.setCurrentIndex(settings["format"])
        self.cb_metadata.setChecked(settings["metadata"])
        self.cb_subtitles.setChecked(settings["subtitles"])
        self.cb_thumbnail.setChecked(settings["thumbnail"])

    def closeEvent(self, event):
        settings = {
            "path": self.le_path.text(),
            "format": self.dd_format.currentIndex(),
            "metadata": self.cb_metadata.isChecked(),
            "subtitles": self.cb_subtitles.isChecked(),
            "thumbnail": self.cb_thumbnail.isChecked()
        }
        with open(Path(__file__).parent / 'conf.json', 'w') as f:
            json.dump(settings, f, indent=4)
        event.accept()

    @staticmethod
    def update_progress(item, emit_data):
        for data in emit_data:
            index, update = data
            item.setText(index, update)


if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
