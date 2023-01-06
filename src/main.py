import json
import os
import shutil
import sys
import traceback

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMessageBox

from gui import Ui_ytdlpgui
from logger import get_logger
from worker import Worker

os.environ["PROJECT_PATH"] = os.path.dirname(__file__)
os.environ['PATH'] += os.pathsep + os.path.join(os.environ["PROJECT_PATH"], "bin")


class Main(QtWidgets.QMainWindow, Ui_ytdlpgui):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)
        self.log = get_logger("Main")
        self.check_bin()
        self.to_download = []
        self.worker = {}
        self.thread = {}
        self.twi = 0

    def closeEvent(self, event):
        settings = {
            "path": self.folderpath.text(),
            "geo_x": self.geometry().x(),
            "geo_y": self.geometry().y(),
            "format": self.cb_format.currentIndex(),
            "metadata": self.cb_meta.checkState(),
            "subtitles": self.cb_subs.checkState(),
            "thumbnail": self.cb_thumb.checkState()
        }
        with open(os.path.join(os.environ.get("PROJECT_PATH"), 'settings.json'), 'w') as f:
            json.dump(settings, f, indent=4)
        self.log.info(f"Saved settings: {settings}")
        event.accept()

    def get_folder_path(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Open Directory", QtCore.QDir.homePath(),
                                                          QtWidgets.QFileDialog.ShowDirsOnly)
        if path:
            self.folderpath.setText(path)

    def index_changed(self, fmt):
        if fmt == "mp3":
            self.cb_subs.setEnabled(False)
        elif fmt == "mp4" or fmt == "best":
            self.cb_subs.setEnabled(True)

    def add_download(self):
        link, folder, video_fmt, metadata, thumbnail, subtitles = (
            self.link_entry.text(),
            self.folderpath.text(),
            self.cb_format.currentText(),
            self.cb_meta.checkState(),
            self.cb_thumb.checkState(),
            self.cb_subs.checkState()
        )
        if link and folder and video_fmt:
            tree_item = QtWidgets.QTreeWidgetItem(self.treew, [link, video_fmt, '-', '0%', 'Queued', '-', '-', link])
            [tree_item.setTextAlignment(i, QtCore.Qt.AlignCenter) for i in range(1, 6)]
            self.link_entry.setText("")
            self.to_download.append([tree_item, link, folder, video_fmt, metadata, thumbnail, subtitles])
            self.log.info(f'Added download to list: {link} as {video_fmt} to the `{folder}` directory.')
        else:
            self.show_error_box("Unable to add the download because some required fields are missing. "
                                "Please ensure that all necessary fields have been filled out and try again.")

    def clear_list(self):
        for w in self.thread.values():
            try:
                w.isFinished()
                return self.show_error_box("Unable to clear list because there are active downloads in progress.")
            except RuntimeError:
                continue

        self.treew.clear()
        self.to_download, self.worker, self.thread = [], {}, {}

    def download_list(self):
        if not self.to_download:
            return self.show_error_box("Unable to perform the requested action because there are no links in the list. "
                                       "Please add some downloads before trying again")

        for download in self.to_download:
            self.thread[self.twi] = QtCore.QThread()
            self.worker[self.twi] = Worker(*download, self.twi)
            self.worker[self.twi].moveToThread(self.thread[self.twi])
            self.thread[self.twi].started.connect(self.worker[self.twi].run)
            self.worker[self.twi].finished.connect(self.thread[self.twi].quit)
            self.worker[self.twi].finished.connect(self.worker[self.twi].deleteLater)
            self.thread[self.twi].finished.connect(self.thread[self.twi].deleteLater)
            self.worker[self.twi].progress.connect(self.update_tree)
            self.thread[self.twi].start()
            self.twi += 1

        self.to_download = []

    def show_error_box(self, text, icon="Critical"):
        self.log.error(text)
        qmb = QMessageBox(self)
        qmb.setText(text)
        qmb.setWindowTitle('Error: yt-dlp-gui')
        if icon == "NoIcon":
            qmb.setIcon(QMessageBox.NoIcon)
        if icon == "Information":
            qmb.setIcon(QMessageBox.Information)
        if icon == "Warning":
            qmb.setIcon(QMessageBox.Warning)
        if icon == "Critical":
            qmb.setIcon(QMessageBox.Critical)
        if icon == "Question":
            qmb.setIcon(QMessageBox.Question)
        qmb.setDetailedText("An error occurred while processing your request. Please check your input and try again.")
        qmb.setStandardButtons(QMessageBox.Ok)
        qmb.exec_()

    def check_bin(self):
        progs = {'yt-dlp': None, 'ffmpeg': None, 'ffprobe': None}
        status = {k: shutil.which(k) for k, v in progs.items()}
        if not all(status.values()):
            missing = " ".join([k for k, v in status.items() if not v])
            sys.exit(self.show_error_box(f"Unable to proceed because required dependencies `{missing}` are missing. "
                                         f"Please install the missing dependencies and try again."))

    def excepthook(self, exc_type, exc_value, exc_tb):
        tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        self.log.error(tb)
        QtWidgets.QApplication.quit()

    @staticmethod
    def update_tree(item, index, update):
        item.setText(index, update)


if __name__ == "__main__":
    sys.excepthook = Main.excepthook
    app = QtWidgets.QApplication(sys.argv)
    window = Main()
    window.show()
    sys.exit(app.exec_())
