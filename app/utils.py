from pathlib import Path

import toml

root = Path(__file__).parent


def load_toml(path):
    with open(path, "r", encoding="utf-8") as file:
        data = toml.load(file)
    return data


def save_toml(path, data: dict):
    with open(path, "w", encoding="utf-8") as file:
        toml.dump(data, file)
