import os
import json
import glob
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')

def load_latest_news():
    news_files = glob.glob(os.path.join(DATA_DIR, 'news', '*.json'))
    if not news_files:
        return None
    latest_file = max(news_files, key=os.path.getctime)
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def build_preview():
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template('dashboard.html')
    
    news_data = load_latest_news()
    
    # Mock data if no news exists
    if not news_data:
        news_data = {
            'video_title': 'Preview News Title',
            'video_date': '2026-02-14',
            'kakao_summary': 'This is a preview of the summary text to show how the design looks with content.'
        }

    context = {
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'news': news_data,
    }
    
    output_html = template.render(context)
    output_path = os.path.join(BASE_DIR, 'preview.html')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_html)
    
    print(f"Preview generated at: {output_path}")

if __name__ == "__main__":
    build_preview()
