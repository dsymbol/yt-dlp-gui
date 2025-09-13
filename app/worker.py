import json
import logging
import shlex
import subprocess as sp
import sys
import os
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
        config,
        link,
        path,
        preset
    ):
        super().__init__()
        self.item = item
        self.config = config
        self.link = link
        self.path = path
        self.preset = preset
        self.args = self.config["presets"][preset]
        self.global_args = self.config["general"].get("global_args")

        self.mutex = qtc.QMutex()
        self._stop = False

    def __str__(self):
        return f"(link={self.link}, preset={self.preset}, path={self.path}, args={self.args})"

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
        args += self.global_args if isinstance(self.global_args, list) else shlex.split(self.global_args)
        args += ["-o", f"{self.path}/%(title)s.%(ext)s", "--", self.link]
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
