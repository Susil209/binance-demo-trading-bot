"""Logging configuration for the trading bot.

Sets up dual logging:
  - Console: INFO level, colored output via Rich
  - File: DEBUG level, rotated at 5 MB, plain text format
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from rich.logging import RichHandler


def setup_logging(log_dir: str = "logs", log_file: str = "trading_bot.log") -> None:
    """Configure application-wide logging with console and file handlers.

    Args:
        log_dir: Directory to store log files. Created if it doesn't exist.
        log_file: Name of the log file.
    """
    # Resolve log_dir relative to the trading_bot package root
    package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(package_root, log_dir)

    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)

    log_path = os.path.join(log_dir, log_file)

    # Root logger for the bot package
    logger = logging.getLogger("bot")
    logger.setLevel(logging.DEBUG)

    # Avoid adding duplicate handlers on repeated calls
    if logger.handlers:
        return

    # ── Console Handler (Rich) ──────────────────────────────────────────
    console_handler = RichHandler(
        level=logging.INFO,
        rich_tracebacks=True,
        tracebacks_show_locals=False,
        show_time=True,
        show_path=False,
    )
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    # ── File Handler (Rotating) ─────────────────────────────────────────
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)-8s] [%(name)s.%(funcName)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.debug("Logging initialized — file: %s", log_path)
