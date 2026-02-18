@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================================
echo 🧹 CommitKim: Cleanup All Schedulers
echo ========================================================
echo.

set TASK_MORNING="CommitKim_Morning"
set TASK_EVENING="CommitKim_Evening"
set TASK_AUTOTRADER="CommitKim_AutoTrader"

:: Also include potentially old task names if any
set TASK_OLD_1="CommitKim_Daily_Job"

echo Deleting task: %TASK_MORNING%
schtasks /delete /tn %TASK_MORNING% /f >nul 2>&1

echo Deleting task: %TASK_EVENING%
schtasks /delete /tn %TASK_EVENING% /f >nul 2>&1

echo Deleting task: %TASK_AUTOTRADER%
schtasks /delete /tn %TASK_AUTOTRADER% /f >nul 2>&1

echo Deleting task: %TASK_OLD_1%
schtasks /delete /tn %TASK_OLD_1% /f >nul 2>&1

echo.
echo ✅ All CommitKim related tasks deleted.
pause
