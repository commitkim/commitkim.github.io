import os
import json
import glob
import shutil
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# Configuration
# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(BASE_DIR, 'data')
DOCS_DIR = os.path.join(PROJECT_ROOT, 'docs')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')

def load_latest_news():
    """Loads the most recent news JSON from data/news/."""
    news_files = glob.glob(os.path.join(DATA_DIR, 'news', '*.json'))
    if not news_files:
        return None
    
    # Sort by filename (assuming YYYY-MM-DD.json format) or modification time
    latest_file = max(news_files, key=os.path.getctime)
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading news file {latest_file}: {e}")
        return None

def build():
    """Renders the dashboard and saves it to docs/index.html."""
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template('dashboard.html')
    
    news_data = load_latest_news()
    
    context = {
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'news': news_data,
        # Add more context here as we integrate more features
    }
    
    output_html = template.render(context)
    
    os.makedirs(DOCS_DIR, exist_ok=True)
    output_path = os.path.join(DOCS_DIR, 'index.html')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_html)
    
    print(f"Build completed successfully! Output: {output_path}")

    # Copy static files
    static_src = os.path.join(BASE_DIR, 'static')
    static_dst = os.path.join(DOCS_DIR, 'static')
    if os.path.exists(static_src):
        if os.path.exists(static_dst):
             shutil.rmtree(static_dst)
        shutil.copytree(static_src, static_dst)
        print(f"Static files copied to {static_dst}")

if __name__ == "__main__":
    build()
