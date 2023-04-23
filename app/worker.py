import json
import subprocess as sp
import sys
from dataclasses import dataclass

from PySide6.QtCore import QThread, Signal
import logging

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


class Worker(QThread):
    progress = Signal(object, list)

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

    def run(self):
        create_window = sp.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        command = self.build_command()
        error = False

        with sp.Popen(command, stdout=sp.PIPE, stderr=sp.STDOUT, text=True,
                      universal_newlines=True, creationflags=create_window) as p:
            for line in p.stdout:
                if line.startswith('{'):
                    info_dict = json.loads(line)
                    title = info_dict['title']
                    log.info(f"`{title}` download started: " + " ".join(command))
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
