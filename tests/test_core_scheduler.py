"""
Unit tests for core.scheduler — registry and job definitions.
"""

import pytest
from core.scheduler.registry import SchedulerRegistry, JobDefinition


class TestJobDefinition:
    def test_create_job(self):
        job = JobDefinition(
            name="test_job",
            description="Test",
            schedule="0 9 * * *",
            command="echo test",
        )
        assert job.name == "test_job"
        assert job.enabled is True
        assert job.tags == []

    def test_job_with_tags(self):
        job = JobDefinition(
            name="tagged",
            description="Tagged job",
            schedule="0 * * * *",
            command="echo",
            tags=["news", "morning"],
        )
        assert "news" in job.tags

    def test_job_empty_name_raises(self):
        with pytest.raises(ValueError, match="name"):
            JobDefinition(name="", description="", schedule="0 * * * *", command="x")

    def test_job_empty_schedule_raises(self):
        with pytest.raises(ValueError, match="schedule"):
            JobDefinition(name="test", description="", schedule="", command="x")


class TestSchedulerRegistry:
    def test_register_and_get_all(self):
        reg = SchedulerRegistry()
        reg.register(JobDefinition("j1", "desc", "0 * * * *", "cmd1"))
        reg.register(JobDefinition("j2", "desc", "0 9 * * *", "cmd2"))

        assert len(reg) == 2
        assert len(reg.get_all()) == 2

    def test_duplicate_name_raises(self):
        reg = SchedulerRegistry()
        reg.register(JobDefinition("dup", "desc", "0 * * * *", "cmd"))

        with pytest.raises(ValueError, match="already registered"):
            reg.register(JobDefinition("dup", "desc2", "0 9 * * *", "cmd2"))

    def test_get_by_name(self):
        reg = SchedulerRegistry()
        reg.register(JobDefinition("finder", "desc", "0 * * * *", "cmd"))

        found = reg.get_by_name("finder")
        assert found is not None
        assert found.name == "finder"
        assert reg.get_by_name("missing") is None

    def test_get_by_tag(self):
        reg = SchedulerRegistry()
        reg.register(JobDefinition("j1", "", "0 * * * *", "c1", tags=["news"]))
        reg.register(JobDefinition("j2", "", "0 * * * *", "c2", tags=["trader"]))
        reg.register(JobDefinition("j3", "", "0 * * * *", "c3", tags=["news"]))

        news_jobs = reg.get_by_tag("news")
        assert len(news_jobs) == 2

    def test_disabled_jobs_excluded_by_default(self):
        reg = SchedulerRegistry()
        reg.register(JobDefinition("a", "", "0 * * * *", "c", enabled=True))
        reg.register(JobDefinition("b", "", "0 * * * *", "c", enabled=False))

        assert len(reg.get_all()) == 1
        assert len(reg.get_all(include_disabled=True)) == 2
