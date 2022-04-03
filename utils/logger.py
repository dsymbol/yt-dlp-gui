import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('err.log')
formatter = logging.Formatter('%(asctime)s : %(message)s', datefmt='%d-%b-%y %H:%M:%S')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.ERROR)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

log.addHandler(file_handler)
log.addHandler(stream_handler)