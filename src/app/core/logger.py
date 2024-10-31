import os
import time

from loguru import logger

basedir = os.path.dirname(os.path.dirname((os.path.dirname(os.path.abspath(__file__)))))
log_dir = os.path.join(basedir, "logs")

if not os.path.exists(log_dir):
    os.mkdir(log_dir)

log_file_path = os.path.join(log_dir, f'{time.strftime("%Y-%m-%d")}.log')

logger.add(log_file_path, rotation="200KB", compression="zip")

__all__ = ["logger"]
