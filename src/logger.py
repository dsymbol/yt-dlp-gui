import logging
import os


def get_logger(name="logger", file="error.log"):
    """
    Logging levels: debug, info, warn, error & critical
    All levels write to stdout however error & critical also write to a file
    """
    if not os.path.exists(os.path.join(os.environ.get("PROJECT_PATH"), "logs")):
        os.mkdir(os.path.join(os.environ.get("PROJECT_PATH"), "logs"))

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
    ch.setFormatter(formatter)

    fh = logging.FileHandler(os.path.join(os.environ.get("PROJECT_PATH"), "logs", file))
    fh.setLevel(logging.ERROR)
    formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger
