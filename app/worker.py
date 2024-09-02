import json
import logging
import shlex
import subprocess as sp
import sys

import PySide6.QtCore as qtc

logger = logging.getLogger(__name__)

TITLE = 0
FORMAT = 1
SIZE = 2
PROGRESS = 3
STATUS = 4
SPEED = 5
ETA = 6


class Worker(qtc.QThread):
    finished = qtc.Signal(int)
    progress = qtc.Signal(object, list)

    def __init__(
        self,
        item,
        link,
        path,
        fmt,
        cargs,
        sponsorblock,
        metadata,
        thumbnail,
        subtitles,
    ):
        super().__init__()
        self.item = item
        self.link = link
        self.path = path
        self.fmt = fmt
        self.cargs = cargs
        self.sponsorblock = sponsorblock
        self.metadata = metadata
        self.thumbnail = thumbnail
        self.subtitles = subtitles

        self.mutex = qtc.QMutex()
        self._stop = False

    def __str__(self):
        s = (
            f"(link={self.link}, "
            f"path={self.path}, "
            f"format={self.fmt}, "
            f"cargs={self.cargs}, "
            f"sponsorblock={self.sponsorblock}, "
            f"metadata={self.metadata}, "
            f"thumbnail={self.thumbnail}, "
            f"subtitles={self.subtitles})"
        )
        return s

    def build_command(self):
        args = [
            "yt-dlp",
            "--newline",
            "--ignore-errors",
            "--ignore-config",
            "--no-simulate",
            "--progress",
            "--progress-template",
            "%(progress.status)s %(progress._total_bytes_estimate_str)s "
            "%(progress._percent_str)s %(progress._speed_str)s %(progress._eta_str)s",
            "--dump-json",
            "-v",
            "-o",
            self.path,
            self.link,
        ]
        if self.fmt == "best":
            args += ["-f", r"bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4] / bv*+ba/b"]
        elif self.fmt == "mp4":
            args += ["-f", r"bv*[vcodec^=avc]+ba[ext=m4a]/b"]
        else:
            args += [
                "--extract-audio",
                "--audio-format",
                self.fmt,
                "--audio-quality",
                "0",
            ]

        if self.cargs:
            args += shlex.split(self.cargs)
        if self.metadata:
            args += ["--embed-metadata"]
        if self.thumbnail:
            args += ["--embed-thumbnail"]
        if self.subtitles:
            args += ["--write-auto-subs"]

        if self.sponsorblock:
            if self.sponsorblock == "remove":
                args += ["--sponsorblock-remove", "all"]
            else:
                args += ["--sponsorblock-mark", "all"]
        return args

    def stop(self):
        with qtc.QMutexLocker(self.mutex):
            self._stop = True

    def run(self):
        create_window = sp.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        command = self.build_command()
        error = False
        logger.info(
            f"Download ({self.item.id}) starting with args: " + shlex.join(command)
        )

        with sp.Popen(
            command,
            stdout=sp.PIPE,
            stderr=sp.STDOUT,
            text=True,
            universal_newlines=True,
            creationflags=create_window,
        ) as p:
            for line in p.stdout:
                with qtc.QMutexLocker(self.mutex):
                    if self._stop:
                        p.terminate()
                        break

                if line.startswith("{"):
                    title = json.loads(line)["title"]
                    logger.debug(f"Download ({self.item.id}) title: `{title}`")
                    self.progress.emit(
                        self.item,
                        [(TITLE, title), (STATUS, "Processing")],
                    )
                elif line.lower().startswith("downloading"):
                    data = line.split()
                    self.progress.emit(
                        self.item,
                        [
                            (SIZE, data[1]),
                            (PROGRESS, data[2]),
                            (SPEED, data[3]),
                            (ETA, data[4]),
                            (STATUS, "Downloading"),
                        ],
                    )
                elif line.lower().startswith("error"):
                    error = True
                    logger.error(line.replace("ERROR:", "").strip())
                    self.progress.emit(
                        self.item,
                        [
                            (SIZE, "ERROR"),
                            (STATUS, "ERROR"),
                            (SPEED, "ERROR"),
                        ],
                    )
                    break
                elif line.startswith(("[Merger]", "[ExtractAudio]")):
                    self.progress.emit(self.item, [(STATUS, "Converting")])

            if not error:
                self.progress.emit(
                    self.item,
                    [
                        (PROGRESS, "100%"),
                        (STATUS, "Finished"),
                    ],
                )

        self.finished.emit(self.item.id)
