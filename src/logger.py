import logging
import os


def get_logger(name="logger", file="debug.log"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%d/%m/%y %H:%M:%S')
    ch.setFormatter(formatter)

    fh = logging.FileHandler(os.path.join(os.environ.get("PROJECT_PATH"), file), delay=True)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s (%(name)s) %(levelname)s: %(message)s', datefmt='%d/%m/%y %H:%M:%S')
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger
