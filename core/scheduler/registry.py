"""
CommitKim Core — Central Scheduler Registry

All modules register their jobs here. OS-specific backends read from
this registry to install/manage scheduled tasks.

Usage:
    from core.scheduler import SchedulerRegistry, JobDefinition

    registry = SchedulerRegistry()

    # Modules register their jobs:
    registry.register(JobDefinition(
        name="news_morning",
        description="아침 경제 뉴스 브리핑",
        schedule="0 9 * * 1-5",
        command="python -m apps.cli run news --mode morning",
    ))

    # Backends read jobs:
    for job in registry.get_all():
        backend.install(job)
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class JobDefinition:
    """A single schedulable job."""

    name: str                # Unique ID, e.g. "news_morning"
    description: str         # Human-readable, e.g. "아침 경제 뉴스 브리핑"
    schedule: str            # Cron expression, e.g. "0 9 * * 1-5"
    command: str             # CLI command to run
    enabled: bool = True     # Can be disabled without removing
    tags: list[str] = field(default_factory=list)  # e.g. ["news", "morning"]

    def __post_init__(self):
        if not self.name:
            raise ValueError("JobDefinition.name cannot be empty")
        if not self.schedule:
            raise ValueError("JobDefinition.schedule cannot be empty")


class SchedulerRegistry:
    """
    Central registry of all scheduled jobs.

    Modules call register() to declare their jobs.
    Backends call get_all() to read and install them.
    """

    def __init__(self):
        self._jobs: List[JobDefinition] = []

    def register(self, job: JobDefinition) -> None:
        """Register a job definition."""
        # Prevent duplicate names
        if any(j.name == job.name for j in self._jobs):
            raise ValueError(f"Job '{job.name}' is already registered")
        self._jobs.append(job)

    def get_all(self, include_disabled: bool = False) -> List[JobDefinition]:
        """Return all registered jobs (enabled only by default)."""
        if include_disabled:
            return list(self._jobs)
        return [j for j in self._jobs if j.enabled]

    def get_by_name(self, name: str) -> Optional[JobDefinition]:
        """Find a job by its unique name."""
        return next((j for j in self._jobs if j.name == name), None)

    def get_by_tag(self, tag: str) -> List[JobDefinition]:
        """Find all jobs with the given tag."""
        return [j for j in self._jobs if tag in j.tags and j.enabled]

    def __len__(self) -> int:
        return len(self._jobs)

    def __repr__(self) -> str:
        return f"SchedulerRegistry(jobs={len(self._jobs)})"
