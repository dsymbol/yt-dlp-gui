import logging
import os


def mk_logger(name="my_logger", file="err.log"):
    if not os.path.exists(os.path.join(os.environ.get("PROJECT_PATH"), "logs")):
        os.mkdir(os.path.join(os.environ.get("PROJECT_PATH"), "logs"))

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(message)s')
    ch.setFormatter(formatter)

    fh = logging.FileHandler(os.path.join(os.environ.get("PROJECT_PATH"), "logs", file))
    fh.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s : %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger
