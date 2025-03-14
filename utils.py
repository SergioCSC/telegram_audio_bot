import config as cfg

import logging
import sys


def _sizeof_fmt(num:int, suffix: str = "B") -> str:
    for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
        if abs(num) < 1024.0:
            rounded_down_num = num // 0.1 / 10
            return f"{rounded_down_num:3.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Y{suffix}"


def _init_logging() -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
    datefmt='%H:%M:%S'
    FORMAT = "[%(asctime)s %(filename)20s:%(lineno)5s - %(funcName)25s() ] %(message)s"
    logging.basicConfig(level=cfg.LOG_LEVEL,
                        format=FORMAT, 
                        datefmt=datefmt,
                        stream=sys.stdout)