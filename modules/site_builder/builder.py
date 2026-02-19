"""
Static Site Builder (was: Dashboard/builder.py)

Builds the main dashboard HTML from templates and data.
Delegates to the existing Dashboard/builder.py during Phase 2.

Refactored: uses core.config and core.logger.
"""

import os
import sys
from pathlib import Path

from core.config import Config, PROJECT_ROOT
from core.logger import get_logger
from core.errors import isolated

log = get_logger("site_builder")

# Paths
_DASHBOARD_DIR = PROJECT_ROOT / "Dashboard"
_DOCS_DIR = PROJECT_ROOT / "docs"


@isolated("site_builder")
def build():
    """Build the main dashboard (index.html, trade.html, etc.)."""
    log.info("Building main dashboard...")

    # Use the existing Dashboard builder
    sys.path.insert(0, str(_DASHBOARD_DIR))
    try:
        # Import and run the existing builder
        import importlib
        spec = importlib.util.spec_from_file_location(
            "dashboard_builder", _DASHBOARD_DIR / "builder.py"
        )
        builder_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder_module)
        builder_module.build()
        log.info("Dashboard build complete.")
    finally:
        if str(_DASHBOARD_DIR) in sys.path:
            sys.path.remove(str(_DASHBOARD_DIR))


@isolated("site_builder")
def build_news():
    """Build the news/summariser sub-site pages."""
    log.info("Building news sub-site...")

    # Use the existing Summariser generator
    _summariser_dir = PROJECT_ROOT / "Summariser"
    sys.path.insert(0, str(_summariser_dir))
    try:
        import importlib
        spec = importlib.util.spec_from_file_location(
            "summariser_generator", _summariser_dir / "modules" / "generator.py"
        )
        gen_module = importlib.util.module_from_spec(spec)

        # The generator needs 'config' module to be importable
        if "config" not in sys.modules:
            config_spec = importlib.util.spec_from_file_location(
                "config", _summariser_dir / "config.py"
            )
            config_module = importlib.util.module_from_spec(config_spec)
            sys.modules["config"] = config_module
            config_spec.loader.exec_module(config_module)

        spec.loader.exec_module(gen_module)
        gen_module.build_all()
        log.info("News sub-site build complete.")
    finally:
        if str(_summariser_dir) in sys.path:
            sys.path.remove(str(_summariser_dir))


def build_all():
    """Build everything: dashboard + news sub-site."""
    build()
    build_news()
    log.info("All builds complete.")
