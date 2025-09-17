# yt-dlp-gui

Simplistic graphical interface for the command line tool [yt-dlp](https://github.com/yt-dlp/yt-dlp).

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

## Preset Customization (Advanced)

Want to create your own presets or modify existing ones? You're in the right section. customization options reside in the `config.toml` file. If a preset fails, check the `debug.log` file for details.

**Notes:** 
- All files mentioned are in the `yt-dlp-gui` root directory.
- The arguments specified will be added to the [base](https://github.com/dsymbol/yt-dlp-gui/blob/main/app/worker.py#L40) `yt-dlp` arguments.
- Prefer lists over strings for complex presets.

### Presets

Defined in the `[presets]` table. Each preset is a key‑value pair, the value can be provided as a string or list.

### Global Arguments

Defined in the `[general]` table. `global_args` is appended to every preset, so you don’t have to repeat common arguments. the value can be provided as a string or list.

### Example

```toml
[general]
...
global_args = "--cookies-from-browser firefox"

[presets]
...
# WAV audio only (string)
"WAV Audio" = "--extract-audio --audio-format wav --audio-quality 0"
# MP4 with embedded thumbnail (list)
mp4_thumbnail = ["-f", "bv*[vcodec^=avc]+ba[ext=m4a]/b", "--embed-thumbnail"]
```
