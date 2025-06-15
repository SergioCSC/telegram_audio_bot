import config as cfg

import logging
import sys

def sec2str(seconds: int) -> str:
    """Convert seconds to a human-readable string."""
    if seconds < 0:
        return "-1 sec"
    seconds = int(seconds)  # Ensure seconds is an integer
    sec_str = f"{seconds % 60:01d}"  # :02d formats the number with leading zeros if needed
    minutes_str = f"{(seconds // 60) % 60:01d}"
    hours_str = f"{(seconds // 3600) % 24:01d}"
    days = seconds // 86400
    if days > 0:
        return f"{days}d {hours_str}h {minutes_str}m {sec_str}s"
    elif (seconds // 3600) % 24 > 0:
        return f"{hours_str}h {minutes_str}m {sec_str}s"
    elif (seconds // 60) % 60 > 0:
        return f"{minutes_str}m {sec_str}s"
    else:
        return f"{sec_str}s"
    

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