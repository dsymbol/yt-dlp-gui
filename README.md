<div align="center">
<h1>yt-dlp-gui</h1>
<p>yt-dlp-gui is a graphical interface for the command line tool <a href=https://github.com/yt-dlp/yt-dlp>yt-dlp</a>, which allows users to download videos from various <a href=https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md>websites</a>, including YouTube. It is designed to be more user-friendly and accessible for those who are not comfortable using the command line. With yt-dlp-gui, users can simply enter the URL of the video they want to download and initiate the download process through a simple interface.</p>
<img src="https://user-images.githubusercontent.com/88138099/211172534-e582b29b-ceb7-43e4-8370-b76b798ad069.gif"></br>
</div>

## Getting Started

There are three ways to begin using yt-dlp-gui, depending on your preference and system:

* [`Portable`](#portable) (Windows only)
* [`Build`](#build) (Windows, Linux & MacOS)
* [`Manual`](#manual)

### Portable

1. Download the latest portable version from the [releases](https://github.com/dsymbol/yt-dlp-gui/releases/latest) section. This will download a ZIP file containing the program files and all necessary dependencies.
2. Extract the files from the ZIP file.
3. Double-click on the `yt-dlp-gui.exe` file to launch the program.

### Build

You **must** have [Python](https://www.python.org/downloads/) 3.9+ installed.

To build yt-dlp-gui from its source code:

1. Clone the repository onto your local machine:

```bash
git clone https://github.com/dsymbol/yt-dlp-gui
cd yt-dlp-gui
```

2. Install the necessary dependencies:

```bash
pip install -r requirements.txt
```

3. Use the provided build script to compile the program:

```bash
cd src
python build.py
```

4. The executable will be ready at:

```bash
./dist/yt-dlp-gui
```

### Manual

You **must** have [Python](https://www.python.org/downloads/) 3.9+ installed.

1. When running using a Python interpreter you must install the executable dependencies first:

* [`ffmpeg`](https://ffmpeg.org/)
* [`ffprobe`](https://ffmpeg.org/)
* [`yt-dlp`](https://github.com/yt-dlp/yt-dlp/)

***Unix***

Use the package manager to install ffmpeg and yt-dlp:

```bash
sudo apt update && sudo apt install ffmpeg yt-dlp
```

***Windows***

Follow the instructions at [windowsloop](https://windowsloop.com/install-ffmpeg-windows-10/) to install ffmpeg on Windows.

Download [yt-dlp](https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe) executable and add it to the Windows Path environment variable

2. Clone the repository onto your local machine:

```bash
git clone https://github.com/dsymbol/yt-dlp-gui
cd yt-dlp-gui
```

3. Install the necessary dependencies:

```bash
pip install -r requirements.txt
```

4. Run the program:

```bash
python main.py
```
