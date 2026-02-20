
from core.scheduler.registry import JobDefinition
from core.config import Config

def register_jobs(registry):
    # This module is primarily for educational visualization and runs on demand
    # or via specific triggers, so no default schedule is strictly required.
    # However, we can add a dummy or disable-by-default job for consistency.
    cfg = Config.instance()
    enabled = cfg.get("microgpt.schedule_enabled", False)

    registry.register(JobDefinition(
        name="microgpt_train",
        description="Run MicroGPT training and generate visualization",
        schedule="0 10 * * *", # Example: Run once a day at 10 AM if enabled
        command="apps.cli run microgpt",
        tags=["microgpt"],
        enabled=enabled,
    ))
