import logging
import shlex
import subprocess as sp
import sys

from PySide6 import QtCore, QtWidgets
from utils import ItemRoles, TreeColumn

logger = logging.getLogger(__name__)


class Worker(QtCore.QThread):
    finished = QtCore.Signal(int)
    progress = QtCore.Signal(object, list)

    def __init__(self, item, config, link, path, preset):
        super().__init__()
        self.item: QtWidgets.QTreeWidgetItem = item
        self.link = link
        self.path = path
        self.preset = preset
        self.id = self.item.data(0, ItemRoles.IdRole)
        self.command = self.build_command(config)
        self._mutex = QtCore.QMutex()
        self._stop = False

    def build_command(self, config):
        args = [
            "yt-dlp",
            "--newline",
            "--no-simulate",
            "--progress",
            "--progress-template",
            "%(progress.status)s__SEP__%(progress._total_bytes_estimate_str)s__SEP__%(progress._percent_str)s__SEP__%(progress._speed_str)s__SEP__%(progress._eta_str)s__SEP__%(info.title)s",
        ]
        p_args = config["presets"][self.preset]
        g_args = config["general"].get("global_args")

        args += ["-P", self.path]
        args += p_args if isinstance(p_args, list) else shlex.split(p_args)
        args += g_args if isinstance(g_args, list) else shlex.split(g_args)
        args += ["--", self.link]
        return args

    def stop(self):
        with QtCore.QMutexLocker(self._mutex):
            self._stop = True

    def run(self):
        create_window = sp.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        output = ""
        logger.info(f"Download ({self.id}) starting with cmd: {self.command}")

        self.progress.emit(self.item, [(TreeColumn.STATUS, "Processing")])

        with sp.Popen(
            self.command,
            stdout=sp.PIPE,
            stderr=sp.STDOUT,
            text=True,
            universal_newlines=True,
            creationflags=create_window,
        ) as p:
            for line in p.stdout:
                output += line
                with QtCore.QMutexLocker(self._mutex):
                    if self._stop:
                        p.terminate()
                        p.wait()
                        logger.info(f"Download ({self.id}) stopped.")
                        return self.finished.emit(self.id)

                line = line.strip()
                if "__SEP__" in line:
                    status, total_bytes, percent, speed, eta, title = [
                        i.strip() for i in line.split("__SEP__")
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
                elif line.startswith("WARNING:"):
                    logger.warning(f"Download ({self.id}) {line}")

        if p.returncode != 0:
            logger.error(f"Download ({self.id}) returncode: {p.returncode}\n{output}")
            self.progress.emit(self.item, [(TreeColumn.STATUS, "ERROR")])
        else:
            logger.info(f"Download ({self.id}) finished.")
            self.progress.emit(
                self.item,
                [
                    (TreeColumn.PROGRESS, "100%"),
                    (TreeColumn.STATUS, "Finished"),
                ],
            )
        self.finished.emit(self.id)
