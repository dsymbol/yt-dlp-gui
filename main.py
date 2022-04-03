from PyQt5 import QtCore, QtGui, QtWidgets
from utils.worker import WorkerThread
from ui import Ui_ytdlpgui
import subprocess
import json
import sys
import os

class Main(QtWidgets.QMainWindow, Ui_ytdlpgui):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)
        self.to_download = []
        
    def closeEvent(self, event):
        config = {"path": self.folderpath.text(), "geo_x": self.geometry().x(), "geo_y": self.geometry().y(),
                  "format": self.cb_format.currentIndex(), "metadata": self.cb_meta.checkState(), 
                  "subtitles": self.cb_subs.checkState(), "thumbnail": self.cb_thumb.checkState()}
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        event.accept()
    
    def get_folder_path(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Open Directory", QtCore.QDir.homePath(), QtWidgets.QFileDialog.ShowDirsOnly)
        if not path:
            return
        self.folderpath.setText(path)
        
    def index_changed(self, s):
        if s == "mp3":
            self.cb_subs.setEnabled(False)
        elif s == "mp4" or  s == "best":
            self.cb_subs.setEnabled(True)
        
    def add_btn(self):
        link, folder, vformat, metadata, thumbnail, subtitles =  (self.link_entry.text() ,self.folderpath.text(), 
                                                                self.cb_format.currentText(), self.cb_meta.checkState(), 
                                                                self.cb_thumb.checkState(), self.cb_subs.checkState())
        if link and folder and vformat:
            self.item = QtWidgets.QTreeWidgetItem(self.treew, [link, vformat, '-', '0%', 'Queued', '-', '-'])
            self.item.setTextAlignment(1, QtCore.Qt.AlignCenter)
            self.item.setTextAlignment(2, QtCore.Qt.AlignCenter)
            self.item.setTextAlignment(3, QtCore.Qt.AlignCenter)
            self.item.setTextAlignment(4, QtCore.Qt.AlignCenter)
            self.item.setTextAlignment(5, QtCore.Qt.AlignCenter)
            self.item.setTextAlignment(6, QtCore.Qt.AlignCenter)
            self.link_entry.setText("")
            self.to_download.append([self.item, link, folder, vformat, metadata, thumbnail, subtitles])
        else:
            Main.error_box("Missing fields")
        
    def clear_btn(self):
        self.treew.clear()
        self.to_download = []
        try:
            for i in self.workerThread.values():
                i.terminate()
            del self.workerThread
        except AttributeError:
            pass
        
    def dl_btn(self):
        try:
            if self.workerThread.values():
                Main.error_box("Clear entries to download")
                return
        except AttributeError:
            if not self.treew.topLevelItemCount():
                Main.error_box("No entries, add some.")
                return
            try:
                subprocess.Popen(['yt-dlp'], creationflags = 0x08000000)
            except FileNotFoundError:
                Main.error_box("Missing yt-dlp binary.")
                return
            self.worker = {}
            self.workerThread = {}
            self.worker_= {}
            if self.to_download:
                for i, entry in enumerate(self.to_download):
                    self.worker[i] = WorkerThread(entry, i)
                    self.workerThread[i] = QtCore.QThread()
                    self.workerThread[i].started.connect(self.worker[i].run)
                    self.worker[i].update_progress.connect(self.update_tree)
                    self.worker[i].moveToThread(self.workerThread[i])
                    self.workerThread[i].start()
    
    def update_tree(self, obj, index, update, worker_num):
        self.worker_[worker_num] = obj
        self.worker_[worker_num].setText(index, update)
        
    @staticmethod 
    def error_box(message):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setText('Error')
        msg.setInformativeText(message)
        msg.setWindowTitle("yt-dlp-gui")
        msg.exec_()
        
if __name__ == "__main__":
    os.environ['PATH'] += os.pathsep + Ui_ytdlpgui.absolute_path("bin")
    app = QtWidgets.QApplication(sys.argv)
    window = Main()
    window.show()
    sys.exit(app.exec_())