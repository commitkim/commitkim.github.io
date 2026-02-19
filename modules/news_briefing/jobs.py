"""
News Briefing — Job definitions for the scheduler registry.
"""

from core.scheduler.registry import JobDefinition
from core.config import Config


def register_jobs(registry):
    """Register news briefing scheduled jobs."""
    cfg = Config.instance()
    enabled = cfg.get("news_briefing.schedule_enabled", True)

    registry.register(JobDefinition(
        name="news_morning",
        description="아침 경제 뉴스 브리핑 (모닝루틴)",
        schedule="0 9 * * 1-5",
        command="python -m apps.cli run news --mode morning",
        tags=["news", "morning"],
        enabled=enabled,
    ))
    registry.register(JobDefinition(
        name="news_evening",
        description="저녁 퇴근요정 브리핑",
        schedule="30 18 * * 1-5",
        command="python -m apps.cli run news --mode evening",
        tags=["news", "evening"],
        enabled=enabled,
    ))
