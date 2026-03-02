"""
Static Site Builder Core Logic
- Ported from Dashboard/builder.py
- Builds index.html, trade.html
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader

from core.config import PROJECT_ROOT
from core.logger import get_logger

log = get_logger("site_builder.core")

# Paths
MODULE_DIR = PROJECT_ROOT / "modules" / "site_builder"
TEMPLATES_DIR = MODULE_DIR / "templates"
STATIC_DIR = MODULE_DIR / "static"
DOCS_DIR = PROJECT_ROOT / "docs"

# Data Paths (Unified)
DATA_DIR = PROJECT_ROOT / "data"
NEWS_DATA_DIR = DATA_DIR / "news"
NEWS_DATA_DIR = DATA_DIR / "news"
TRADE_DATA_FILE = DATA_DIR / "trade" / "status.json"
MICROGPT_DATA_FILE = DATA_DIR / "microgpt" / "trace.json"


def load_latest_news():
    """Loads the most recent news JSON from data/news/."""
    # Recursive search: data/news/**/*.json
    if not NEWS_DATA_DIR.exists():
        return None

    news_files = list(NEWS_DATA_DIR.rglob("*.json"))

    if not news_files:
        return None

    all_news = []
    for f_path in news_files:
        try:
            with open(f_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'created_at' in data:
                    all_news.append(data)
        except Exception as e:
            log.warning(f"Error loading news {f_path}: {e}")
            continue

    if not all_news:
        return None

    # Sort by created_at descending
    all_news.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return all_news[0]



def load_recent_news_list(limit=7):
    """Loads recent news metadata for sidebar navigation."""
    if not NEWS_DATA_DIR.exists():
        return []

    news_items = []
    # Scan both morning and evening directories
    for mode in ['morning', 'evening']:
        mode_dir = NEWS_DATA_DIR / mode
        if not mode_dir.exists():
            continue

        for f_path in mode_dir.glob("*.json"):
            try:
                with open(f_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Extract minimal info needed for link
                    item = {
                        'date': f_path.stem,  # YYYYMMDD
                        'mode': mode,
                        'title': data.get('video_title', 'News Briefing'),
                        'created_at': data.get('created_at', '')
                    }
                    news_items.append(item)
            except Exception as e:
                log.warning(f"Error loading news metadata {f_path}: {e}")
                continue

    # Sort by created_at descending (or date if created_at missing)
    news_items.sort(key=lambda x: x.get('created_at', x['date']), reverse=True)
    return news_items[:limit]


def load_trade_status():
    """Loads the latest trade status from data/trade/status.json."""
    if TRADE_DATA_FILE.exists():
        try:
            with open(TRADE_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log.error(f"Error loading trade status: {e}")
    return None


def map_reason_code(log_entry):
    """Passes through the direct Korean reason from the AI or log."""
    # Handle both new 'reason_kr' format and old 'reason_code', prioritizing reason_kr if it exists.
    # In the JSON trace, it might just be stored as 'reason' from engine.py
    code_or_reason = log_entry.get('reason_kr', log_entry.get('reason', log_entry.get('reason_code', ''))).strip()

    # Create a simple bullet point for the reason
    explanation = f"<ul class='list-disc pl-5 space-y-1 mt-1'><li>{code_or_reason}</li></ul>"

    log_entry['reason_mapped'] = explanation
    return log_entry



def load_microgpt_data():
    """Loads the latest microgpt trace from data/microgpt/trace.json."""
    if MICROGPT_DATA_FILE.exists():
        try:
            with open(MICROGPT_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log.error(f"Error loading microgpt data: {e}")
    return None


def build_trade_page(output_dir, context):
    """Builds the dedicated trading status page."""

    # Process logs to map reasons
    if context.get('trade') and 'recent_trades' in context['trade']:
        # Create a copy/map to avoid modifying original if needed, but here modifying in place is fine or map
        # map_reason_code modifies dict in place and returns it
        context['trade']['recent_trades'] = [
            map_reason_code(log_item) for log_item in context['trade']['recent_trades']
        ]

    # Group trades by ticker
    grouped_trades = {}
    if context.get('trade') and 'recent_trades' in context['trade']:
        for log_entry in context['trade']['recent_trades']:
            ticker = log_entry.get('ticker', 'Unknown')
            if ticker not in grouped_trades:
                grouped_trades[ticker] = []
            grouped_trades[ticker].append(log_entry)

    context['grouped_trades'] = grouped_trades

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template('trade.html')
    output = template.render(context)

    with open(output_dir / 'index.html', 'w', encoding='utf-8') as f:
        f.write(output)
    log.info("[OK] Built crypto_trader/index.html")


def build_microgpt_page(output_dir, context):
    """Builds the microgpt visualization page."""
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template('microgpt.html')
    output = template.render(context)

    # Output to docs/microgpt/index.html
    microgpt_dir = output_dir / "microgpt"
    microgpt_dir.mkdir(parents=True, exist_ok=True)
    
    with open(microgpt_dir / 'index.html', 'w', encoding='utf-8') as f:
        f.write(output)
    log.info("[OK] Built microgpt/index.html")


def build(output_dir=None):
    """Main build function."""
    if output_dir is None:
        output_dir = DOCS_DIR
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Data
    news_data = load_latest_news()
    recent_news = load_recent_news_list()  # Fetch sidebar list
    trade_data = load_trade_status()
    microgpt_data = load_microgpt_data()

    context = {
        'news': news_data,
        'recent_news': recent_news,  # Pass to template
        'trade': trade_data,
        'microgpt': microgpt_data,
        'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'summary_html': markdown.markdown(news_data.get('web_report', '')) if news_data else None,
        'coin_names': {
            "KRW-BTC": "비트코인",
            "KRW-ETH": "이더리움",
            "KRW-XRP": "리플",
            "KRW-SOL": "솔라나",
            "KRW-AVAX": "아발란체",
            "KRW-DOGE": "도지코인"
        }
    }

    # 2. Render Dashboard (index.html)
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template('dashboard.html')
    output_html = template.render(context)

    with open(output_dir / 'index.html', 'w', encoding='utf-8') as f:
        f.write(output_html)
    log.info(f"[OK] Built index.html at {output_dir}")

    # 3. Render Trade Page
    # Output to docs/crypto_trader/index.html
    if trade_data:
        trade_dir = output_dir / "crypto_trader"
        trade_dir.mkdir(parents=True, exist_ok=True)
        build_trade_page(trade_dir, context)

    # 4. Built MicroGPT Page - Always build as it is client-side now
    build_microgpt_page(output_dir, context)

    # 5. Copy Static Files
    if STATIC_DIR.exists():
        static_dst = output_dir / 'static'
        if static_dst.exists():
            shutil.rmtree(static_dst)
        shutil.copytree(STATIC_DIR, static_dst)
        log.info(f"[OK] Static files copied to {static_dst}")
