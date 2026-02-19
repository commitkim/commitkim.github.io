"""
Git 배포 모듈 (Refactored from Dashboard/deploy.py)

Uses core.config for Git path and GitHub credentials.
"""

import subprocess
from datetime import datetime

from core.config import PROJECT_ROOT, Config
from core.logger import get_logger

log = get_logger("site_builder.deployer")


def _run_git(*args):
    """Git 명령을 실행하고 결과를 반환합니다."""
    cfg = Config.instance()
    git_path = cfg.get_secret("GIT_EXECUTABLE") or "git"

    cmd = [git_path] + list(args)

    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=60
        )
        if result.returncode != 0:
            log.warning(f"git {' '.join(args)} 실패: {result.stderr.strip()}")
        return result
    except FileNotFoundError:
        log.error(f"Git을 찾을 수 없습니다. ({git_path})")
        return None
    except subprocess.TimeoutExpired:
        log.error(f"Git 명령 타임아웃: git {' '.join(args)}")
        return None


def deploy(commit_message=None):
    """
    변경사항을 Git으로 커밋하고 push합니다.

    Args:
        commit_message: 커밋 메시지 (기본: 날짜 기반 자동 생성)

    Returns:
        bool: 성공 여부
    """
    cfg = Config.instance()

    if not commit_message:
        commit_message = f"Auto-deploy: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    log.info("Git 배포 시작...")

    # 1. HTTPS + PAT 설정
    token = cfg.get_secret("GITHUB_TOKEN")
    repo_url = cfg.get_secret("GITHUB_REPO_URL") or ""

    if token and repo_url.startswith("https://"):
        authed_url = repo_url.replace("https://", f"https://{token}@")
        _run_git("remote", "set-url", "origin", authed_url)

    # 2. Stage all changes
    result = _run_git("add", ".")
    if result is None:
        return False

    # 3. Check for changes
    status = _run_git("status", "--porcelain")
    if status and not status.stdout.strip():
        log.info("변경사항 없음. 배포 생략.")
        return True

    # 4. Commit
    result = _run_git("commit", "-m", commit_message)
    if result is None or result.returncode != 0:
        if result and "nothing to commit" in result.stdout:
            log.info("커밋할 내용 없음.")
            return True
        return False

    log.info(f"커밋 완료: {commit_message}")

    # 5. Push
    result = _run_git("push", "origin", "main")
    if result is None or result.returncode != 0:
        log.warning("'main' 브랜치 push 실패. 'master' 시도...")
        result = _run_git("push", "origin", "master")
        if result is None or result.returncode != 0:
            log.error("Git push 실패. 브랜치 이름을 확인하세요.")
            return False

    log.info("Git push 완료! GitHub Pages에 곧 반영됩니다.")
    return True
