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

        self.dl_list = []
        self.worker = {}
        self.wi = 0

        self.tb_path.clicked.connect(self.button_path)
        self.dd_format.currentTextChanged.connect(self.format_change)
        self.pb_add.clicked.connect(self.button_add)
        self.pb_clear.clicked.connect(self.button_clear)
        self.pb_download.clicked.connect(self.button_download)

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
            self.le_link.setText("")
            self.le_cargs.setText("")
            self.dl_list += [[item, link, path, format_, cargs, metadata, thumbnail, subtitles]]
            log.info(f'Added download to list: {link} as {format_} to the `{path}` directory.')
        else:
            self.error_box("Unable to add the download because some required fields are missing.")

    def button_clear(self):
        for w in self.worker.values():
            try:
                w.isFinished()
                return self.error_box("Unable to clear list because there are active downloads in progress.")
            except RuntimeError:
                continue

        self.worker = {}
        self.dl_list = []
        self.tw.clear()

    def button_download(self):
        if not self.dl_list:
            return self.error_box("Unable to download because there are no links in the list.")

        for dl in self.dl_list:
            self.worker[self.wi] = Worker(*dl)
            self.worker[self.wi].finished.connect(self.worker[self.wi].deleteLater)
            self.worker[self.wi].progress.connect(self.update_progress)
            self.worker[self.wi].start()
            self.wi += 1

        self.dl_list = []

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

    def error_box(self, text, icon="Critical"):
        log.error(text)
        qmb = qtw.QMessageBox(self)
        qmb.setText(text)
        qmb.setWindowTitle('Application Error')
        if icon == "NoIcon":
            qmb.setIcon(qtw.QMessageBox.NoIcon)
        if icon == "Information":
            qmb.setIcon(qtw.QMessageBox.Information)
        if icon == "Warning":
            qmb.setIcon(qtw.QMessageBox.Warning)
        if icon == "Critical":
            qmb.setIcon(qtw.QMessageBox.Critical)
        if icon == "Question":
            qmb.setIcon(qtw.QMessageBox.Question)
        qmb.setDetailedText("An error occurred while processing your request. Please check your input and try again.")
        qmb.setStandardButtons(qtw.QMessageBox.Ok)
        qmb.exec()

    @staticmethod
    def update_progress(item, emit_data):
        for data in emit_data:
            index, update = data
            item.setText(index, update)


if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
