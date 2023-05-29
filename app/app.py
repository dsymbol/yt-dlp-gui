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
from version import __version__

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
        self.statusBar.showMessage(f"Version {__version__}")

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
        if fmt == 'mp4':
            self.cb_subtitles.setEnabled(True)
            self.cb_thumbnail.setEnabled(True)
        else:
            if fmt in ['mp3', 'flac']:
                self.cb_thumbnail.setEnabled(True)
            else:
                self.cb_thumbnail.setEnabled(False)
                self.cb_thumbnail.setChecked(False)
            self.cb_subtitles.setEnabled(False)
            self.cb_subtitles.setChecked(False)

    def button_add(self):
        link, path, format_, cargs, filename, sponsorblock, metadata, thumbnail, subtitles = [
            self.le_link.text(),
            self.le_path.text(),
            self.dd_format.currentText(),
            self.le_cargs.text(),
            self.le_filename.text(),
            self.dd_sponsorblock.currentText(),
            self.cb_metadata.isChecked(),
            self.cb_thumbnail.isChecked(),
            self.cb_subtitles.isChecked()
        ]

        if not all([link, path, format_]):
            return qtw.QMessageBox.information(
                self,
                'Application Message',
                "Unable to add the download because some required fields are missing.\nRequired fields: Link, Path & Format."
            )

        item = qtw.QTreeWidgetItem(self.tw, [link, format_, '-', '0%', 'Queued', '-', '-'])
        pb = qtw.QProgressBar()
        pb.setStyleSheet("QProgressBar { margin-bottom: 3px; }")
        pb.setTextVisible(False)
        pb.setValue(0)
        pb.setRange(0, 100)
        self.tw.setItemWidget(item, 3, pb)
        [item.setTextAlignment(i, qtc.Qt.AlignCenter) for i in range(1, 6)]
        item.id = self.index
        filename = filename if filename else "%(title)s.%(ext)s"
        self.le_link.clear()
        self.to_dl[self.index] = [item, link, path, format_, cargs, filename, sponsorblock, metadata, thumbnail, subtitles]
        self.index += 1
        log.info(f'Queued download added: (link={link}, path={path}, format={format_}, cargs={cargs}, '
                 f'filename={filename}, sponsorblock={sponsorblock}, metadata={metadata}, thumbnail={thumbnail}, '
                 f'subtitles={subtitles})')

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
                    "sponsorblock": 0,
                    "metadata": False,
                    "subtitles": False,
                    "thumbnail": False
                }
                json.dump(settings, f, indent=4)

        self.le_path.setText(settings["path"])
        self.dd_format.setCurrentIndex(settings["format"])
        self.dd_sponsorblock.setCurrentIndex(settings["sponsorblock"])
        self.cb_metadata.setChecked(settings["metadata"])
        self.cb_subtitles.setChecked(settings["subtitles"])
        self.cb_thumbnail.setChecked(settings["thumbnail"])

    def closeEvent(self, event):
        settings = {
            "path": self.le_path.text(),
            "format": self.dd_format.currentIndex(),
            "sponsorblock": self.dd_sponsorblock.currentIndex(),
            "metadata": self.cb_metadata.isChecked(),
            "subtitles": self.cb_subtitles.isChecked(),
            "thumbnail": self.cb_thumbnail.isChecked()
        }
        with open(Path(__file__).parent / 'conf.json', 'w') as f:
            json.dump(settings, f, indent=4)
        event.accept()

    def update_progress(self, item, emit_data):
        try:
            for data in emit_data:
                index, update = data
                if index != 3:
                    item.setText(index, update)
                else:
                    pb = self.tw.itemWidget(item, index)
                    pb.setValue(round(float(update.replace('%',''))))
        except AttributeError:
            log.info(f'Item {item.id} no longer exists')


if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
