"""
CommitKim — Unified CLI Entry Point

Single command to run any module, manage schedules, build, deploy, and test.

Usage:
    python -m apps.cli run news --mode morning
    python -m apps.cli run trader
    python -m apps.cli build
    python -m apps.cli deploy
    python -m apps.cli schedule --install
    python -m apps.cli schedule --list
    python -m apps.cli setup kakao
"""

import argparse
import platform

from core.config import Config
from core.logger import get_logger

log = get_logger("cli")


def _run_news(args):
    """Run the news briefing pipeline."""
    mode = getattr(args, 'mode', 'morning')
    log.info(f"Running news briefing ({mode} mode)...")

    from modules.messenger.kakao import send_message
    from modules.news_briefing import collector, summarizer

    cfg = Config.instance()
    keyword = cfg.get(f"news_briefing.modes.{mode}.keyword")

    # 1. Collect videos
    candidates = collector.find_todays_videos(keyword=keyword)
    if not candidates:
        log.warning("오늘자 영상을 찾지 못했습니다.")
        return

    # 2. Extract transcript & summarize
    for video_id, title, date_str in candidates:
        log.info(f"Processing: {title}")
        transcript = collector.extract_transcript(video_id)
        if not transcript:
            log.warning(f"자막 추출 실패: {title}")
            continue

        summary = summarizer.summarize(transcript, video_id)
        if not summary:
            log.warning(f"요약 생성 실패: {title}")
            continue

        # 3. Save data
        _save_summary(summary, date_str, mode, video_id, title)

        # 4. Send KakaoTalk
        if summary.get('kakao_summary'):
            header = cfg.get(f"news_briefing.modes.{mode}.title_prefix", "뉴스 요약")
            message = f"📰 {header}\n\n{summary['kakao_summary']}"
            send_message(message)

    # 5. Build & Deploy
    if not getattr(args, 'no_deploy', False):
        _build_and_deploy()


def _run_trader(args):
    """Run the crypto trading cycle."""
    log.info("Running crypto trading cycle...")

    from modules.crypto_trader.trader import CryptoTrader

    trader = CryptoTrader()
    trader.run_cycle()

    # Build & Deploy to update dashboard (skip in CI)
    if not getattr(args, 'no_deploy', False):
        _build_and_deploy()


def _run_microgpt(args):
    """Run MicroGPT training and visualization."""
    log.info("Running MicroGPT...")

    from modules.microgpt.engine import MicroGPTVisualizer
    
    viz = MicroGPTVisualizer()
    viz.run()
    
    # Build & Deploy to update dashboard
    if not getattr(args, 'no_deploy', False):
        _build_and_deploy()


def _build(args=None):
    """Build the static site."""
    log.info("Building static site...")

    from modules.site_builder.builder import build_all
    build_all()


def _deploy(args=None):
    """Deploy to GitHub Pages."""
    log.info("Deploying to GitHub Pages...")

    from modules.site_builder.deployer import deploy
    deploy()


def _deploy_command(args):
    """Run tests then deploy (CLI command)."""
    if _run_tests():
        _deploy(args)


def _build_and_deploy():
    """Build then deploy."""
    _build()
    _deploy()


def _run_tests():
    """Run unit tests."""
    import subprocess
    import sys

    log.info("Running tests before deploy...")

    # Run pytest
    # We use sys.executable to ensure we use the same python interpreter
    cmd = [sys.executable, "-m", "pytest", "tests/"]

    try:
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            log.error("Tests failed! Aborting deploy.")
            return False
        log.info("Tests passed.")
        return True
    except Exception as e:
        log.error(f"Error running tests: {e}")
        return False


def _schedule(args):
    """Manage scheduled tasks."""
    from core.scheduler import SchedulerRegistry

    registry = SchedulerRegistry()

    # Register all module jobs
    from modules.crypto_trader.jobs import register_jobs as register_trader
    from modules.news_briefing.jobs import register_jobs as register_news
    from modules.microgpt.jobs import register_jobs as register_microgpt

    register_news(registry)
    register_trader(registry)
    register_microgpt(registry)

    if getattr(args, 'list', False):
        log.info(f"Registered jobs ({len(registry)}):")
        for job in registry.get_all(include_disabled=True):
            status = "[ON]" if job.enabled else "[OFF]"
            print(f"  {status:5s} {job.name:25s} {job.schedule:15s} {job.description}")
        return

    if getattr(args, 'install', False):
        backend = _get_scheduler_backend()
        jobs = registry.get_all()
        backend.sync(jobs)
        log.info(f"Installed {len(jobs)} jobs on {platform.system()}")
        return

    if getattr(args, 'remove', False):
        backend = _get_scheduler_backend()
        backend.remove_all()
        log.info("Removed all scheduled jobs.")
        return

    # Default: show list
    _schedule_list(registry)


def _schedule_list(registry):
    """Show all registered jobs."""
    for job in registry.get_all(include_disabled=True):
        status = "[ON]" if job.enabled else "[OFF]"
        print(f"  {status:5s} {job.name:25s} {job.schedule:15s} {job.description}")


def _get_scheduler_backend():
    """Get the appropriate scheduler backend for the current OS."""
    system = platform.system()

    if system == "Windows":
        from core.scheduler.backends.windows import WindowsSchedulerBackend
        return WindowsSchedulerBackend()
    elif system in ("Linux", "Darwin"):
        from core.scheduler.backends.cron import CronSchedulerBackend
        return CronSchedulerBackend()
    else:
        from core.scheduler.backends.process import ProcessSchedulerBackend
        return ProcessSchedulerBackend()


def _setup(args):
    """Run setup wizards."""
    target = getattr(args, 'target', None)

    if target == 'kakao':
        from modules.messenger.kakao import setup_auth
        setup_auth()
    else:
        print("Available setup targets: kakao")


def _save_summary(summary, date_str, mode, video_id, title):
    """Save summary data to JSON file."""
    import json
    import os
    from datetime import datetime

    from core.config import PROJECT_ROOT

    data_dir = PROJECT_ROOT / "data" / "news" / mode
    os.makedirs(data_dir, exist_ok=True)

    data = {
        "video_id": video_id,
        "title": title,
        "date": date_str,
        "mode": mode,
        "created_at": datetime.now().isoformat(),
        **summary
    }

    filepath = data_dir / f"{date_str}.json"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    log.info(f"데이터 저장: {filepath}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="commitkim",
        description="CommitKim - AI-powered personal assistant CLI",
    )
    parser.add_argument(
        "--env", choices=["dev", "prod", "test"], default=None,
        help="Environment (default: COMMITKIM_ENV or prod)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- run ---
    run_parser = subparsers.add_parser("run", help="Run a module")
    run_sub = run_parser.add_subparsers(dest="module")

    # run news
    news_parser = run_sub.add_parser("news", help="Run news briefing")
    news_parser.add_argument("--mode", choices=["morning", "evening"], default="morning")
    news_parser.add_argument("--no-deploy", action="store_true", help="Skip deployment")
    news_parser.set_defaults(func=_run_news)

    # run trader
    trader_parser = run_sub.add_parser("trader", help="Run crypto trading cycle")
    trader_parser.add_argument("--no-deploy", action="store_true", help="Skip build and deployment")
    trader_parser.set_defaults(func=_run_trader)

    # run microgpt
    microgpt_parser = run_sub.add_parser("microgpt", help="Run MicroGPT visualization")
    microgpt_parser.add_argument("--no-deploy", action="store_true", help="Skip build and deployment")
    microgpt_parser.set_defaults(func=_run_microgpt)

    # --- build ---
    build_parser = subparsers.add_parser("build", help="Build static site")
    build_parser.set_defaults(func=_build)

    # --- deploy ---
    deploy_parser = subparsers.add_parser("deploy", help="Deploy to GitHub Pages")
    deploy_parser.set_defaults(func=_deploy_command)

    # --- schedule ---
    sched_parser = subparsers.add_parser("schedule", help="Manage scheduled tasks")
    sched_parser.add_argument("--install", action="store_true", help="Install all scheduled jobs")
    sched_parser.add_argument("--list", action="store_true", help="List all scheduled jobs")
    sched_parser.add_argument("--remove", action="store_true", help="Remove all scheduled jobs")
    sched_parser.set_defaults(func=_schedule)

    # --- setup ---
    setup_parser = subparsers.add_parser("setup", help="Run setup wizards")
    setup_parser.add_argument("target", nargs="?", help="Setup target (e.g., kakao)")
    setup_parser.set_defaults(func=_setup)

    # Parse and execute
    args = parser.parse_args()

    # Initialize config with env from CLI flag
    Config(env=args.env)

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
