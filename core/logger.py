import logging
import os

LOG_DIR = "logs"

os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "pidash.log"),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("PiDash")


def info(text):
    logger.info(text)
    print("[INFO]", text)


def warning(text):
    logger.warning(text)
    print("[WARNING]", text)


def error(text):
    logger.error(text)
    print("[ERROR]", text)
