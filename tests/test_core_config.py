"""
Unit tests for core.config — YAML hierarchical config loader.
"""

from pathlib import Path


def _create_config_files(tmpdir):
    """Create test YAML files in a temporary directory."""
    config_dir = Path(tmpdir) / "config"
    config_dir.mkdir()

    base = config_dir / "base.yaml"
    base.write_text("""
ai:
  model: "gemini-base"
crypto_trader:
  coins:
    - "KRW-BTC"
    - "KRW-ETH"
  interval_minutes: 60
github:
  pages_url: "https://test.example.com"
logging:
  level: "INFO"
""", encoding="utf-8")

    dev = config_dir / "dev.yaml"
    dev.write_text("""
logging:
  level: "DEBUG"
ai:
  model: "gemini-dev"
""", encoding="utf-8")

    test = config_dir / "test.yaml"
    test.write_text("""
logging:
  level: "WARNING"
crypto_trader:
  interval_minutes: 1
""", encoding="utf-8")

    return config_dir


class TestConfig:
    def test_base_config_loads(self, tmp_path, monkeypatch):
        """Test that base.yaml loads correctly."""
        _create_config_files(tmp_path)
        monkeypatch.setattr("core.config._CORE_DIR", tmp_path / "core")
        monkeypatch.setattr("core.config.PROJECT_ROOT", tmp_path)

        from core.config import Config
        Config._instance = None  # Reset singleton
        cfg = Config(env="prod")

        assert cfg.get("ai.model") == "gemini-base"
        assert cfg.get("crypto_trader.coins") == ["KRW-BTC", "KRW-ETH"]
        assert cfg.get("github.pages_url") == "https://test.example.com"

    def test_env_override(self, tmp_path, monkeypatch):
        """Test that env-specific YAML overrides base values."""
        _create_config_files(tmp_path)
        monkeypatch.setattr("core.config._CORE_DIR", tmp_path / "core")
        monkeypatch.setattr("core.config.PROJECT_ROOT", tmp_path)

        from core.config import Config
        Config._instance = None
        cfg = Config(env="dev")

        assert cfg.get("logging.level") == "DEBUG"
        assert cfg.get("ai.model") == "gemini-dev"
        # Non-overridden values should remain from base
        assert cfg.get("github.pages_url") == "https://test.example.com"

    def test_deep_merge(self, tmp_path, monkeypatch):
        """Test that test env overrides only specified keys."""
        _create_config_files(tmp_path)
        monkeypatch.setattr("core.config._CORE_DIR", tmp_path / "core")
        monkeypatch.setattr("core.config.PROJECT_ROOT", tmp_path)

        from core.config import Config
        Config._instance = None
        cfg = Config(env="test")

        assert cfg.get("crypto_trader.interval_minutes") == 1
        assert cfg.get("crypto_trader.coins") == ["KRW-BTC", "KRW-ETH"]
        assert cfg.get("logging.level") == "WARNING"

    def test_dotted_key_missing_returns_default(self, tmp_path, monkeypatch):
        """Test that missing keys return the default value."""
        _create_config_files(tmp_path)
        monkeypatch.setattr("core.config._CORE_DIR", tmp_path / "core")
        monkeypatch.setattr("core.config.PROJECT_ROOT", tmp_path)

        from core.config import Config
        Config._instance = None
        cfg = Config(env="prod")

        assert cfg.get("nonexistent.key") is None
        assert cfg.get("nonexistent.key", "fallback") == "fallback"

    def test_get_secret(self, monkeypatch):
        """Test that secrets are read from environment variables."""
        monkeypatch.setenv("TEST_SECRET", "my_secret_value")

        from core.config import Config
        Config._instance = None
        cfg = Config.__new__(Config)
        cfg._data = {}
        cfg.env = "test"

        assert cfg.get_secret("TEST_SECRET") == "my_secret_value"
        assert cfg.get_secret("MISSING_SECRET", "default") == "default"

    def test_singleton(self, tmp_path, monkeypatch):
        """Test that Config.instance() returns singleton."""
        _create_config_files(tmp_path)
        monkeypatch.setattr("core.config._CORE_DIR", tmp_path / "core")
        monkeypatch.setattr("core.config.PROJECT_ROOT", tmp_path)

        from core.config import Config
        Config._instance = None

        cfg1 = Config(env="prod")
        cfg2 = Config.instance()

        assert cfg1 is cfg2
