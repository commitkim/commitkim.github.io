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

def build(output_dir=None):
    """Renders the dashboard and saves it to docs/index.html (or custom output_dir)."""
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template('dashboard.html')
    
    news_files = load_all_news()
    news_data = load_latest_news()
    
    context = {
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'news': news_data,
        # Add more context here as we integrate more features
    }
    
    output_html = template.render(context)
    
    target_dir = output_dir if output_dir else DOCS_DIR
    os.makedirs(target_dir, exist_ok=True)
    output_path = os.path.join(target_dir, 'index.html')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_html)
    
    print(f"Build completed successfully! Output: {output_path}")

    # Build detail pages and archive
    build_reports(news_files, target_dir)
    build_archive(news_files, target_dir)

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

def build_reports(news_files, output_dir=DOCS_DIR):
    """Generates individual report pages."""
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template('detail.html')
    
    reports_dir = os.path.join(output_dir, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    for file_path in news_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                news_data = json.load(f)
            
            output_html = template.render(news={'video_title': news_data.get('video_title', 'Untitled'),
                                              'video_date': news_data.get('video_date', 'Unknown Date'),
                                              'youtube_url': news_data.get('youtube_url'),
                                              'key_insights': news_data.get('key_insights', []),
                                              'summary_content': news_data.get('summary_content'),
                                              'kakao_summary': news_data.get('kakao_summary')})
            
            filename = os.path.basename(file_path).replace('.json', '.html')
            output_path = os.path.join(reports_dir, filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_html)
                
            print(f"Generated report: {filename}")
        except Exception as e:
            print(f"Error generating report for {file_path}: {e}")

def build_archive(news_files, output_dir=DOCS_DIR):
    """Generates the archive page."""
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template('archive.html')
    
    archive_data = []
    for file_path in news_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                archive_data.append({
                    'title': data.get('video_title', 'Untitled'),
                    'date': data.get('video_date', 'Unknown Date'),
                    'filename': os.path.basename(file_path).replace('.json', '.html')
                })
        except:
            continue
            
    output_html = template.render(archive=archive_data)
    output_path = os.path.join(output_dir, 'archive.html')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_html)
    print("Generated archive page.")

if __name__ == "__main__":
    build()
