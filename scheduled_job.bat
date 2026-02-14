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

:: 2. Run Tests
echo.
echo [2/4] Running Tests...
call tests\run_all_tests.bat
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Tests Failed! Skipping deployment.
    exit /b %ERRORLEVEL%
)

:: 3. Git Sync (Data is now updated)
echo.
echo [3/4] Deploying to GitHub...
set GIT_CMD="C:\Program Files\Git\cmd\git.exe"

%GIT_CMD% add .
%GIT_CMD% commit -m "Daily Update: %DATE% %TIME%"
%GIT_CMD% push origin main

echo.
echo ✅ All automation jobs completed!
