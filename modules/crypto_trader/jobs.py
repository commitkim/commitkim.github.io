"""
Crypto Trader — Job definitions for the scheduler registry.
"""

from core.scheduler.registry import JobDefinition


def register_jobs(registry):
    """Register crypto trading scheduled jobs."""
    from core.config import Config
    cfg = Config.instance()
    schedule_str = cfg.get("crypto_trader.schedule", "0 * * * *")

    registry.register(JobDefinition(
        name="crypto_trade_cycle",
        description="암호화폐 자동매매 사이클",
        schedule=schedule_str,
        command="apps.cli run trader",
        tags=["trader"],
    ))
