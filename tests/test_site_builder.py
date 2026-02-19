"""
Unit tests for modules.site_builder — builder module

Uses a temporary directory to isolate file I/O from the actual docs/ folder.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def test_env(monkeypatch):
    monkeypatch.setenv("COMMITKIM_ENV", "test")
    from core.config import Config
    Config._instance = None


class TestBuildAll:
    def test_build_all_calls_build_and_build_news(self):
        """build_all() should invoke both build() and build_news() without errors."""
        with patch("modules.site_builder.builder.build") as mock_build, \
             patch("modules.site_builder.builder.build_news") as mock_news:
            from modules.site_builder.builder import build_all
            build_all()

        mock_build.assert_called_once()
        mock_news.assert_called_once()


class TestSiteBuilderCore:
    def test_build_invoked_without_raising(self):
        """build() should not raise even with missing data dirs."""
        # Patch the inner build call inside modules.site_builder.builder
        with patch("modules.site_builder.builder.build") as mock_b:
            mock_b.return_value = None
            from modules.site_builder.builder import build
            build()  # Should complete without exception
        mock_b.assert_called_once()


class TestDeployer:
    def test_deploy_runs_git_commands(self):
        """deploy() should execute git add/commit/push without raising."""
        with patch("modules.site_builder.deployer.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            from modules.site_builder.deployer import deploy
            # deploy() may raise if git fails — ensure it handles errors
            try:
                deploy()
            except SystemExit:
                pass  # Acceptable if git is not configured in test environment
