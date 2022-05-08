import os
import subprocess
import sys

from PyQt5 import QtCore

from utils.logger import mk_logger


class WorkerThread(QtCore.QObject):
    update_progress = QtCore.pyqtSignal(object, int, str)

    def __init__(self, entry):
        super().__init__()
        self.entry = entry
        self.log = mk_logger("worker_log")

    def get_args(self):
        if self.entry[3] == "best":
            ytdlp_args = ['yt-dlp', '--newline', '-i', '-o', f'{self.entry[2]}/%(title)s.%(ext)s', '--ignore-config',
                          '--hls-prefer-native', self.entry[1]]
        elif self.entry[3] == "mp4":
            ytdlp_args = ['yt-dlp', '--newline', '-i', '-o', f'{self.entry[2]}/%(title)s.%(ext)s', '-f mp4',
                          '--ignore-config', '--hls-prefer-native', self.entry[1]]
        elif self.entry[3] == "mp3":
            ytdlp_args = ['yt-dlp', '--newline', '-i', '-o', f'{self.entry[2]}/%(title)s.%(ext)s', '-x',
                          '--audio-format',
                          'mp3', '--ignore-config', '--hls-prefer-native', self.entry[1]]
        if self.entry[4] > 0:
            ytdlp_args.insert(len(ytdlp_args) - 1, '--embed-metadata')
        if self.entry[5] > 0:
            ytdlp_args.insert(len(ytdlp_args) - 1, '--embed-thumbnail')
        if self.entry[6] > 0:
            ytdlp_args.insert(len(ytdlp_args) - 1, '--write-auto-subs')
        return ytdlp_args

    @QtCore.pyqtSlot()
    def run(self):
        create_window = 0
        if sys.platform == 'win32':
            create_window = subprocess.CREATE_NO_WINDOW
        with subprocess.Popen(self.get_args(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              universal_newlines=True, creationflags=create_window) as p:
            for line in p.stdout:
                if "[youtube]" in line:
                    self.update_progress.emit(self.entry[0], 4, "Processing")
                elif "[download]" in line and "Destination" in line:
                    title = line.replace("[download] Destination: ", "")
                    title = os.path.split(title)[1]
                    title = os.path.splitext(title)[0]
                    self.update_progress.emit(self.entry[0], 0, title)
                elif "[download]" in line and "100%" not in line and "ETA" in line:
                    self.update_progress.emit(self.entry[0], 4, "Downloading")
                    line_split = line.split()
                    self.update_progress.emit(self.entry[0], 2, line_split[3])
                    self.update_progress.emit(self.entry[0], 3, line_split[1])
                    self.update_progress.emit(self.entry[0], 6, line_split[7])
                    self.update_progress.emit(self.entry[0], 5, line_split[5])

                if "error" in line.lower() and "warning" not in line.lower():
                    err = True
                    self.log.error(line)
                    self.update_progress.emit(self.entry[0], 2, "ERROR")
                    self.update_progress.emit(self.entry[0], 3, "ERROR")
                    self.update_progress.emit(self.entry[0], 4, "ERROR")
                    self.update_progress.emit(self.entry[0], 5, "ERROR")
                else:
                    err = False

            if not err:
                self.update_progress.emit(self.entry[0], 3, "100%")
                self.update_progress.emit(self.entry[0], 4, "Finished")
