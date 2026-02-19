"""
CommitKim Core — In-Process Scheduler Backend

Uses the `schedule` library to run jobs within the current process.
Useful for development, Docker containers, or single-process deployments.
"""

import time
import threading
from typing import List

import schedule as schedule_lib

from core.logger import get_logger
from core.scheduler.backends.base import SchedulerBackend
from core.scheduler.registry import JobDefinition

log = get_logger("scheduler.process")


class ProcessSchedulerBackend(SchedulerBackend):
    """In-process scheduler using the `schedule` library."""

    def __init__(self):
        self._stop_event = threading.Event()

    def install_jobs(self, jobs: List[JobDefinition]) -> None:
        for job in jobs:
            self._register_job(job)
            log.info(f"✅ Scheduled in-process: {job.name} ({job.schedule})")

    def remove_all(self, prefix: str = "CommitKim") -> None:
        schedule_lib.clear()
        log.info("🗑️ Cleared all in-process schedules")

    def list_installed(self) -> List[str]:
        return [str(j) for j in schedule_lib.get_jobs()]

    def run_forever(self) -> None:
        """Block and run scheduled jobs until stop() is called."""
        log.info("🚀 In-process scheduler started. Press Ctrl+C to exit.")
        try:
            while not self._stop_event.is_set():
                schedule_lib.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            log.info("🛑 Scheduler stopped by user.")

    def stop(self) -> None:
        """Signal the scheduler to stop."""
        self._stop_event.set()

    def _register_job(self, job: JobDefinition) -> None:
        """Convert cron expression to schedule library calls."""
        import subprocess
        import sys

        parts = job.schedule.strip().split()
        if len(parts) != 5:
            log.warning(f"Cannot parse schedule '{job.schedule}' for {job.name}")
            return

        minute, hour, *_ = parts

        def run_job():
            log.info(f"▶ Running job: {job.name}")
            subprocess.run([sys.executable, "-m"] + job.command.split())

        # Every N minutes
        if minute.startswith("*/"):
            interval = int(minute.split("/")[1])
            schedule_lib.every(interval).minutes.do(run_job)
        # Every hour
        elif hour == "*" and minute.isdigit():
            schedule_lib.every().hour.at(f":{int(minute):02d}").do(run_job)
        # Specific time daily
        elif minute.isdigit() and hour.isdigit():
            time_str = f"{int(hour):02d}:{int(minute):02d}"
            schedule_lib.every().day.at(time_str).do(run_job)
