"""
CommitKim Core — Unified Logging

Provides consistent log formatting across all modules.
Supports both console and file output with automatic rotation.

Usage:
    from core.logger import get_logger
    log = get_logger("crypto_trader")
    log = get_logger("news_briefing", log_dir="logs/")  # + file output
"""

import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

# Default format matching the style already used in the project
_DEFAULT_FMT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# Track which loggers have been configured to avoid duplicate handlers
_configured: set[str] = set()


def get_logger(
    name: str,
    log_dir: str | None = None,
    level: int = logging.INFO,
    fmt: str = _DEFAULT_FMT,
) -> logging.Logger:
    """
    Return a configured logger.

    Args:
        name:    Logger name (usually module name, e.g. "crypto_trader").
        log_dir: If provided, also logs to a rotating file in this directory.
        level:   Logging level (default: INFO).
        fmt:     Log line format string.

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)

    # Only configure once per name
    if name in _configured:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(fmt)

    # ── Console handler ──────────────────────────────────────────────
    # On Windows the default console encoding is cp949 / cp1252 which
    # cannot render emoji.  Force UTF-8 with error-replacement so
    # logging never crashes the process.
    import io
    import os
    stream = sys.stdout
    if os.name == "nt":
        # Create a wrapper that doesn't close the underlying stdout
        class NoCloseTextIOWrapper(io.TextIOWrapper):
            def close(self):
                self.flush()
                # Do NOT call super().close() to keep stdout open

        stream = NoCloseTextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace",
        )

    console = logging.StreamHandler(stream)
    console.setFormatter(formatter)
    console.setLevel(level)
    logger.addHandler(console)

    # ── File handler (optional) ──────────────────────────────────────
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        file_handler = TimedRotatingFileHandler(
            filename=log_path / f"{name}.log",
            when="midnight",
            backupCount=30,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

    # Prevent log propagation to the root logger (avoids duplicate output)
    logger.propagate = False
    _configured.add(name)

    return logger
