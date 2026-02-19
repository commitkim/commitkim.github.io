"""
conftest.py — pytest configuration

Excludes legacy test files during the transition period.
"""

# Legacy tests still import from old config structure — skip during transition
collect_ignore = [
    "tests/test_summariser.py",
    "tests/test_summariser_live.py",
]
