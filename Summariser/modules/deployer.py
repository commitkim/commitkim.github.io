"""
Git 배포 모듈
- docs/ 및 data/ 변경사항을 자동으로 commit & push
- HTTPS + PAT 또는 SSH 지원
"""

import os
import subprocess

import config


def _run_git(*args):
    """Git 명령을 실행하고 결과를 반환합니다."""
    git_path = config.GIT_EXECUTABLE
    cmd = [git_path] + list(args)
    
    try:
        result = subprocess.run(
            cmd,
            cwd=config.PROJECT_DIR,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=60
        )
        if result.returncode != 0:
            print(f"⚠️ git {' '.join(args)} 실패: {result.stderr.strip()}")
        return result
    except FileNotFoundError:
        print(f"❌ Git을 찾을 수 없습니다. ({git_path})")
        print("   Git을 설치하거나 config.py의 GIT_EXECUTABLE 경로를 확인하세요.")
        return None
    except subprocess.TimeoutExpired:
        print(f"❌ Git 명령 타임아웃: git {' '.join(args)}")
        return None


def deploy(commit_message=None):
    """
    변경사항을 Git으로 커밋하고 push합니다.
    
    Args:
        commit_message: 커밋 메시지 (기본: 날짜 기반 자동 생성)
    
    Returns:
        bool: 성공 여부
    """
    from datetime import datetime
    
    if not commit_message:
        commit_message = f"📰 뉴스 요약 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    print(f"\n📦 Git 배포 시작...")
    
    # 1. HTTPS + PAT 설정 (토큰이 있는 경우)
    token = config.GITHUB_TOKEN
    repo_url = config.GITHUB_REPO_URL
    
    if token and repo_url:
        # remote URL에 토큰 삽입 (https://TOKEN@github.com/user/repo.git)
        if repo_url.startswith("https://"):
            authed_url = repo_url.replace("https://", f"https://{token}@")
            _run_git("remote", "set-url", "origin", authed_url)
    
    # 2. data/ 및 docs/ 스테이징
    result = _run_git("add", "data/", "docs/")
    if result is None:
        return False
    
    # 3. 변경사항 확인
    status = _run_git("status", "--porcelain")
    if status and not status.stdout.strip():
        print("ℹ️ 변경사항 없음. 배포 생략.")
        return True
    
    # 4. 커밋
    result = _run_git("commit", "-m", commit_message)
    if result is None or result.returncode != 0:
        # 커밋할 내용이 없는 경우도 처리
        if result and "nothing to commit" in result.stdout:
            print("ℹ️ 커밋할 내용 없음.")
            return True
        return False
    
    print(f"✅ 커밋 완료: {commit_message}")
    
    # 5. Push
    result = _run_git("push", "origin", "main")
    if result is None or result.returncode != 0:
        # main 브랜치가 아닐 수 있음 → master 시도
        print("⚠️ 'main' 브랜치 push 실패. 'master' 시도...")
        result = _run_git("push", "origin", "master")
        if result is None or result.returncode != 0:
            print("❌ Git push 실패. 브랜치 이름을 확인하세요.")
            return False
    
    print("✅ Git push 완료! GitHub Pages에 곧 반영됩니다.")
    return True
