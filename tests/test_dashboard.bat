@echo off
chcp 65001 > nul
echo 🧪 Running Dashboard Builder Test...

"%~dp0..\Dashboard\venv\Scripts\python.exe" "%~dp0test_dashboard_wrapper.py"

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Dashboard Build Failed!
    exit /b 1
)


