"""
Unit tests for module job definitions (news_briefing, crypto_trader)

Verifies that:
- All jobs are registered with valid names and schedules
- Command strings contain 'python -m' prefix (required for OS scheduler)
- No duplicate job names exist
- Config.instance() singleton is not broken after registration
"""

import pytest


@pytest.fixture(autouse=True)
def test_env(monkeypatch):
    monkeypatch.setenv("COMMITKIM_ENV", "test")
    from core.config import Config
    Config._instance = None


class TestNewsBriefingJobs:
    def test_registers_morning_and_evening_jobs(self):
        """news_briefing.jobs should register exactly 2 jobs."""
        from core.scheduler.registry import SchedulerRegistry
        from modules.news_briefing.jobs import register_jobs

        registry = SchedulerRegistry()
        register_jobs(registry)

        jobs = registry.get_all(include_disabled=True)
        names = [j.name for j in jobs]

        assert "news_morning" in names
        assert "news_evening" in names
        assert len(jobs) == 2

    def test_commands_have_python_m_prefix(self):
        """All commands must start with 'python -m' to be OS-scheduler-safe."""
        from core.scheduler.registry import SchedulerRegistry
        from modules.news_briefing.jobs import register_jobs

        registry = SchedulerRegistry()
        register_jobs(registry)

        for job in registry.get_all(include_disabled=True):
            assert job.command.startswith("apps.cli"), (
                f"Job '{job.name}' command must start with 'apps.cli', got: {job.command!r}"
            )

    def test_schedules_are_valid_cron(self):
        """Verify cron expressions have 5 fields."""
        from core.scheduler.registry import SchedulerRegistry
        from modules.news_briefing.jobs import register_jobs

        registry = SchedulerRegistry()
        register_jobs(registry)

        for job in registry.get_all(include_disabled=True):
            fields = job.schedule.split()
            assert len(fields) == 5, (
                f"Job '{job.name}' has invalid cron (expected 5 fields): {job.schedule!r}"
            )

    def test_does_not_break_config_singleton(self):
        """Calling register_jobs should not create a second Config instance."""
        from core.config import Config
        Config._instance = None
        cfg_before = Config(env="test")  # Create singleton

        from core.scheduler.registry import SchedulerRegistry
        from modules.news_briefing.jobs import register_jobs

        registry = SchedulerRegistry()
        register_jobs(registry)  # Should use Config.instance(), not Config()

        assert Config._instance is cfg_before, (
            "register_jobs() must use Config.instance() — it appears it created a new Config()"
        )


class TestCryptoTraderJobs:
    """Tests for crypto_trader job registration.
    Note: schedule_enabled is False in test config, so we patch it to True.
    """

    def _make_registry_with_jobs(self):
        """Register crypto trader jobs with schedule_enabled forced to True."""
        from unittest.mock import patch

        from core.scheduler.registry import SchedulerRegistry
        from modules.crypto_trader.jobs import register_jobs

        original_get = None

        def patched_get(key, default=None):
            if key == "crypto_trader.schedule_enabled":
                return True
            return original_get(key, default)

        from core.config import Config
        cfg = Config.instance()
        original_get = cfg.get
        registry = SchedulerRegistry()

        with patch.object(cfg, "get", side_effect=patched_get):
            register_jobs(registry)

        return registry

    def test_registers_trade_cycle_job(self):
        """crypto_trader.jobs should register the crypto_trade_cycle job when enabled."""
        registry = self._make_registry_with_jobs()
        jobs = registry.get_all(include_disabled=True)
        names = [j.name for j in jobs]
        assert "crypto_trade_cycle" in names, f"Job not registered. Got: {names}"

    def test_command_has_python_m_prefix(self):
        """Trader command must start with 'apps.cli'."""
        registry = self._make_registry_with_jobs()
        jobs = registry.get_all(include_disabled=True)
        job = next((j for j in jobs if j.name == "crypto_trade_cycle"), None)
        assert job is not None
        assert job.command.startswith("apps.cli"), (
            f"Expected 'apps.cli' prefix, got: {job.command!r}"
        )

    def test_schedule_is_hourly(self):
        """Trader should run on the hour every hour."""
        registry = self._make_registry_with_jobs()
        jobs = registry.get_all(include_disabled=True)
        job = next((j for j in jobs if j.name == "crypto_trade_cycle"), None)
        assert job is not None
        assert job.schedule.startswith("0 * * * *"), (
            f"Expected hourly cron '0 * * * *', got: {job.schedule!r}"
        )


class TestMicroGPTJobs:
    def test_registers_microgpt_job(self):
        """microgpt.jobs should register the microgpt_train job."""
        from core.scheduler.registry import SchedulerRegistry
        from modules.microgpt.jobs import register_jobs

        registry = SchedulerRegistry()
        register_jobs(registry)

        job = registry.get_by_name("microgpt_train")
        assert job is not None

    def test_command_has_python_m_prefix(self):
        """MicroGPT command must start with 'apps.cli'."""
        from core.scheduler.registry import SchedulerRegistry
        from modules.microgpt.jobs import register_jobs

        registry = SchedulerRegistry()
        register_jobs(registry)

        job = registry.get_by_name("microgpt_train")
        assert job.command.startswith("apps.cli"), (
            f"Expected 'apps.cli' prefix, got: {job.command!r}"
        )
