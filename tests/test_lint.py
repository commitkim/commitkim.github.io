"""
Linting tests for the project.
"""

import subprocess


def test_project_linting():
    """Run ruff linter to ensure code meets standards."""
    result = subprocess.run(["ruff", "check", "."], capture_output=True, text=True)
    assert result.returncode == 0, f"Linting failed. Please fix the following errors:\n{result.stdout}\n{result.stderr}"
