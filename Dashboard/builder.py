import os
import json
import glob
import shutil
import sys
from datetime import datetime
import markdown
from jinja2 import Environment, FileSystemLoader

# Set encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

# Configuration
# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(BASE_DIR, 'data')
DOCS_DIR = os.path.join(PROJECT_ROOT, 'docs')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')

def load_latest_news():
    """Loads the most recent news JSON from data/news/ subdirectories."""
    # Summariser saves to: Dashboard/data/news/[morning|evening]/YYYY-MM-DD.json
    # We search recursively: Dashboard/data/news/**/*.json
    news_dir = os.path.join(DATA_DIR, 'news')
    news_files = glob.glob(os.path.join(news_dir, '**', '*.json'), recursive=True)
    
    if not news_files:
        return None
    
    all_news = []
    for f_path in news_files:
        try:
            with open(f_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure it has a date
                if 'created_at' in data:
                    all_news.append(data)
        except:
            continue
            
    if not all_news:
        return None
        
    # Sort by created_at descending
    all_news.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return all_news[0]

def load_trade_status():
    """Loads the latest trade status from Auto trader/data/status.json."""
    status_path = os.path.join(PROJECT_ROOT, 'Auto trader', 'data', 'status.json')
    if os.path.exists(status_path):
        try:
            with open(status_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading trade status: {e}")
    return None

def build_trade_page(output_dir, context):
    """Builds the dedicated trading status page."""
    env = Environment(loader=FileSystemLoader(os.path.join(PROJECT_ROOT, 'Dashboard', 'templates')))
    template = env.get_template('trade.html')
    output = template.render(context)
    
    with open(os.path.join(output_dir, 'trade.html'), 'w', encoding='utf-8') as f:
        f.write(output)
    print("✅ Built trade.html")

def build(output_dir=None):
    if output_dir is None:
        output_dir = os.path.join(PROJECT_ROOT, 'docs') # Output to docs for GitHub Pages
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Load Data
    news_data = load_latest_news()
    trade_data = load_trade_status() # Load trade data
    
    context = {
        'news': news_data,
        'trade': trade_data, # Pass trade data to context
        'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'summary_html': markdown.markdown(news_data.get('web_report', '')) if news_data else None,
    }

    # 2. Render Dashboard (index.html)
    env = Environment(loader=FileSystemLoader(os.path.join(PROJECT_ROOT, 'Dashboard', 'templates')))
    template = env.get_template('dashboard.html')
    output_html = template.render(context)
    
    with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(output_html)
    print(f"✅ Built index.html at {output_dir}")
    
    # 3. Render Trade Page
    if trade_data:
        build_trade_page(output_dir, context)

    # 4. Copy Static Files
    static_src = os.path.join(BASE_DIR, 'static')
    static_dst = os.path.join(output_dir, 'static')
    if os.path.exists(static_src):
        if os.path.exists(static_dst):
             shutil.rmtree(static_dst)
        shutil.copytree(static_src, static_dst)
        print(f"✅ Static files copied to {static_dst}")

def load_all_news():
    """Loads all news JSON files from data/news/."""
    news_files = glob.glob(os.path.join(DATA_DIR, 'news', '*.json'))
    news_files.sort(key=os.path.getctime, reverse=True)
    return news_files

if __name__ == "__main__":
    build()
