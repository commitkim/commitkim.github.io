"""
CommitKim Core — Error Isolation & Custom Exceptions

Provides:
  1. Module-specific exception hierarchy
  2. @isolated decorator that catches exceptions so one failing module
     does not crash the entire system

Usage:
    from core.errors import isolated, TradeExecutionError

    @isolated("crypto_trader")
    def run_trade_cycle():
        ...  # If this raises, it's logged but won't crash the scheduler

    # Or raise specific exceptions:
    raise TradeExecutionError("Insufficient balance")
"""

import functools
import traceback
from typing import Callable, Any


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
