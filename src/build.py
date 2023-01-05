import os
import shutil
from urllib.parse import urlparse

import PyInstaller.__main__
import requests
import tqdm

__version__ = "1.1.2.0"


def create_bin_folder():
    deps = {
        'yt-dlp.exe': 'https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe',
        'ffmpeg.exe': 'https://github.com/imageio/imageio-binaries/raw/master/ffmpeg/ffmpeg-win64-v4.1.exe',
        'ffprobe.exe': 'https://github.com/imageio/imageio-binaries/raw/master/ffmpeg/ffprobe-win64-v4.1.exe'
    }

    if os.path.exists('bin'):
        if sorted(deps.keys()) == sorted(os.listdir('bin')):
            return
        else:
            shutil.rmtree('bin')

    print('Creating bin folder.')
    os.mkdir('bin')

    for k, v in deps.items():
        path = os.path.join('bin', k)
        download_file(v, path)


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


def create_version_rc(ver):
    comma_ver = __version__.replace('.', ',')
    data = ['VSVersionInfo(', 'ffi=FixedFileInfo(', f'filevers=({comma_ver}),', f'prodvers=({comma_ver}),',
            'mask=0x3f,',
            'flags=0x0,', 'OS=0x40004,', 'fileType=0x1,', 'subtype=0x0,', 'date=(0, 0)', '),', 'kids=[',
            'StringFileInfo(', '[', 'StringTable(', "u'040904B0',", "[StringStruct(u'CompanyName', u'dsymbol'),",
            "StringStruct(u'FileDescription', u'yt-dlp-gui'),", f"StringStruct(u'FileVersion', u'{ver}'),",
            "StringStruct(u'InternalName', u'yt-dlp-gui'),",
            "StringStruct(u'LegalCopyright', u'https://github.com/dsymbol/yt-dlp-gui'),",
            "StringStruct(u'OriginalFilename', u'yt-dlp-gui.exe'),", "StringStruct(u'ProductName', u'yt-dlp-gui'),",
            f"StringStruct(u'ProductVersion', u'{ver}')])", ']),',
            "VarFileInfo([VarStruct(u'Translation', [1033, 1252])])", ']', ')']

    with open("version.rc", "w") as f:
        f.writelines(data)


def delete(*paths):
    for path in paths:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        else:
            pass


if __name__ == '__main__':
    create_bin_folder()
    create_version_rc(__version__)
    PyInstaller.__main__.run(
        [
            '--name=yt-dlp-gui',
            '--version-file=version.rc',
            '--icon', os.path.join('assets', 'yt-dlp-gui.ico'),
            '--add-data', 'assets' + os.pathsep + 'assets',
            '--add-data', 'bin' + os.pathsep + 'bin',
            '--noconsole',
            '--clean',
            '-y',
            'main.py'
        ]
    )
    delete('build', 'yt-dlp-gui.spec', 'version.rc')
