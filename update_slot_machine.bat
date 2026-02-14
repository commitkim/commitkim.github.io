@echo off
chcp 65001
cd /d "%~dp0"

set GIT_CMD="C:\Program Files\Git\cmd\git.exe"

echo ========================================================
echo 🎰 Slot Machine Data Sync
echo ========================================================

:: Check if git is initialized
if not exist .git (
    echo ❌ Error: Not a git repository.
    pause
    exit /b 1
)

:: Add Slot machine folder
echo [1/3] Adding changes...
%GIT_CMD% add "Slot machine"

:: Commit changes
echo [2/3] Committing...
set TIMESTAMP=%DATE% %TIME%
%GIT_CMD% commit -m "Update Slot Machine Data: %TIMESTAMP%"

:: Push to remote
echo [3/3] Pushing to GitHub...
%GIT_CMD% push origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Sync successful!
) else (
    echo.
    echo ❌ Sync failed!
)

pause
