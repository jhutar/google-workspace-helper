import logging

import pytest

from google_workspace_helper.logging_config import get_log_file_path, setup_logging


@pytest.fixture(autouse=True)
def isolated_logger(monkeypatch, tmp_path):
    """Point logs to temp cache dir and reset handlers between tests."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    logger = logging.getLogger("google_workspace_helper")
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
    yield


def test_setup_logging_returns_logger():
    logger = setup_logging()
    assert isinstance(logger, logging.Logger)
    assert logger.name == "google_workspace_helper"
    assert logger.level == logging.DEBUG


def test_setup_logging_has_file_handler():
    logger = setup_logging()
    file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) >= 1
    assert file_handlers[0].level == logging.DEBUG


def test_setup_logging_has_stderr_handler():
    logger = setup_logging()
    stream_handlers = [
        h
        for h in logger.handlers
        if isinstance(h, logging.StreamHandler)
        and not isinstance(h, logging.FileHandler)
    ]
    assert len(stream_handlers) >= 1
    assert stream_handlers[0].level == logging.WARNING


def test_get_log_file_path_uses_xdg_cache(tmp_path):
    log_path = get_log_file_path()
    assert (
        log_path == tmp_path / "google-workspace-helper" / "google-workspace-helper.log"
    )
    assert log_path.parent.is_dir()


def test_setup_logging_idempotent():
    logger1 = setup_logging()
    handler_count = len(logger1.handlers)
    logger2 = setup_logging()
    assert len(logger2.handlers) == handler_count
    assert logger1 is logger2
