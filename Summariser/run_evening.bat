@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo 🌇 [퇴근요정] 수집 및 요약 시작...
call automation.bat evening
pause
