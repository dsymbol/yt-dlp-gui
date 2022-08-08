import json
import os
import sys
import traceback
from pathlib import Path

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMessageBox

from gui import Ui_ytdlpgui
from logger import get_logger
from worker import WorkerThread


class Main(QtWidgets.QMainWindow, Ui_ytdlpgui):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)
        self.to_download = []

    def closeEvent(self, event):
        self.quit_threads()
        config = {
            "path": self.folderpath.text(),
            "geo_x": self.geometry().x(),
            "geo_y": self.geometry().y(),
            "format": self.cb_format.currentIndex(),
            "metadata": self.cb_meta.checkState(),
            "subtitles": self.cb_subs.checkState(),
            "thumbnail": self.cb_thumb.checkState()
        }
        with open(os.path.join(os.environ.get("PROJECT_PATH"), 'config.json'), 'w') as f:
            json.dump(config, f, indent=4)
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

    def add_btn(self):
        link, folder, video_fmt, metadata, thumbnail, subtitles = (
            self.link_entry.text(),
            self.folderpath.text(),
            self.cb_format.currentText(),
            self.cb_meta.checkState(),
            self.cb_thumb.checkState(),
            self.cb_subs.checkState()
        )
        if link and folder and video_fmt:
            item = QtWidgets.QTreeWidgetItem(self.treew, [link, video_fmt, '-', '0%', 'Queued', '-', '-', link])
            [item.setTextAlignment(i, QtCore.Qt.AlignCenter) for i in range(1, 6)]
            self.link_entry.setText("")
            self.to_download.append([item, link, folder, video_fmt, metadata, thumbnail, subtitles, link])
        else:
            self.error_box("Missing fields")

    def quit_threads(self):
        if hasattr(self, 'worker_thread'):
            for i in self.worker_thread.values():
                i.quit()
            del self.worker_thread

    def clear_btn(self):
        self.quit_threads()
        self.treew.clear()
        self.to_download = []

    def dl_btn(self):
        if hasattr(self, 'worker_thread'):
            self.error_box("Clear entries to download")
            return
        elif not self.treew.topLevelItemCount():
            self.error_box("No entries, add some.")
            return
        self.worker = {}
        self.worker_thread = {}
        if self.to_download:
            for i, entry in enumerate(self.to_download):
                self.worker[i] = WorkerThread(entry)
                self.worker_thread[i] = QtCore.QThread(parent=self)
                self.worker_thread[i].started.connect(self.worker[i].run)
                self.worker[i].update_progress.connect(self.update_tree)
                self.worker[i].moveToThread(self.worker_thread[i])
                self.worker_thread[i].start()

    def error_box(self, message):
        QMessageBox.critical(self, "yt-dlp-gui", message, defaultButton=QMessageBox.Ok)

    def excepthook(self, exc_type, exc_value, exc_tb):
        tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        if "No such file or directory: 'yt-dlp'" in str(tb):
            self.error_box("yt-dlp executable not found")
        log.error(tb)
        QtWidgets.QApplication.quit()

    @staticmethod
    def update_tree(entry, index, update):
        entry.setText(index, update)


if __name__ == "__main__":
    os.environ["PROJECT_PATH"] = str(Path(__file__).parent)
    os.environ['PATH'] += os.pathsep + os.path.join(os.environ.get("PROJECT_PATH"), "bin")
    log = get_logger("gui_logger")
    sys.excepthook = Main.excepthook
    app = QtWidgets.QApplication(sys.argv)
    window = Main()
    window.show()
    sys.exit(app.exec_())
