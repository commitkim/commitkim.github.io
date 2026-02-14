"""
정적 HTML 생성 모듈 (Jinja2 기반)
- data/*.json → docs/ 하위 HTML 파일 빌드
- index.html, archive.html, reports/YYYY-MM-DD.html 생성
"""

import os
import json
import shutil
import markdown

from jinja2 import Environment, FileSystemLoader

import config


def _load_all_data():
    """
    data/ 디렉토리의 모든 JSON 파일을 로드합니다.
    
    Returns:
        list[dict]: 날짜 기준 최신순 정렬된 데이터 목록
    """
    data_list = []
    
    if not os.path.exists(config.DATA_DIR):
        os.makedirs(config.DATA_DIR, exist_ok=True)
        return data_list
    
    for filename in os.listdir(config.DATA_DIR):
        if not filename.endswith('.json'):
            continue
        
        filepath = os.path.join(config.DATA_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['_filename'] = filename
                data['_date'] = filename.replace('.json', '')
                data_list.append(data)
        except Exception as e:
            print(f"⚠️ JSON 로드 실패 ({filename}): {e}")
    
    # 날짜 내림차순 정렬
    data_list.sort(key=lambda x: x['_date'], reverse=True)
    return data_list


def _render_markdown(text):
    """Markdown 텍스트를 HTML로 변환합니다."""
    if not text:
        return ""
    return markdown.markdown(
        text,
        extensions=['tables', 'fenced_code', 'nl2br']
    )


def _setup_jinja():
    """Jinja2 환경을 설정합니다."""
    env = Environment(
        loader=FileSystemLoader(config.TEMPLATES_DIR),
        autoescape=True
    )
    # 커스텀 필터 등록
    env.filters['markdown'] = _render_markdown
    return env


def build_all():
    """
    전체 사이트를 빌드합니다.
    data/*.json → docs/ 하위 HTML 파일 생성
    """
    print("\n🔨 정적 사이트 빌드 시작...")
    
    # 1. 출력 디렉토리 준비
    os.makedirs(config.DOCS_DIR, exist_ok=True)
    os.makedirs(os.path.join(config.DOCS_DIR, 'reports'), exist_ok=True)
    os.makedirs(os.path.join(config.DOCS_DIR, 'data'), exist_ok=True)
    
    # 2. 데이터 로드
    all_data = _load_all_data()
    
    if not all_data:
        print("ℹ️ 빌드할 데이터가 없습니다. (data/ 디렉토리가 비어있음)")
        return
    
    # 3. Jinja2 환경 설정
    env = _setup_jinja()
    
    # 4. 각 날짜별 상세 페이지 빌드 (reports/YYYY-MM-DD.html)
    detail_template = env.get_template('detail.html')
    for i, data in enumerate(all_data):
        prev_data = all_data[i - 1] if i > 0 else None
        next_data = all_data[i + 1] if i < len(all_data) - 1 else None
        
        html = detail_template.render(
            data=data,
            prev_date=prev_data['_date'] if prev_data else None,
            next_date=next_data['_date'] if next_data else None,
            web_report_html=_render_markdown(data.get('web_report', '')),
            base_path='../',
            build_time=_get_build_time()
        )
        
        output_path = os.path.join(config.DOCS_DIR, 'reports', f"{data['_date']}.html")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
    
    print(f"  📄 상세 페이지 {len(all_data)}개 생성")
    
    # 5. 메인 페이지 빌드 (index.html) — 최신 데이터 사용
    latest = all_data[0]
    index_template = env.get_template('index.html')
    html = index_template.render(
        data=latest,
        recent_list=all_data[:5],  # 최근 5개 표시
        web_report_html=_render_markdown(latest.get('web_report', '')),
        base_path='',
        build_time=_get_build_time()
    )
    
    with open(os.path.join(config.DOCS_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    print("  📄 index.html 생성")
    
    # 6. 아카이브 페이지 빌드 (archive.html)
    archive_template = env.get_template('archive.html')
    html = archive_template.render(
        data_list=all_data,
        base_path='',
        build_time=_get_build_time()
    )
    
    with open(os.path.join(config.DOCS_DIR, 'archive.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  📄 archive.html 생성 (총 {len(all_data)}일치)")
    
    # 7. JSON 데이터 복사 (docs/data/)
    for data in all_data:
        src = os.path.join(config.DATA_DIR, data['_filename'])
        dst = os.path.join(config.DOCS_DIR, 'data', data['_filename'])
        shutil.copy2(src, dst)
    
    print(f"\n✅ 빌드 완료! (docs/ 디렉토리에 {len(all_data) + 2}개 파일 생성)")


def _get_build_time():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M KST")
