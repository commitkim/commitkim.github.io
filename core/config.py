"""
CommitKim Core — Hierarchical Configuration Loader

Loads configuration in order of priority:
  1. config/base.yaml       (shared defaults)
  2. config/{env}.yaml      (environment overrides: dev/prod/test)
  3. .env file              (secrets — never committed to git)

Usage:
    from core.config import Config
    cfg = Config()                         # auto-detects env from COMMITKIM_ENV
    cfg = Config(env="dev")                # explicit environment

    model = cfg.get("ai.model")           # "gemini-2.5-flash"
    coins = cfg.get("crypto_trader.coins") # ["KRW-BTC", ...]
    url = cfg.get("github.pages_url")     # "https://commitkim.github.io"
"""

import os
import copy
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# Resolve project root (the parent of the 'core/' directory)
# ---------------------------------------------------------------------------
_CORE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _CORE_DIR.parent


class Config:
    """Hierarchical config: base.yaml → env.yaml → .env overrides."""

    _instance: "Config | None" = None  # Singleton for convenience

    def __init__(self, env: str | None = None):
        # Load .env early so COMMITKIM_ENV can come from there
        load_dotenv(PROJECT_ROOT / ".env")

        self.env = env or os.getenv("COMMITKIM_ENV", "prod")
        self._data: dict = {}
        self._load()

        # Cache as singleton
        Config._instance = self

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get(self, dotted_key: str, default: Any = None) -> Any:
        """
        Retrieve a value using dot-separated keys.
        Example: config.get("crypto_trader.capital.max_coins_held")
        """
        keys = dotted_key.split(".")
        val: Any = self._data
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
                if val is None:
                    return default
            else:
                return default
        return val

    def get_secret(self, env_var: str, default: str | None = None) -> str | None:
        """
        Retrieve a secret from environment variables (.env file).
        Secrets are NEVER stored in YAML files.
        """
        return os.getenv(env_var, default)

    def as_dict(self) -> dict:
        """Return a deep copy of the entire config tree."""
        return copy.deepcopy(self._data)

    @classmethod
    def instance(cls) -> "Config":
        """Return the singleton Config. Creates one if not yet initialized."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _load(self):
        config_dir = PROJECT_ROOT / "config"

        # 1. Base config (always loaded)
        base = config_dir / "base.yaml"
        if base.exists():
            with open(base, encoding="utf-8") as f:
                self._data = yaml.safe_load(f) or {}

        # 2. Environment-specific override
        env_file = config_dir / f"{self.env}.yaml"
        if env_file.exists():
            with open(env_file, encoding="utf-8") as f:
                env_data = yaml.safe_load(f) or {}
                self._deep_merge(self._data, env_data)

    @staticmethod
    def _deep_merge(base: dict, override: dict):
        """Recursively merge override into base (in-place)."""
        for key, value in override.items():
            if (
                key in base
                and isinstance(base[key], dict)
                and isinstance(value, dict)
            ):
                Config._deep_merge(base[key], value)
            else:
                base[key] = value

    def __repr__(self) -> str:
        return f"Config(env={self.env!r}, keys={list(self._data.keys())})"
