@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================================
echo 🧪 CommitKim Project: Build, Test & Deploy
echo ========================================================

echo [1/3] Building Dashboard...
:: Build the main dashboard to reflect any new data
Dashboard\venv\Scripts\python Dashboard\builder.py
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Dashboard Build Failed!
    goto :exit_script
)

:: 2. Run Tests
echo.
echo [2/3] Running Tests...
call tests\run_all_tests.bat
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Tests Failed! Deployment aborted.
    goto :exit_script
)

:: 3. Deploy to GitHub
echo.
echo [3/3] Deploying to GitHub...
:: Use the robust deploy.py script for consistent deployment logic
Dashboard\venv\Scripts\python Dashboard\deploy.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Deployment failed!
    goto :exit_script
)

echo.
echo ========================================================
echo ✅ Deployment completed successfully!
echo ========================================================
pause
goto :eof

:exit_script
if "%1"=="auto" (
    if %ERRORLEVEL% NEQ 0 (
        exit /b %ERRORLEVEL%
    )
) else (
    if %ERRORLEVEL% NEQ 0 (
        pause
        exit /b %ERRORLEVEL%
    )
    pause
)
exit /b %ERRORLEVEL%
