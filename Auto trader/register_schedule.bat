@echo off
chcp 65001 > nul
cd /d "%~dp0"

set TASK_NAME="CommitKim_AutoTrader"
set "RUN_FILE=%~dp0automation.bat"

:: Frequent Schedule: Every 60 minutes (1 Hour)
echo.
echo ========================================================
echo 🤖 Auto Trader Scheduler Setup
echo ========================================================
echo.

:: 1. Delete Existing Task
echo [1/2] Cleaning up old task...
schtasks /delete /tn %TASK_NAME% /f >nul 2>&1

:: 2. Create New Task
echo.
echo [2/2] Registering new task...
echo    Running every 60 minutes infinitely.
schtasks /create /tn %TASK_NAME% /tr "\"%RUN_FILE%\"" /sc minute /mo 60 /f

if %errorlevel% neq 0 (
    echo.
    echo ❌ Registration Failed!
    echo ⚠️ Please run as Administrator.
    pause
    exit /b 1
)

echo.
echo ✅ Schedule Registered Successfully!
pause
