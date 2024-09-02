import json
from pathlib import Path

ROOT = Path(__file__).parent

def load_json(path, default_value: dict | list = {}):
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        data = default_value
    return data


def save_json(path, data: dict):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)