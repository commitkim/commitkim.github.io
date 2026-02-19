"""
Static Site Builder Wrapper
- Delegates to modules.site_builder.core and modules.news_briefing.page_builder
- Replaces legacy Dashboard/builder.py usage
"""

from core.logger import get_logger
from core.errors import isolated

log = get_logger("site_builder")


@isolated("site_builder")
def build():
    """Build the main dashboard (index.html, trade.html)."""
    log.info("Building main dashboard...")
    from modules.site_builder import core
    core.build()
    log.info("Dashboard build complete.")


@isolated("site_builder")
def build_news():
    """Build the news sub-site (detail pages, reports)."""
    log.info("Building news sub-site...")
    from modules.news_briefing import page_builder
    page_builder.build_all()
    log.info("News sub-site build complete.")


def build_all():
    """Build everything: dashboard + news sub-site."""
    build()
    build_news()
    log.info("All builds complete.")
