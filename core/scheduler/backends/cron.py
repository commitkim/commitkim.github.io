"""
CommitKim Core — Unix Cron Backend

Translates JobDefinitions into crontab entries for Linux/macOS.
"""

import os
import subprocess
import sys
from typing import List

from core.logger import get_logger
from core.scheduler.backends.base import SchedulerBackend
from core.scheduler.registry import JobDefinition

log = get_logger("scheduler.cron")

_MARKER = "# CommitKim Managed"


class CronSchedulerBackend(SchedulerBackend):
    """Unix crontab backend."""

    def __init__(self, python_path: str | None = None, project_root: str | None = None):
        self.python = python_path or sys.executable
        self.project_root = project_root or os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

    def install_jobs(self, jobs: List[JobDefinition]) -> None:
        # Read current crontab
        existing = self._read_crontab()

        # Remove our managed lines
        cleaned = [line for line in existing if _MARKER not in line]

        # Add new lines
        for job in jobs:
            cmd = f"cd {self.project_root} && {self.python} -m {job.command}"
            entry = f"{job.schedule} {cmd}  {_MARKER} [{job.name}]"
            cleaned.append(entry)
            log.info(f"✅ Added cron entry: {job.name} ({job.schedule})")

        self._write_crontab(cleaned)

    def remove_all(self, prefix: str = "CommitKim") -> None:
        existing = self._read_crontab()
        cleaned = [line for line in existing if _MARKER not in line]
        self._write_crontab(cleaned)
        log.info("🗑️ Removed all CommitKim cron entries")

    def list_installed(self) -> List[str]:
        existing = self._read_crontab()
        jobs = []
        for line in existing:
            if _MARKER in line:
                # Extract job name from: ... # CommitKim Managed [name]
                try:
                    name = line.split("[")[-1].rstrip("]")
                    jobs.append(name)
                except IndexError:
                    pass
        return jobs

    @staticmethod
    def _read_crontab() -> List[str]:
        try:
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip().split("\n")
            return []
        except Exception:
            return []

    @staticmethod
    def _write_crontab(lines: List[str]) -> None:
        content = "\n".join(lines) + "\n"
        proc = subprocess.Popen(
            ["crontab", "-"],
            stdin=subprocess.PIPE, text=True,
        )
        proc.communicate(input=content)
