@echo off
chcp 65001 > nul
echo 📰 Running Summariser Task...

:: Use the shared venv from Dashboard
..\Dashboard\venv\Scripts\python main.py run --no-deploy

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Summariser task failed!
    exit /b %ERRORLEVEL%
)
echo ✅ Summariser task completed.
