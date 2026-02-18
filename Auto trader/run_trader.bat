@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo.
echo ========================================================
echo 🚀 Auto Trader Manual Execution
echo ========================================================
echo.

..\Dashboard\venv\Scripts\python trader.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Execution Failed!
    exit /b %ERRORLEVEL%
)

echo.
echo ✅ Execution Finished.
echo 📊 Check 'logs/' folder or Dashboard for details.
