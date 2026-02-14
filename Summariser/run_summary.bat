@echo off
echo ========================================
echo 📰 뉴스 요약 실행
echo ========================================
cd /d %~dp0
.\venv\Scripts\python main.py run
pause
