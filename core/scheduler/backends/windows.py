"""
CommitKim Core — Windows Task Scheduler Backend

Translates JobDefinitions into schtasks commands for Windows.

Cron expression mapping:
  "0 9 * * 1-5"          → /sc weekly /d MON,TUE,WED,THU,FRI /st 09:00
  "0 * * * *"            → /sc hourly /mo 1 /st (next hour)
  "30 18 * * 1-5"        → /sc weekly /d MON,TUE,WED,THU,FRI /st 18:30
  "*/10 * * * *"         → /sc minute /mo 10
"""

import subprocess
import sys
from typing import List

from core.logger import get_logger
from core.scheduler.backends.base import SchedulerBackend
from core.scheduler.registry import JobDefinition

log = get_logger("scheduler.windows")

# Day mapping: cron (0=Sun) → schtasks abbreviation
_CRON_DAYS = {
    "0": "SUN", "1": "MON", "2": "TUE", "3": "WED",
    "4": "THU", "5": "FRI", "6": "SAT", "7": "SUN",
}

_TASK_PREFIX = "CommitKim_"


class WindowsSchedulerBackend(SchedulerBackend):
    """Windows Task Scheduler (schtasks.exe) backend."""

    def __init__(self, python_path: str | None = None):
        self.python = python_path or sys.executable

    def install_jobs(self, jobs: List[JobDefinition]) -> None:
        for job in jobs:
            task_name = f"{_TASK_PREFIX}{job.name}"
            schtasks_args = self._cron_to_schtasks(job.schedule)

            if schtasks_args is None:
                log.warning(f"Cannot convert schedule '{job.schedule}' for job '{job.name}'")
                continue

            # Build the command that Task Scheduler will execute
            cmd = f'"{self.python}" -m {job.command}' if not job.command.startswith('"') else job.command

            # Delete existing task (ignore errors if it doesn't exist)
            self._run_schtasks(["schtasks", "/delete", "/tn", task_name, "/f"], ignore_errors=True)

            # Create new task
            create_cmd = [
                "schtasks", "/create",
                "/tn", task_name,
                "/tr", cmd,
            ] + schtasks_args + ["/f"]

            success = self._run_schtasks(create_cmd)
            if success:
                log.info(f"[OK] Registered: {task_name} ({job.schedule})")
            else:
                log.error(f"[ERR] Failed to register: {task_name}")

    def remove_all(self, prefix: str = "CommitKim") -> None:
        """Remove all tasks matching the prefix."""
        full_prefix = f"{prefix}_" if not prefix.endswith("_") else prefix
        installed = self.list_installed()
        for task_name in installed:
            if task_name.startswith(full_prefix):
                self._run_schtasks(["schtasks", "/delete", "/tn", task_name, "/f"])
                log.info(f"[DEL] Removed: {task_name}")

    def list_installed(self) -> List[str]:
        """List all CommitKim tasks in Task Scheduler."""
        try:
            result = subprocess.run(
                ["schtasks", "/query", "/fo", "CSV", "/nh"],
                capture_output=True, text=True, encoding="cp949", errors="replace",
            )
            tasks = []
            for line in result.stdout.strip().split("\n"):
                if _TASK_PREFIX in line:
                    # CSV format: "\\TaskName","next_run","status"
                    name = line.split(",")[0].strip('"').strip("\\")
                    tasks.append(name)
            return tasks
        except Exception as e:
            log.error(f"Failed to list tasks: {e}")
            return []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _cron_to_schtasks(self, cron_expr: str) -> list[str] | None:
        """
        Convert a cron expression to schtasks arguments.
        Supports common patterns — not a full cron parser.
        """
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            return None

        minute, hour, day_m, month, day_w = parts

        # Every N minutes: "*/10 * * * *"
        if minute.startswith("*/") and hour == "*":
            interval = minute.split("/")[1]
            return ["/sc", "minute", "/mo", interval]

        # Every hour: "0 * * * *"
        if hour == "*" and minute.isdigit():
            return ["/sc", "hourly", "/mo", "1"]

        # Specific time, specific weekdays: "0 9 * * 1-5"
        if minute.isdigit() and hour.isdigit() and day_w != "*":
            time_str = f"{int(hour):02d}:{int(minute):02d}"
            days = self._parse_days(day_w)
            if days:
                return ["/sc", "weekly", "/d", days, "/st", time_str]

        # Specific time, daily: "0 9 * * *"
        if minute.isdigit() and hour.isdigit() and day_w == "*":
            time_str = f"{int(hour):02d}:{int(minute):02d}"
            return ["/sc", "daily", "/st", time_str]

        return None

    def _parse_days(self, day_w: str) -> str | None:
        """Parse cron day-of-week field into schtasks /d format."""
        days = []

        for part in day_w.split(","):
            if "-" in part:
                start, end = part.split("-")
                for d in range(int(start), int(end) + 1):
                    days.append(_CRON_DAYS.get(str(d), ""))
            else:
                days.append(_CRON_DAYS.get(part, ""))

        days = [d for d in days if d]
        return ",".join(days) if days else None

    @staticmethod
    def _run_schtasks(cmd: list[str], ignore_errors: bool = False) -> bool:
        """Run a schtasks command and return success status."""
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, encoding="cp949", errors="replace",
            )
            if result.returncode != 0 and not ignore_errors:
                log.debug(f"schtasks error: {result.stderr}")
                return False
            return True
        except Exception as e:
            if not ignore_errors:
                log.error(f"schtasks exception: {e}")
            return False
