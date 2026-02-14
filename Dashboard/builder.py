import os
import json
import glob
import shutil
from datetime import datetime
import markdown
from jinja2 import Environment, FileSystemLoader

# Configuration
# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(BASE_DIR, 'data')
DOCS_DIR = os.path.join(PROJECT_ROOT, 'docs')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')

def load_latest_news():
    """Loads the most recent news JSON from data/news/ subdirectories."""
    # Search recursively for JSON files
    news_files = glob.glob(os.path.join(DATA_DIR, 'news', '**', '*.json'), recursive=True)
    if not news_files:
        return None
    
    all_news = []
    for f_path in news_files:
        try:
            with open(f_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_news.append(data)
        except:
            continue
            
    if not all_news:
        return None
        
    # Sort by created_at descending
    all_news.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return all_news[0]

def build(output_dir=None):
    """Renders the dashboard and saves it to docs/index.html (or custom output_dir)."""
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template('dashboard.html')
    
    news_files = load_all_news()
    news_data = load_latest_news()
    
    context = {
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'news': news_data,
        'summary_html': markdown.markdown(news_data.get('web_report', '')) if news_data else None,
        # Add more context here as we integrate more features
    }
    
    output_html = template.render(context)
    
    target_dir = output_dir if output_dir else DOCS_DIR
    os.makedirs(target_dir, exist_ok=True)
    output_path = os.path.join(target_dir, 'index.html')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_html)
    
    print(f"Build completed successfully! Output: {output_path}")

    # Copy static files
    static_src = os.path.join(BASE_DIR, 'static')
    static_dst = os.path.join(target_dir, 'static')
    if os.path.exists(static_src):
        if os.path.exists(static_dst):
             shutil.rmtree(static_dst)
        shutil.copytree(static_src, static_dst)
        print(f"Static files copied to {static_dst}")

def load_all_news():
    """Loads all news JSON files from data/news/."""
    news_files = glob.glob(os.path.join(DATA_DIR, 'news', '*.json'))
    news_files.sort(key=os.path.getctime, reverse=True)
    return news_files

if __name__ == "__main__":
    build()
