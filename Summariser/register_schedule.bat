@echo off
chcp 65001 > nul
cd /d "%~dp0"

set TASK_NAME_MORNING="CommitKim_Morning"
set TASK_NAME_EVENING="CommitKim_Evening"
set RUN_FILE_MORNING="%~dp0run_morning.bat"
set RUN_FILE_EVENING="%~dp0run_evening.bat"

:: Read schedule times from local config.py
:: Now we import config from the current directory (Summariser)
set VENV_PYTHON=..\Dashboard\venv\Scripts\python.exe

for /f "delims=" %%i in ('%VENV_PYTHON% -c "import config; print(config.MORNING_JOB_TIME)"') do set MORNING_TIME=%%i
for /f "delims=" %%i in ('%VENV_PYTHON% -c "import config; print(config.EVENING_JOB_TIME)"') do set EVENING_TIME=%%i

echo.
echo ========================================================
echo 📅 Summariser Scheduler Setup
echo ========================================================
echo.

:: 1. Delete Existing specific Tasks
echo [1/2] Cleaning up old tasks...
schtasks /delete /tn %TASK_NAME_MORNING% /f >nul 2>&1
schtasks /delete /tn %TASK_NAME_EVENING% /f >nul 2>&1

:: 2. Create New Tasks
echo.
echo [2/2] Registering new tasks...
echo.
echo 🌅 [Morning Routine] %MORNING_TIME%
schtasks /create /tn %TASK_NAME_MORNING% /tr "%RUN_FILE_MORNING%" /sc weekly /d MON,TUE,WED,THU,FRI /st %MORNING_TIME% /f

echo 🌇 [Evening Fairy] %EVENING_TIME%
schtasks /create /tn %TASK_NAME_EVENING% /tr "%RUN_FILE_EVENING%" /sc weekly /d MON,TUE,WED,THU,FRI /st %EVENING_TIME% /f

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
