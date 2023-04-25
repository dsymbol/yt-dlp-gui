import json
import logging
import subprocess as sp
import sys
from dataclasses import dataclass

import PySide6.QtCore as qtc
from psutil import Process

log = logging.getLogger(__name__)


@dataclass
class TreeDex:
    TITLE: int = 0
    FORMAT: int = 1
    SIZE: int = 2
    PROGRESS: int = 3
    STATUS: int = 4
    SPEED: int = 5
    ETA: int = 6


class Worker(qtc.QThread):
    finished = qtc.Signal(int)
    progress = qtc.Signal(object, list)

    def __init__(self, item, link, path, format_, cargs, metadata, thumbnail, subtitles):
        super().__init__()
        self.item = item
        self.link = link
        self.path = path
        self.format_ = format_
        self.cargs = cargs
        self.metadata = metadata
        self.thumbnail = thumbnail
        self.subtitles = subtitles

        self.mutex = qtc.QMutex()
        self._stop = False

    def build_command(self):
        args = [
            'yt-dlp', '--newline', '--ignore-errors', '--ignore-config', '--hls-prefer-native', '--no-simulate',
            '--progress', '--progress-template', '%(progress.status)s %(progress._total_bytes_estimate_str)s '
            '%(progress._percent_str)s %(progress._speed_str)s %(progress._eta_str)s', '--dump-json', '-v'
        ]
        if self.format_ == "mp4":
            args += ['-o', f'{self.path}/%(title)s.%(ext)s', '--format-sort', 'ext:mp4:m4a', self.link]
        elif self.format_ == "mp3":
            args += ['-o', f'{self.path}/%(title)s.%(ext)s', '--extract-audio', '--audio-format', 'mp3',
                     '--audio-quality', '0', self.link]

        if self.cargs:
            args += self.cargs.split()
        if self.metadata:
            args += ['--embed-metadata']
        if self.thumbnail:
            args += ['--embed-thumbnail']
        if self.subtitles:
            args += ['--write-auto-subs']
        return args

    def stop(self):
        with qtc.QMutexLocker(self.mutex):
            self._stop = True

    def run(self):
        create_window = sp.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        command = self.build_command()
        error = False

        with sp.Popen(command, stdout=sp.PIPE, stderr=sp.STDOUT, text=True,
                      universal_newlines=True, creationflags=create_window) as p:
            for line in p.stdout:
                with qtc.QMutexLocker(self.mutex):
                    if self._stop:
                        for child in Process(p.pid).children(recursive=True):
                            child.kill()
                        p.kill()
                        break

                if line.startswith('{'):
                    info_dict = json.loads(line)
                    title = info_dict['title']
                    log.info(f"`{title}` with id {self.item.id} download started with args: " + " ".join(command))
                    self.progress.emit(
                        self.item,
                        [
                            [TreeDex.TITLE, title],
                            [TreeDex.STATUS, "Processing"]
                        ]
                    )
                elif line.startswith('downloading'):
                    data = line.split()
                    self.progress.emit(
                        self.item,
                        [
                            [TreeDex.SIZE, data[1]],
                            [TreeDex.PROGRESS, data[2]],
                            [TreeDex.SPEED, data[3]],
                            [TreeDex.ETA, data[4]],
                            [TreeDex.STATUS, "Downloading"]
                        ]
                    )
                elif line.lower().startswith('error'):
                    error = True
                    log.error(line)
                    self.progress.emit(
                        self.item,
                        [
                            [TreeDex.SIZE, "ERROR"],
                            [TreeDex.PROGRESS, "ERROR"],
                            [TreeDex.STATUS, "ERROR"],
                            [TreeDex.SPEED, "ERROR"]
                        ]
                    )
                    break
                elif line.startswith(("[Merger]", "[ExtractAudio]")):
                    self.progress.emit(
                        self.item,
                        [[TreeDex.STATUS, "Converting"]]
                    )

            if not error:
                self.progress.emit(
                    self.item,
                    [
                        [TreeDex.PROGRESS, "100%"],
                        [TreeDex.STATUS, "Finished"],
                    ]
                )

        self.finished.emit(self.item.id)