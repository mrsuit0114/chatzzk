import time

from loguru import logger

logger.info("worker is running")

while True:
    time.sleep(1)
    logger.info("monitoring...")
