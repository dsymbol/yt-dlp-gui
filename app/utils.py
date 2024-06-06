import json
import logging
from pathlib import Path

ROOT = Path(__file__).parent

def init_logger(file="debug.log"):
    logging.basicConfig(
        level=logging.NOTSET,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%d-%m-%y %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(file, encoding='utf-8', delay=True),
        ],
    )

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