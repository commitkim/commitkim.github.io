@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================================
echo ⏰ CommitKim Monorepo Automation
echo ========================================================

:: 1. Subdirectory Automation
:: Loop through all subdirectories and look for automation.bat
for /d %%D in (*) do (
    if exist "%%D\automation.bat" (
        echo.
        echo [1/3] Running automation for: %%D
        pushd "%%D"
        call automation.bat
        popd
    )
)

:: 2. Run Tests
echo.
echo [2/3] Running Tests...
call tests\run_all_tests.bat
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Tests Failed! Skipping deployment.
    exit /b %ERRORLEVEL%
)

:: 3. Deploy to GitHub
echo.
echo [3/3] Deploying to GitHub...
:: Use the robust deploy.py script for consistent deployment logic
Dashboard\venv\Scripts\python Dashboard\deploy.py

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Deployment failed!
    exit /b %ERRORLEVEL%
)

echo.
echo ========================================================
echo ✅ All automation jobs completed successfully!
echo ========================================================
