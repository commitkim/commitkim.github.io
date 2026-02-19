"""
CommitKim Core — Error Isolation & Custom Exceptions

Provides:
  1. Module-specific exception hierarchy
  2. @isolated decorator — catches exceptions, prevents cascade failures
  3. @retry decorator — retries with exponential backoff for API calls

Usage:
    from core.errors import isolated, retry, TradeExecutionError

    @isolated("crypto_trader")
    def run_trade_cycle():
        ...  # If this raises, it's logged but won't crash the scheduler

    @retry(max_retries=3, delay=2.0)
    def call_api():
        ...  # Retries up to 3 times with exponential backoff
"""

import functools
import time
import traceback
from typing import Any, Callable


# ---------------------------------------------------------------------------
# Exception Hierarchy
# ---------------------------------------------------------------------------
class CommitKimError(Exception):
    """Base exception for all CommitKim modules."""
    pass


class TradeExecutionError(CommitKimError):
    """Raised when a trade cannot be executed."""
    pass


class NewsCollectionError(CommitKimError):
    """Raised when news collection or summarization fails."""
    pass


class MessengerError(CommitKimError):
    """Raised when messaging (KakaoTalk) fails."""
    pass


class BuildError(CommitKimError):
    """Raised when static site build or deploy fails."""
    pass


class ConfigError(CommitKimError):
    """Raised when configuration is invalid or missing."""
    pass


# ---------------------------------------------------------------------------
# Isolation Decorator
# ---------------------------------------------------------------------------
def isolated(logger_name: str | None = None) -> Callable:
    """
    Decorator that isolates a function's execution.

    If the decorated function raises an exception:
      - The error is logged (with full traceback at DEBUG level)
      - The function returns None instead of propagating the exception
      - The rest of the system continues running

    Args:
        logger_name: Name for the logger (defaults to the function's module).

    Example:
        @isolated("crypto_trader")
        def run_cycle():
            ...  # safe — won't crash the scheduler
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Lazy import to avoid circular dependency
            from core.logger import get_logger

            log = get_logger(logger_name or func.__module__)
            try:
                return func(*args, **kwargs)
            except KeyboardInterrupt:
                # Always let Ctrl+C through
                raise
            except Exception as e:
                log.error(f"Module '{func.__name__}' failed: {e}")
                log.debug(traceback.format_exc())
                return None  # Graceful degradation

        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Retry Decorator
# ---------------------------------------------------------------------------
def retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    logger_name: str | None = None,
) -> Callable:
    """
    Decorator that retries a function on failure with exponential backoff.

    Essential for API calls (Upbit, Gemini, KakaoTalk) that may temporarily fail.

    Args:
        max_retries: Maximum number of retry attempts.
        delay: Initial delay between retries (seconds).
        backoff: Multiplier applied to delay after each retry.
        exceptions: Tuple of exception types to catch and retry on.
        logger_name: Logger name for retry messages.

    Example:
        @retry(max_retries=3, delay=2.0)
        def call_upbit_api():
            ...  # Retries up to 3 times: wait 2s, 4s, 8s
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            from core.logger import get_logger

            log = get_logger(logger_name or func.__module__)
            current_delay = delay

            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except KeyboardInterrupt:
                    raise
                except exceptions as e:
                    if attempt == max_retries:
                        log.error(f"'{func.__name__}' failed after {max_retries} retries: {e}")
                        raise
                    log.warning(
                        f"'{func.__name__}' attempt {attempt}/{max_retries} failed: {e}. "
                        f"Retrying in {current_delay:.1f}s..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff

        return wrapper
    return decorator
