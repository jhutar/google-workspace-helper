import logging
import os
from pathlib import Path

LOG_DIR_NAME = "google-workspace-helper"
LOG_FILE_NAME = "google-workspace-helper.log"


def get_log_file_path() -> Path:
    """Return XDG cache log path, creating parent dirs if needed."""
    cache_home = os.environ.get("XDG_CACHE_HOME")
    base_dir = Path(cache_home) if cache_home else Path.home() / ".cache"
    log_dir = base_dir / LOG_DIR_NAME
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / LOG_FILE_NAME


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("google_workspace_helper")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    file_handler = logging.FileHandler(get_log_file_path(), mode="a", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )

    stderr_handler = logging.StreamHandler()
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    logger.addHandler(file_handler)
    logger.addHandler(stderr_handler)

    return logger
