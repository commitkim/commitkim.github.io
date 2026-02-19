"""
Unit tests for core.logger — unified logging.
"""

import logging
from core.logger import get_logger, _configured


class TestLogger:
    def setup_method(self):
        """Reset logger state before each test."""
        _configured.discard("test_logger")
        logger = logging.getLogger("test_logger")
        logger.handlers.clear()

    def test_get_logger_returns_logger(self):
        log = get_logger("test_logger")
        assert isinstance(log, logging.Logger)
        assert log.name == "test_logger"

    def test_logger_has_console_handler(self):
        log = get_logger("test_logger")
        assert len(log.handlers) >= 1
        assert isinstance(log.handlers[0], logging.StreamHandler)

    def test_logger_level_default_info(self):
        log = get_logger("test_logger")
        assert log.level == logging.INFO

    def test_logger_custom_level(self):
        log = get_logger("test_logger", level=logging.DEBUG)
        assert log.level == logging.DEBUG

    def test_logger_no_propagate(self):
        log = get_logger("test_logger")
        assert log.propagate is False

    def test_get_logger_idempotent(self):
        """Same name returns same logger without adding duplicate handlers."""
        _configured.discard("test_logger")
        log1 = get_logger("test_logger")
        handler_count = len(log1.handlers)
        log2 = get_logger("test_logger")
        assert log1 is log2
        assert len(log2.handlers) == handler_count

    def test_file_handler(self, tmp_path):
        log = get_logger("test_logger", log_dir=str(tmp_path))
        assert len(log.handlers) == 2  # console + file
        log.info("test message")
        log_file = tmp_path / "test_logger.log"
        assert log_file.exists()
