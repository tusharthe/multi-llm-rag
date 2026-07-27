import logging
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "logger.log"

_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), None)
LOG_LEVEL = _level if isinstance(_level, int) else logging.NOTSET


def daily_namer(default_name: str) -> str:
    path = Path(default_name)
    date = path.suffix.lstrip(".")      # ".2026-07-25" -> "2026-07-25"
    stem = Path(path.stem).stem         # "logger.log"  -> "logger"
    return str(path.with_name(f"{stem}-{date}.log"))


logger = logging.getLogger("app")
logger.setLevel(LOG_LEVEL)
logger.propagate = False

# Prevent duplicate handlers if imported multiple times
if not logger.handlers:

    # threadName matters here: the LangGraph model nodes run in parallel
    # threads, so records from different models interleave in the file.
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(module)-10s | %(threadName)-16s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(formatter)

    # Daily rotating file
    file_handler = TimedRotatingFileHandler(
        filename=LOG_FILE,
        when="midnight",
        interval=1,
        backupCount=300,     # Keep the last 300 rotated files
        encoding="utf-8",
        errors="replace",    # never let an unencodable char raise
    )
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(formatter)
    file_handler.namer = daily_namer

    # logger.addHandler(console_handler)
    logger.addHandler(file_handler)
