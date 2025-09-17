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

    def __init__(self, item, config, link, path, preset, preset_options=None):
        super().__init__()
        self.item = item
        self.config = config
        self.link = link
        self.path = path
        self.preset = preset
        self.preset_options = preset_options or {}
        preset_config = self.config["presets"][preset]
        self.args = preset_config.get("args", preset_config) if isinstance(preset_config, dict) else preset_config
        self.global_args = self.config["general"].get("global_args")

        self.mutex = qtc.QMutex()
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

        # Add preset-specific options based on UI selections
        if self.preset_options.get("metadata", False):
            args.extend(["--write-info-json", "--write-description"])
            
        if self.preset_options.get("subtitles", False):
            args.extend(["--write-subs", "--write-auto-subs"])
            
        if self.preset_options.get("thumbnail", False):
            args.append("--write-thumbnail")
            
        sponsorblock = self.preset_options.get("sponsorblock", 0)
        if sponsorblock == 1:  # Remove
            args.append("--sponsorblock-remove=all")
        elif sponsorblock == 2:  # Mark
            args.append("--sponsorblock-mark=all")

        args += self.args if isinstance(self.args, list) else shlex.split(self.args)
        if self.global_args:
            args += self.global_args if isinstance(self.global_args, list) else shlex.split(self.global_args)
        args += ["-P", self.path, "--", self.link]
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

        self.progress.emit(self.item, [(STATUS, "Processing")])

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
                            (TITLE, title),
                            (SIZE, total_bytes),
                            (PROGRESS, percent),
                            (SPEED, speed),
                            (ETA, eta),
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
