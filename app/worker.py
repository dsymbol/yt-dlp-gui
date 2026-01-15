import logging
import shlex
import subprocess as sp
import sys

from PySide6 import QtCore, QtWidgets
from utils import ItemRoles, TreeColumn

logger = logging.getLogger(__name__)


class DownloadWorker(QtCore.QThread):
    finished = QtCore.Signal(int)
    progress = QtCore.Signal(object, list)
    
    # Quality presets mapping to height values
    QUALITY_MAP = {
        "Best": None,      # No height limit
        "1080p": 1080,
        "720p": 720,
        "480p": 480,
        "360p": 360,
        "Audio Only": "audio",
    }

    def __init__(self, item, config, link, path, quality="720p"):
        super().__init__()
        self.item: QtWidgets.QTreeWidgetItem = item
        self.link = link
        self.path = path
        self.quality = quality
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
        
        # Apply quality filter
        quality_value = self.QUALITY_MAP.get(self.quality)
        
        if quality_value == "audio":
            # Audio only - extract as MP3
            args += ["--extract-audio", "--audio-format", "mp3", "--audio-quality", "0"]
        elif quality_value is not None:
            # Video at specified quality + audio, merged
            args += ["-f", f"bv*[height<={quality_value}][ext=mp4]+ba[ext=m4a]/b[height<={quality_value}][ext=mp4]/bv*[height<={quality_value}]+ba/b[height<={quality_value}]"]
        else:
            # Best quality - best video + audio, merged
            args += ["-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b"]
        
        # Add global args from config
        g_args = config["general"].get("global_args", "")

        args += ["-P", self.path]
        args += g_args if isinstance(g_args, list) else shlex.split(g_args) if g_args else []
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
