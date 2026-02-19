"""
News Briefing — Job definitions for the scheduler registry.
"""

from core.scheduler.registry import JobDefinition


def register_jobs(registry):
    """Register news briefing scheduled jobs."""
    registry.register(JobDefinition(
        name="news_morning",
        description="아침 경제 뉴스 브리핑 (모닝루틴)",
        schedule="0 9 * * 1-5",
        command="apps.cli run news --mode morning",
        tags=["news", "morning"],
    ))
    registry.register(JobDefinition(
        name="news_evening",
        description="저녁 퇴근요정 브리핑",
        schedule="30 18 * * 1-5",
        command="apps.cli run news --mode evening",
        tags=["news", "evening"],
    ))
