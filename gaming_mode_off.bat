@echo off
chcp 65001 > nul

echo.
echo ========================================================
echo 💼 Gaming Mode OFF (Resume Background Tasks)
echo ========================================================
echo.

echo Enabling Auto Trader...
schtasks /Change /TN "CommitKim_AutoTrader" /Enable
if %ERRORLEVEL% EQU 0 echo ✅ Auto Trader Resumed.

echo Enabling Summariser (Morning)...
schtasks /Change /TN "CommitKim_Morning" /Enable
if %ERRORLEVEL% EQU 0 echo ✅ Summariser (Morning) Resumed.

echo Enabling Summariser (Evening)...
schtasks /Change /TN "CommitKim_Evening" /Enable
if %ERRORLEVEL% EQU 0 echo ✅ Summariser (Evening) Resumed.

echo.
echo 🤖 System operates normally.
pause
