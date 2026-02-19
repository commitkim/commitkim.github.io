"""
CommitKim — Unified Schedule Registration

Registers all scheduled jobs with the OS-appropriate backend.
Replaces the 3 separate register_schedule.bat files.

Usage:
    python scripts/register_all.py          # Install all jobs
    python scripts/register_all.py --list   # Show jobs
    python scripts/register_all.py --remove # Uninstall all
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.cli import main as cli_main

if __name__ == "__main__":
    # Forward to CLI schedule command
    sys.argv = [sys.argv[0], "schedule"] + sys.argv[1:]
    cli_main()
