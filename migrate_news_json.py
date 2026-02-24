import glob
import json

# Convert newer json files to old format
files = glob.glob('data/news/*/*.json')
modified_count = 0
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    modified = False
    
    # 23일 이후 데이터이거나 타이틀이 있는 경우 전환
    if 'title' in data:
        data['video_title'] = data.pop('title')
        modified = True
    if 'date' in data:
        data['video_date'] = data.pop('date')
        modified = True
    if 'video_url' not in data and 'video_id' in data:
        data['video_url'] = f"https://youtube.com/watch?v={data['video_id']}"
        modified = True
    if 'market_summary' not in data:
        data['market_summary'] = {}
        modified = True
        
    if modified:
        with open(f, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        print(f"Updated {f}")
        modified_count += 1

print(f"Migration complete. Updated {modified_count} files.")
