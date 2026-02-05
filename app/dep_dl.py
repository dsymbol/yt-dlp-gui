import os
import platform
import shutil
import stat
import zipfile
from typing import Optional, List, Tuple

import requests
from PySide6.QtCore import QThread, QTimer, Signal
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QIcon

from ui.download_widget import Ui_Download
from utils import root

BIN_DIR = root / "bin"

BINARIES = {
    "Linux": {
        "ffmpeg": "ffmpeg-linux64-v4.1",
        "ffprobe": "ffprobe-linux64-v4.1",
        "yt-dlp": "yt-dlp_linux",
        "deno": "deno-x86_64-unknown-linux-gnu.zip",
    },
    "Darwin": {
        "ffmpeg": "ffmpeg-osx64-v4.1",
        "ffprobe": "ffprobe-osx64-v4.1",
        "yt-dlp": "yt-dlp_macos",
        "deno": "deno-x86_64-apple-darwin.zip",
    },
    "Windows": {
        "ffmpeg": "ffmpeg-win64-v4.1.exe",
        "ffprobe": "ffprobe-win64-v4.1.exe",
        "yt-dlp": "yt-dlp.exe",
        "deno": "deno-x86_64-pc-windows-msvc.zip",
    },
}

YT_DLP_BASE_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/"
FFMPEG_BASE_URL = "https://github.com/imageio/imageio-binaries/raw/183aef992339cc5a463528c75dd298db15fd346f/ffmpeg/"
DENO_BASE_URL = "https://github.com/denoland/deno/releases/latest/download/"


class DownloadWindow(QWidget, Ui_Download):
    finished = Signal()

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon(str(root / "assets" / "yt-dlp-gui.ico")))
        self.pb.setMaximum(100)
        
        self.missing: List[Tuple[str, str]] = []
        self._check_missing_dependencies()

        if self.missing:
            self.show()
            self._start_next_download()
        else:
            QTimer.singleShot(0, self.finished.emit)

    def _check_missing_dependencies(self):
        system_os = platform.system()
        if system_os not in BINARIES:
            return

        required_binaries = ["ffmpeg", "ffprobe", "yt-dlp", "deno"]
        missing_exes = [
            exe for exe in required_binaries 
            if not shutil.which(exe) and not (BIN_DIR / (exe + (".exe" if system_os == "Windows" else ""))).exists()
        ]

        if not missing_exes:
            return

        BIN_DIR.mkdir(parents=True, exist_ok=True)

        for exe in missing_exes:
            binary_name = BINARIES[system_os][exe]
            
            if exe == "yt-dlp":
                url = YT_DLP_BASE_URL + binary_name
            elif exe == "deno":
                url = DENO_BASE_URL + binary_name
            else:
                url = FFMPEG_BASE_URL + binary_name

            target_name = f"{exe}.exe" if system_os == "Windows" else exe
            target_path = str(BIN_DIR / target_name)
            
            self.missing.append((url, target_path))

    def _start_next_download(self):
        if not self.missing:
            self.finished.emit()
            return

        url, filename = self.missing[0]
        self.downloader = _DownloadWorker(url, filename)
        self.downloader.progress.connect(self.update_progress)
        self.downloader.finished.connect(self.downloader.deleteLater)
        self.downloader.finished.connect(self.on_download_finished)
        self.downloader.start()

    def on_download_finished(self):
        if not self.missing:
            return

        _, filename = self.missing.pop(0)
        
        try:
            st = os.stat(filename)
            os.chmod(filename, st.st_mode | stat.S_IEXEC)
        except OSError:
            pass

        if self.missing:
            self._start_next_download()
        else:
            self.finished.emit()

    def update_progress(self, percentage: int, status_text: str):
        self.pb.setValue(percentage)
        self.lb_progress.setText(status_text)


class _DownloadWorker(QThread):
    progress = Signal(int, str)  # percentage, status text

    def __init__(self, url: str, filename: str):
        super().__init__()
        self.url = url
        self.filename = filename

    def run(self):
        try:
            self._download()
        except Exception as e:
            self.progress.emit(0, f"Error: {str(e)}")

    def _download(self):
        response = requests.get(self.url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get("content-length", 0))
        block_size = 8192
        downloaded = 0
        
        display_name = os.path.basename(self.filename)
        temp_filename = self.filename + ".part"
        
        with open(temp_filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)
                
                if total_size > 0:
                    percentage = int((downloaded / total_size) * 100)
                    dl_mb = downloaded / (1024 * 1024)
                    tot_mb = total_size / (1024 * 1024)
                    status = f"{display_name}: {dl_mb:.2f} MB / {tot_mb:.2f} MB"
                else:
                    percentage = 0
                    dl_mb = downloaded / (1024 * 1024)
                    status = f"{display_name}: {dl_mb:.2f} MB"
                
                self.progress.emit(percentage, status)

        if self.url.endswith(".zip"):
            try:
                zip_filename = temp_filename + ".zip"
                shutil.move(temp_filename, zip_filename)
                
                with zipfile.ZipFile(zip_filename, 'r') as zf:
                    target_filename = zf.namelist()[0]
                    with zf.open(target_filename) as source, open(self.filename, 'wb') as target:
                        shutil.copyfileobj(source, target)
                
                if os.path.exists(zip_filename):
                    os.remove(zip_filename)
                return
            except Exception as e:
                 if os.path.exists(zip_filename):
                     os.remove(zip_filename)
                 raise e

        if os.path.exists(self.filename):
            os.remove(self.filename)
        os.rename(temp_filename, self.filename)
