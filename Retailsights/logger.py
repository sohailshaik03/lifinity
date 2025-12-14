# logger.py
from __future__ import annotations

import logging
import logging.handlers
import os
import sys
import io

# ------------------------------------------------------------
# Env-based configuration
# ------------------------------------------------------------

LOG_LEVEL = os.getenv("RETAILSIGHT_LOG_LEVEL", "INFO").upper()
LOG_DIR = os.getenv("RETAILSIGHT_LOG_DIR", ".")
LOG_FILE = os.path.join(LOG_DIR, "retailsight.log")


def _create_logger() -> logging.Logger:
    """
    Enterprise-style logger:
    - Console + rotating file
    - Env-driven level
    - Safe with Streamlit reloads
    """
    logger = logging.getLogger("retailsight")

    # Avoid duplicate handlers when Streamlit reloads
    if logger.handlers:
        return logger

    logger.setLevel(LOG_LEVEL)

    # -------- Formatter --------
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # -------- Console handler (force UTF-8) --------
    try:
        console_stream = io.TextIOWrapper(getattr(sys.stdout, "buffer", sys.stdout), encoding="utf-8", errors="replace")
        console_handler = logging.StreamHandler(console_stream)
    except Exception:
        console_handler = logging.StreamHandler(sys.stdout)

    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # -------- Rotating file handler --------
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE,
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(LOG_LEVEL)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # If file logging fails, we still keep console logging
        console_handler.stream.write(f"⚠ Logging to file failed: {e}\n")

    logger.propagate = False
    return logger


# Main logger instance
logger = _create_logger()

# Shortcut used everywhere:
# from logger import log
log = logger
