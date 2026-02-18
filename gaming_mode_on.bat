@echo off
chcp 65001 > nul

echo.
echo ========================================================
echo 🎮 Gaming Mode ON (Pause Background Tasks)
echo ========================================================
echo.

echo Disabling Auto Trader...
schtasks /Change /TN "CommitKim_AutoTrader" /Disable
if %ERRORLEVEL% EQU 0 echo ✅ Auto Trader Paused.

echo Disabling Summariser (Morning)...
schtasks /Change /TN "CommitKim_Morning" /Disable
if %ERRORLEVEL% EQU 0 echo ✅ Summariser (Morning) Paused.

echo Disabling Summariser (Evening)...
schtasks /Change /TN "CommitKim_Evening" /Disable
if %ERRORLEVEL% EQU 0 echo ✅ Summariser (Evening) Paused.

echo.
echo 🚀 Enjoy your game! No background tasks will run.
echo ⚠️ Remember to run 'gaming_mode_off.bat' when finished!
pause
