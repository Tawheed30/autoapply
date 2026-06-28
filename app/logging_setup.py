import logging
import logging.handlers
import os
from pathlib import Path


def setup_logging(log_file: str, level: str = "INFO", max_bytes: int = 10485760, backup_count: int = 5):
    """Set up central logging for the application."""
    os.makedirs(os.path.dirname(os.path.expanduser(log_file)), exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level))

    # Rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.expanduser(log_file),
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setLevel(getattr(logging, level))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level))

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
