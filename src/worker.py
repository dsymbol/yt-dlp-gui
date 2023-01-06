import json
import subprocess
import sys
from dataclasses import dataclass

from PyQt5.QtCore import QObject, pyqtSignal

from logger import get_logger


@dataclass
class TreeDex:
    TITLE: int = 0
    FORMAT: int = 1
    SIZE: int = 2
    PROGRESS: int = 3
    STATUS: int = 4
    SPEED: int = 5
    ETA: int = 6


class Worker(QObject):
    progress = pyqtSignal(object, int, str)
    finished = pyqtSignal()

    def __init__(self, tree_item, link, folder, video_fmt, metadata, thumbnail, subtitles, num):
        super().__init__()
        self.tree_item = tree_item
        self.link = link
        self.folder = folder
        self.video_fmt = video_fmt
        self.metadata = metadata
        self.thumbnail = thumbnail
        self.subtitles = subtitles
        self.log = get_logger(f"Worker {num}")

    def get_args(self):
        args = ['yt-dlp', '--newline', '-i', '--ignore-config', '--hls-prefer-native', '--print-json']
        if self.video_fmt == "best":
            args.extend(['-o', f'{self.folder}/%(title)s.%(ext)s', self.link])
        elif self.video_fmt == "mp4":
            args.extend(['-o', f'{self.folder}/%(title)s.%(ext)s', '-S', 'ext:mp4:m4a', self.link])
        elif self.video_fmt == "mp3":
            args.extend(
                ['-o', f'{self.folder}/%(title)s.%(ext)s', '-x', '--audio-format', 'mp3', '--audio-quality', '0',
                 self.link])

        if self.metadata > 0:
            args.append('--embed-metadata')
        if self.thumbnail > 0:
            args.append('--embed-thumbnail')
        if self.subtitles > 0:
            args.append('--write-auto-subs')
        return args

    def run(self):
        create_window = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0

        args = self.get_args()
        err = False

        with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              universal_newlines=True, creationflags=create_window) as p:
            for line in p.stdout:
                if line.startswith('{'):
                    info_dict = json.loads(line)
                    self.log.info(f"`{info_dict['title']}` download started: " + " ".join(args))
                    self.progress.emit(self.tree_item, TreeDex.TITLE, info_dict['title'])

                elif "[youtube]" in line:
                    self.progress.emit(self.tree_item, TreeDex.STATUS, "Processing")

                elif "[download]" in line and "100%" not in line and "ETA" in line:
                    self.progress.emit(self.tree_item, TreeDex.STATUS, "Downloading")
                    data = line.split()
                    self.progress.emit(self.tree_item, TreeDex.SIZE, data[3])
                    self.progress.emit(self.tree_item, TreeDex.PROGRESS, data[1])
                    self.progress.emit(self.tree_item, TreeDex.ETA, data[7])
                    self.progress.emit(self.tree_item, TreeDex.SPEED, data[5])

                elif "[Merger]" in line or "[ExtractAudio]" in line:
                    self.progress.emit(self.tree_item, TreeDex.STATUS, "Converting")

                if "error" in line.lower() and "warning" not in line.lower():
                    err = True
                    self.log.error(line)
                    self.progress.emit(self.tree_item, TreeDex.SIZE, "ERROR")
                    self.progress.emit(self.tree_item, TreeDex.PROGRESS, "ERROR")
                    self.progress.emit(self.tree_item, TreeDex.STATUS, "ERROR")
                    self.progress.emit(self.tree_item, TreeDex.SPEED, "ERROR")

            if not err:
                self.progress.emit(self.tree_item, TreeDex.PROGRESS, "100%")
                self.progress.emit(self.tree_item, TreeDex.STATUS, "Finished")
            self.finished.emit()
