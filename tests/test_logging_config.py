import logging
from google_workspace_helper.logging_config import setup_logging


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


def test_setup_logging_idempotent():
    logger1 = setup_logging()
    handler_count = len(logger1.handlers)
    logger2 = setup_logging()
    assert len(logger2.handlers) == handler_count
    assert logger1 is logger2
