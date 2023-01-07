import contextlib
import os
import platform
import shutil
import stat
import sys
from urllib.parse import urlparse

import PyInstaller.__main__
import requests
import tqdm


class Builder:
    def __init__(self, version):
        self.__version__ = version
        self.os = platform.system()
        self.args = [
            '--name=yt-dlp-gui',
            '--add-data', 'assets' + os.pathsep + 'assets',
            '--add-data', 'bin' + os.pathsep + 'bin',
            '--clean',
            '-y',
            'main.py'
        ]

    def __call__(self, *args, **kwargs):
        print("Building yt-dlp-gui")
        print(f"Version: {self.__version__}")
        self.create_bin_folder()
        try:
            PyInstaller.__main__.run(self.args)
        except Exception as f:
            delete('version.rc')
            sys.exit(str(f))

    @property
    def args(self):
        return self._args

    @args.setter
    def args(self, a):
        if self.os == "Windows":
            self.create_version_rc()
            a.extend(['--version-file=version.rc', '--icon', os.path.join('assets', 'yt-dlp-gui.ico'), '--noconsole'])
        elif self.os == "Darwin":
            a.extend(['--icon', os.path.join('assets', 'yt-dlp-gui.ico'), '--noconsole'])
        elif self.os == "Linux":
            pass
        else:
            raise ValueError(f"Unsupported platform {self.os}")
        self._args = a

    def create_bin_folder(self):
        ff = "https://github.com/imageio/imageio-binaries/raw/master/ffmpeg/{}"
        yt = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/{}"

        deps = {
            "Linux": {
                "ffmpeg": ff.format("ffmpeg-linux64-v4.1"),
                "ffprobe": ff.format("ffprobe-linux64-v4.1"),
                "yt-dlp": yt.format("yt-dlp")
            },
            "Darwin": {
                "ffmpeg": ff.format("ffmpeg-osx64-v4.1"),
                "ffprobe": ff.format("ffprobe-osx64-v4.1"),
                "yt-dlp": yt.format("yt-dlp_macos")
            },
            "Windows": {
                "ffmpeg.exe": ff.format("ffmpeg-win64-v4.1.exe"),
                "ffprobe.exe": ff.format("ffprobe-win64-v4.1.exe"),
                "yt-dlp.exe": yt.format("yt-dlp.exe")
            }
        }

        os_deps = deps[self.os]

        if not os.path.exists('bin'):
            os.mkdir('bin')

        with change_dir("bin"):
            if sorted(os_deps.keys()) == sorted(os.listdir()):
                return

            for filename, url in os_deps.items():
                download_file(url, filename)
                st = os.stat(filename)
                os.chmod(filename, st.st_mode | stat.S_IEXEC)

    def create_version_rc(self):
        comma_ver = self.__version__.replace('.', ',')
        data = ['VSVersionInfo(', 'ffi=FixedFileInfo(', f'filevers=({comma_ver}),', f'prodvers=({comma_ver}),',
                'mask=0x3f,',
                'flags=0x0,', 'OS=0x40004,', 'fileType=0x1,', 'subtype=0x0,', 'date=(0, 0)', '),', 'kids=[',
                'StringFileInfo(', '[', 'StringTable(', "u'040904B0',", "[StringStruct(u'CompanyName', u'dsymbol'),",
                "StringStruct(u'FileDescription', u'yt-dlp-gui'),",
                f"StringStruct(u'FileVersion', u'{self.__version__}'),",
                "StringStruct(u'InternalName', u'yt-dlp-gui'),",
                "StringStruct(u'LegalCopyright', u'https://github.com/dsymbol/yt-dlp-gui'),",
                "StringStruct(u'OriginalFilename', u'yt-dlp-gui.exe'),", "StringStruct(u'ProductName', u'yt-dlp-gui'),",
                f"StringStruct(u'ProductVersion', u'{self.__version__}')])", ']),',
                "VarFileInfo([VarStruct(u'Translation', [1033, 1252])])", ']', ')']

        with open("version.rc", "w") as f:
            f.writelines(data)


@contextlib.contextmanager
def change_dir(new_path):
    saved_path = os.getcwd()
    os.chdir(new_path)
    try:
        yield
    finally:
        os.chdir(saved_path)


def delete(*paths):
    for path in paths:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        else:
            pass


def download_file(url, filename=None):
    if not filename:
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)

    r = requests.get(url, stream=True)
    try:
        file_size = int(r.headers['Content-Length'])
    except KeyError:
        file_size = 1000
    chunk_size = 1024
    num_bars = int(file_size / chunk_size)

    with open(filename, 'wb') as fp:
        for chunk in tqdm.tqdm(
                r.iter_content(chunk_size=chunk_size)
                , total=num_bars
                , unit='KB'
                , desc=filename
                , leave=True
        ):
            fp.write(chunk)


if __name__ == '__main__':
    Builder(version="1.1.2.0")()
