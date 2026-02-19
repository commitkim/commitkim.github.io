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
    def test_registers_trade_cycle_job(self):
        """crypto_trader.jobs should register the crypto_trade_cycle job."""
        from core.scheduler.registry import SchedulerRegistry
        from modules.crypto_trader.jobs import register_jobs

        registry = SchedulerRegistry()
        register_jobs(registry)

        job = registry.get_by_name("crypto_trade_cycle")
        assert job is not None

    def test_command_has_python_m_prefix(self):
        """Trader command must start with 'python -m'."""
        from core.scheduler.registry import SchedulerRegistry
        from modules.crypto_trader.jobs import register_jobs

        registry = SchedulerRegistry()
        register_jobs(registry)

        job = registry.get_by_name("crypto_trade_cycle")
        assert job.command.startswith("apps.cli"), (
            f"Expected 'apps.cli' prefix, got: {job.command!r}"
        )

    def test_schedule_is_hourly(self):
        """Trader should run on the hour every hour."""
        from core.scheduler.registry import SchedulerRegistry
        from modules.crypto_trader.jobs import register_jobs

        registry = SchedulerRegistry()
        register_jobs(registry)

        job = registry.get_by_name("crypto_trade_cycle")
        assert job.schedule.startswith("0 * * * *"), (
            f"Expected hourly cron '0 * * * *', got: {job.schedule!r}"
        )
