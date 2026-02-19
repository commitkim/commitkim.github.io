"""
CommitKim Core — Abstract Scheduler Backend

All OS-specific scheduler implementations extend this base class.
"""

from abc import ABC, abstractmethod
from typing import List

from core.scheduler.registry import JobDefinition


class SchedulerBackend(ABC):
    """Abstract base for OS-specific scheduler implementations."""

    @abstractmethod
    def install_jobs(self, jobs: List[JobDefinition]) -> None:
        """Install/register the given jobs with the OS scheduler."""
        ...

    @abstractmethod
    def remove_all(self, prefix: str = "CommitKim") -> None:
        """Remove all jobs matching the given prefix."""
        ...

    @abstractmethod
    def list_installed(self) -> List[str]:
        """List currently installed job names."""
        ...

    def sync(self, jobs: List[JobDefinition]) -> None:
        """Remove old jobs and install new ones (convenience method)."""
        self.remove_all()
        self.install_jobs(jobs)
