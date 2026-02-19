"""
Unit tests for core.errors — exception hierarchy and @isolated decorator.
"""

import pytest

from core.errors import (
    BuildError,
    CommitKimError,
    ConfigError,
    MessengerError,
    NewsCollectionError,
    TradeExecutionError,
    isolated,
    retry,
)


class TestExceptionHierarchy:
    def test_base_exception(self):
        assert issubclass(CommitKimError, Exception)

    def test_trade_error(self):
        assert issubclass(TradeExecutionError, CommitKimError)

    def test_news_error(self):
        assert issubclass(NewsCollectionError, CommitKimError)

    def test_messenger_error(self):
        assert issubclass(MessengerError, CommitKimError)

    def test_build_error(self):
        assert issubclass(BuildError, CommitKimError)

    def test_config_error(self):
        assert issubclass(ConfigError, CommitKimError)


class TestIsolated:
    def test_isolated_catches_exception(self):
        @isolated("test")
        def failing_function():
            raise ValueError("test error")

        # Should NOT raise — returns None
        result = failing_function()
        assert result is None

    def test_isolated_returns_value(self):
        @isolated("test")
        def working_function():
            return 42

        assert working_function() == 42

    def test_isolated_passes_keyboard_interrupt(self):
        @isolated("test")
        def interrupt():
            raise KeyboardInterrupt()

        with pytest.raises(KeyboardInterrupt):
            interrupt()

    def test_isolated_preserves_function_name(self):
        @isolated("test")
        def my_function():
            pass

        assert my_function.__name__ == "my_function"


class TestRetry:
    def test_retry_succeeds_after_failures(self):
        call_count = 0

        @retry(max_retries=3, delay=0.01)
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("temporary failure")
            return "success"

        result = flaky()
        assert result == "success"
        assert call_count == 3

    def test_retry_raises_after_max_retries(self):
        @retry(max_retries=2, delay=0.01)
        def always_fails():
            raise ValueError("permanent failure")

        with pytest.raises(ValueError, match="permanent failure"):
            always_fails()

    def test_retry_passes_keyboard_interrupt(self):
        @retry(max_retries=3, delay=0.01)
        def interrupted():
            raise KeyboardInterrupt()

        with pytest.raises(KeyboardInterrupt):
            interrupted()

    def test_retry_preserves_function_name(self):
        @retry(max_retries=2, delay=0.01)
        def my_api_call():
            return 42

        assert my_api_call.__name__ == "my_api_call"
        assert my_api_call() == 42

    def test_retry_specific_exceptions(self):
        call_count = 0

        @retry(max_retries=3, delay=0.01, exceptions=(ConnectionError,))
        def specific_retry():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("network error")
            if call_count == 2:
                raise ValueError("different error")
            return "done"

        # Should retry ConnectionError but NOT ValueError
        with pytest.raises(ValueError):
            specific_retry()
        assert call_count == 2

