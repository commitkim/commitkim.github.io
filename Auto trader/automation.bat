@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo [Auto Trader] Running...
..\Dashboard\venv\Scripts\python main.py

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Auto Trader Failed!
    exit /b %ERRORLEVEL%
)

:: --------------------------------------------------------
:: 🚀 Global Test & Deploy (Auto Mode)
:: --------------------------------------------------------
echo.
echo [Auto Trader] Triggering Global Deployment...
call ..\build_test_deploy.bat auto

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Global Deployment Failed!
    exit /b %ERRORLEVEL%
)

echo ✅ All workflows completed!
