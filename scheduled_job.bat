@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================================
echo ⏰ CommitKim Monorepo Automation
echo ========================================================

:: 1. Dynamic Discovery & Execution
:: Loop through all subdirectories and look for automation.bat
for /d %%D in (*) do (
    if exist "%%D\automation.bat" (
        echo.
        echo [📂 Found Automation] %%D
        pushd "%%D"
        call automation.bat
        popd
    )
)

:: 2. Git Sync (Data is now updated)
echo.
echo [3/3] Deploying to GitHub...
set GIT_CMD="C:\Program Files\Git\cmd\git.exe"

%GIT_CMD% add .
%GIT_CMD% commit -m "Daily Update: %DATE% %TIME%"
%GIT_CMD% push origin main

echo.
echo ✅ All automation jobs completed!
