"""
Crypto Trader — Job definitions for the scheduler registry.
"""

from core.scheduler.registry import JobDefinition


def register_jobs(registry):
    """Register crypto trading scheduled jobs."""
    registry.register(JobDefinition(
        name="crypto_trade_cycle",
        description="암호화폐 자동매매 사이클 (매시 정각)",
        schedule="0 * * * *",
        command="python -m apps.cli run trader",
        tags=["trader"],
    ))
