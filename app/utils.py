from pathlib import Path

import toml
from PySide6 import QtCore

root = Path(__file__).parent


def load_toml(path):
    with open(path, "r", encoding="utf-8") as file:
        data = toml.load(file)
    return data


def save_toml(path, data: dict):
    with open(path, "w", encoding="utf-8") as file:
        toml.dump(data, file)


class ItemRoles:
    IdRole = QtCore.Qt.UserRole
    LinkRole = QtCore.Qt.UserRole + 1
    PathRole = QtCore.Qt.UserRole + 2
