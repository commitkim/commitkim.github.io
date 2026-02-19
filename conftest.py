"""
conftest.py — pytest configuration

Excludes legacy test files that depend on old module structure
and third-party packages not installed in CI.
"""

# Only run new core tests — legacy tests are excluded
collect_ignore = [
    "tests/test_summariser.py",
    "tests/test_summariser_live.py",
    "tests/test_autotrader.py",
    "tests/test_autotrader_strategy.py",
    "tests/test_dashboard_wrapper.py",
]
