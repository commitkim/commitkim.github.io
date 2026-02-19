"""
News Page Builder
- Ported from Summariser/modules/generator.py
- Builds detail pages, archive.html, reports/
"""

import os
import json
import shutil
import markdown
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from core.config import PROJECT_ROOT
from core.logger import get_logger

log = get_logger("news_briefing.page_builder")

# Paths
MODULE_DIR = PROJECT_ROOT / "modules" / "news_briefing"
TEMPLATES_DIR = MODULE_DIR / "templates"
DOCS_DIR = PROJECT_ROOT / "docs"
NEWS_DATA_DIR = PROJECT_ROOT / "data" / "news"


def _load_all_data():
    """
    Load all JSON files from data/news/morning and data/news/evening.
    """
    data_list = []
    
    if not NEWS_DATA_DIR.exists():
        return data_list
    
    for mode in ['morning', 'evening']:
        mode_dir = NEWS_DATA_DIR / mode
        if not mode_dir.exists():
            continue
            
        for filepath in mode_dir.glob("*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    filename = filepath.name
                    data['_filename'] = f"{mode}/{filename}"
                    data['_date'] = filename.replace('.json', '')
                    data['_mode'] = mode
                    data_list.append(data)
            except Exception as e:
                log.warning(f"Error loading JSON ({filepath}): {e}")
    
    # Sort by created_at descending
    data_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return data_list


def _render_markdown(text):
    """Convert Markdown to HTML."""
    if not text:
        return ""
    return markdown.markdown(
        text,
        extensions=['tables', 'fenced_code', 'nl2br']
    )


def _setup_jinja():
    """Setup Jinja2 environment."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True
    )
    env.filters['markdown'] = _render_markdown
    return env


def _get_build_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M KST")


def build_all():
    """Build the news sub-site."""
    log.info("Building news sub-site...")
    
    # 1. Prepare Output Dirs
    (DOCS_DIR / "reports").mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / "data").mkdir(parents=True, exist_ok=True)
    
    # 2. Load Data
    all_data = _load_all_data()
    
    if not all_data:
        log.info("No news data found to build.")
        return
    
    # 3. Setup Jinja
    env = _setup_jinja()
    
    # 4. Build Detail Pages
    detail_template = env.get_template('detail.html')
    
    mode_groups = {'morning': [], 'evening': []}
    for d in all_data:
        mode = d.get('_mode', 'morning')
        mode_groups[mode].append(d)
        
    for mode, group in mode_groups.items():
        for i, data in enumerate(group):
            prev_data = group[i - 1] if i > 0 else None
            next_data = group[i + 1] if i < len(group) - 1 else None
            
            html = detail_template.render(
                data=data,
                prev_date=prev_data['_date'] if prev_data else None,
                next_date=next_data['_date'] if next_data else None,
                web_report_html=_render_markdown(data.get('web_report', '')),
                base_path='../../', # reports/mode/ directory
                build_time=_get_build_time()
            )
            
            mode_report_dir = DOCS_DIR / "reports" / mode
            mode_report_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = mode_report_dir / f"{data['_date']}.html"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)

    log.info(f"Generated {len(all_data)} detail pages.")
    
    # 5. Build Main Report (Latest)
    # The main index.html for news is typically report.html? 
    # Legacy output to DOCS_DIR / 'report.html'
    latest = all_data[0]
    # Note: Using index.html template but saving as report.html because root index.html is the Dashboard
    index_template = env.get_template('index.html') 
    
    html = index_template.render(
        data=latest,
        recent_list=all_data[:5],
        web_report_html=_render_markdown(latest.get('web_report', '')),
        base_path='',
        build_time=_get_build_time()
    )
    
    with open(DOCS_DIR / 'report.html', 'w', encoding='utf-8') as f:
        f.write(html)
        
    # 6. Archive Page
    archive_template = env.get_template('archive.html')
    html = archive_template.render(
        mode_groups=mode_groups,
        base_path='',
        build_time=_get_build_time()
    )
    with open(DOCS_DIR / 'archive.html', 'w', encoding='utf-8') as f:
        f.write(html)
        
    # 7. Copy JSON Data
    for data in all_data:
        src = NEWS_DATA_DIR / data['_filename']
        dst = DOCS_DIR / 'data' / data['_filename']
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        
    log.info("News sub-site build complete.")
