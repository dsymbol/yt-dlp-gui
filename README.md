# yt-dlp-gui

Graphical interface for the command line tool [yt-dlp](https://github.com/yt-dlp/yt-dlp) with preset customization.

## Screenshot

![](https://github.com/user-attachments/assets/8e758f07-3cdb-477c-91ab-0ee20c2443e8)

## Usage

There are two ways to get started, depending on your preference and system:

* [`Portable`](#portable) ~ *Windows*
* [`Manual`](#manual) ~ *Platform independent*

### Portable

Download the latest portable version from the the [releases](https://github.com/dsymbol/yt-dlp-gui/releases/latest) section. 
This is a ZIP file containing the program files and all necessary dependencies.

*All releases are built and released using GitHub Workflow*

### Manual

You **must** have [Python](https://www.python.org/downloads/) 3.9+ installed.

```bash
git clone https://github.com/dsymbol/yt-dlp-gui
cd yt-dlp-gui
pip install -r requirements.txt
cd app
python app.py
```

## Preset Customization

If you want to create your own presets or modify the existing ones, you're in the right place. All customization options can be found in the `config.toml` file.

###  Available Fields

To define a preset, the section name must begin with `presets.`. Below are the fields you can use to customize your presets:

- **args** (required): This field specifies the arguments for `yt-dlp`. It can be provided as a string or a list.

- **path** (optional): This string field allows you to specify the output path. If this field is left out, it must be included in the `args` field.

- **filename** (optional): This string field allows you to define the naming convention. If this field is left out, it must be specified in the `args` field.

- **sponsorblock** (optional): This integer field allows you to set SponsorBlock functionality. `0` to disable or `1` to remove and `2` to mark.

- **metadata** (optional): This boolean field determines whether to include metadata.

- **subtitles** (optional): This boolean field determines whether to include subtitles.

- **thumbnail** (optional): This boolean field determines whether to include thumbnail.

Below an example of how to add the `wav` format, you will notice I left out `subtitles` and `thumbnail` as they're not applicable for this format.

```toml
[presets.wav]
args = "--extract-audio --audio-format wav --audio-quality 0"
path = ""
filename = "%(title)s.%(ext)s"
sponsorblock = 0
metadata = false
```

Try it yourself by pasting it to the bottom of your `config.toml` file! You will see that any fields not included in the preset will be disabled in the GUI. If you encounter any issues with your preset, check the `debug.log` file which is located in the root directory of the program for details.