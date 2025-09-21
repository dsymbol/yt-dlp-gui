import json
import logging
import shlex
import subprocess as sp
import sys

from PySide6 import QtCore
from utils import ItemRoles, TreeColumn

logger = logging.getLogger(__name__)


class Worker(QtCore.QThread):
    finished = QtCore.Signal(int)
    progress = QtCore.Signal(object, list)

    def __init__(self, item, config, link, path, preset):
        super().__init__()
        self.item = item
        self.config = config
        self.link = link
        self.path = path
        self.preset = preset
        self.args = self.config["presets"][preset]
        self.global_args = self.config["general"].get("global_args")

        self.mutex = QtCore.QMutex()
        self._stop = False

    def __str__(self):
        return f"(link={self.link}, preset={self.preset}, path={self.path}, args={self.args})"

    def build_command(self):
        args = [
            "yt-dlp",
            "--newline",
            "--no-simulate",
            "--progress",
            "--progress-template",
            '["%(progress.status)s","%(progress._total_bytes_estimate_str)s","%(progress._percent_str)s","%(progress._speed_str)s","%(progress._eta_str)s","%(info.title)s"]',
        ]

        args += self.args if isinstance(self.args, list) else shlex.split(self.args)
        args += (
            self.global_args
            if isinstance(self.global_args, list)
            else shlex.split(self.global_args)
        )
        args += ["-P", self.path, "--", self.link]
        return args

    def stop(self):
        with QtCore.QMutexLocker(self.mutex):
            self._stop = True

    def run(self):
        create_window = sp.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        command = self.build_command()
        output = []
        logger.info(
            f"Download ({self.item.data(0, ItemRoles.IdRole)}) starting with cmd: "
            + shlex.join(command)
        )

        self.progress.emit(self.item, [(TreeColumn.STATUS, "Processing")])

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
                with QtCore.QMutexLocker(self.mutex):
                    if self._stop:
                        p.terminate()
                        p.returncode = 0
                        break

                line = line.strip()
                if line.startswith("[") and line.endswith("]"):
                    _, total_bytes, percent, speed, eta, title = [
                        i.strip() for i in json.loads(line)
                    ]
                    self.progress.emit(
                        self.item,
                        [
                            (TreeColumn.TITLE, title),
                            (TreeColumn.SIZE, total_bytes),
                            (TreeColumn.PROGRESS, percent),
                            (TreeColumn.SPEED, speed),
                            (TreeColumn.ETA, eta),
                            (TreeColumn.STATUS, "Downloading"),
                        ],
                    )
                elif line.startswith(("[Merger]", "[ExtractAudio]")):
                    self.progress.emit(self.item, [(TreeColumn.STATUS, "Converting")])

        if p.returncode != 0:
            logger.error(
                f'Download ({self.item.data(0, ItemRoles.IdRole)}) returncode: {p.returncode}\n{"".join(output)}'
            )
            self.progress.emit(
                self.item,
                [
                    (TreeColumn.SIZE, "ERROR"),
                    (TreeColumn.STATUS, "ERROR"),
                    (TreeColumn.SPEED, "ERROR"),
                ],
            )
        else:
            self.progress.emit(
                self.item,
                [
                    (TreeColumn.PROGRESS, "100%"),
                    (TreeColumn.STATUS, "Finished"),
                ],
            )
        self.finished.emit(self.item.data(0, ItemRoles.IdRole))
