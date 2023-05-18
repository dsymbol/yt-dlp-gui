import os
import platform
import shutil
import stat
from io import StringIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse

import requests
from PySide6.QtCore import QThread, Signal, QTimer
from PySide6.QtWidgets import QWidget
from tqdm import tqdm

from ui.download_ui import Ui_w_Downloader

BIN = Path(__file__).parent / 'bin'


class Downloader(QThread):
    total_progress = Signal(int)
    progress = Signal(int, str)

    def __init__(self, url, filename=None):
        super().__init__()
        self.url = url
        self.filename = filename

    def run(self):
        if not self.filename:
            parsed_url = urlparse(self.url)
            self.filename = os.path.basename(parsed_url.path)

        r = requests.get(self.url, stream=True)
        file_size = int(r.headers.get('content-length', 0))
        chunk_size = 1024

        self.total_progress.emit(file_size)

        data = StringIO()
        chunk_size = 1024
        read_bytes = 0

        with NamedTemporaryFile(mode='wb', delete=False) as temp, tqdm(
                desc=os.path.basename(self.filename),
                total=file_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
                file=data,
                bar_format='{desc}: {n_fmt}/{total_fmt} [{elapsed}/{remaining}, {rate_fmt}{postfix}]',
                leave=True
        ) as bar:
            for chunk in r.iter_content(chunk_size=chunk_size):
                temp.write(chunk)
                bar.update(chunk_size)
                read_bytes += chunk_size
                self.progress.emit(read_bytes, data.getvalue().split('\r')[-1].strip())
            self.progress.emit(read_bytes, data.getvalue().split('\r')[-1].strip())

        data.close()
        shutil.move(temp.name, self.filename)


class DownloaderUi(QWidget, Ui_w_Downloader):
    finished = Signal()

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.missing = []

        self.get_missing_dep()

        if self.missing:
            self.show()
            self.download_init()
        else:
            QTimer.singleShot(0, self.finished.emit)

    def get_missing_dep(self):
        binaries = {
            "Linux": {"ffmpeg": "ffmpeg-linux64-v4.1", "ffprobe": "ffprobe-linux64-v4.1", "yt-dlp": "yt-dlp_linux"},
            "Darwin": {"ffmpeg": "ffmpeg-osx64-v4.1", "ffprobe": "ffprobe-osx64-v4.1", "yt-dlp": "yt-dlp_macos"},
            "Windows": {"ffmpeg": "ffmpeg-win64-v4.1.exe", "ffprobe": "ffprobe-win64-v4.1.exe", "yt-dlp": "yt-dlp.exe"}
        }

        exes = [exe for exe in ['ffmpeg', 'ffprobe', 'yt-dlp'] if not shutil.which(exe)]
        os_ = platform.system()

        if exes:
            if not os.path.exists(BIN):
                os.makedirs(BIN)

            for exe in exes:
                if exe == 'yt-dlp':
                    url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/" + binaries[os_][exe]
                else:
                    url = "https://github.com/imageio/imageio-binaries/raw/master/ffmpeg/" + binaries[os_][exe]

                filename = os.path.join(BIN, f"{exe}.exe" if os_ == "Windows" else exe)

                self.missing += [[url, filename]]

    def download_init(self):
        url, filename = self.missing[0]
        self.downloader = Downloader(url, filename)
        self.downloader.total_progress.connect(self.pb.setMaximum)
        self.downloader.progress.connect(self.update_progress)
        self.downloader.finished.connect(self.downloader.deleteLater)
        self.downloader.finished.connect(self.on_download_finished)
        self.downloader.start()

    def on_download_finished(self):
        url, filename = self.missing.pop(0)
        st = os.stat(filename)
        os.chmod(filename, st.st_mode | stat.S_IEXEC)

        if self.missing:
            self.download_init()
        else:
            self.finished.emit()

    def update_progress(self, progress, data):
        self.pb.setValue(progress)
        self.lb_progress.setText(data)
