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
        args,
        link,
        path,
        filename,
        fmt,
        sponsorblock,
        metadata,
        thumbnail,
        subtitles,
    ):
        super().__init__()
        self.item = item
        self.args = args
        self.link = link
        self.path = path
        self.filename = filename
        self.fmt = fmt
        self.sponsorblock = sponsorblock
        self.metadata = metadata
        self.thumbnail = thumbnail
        self.subtitles = subtitles

        self.mutex = qtc.QMutex()
        self._stop = False

    def __str__(self):
        s = (
            f"(link={self.link}, "
            f"args={self.args}, "
            f"path={self.path}, "
            f"filename={self.filename}, "
            f"format={self.fmt}, "
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
        ]

        args += self.args if isinstance(self.args, list) else shlex.split(self.args)
        if self.metadata:
            args += ["--embed-metadata"]
        if self.thumbnail:
            args += ["--embed-thumbnail"]
        if self.subtitles:
            args += ["--write-auto-subs"]

        if self.sponsorblock == "remove":
            args += ["--sponsorblock-remove", "all"]
            print("remove")
        elif self.sponsorblock == "mark":
            args += ["--sponsorblock-mark", "all"]
            print("mark")

        if self.path:
            args += [
                "-o",
                f"{self.path}/{self.filename}" if self.filename else self.path,
            ]
        args += ["--", self.link]
        return args

    def stop(self):
        with qtc.QMutexLocker(self.mutex):
            self._stop = True

    def run(self):
        create_window = sp.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        command = self.build_command()
        output = []
        logger.info(
            f"Download ({self.item.id}) starting with cmd: " + shlex.join(command)
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
                output.append(line)
                with qtc.QMutexLocker(self.mutex):
                    if self._stop:
                        p.terminate()
                        break

                if line.startswith("{"):
                    title = json.loads(line)["title"]
                    logger.debug(f"Download ({self.item.id}) title: {title}")
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
                elif line.startswith(("[Merger]", "[ExtractAudio]")):
                    self.progress.emit(self.item, [(STATUS, "Converting")])

        if p.returncode != 0:
            logger.error(
                f'Download ({self.item.id}) returncode: {p.returncode}\n{"".join(output)}'
            )
            self.progress.emit(
                self.item,
                [
                    (SIZE, "ERROR"),
                    (STATUS, "ERROR"),
                    (SPEED, "ERROR"),
                ],
            )
        else:
            self.progress.emit(
                self.item,
                [
                    (PROGRESS, "100%"),
                    (STATUS, "Finished"),
                ],
            )
        self.finished.emit(self.item.id)
