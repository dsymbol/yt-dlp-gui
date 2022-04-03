from PyQt5 import QtWidgets, QtCore
from utils.logger import log
import subprocess
import os

class WorkerThread(QtCore.QObject):
    update_progress = QtCore.pyqtSignal(object, int, str, int)
    
    def __init__(self, entry, worker_num):
        super().__init__()
        self.entry = entry
        self.worker_num = worker_num

    def get_args(self):
        if self.entry[3] == "best":
            ytdlp_args = ['yt-dlp', '--newline', '-i', '-o', f'{self.entry[2]}/%(title)s.%(ext)s', '--ignore-config', '--hls-prefer-native', self.entry[1]]
        elif self.entry[3] == "mp4":
            ytdlp_args = ['yt-dlp', '--newline', '-i', '-o', f'{self.entry[2]}/%(title)s.%(ext)s', '-f mp4', '--ignore-config', '--hls-prefer-native', self.entry[1]]
        elif self.entry[3] == "mp3":
            ytdlp_args = ['yt-dlp', '--newline', '-i', '-o', f'{self.entry[2]}/%(title)s.%(ext)s', '-x', '--audio-format',
                          'mp3', '--ignore-config', '--hls-prefer-native', self.entry[1]]        
        if self.entry[4] > 0:
            ytdlp_args.insert(len(ytdlp_args)-1, '--embed-metadata')
        if self.entry[5] > 0:
            ytdlp_args.insert(len(ytdlp_args)-1, '--embed-thumbnail')
        if self.entry[6] > 0:
            ytdlp_args.insert(len(ytdlp_args)-1, '--write-auto-subs')
        return ytdlp_args
    
    @QtCore.pyqtSlot()
    def run(self):
        with subprocess.Popen(self.get_args(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True) as p:
            for line in p.stdout:
                if "[youtube]" in line:
                    self.update_progress.emit(self.entry[0], 4, "Processing", self.worker_num)
                elif "[download]" in line and "Destination" in line:
                    title = line.replace("[download] Destination: ", "")
                    title = os.path.split(title)[1]
                    title = os.path.splitext(title)[0]
                    self.update_progress.emit(self.entry[0], 0, title, self.worker_num)
                elif "[download]" in line and "100%" not in line and "ETA" in line:
                    self.update_progress.emit(self.entry[0], 4, "Downloading", self.worker_num)
                    line_split = line.split()
                    self.update_progress.emit(self.entry[0], 2, line_split[3], self.worker_num)
                    self.update_progress.emit(self.entry[0], 3, line_split[1], self.worker_num)
                    self.update_progress.emit(self.entry[0], 6, line_split[7], self.worker_num)
                    self.update_progress.emit(self.entry[0], 5, line_split[5], self.worker_num)
                elif "[download]" in line and "100%" in line and "ETA" not in line:
                    self.update_progress.emit(self.entry[0], 3, "100%", self.worker_num)
                    self.update_progress.emit(self.entry[0], 4, "Finished", self.worker_num) 
                    
                if "error" in line.lower():
                    log.error(line)
                    self.update_progress.emit(self.entry[0], 2, "ERROR", self.worker_num)
                    self.update_progress.emit(self.entry[0], 3, "ERROR", self.worker_num) 
                    self.update_progress.emit(self.entry[0], 4, "ERROR", self.worker_num) 
                    self.update_progress.emit(self.entry[0], 5, "ERROR", self.worker_num) 
                    