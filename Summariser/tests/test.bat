@echo off
chcp 65001 > nul
cd /d %~dp0\..
set PYTHONIOENCODING=utf-8
echo ========================================
echo 🧪 어제 날짜 기준 파이프라인 테스트
echo ========================================
.\venv\Scripts\python tests\test_yesterday.py
pause
