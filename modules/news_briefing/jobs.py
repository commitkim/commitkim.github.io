"""
News Briefing — Job definitions for the scheduler registry.
"""

from core.config import Config
from core.scheduler.registry import JobDefinition


def register_jobs(registry):
    """Register news briefing scheduled jobs."""
    cfg = Config.instance()
    enabled = cfg.get("news_briefing.schedule_enabled", True)

    morning_schedule = cfg.get("news_briefing.modes.morning.schedule", "0 10 * * 1-5")
    evening_schedule = cfg.get("news_briefing.modes.evening.schedule", "30 18 * * 1-5")

    registry.register(JobDefinition(
        name="news_morning",
        description="아침 경제 뉴스 브리핑 (모닝루틴)",
        schedule=morning_schedule,
        command="apps.cli run news --mode morning",
        tags=["news", "morning"],
        enabled=enabled and cfg.get("news_briefing.morning_enabled", True),
    ))
    registry.register(JobDefinition(
        name="news_evening",
        description="저녁 퇴근요정 브리핑",
        schedule=evening_schedule,
        command="apps.cli run news --mode evening",
        tags=["news", "evening"],
        enabled=enabled and cfg.get("news_briefing.evening_enabled", True),
    ))
