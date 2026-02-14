@echo off
chcp 65001
cd /d "%~dp0"
echo ========================================================
echo 🚀 Dashboard Build ^& Deploy Script
echo ========================================================

:: Define Python command
set PYTHON_CMD=python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] 'python' not found in PATH. Checking known locations...
    if exist "C:\Users\geonwoo\AppData\Local\Programs\Python\Python312\python.exe" (
        set PYTHON_CMD="C:\Users\geonwoo\AppData\Local\Programs\Python\Python312\python.exe"
        echo [INFO] Found Python at: %PYTHON_CMD%
    ) else (
        echo [WARN] Python not found. Please ensure Python is installed and added to PATH.
        echo [WARN] Script might fail if 'python' command is not available.
    )
)

:: 0. Check Setup
if not exist Dashboard\venv (
    echo [0/4] Setting up virtual environment...
    python -m venv Dashboard\venv
    Dashboard\venv\Scripts\pip install -r Dashboard\requirements.txt
    Dashboard\venv\Scripts\pip install -r Summariser\requirements.txt
)

:: 1. Run the builder script
echo.
echo [1/4] Building static site...
Dashboard\venv\Scripts\python Dashboard\builder.py
Dashboard\venv\Scripts\python Summariser\main.py build
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Build failed!
    pause
    exit /b %ERRORLEVEL%
)

:: 2. Run Tests
echo.
echo [2/5] Running Tests...
call tests\run_all_tests.bat
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Tests Failed! deployment aborted.
    pause
    exit /b %ERRORLEVEL%
)

:: 3. Run the deployment script
echo.
echo [3/5] Deploying...
Dashboard\venv\Scripts\python Dashboard\deploy.py

pause
