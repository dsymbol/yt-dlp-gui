from pathlib import Path

import tomlkit
from PySide6 import QtCore
from platformdirs import user_data_dir

ROOT = Path(__file__).parent
BIN_DIR = Path(user_data_dir("yt-dlp-gui"))  # user data dir for persistence


def load_toml(path):
    with open(path, "r", encoding="utf-8") as file:
        return tomlkit.parse(file.read())


def save_toml(path, data):
    with open(path, "w", encoding="utf-8") as file:
        file.write(tomlkit.dumps(data))


class ItemRoles:
    IdRole = QtCore.Qt.UserRole
    LinkRole = QtCore.Qt.UserRole + 1
    PathRole = QtCore.Qt.UserRole + 2


class TreeColumn:
    TITLE = 0
    PRESET = 1
    SIZE = 2
    PROGRESS = 3
    STATUS = 4
    SPEED = 5
    ETA = 6
