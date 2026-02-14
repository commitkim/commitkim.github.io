@echo off
chcp 65001
cd /d "%~dp0"
echo ========================================================
echo 🔨 Commitment Dashboard Local Build
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
    )
)

:: 0. Check Setup
if not exist Dashboard\venv (
    echo [0/1] Setting up virtual environment...
    %PYTHON_CMD% -m venv Dashboard\venv
    Dashboard\venv\Scripts\pip install -r Dashboard\requirements.txt
    Dashboard\venv\Scripts\pip install -r Summariser\requirements.txt
)

:: 1. Run the builder script
echo.
echo [1/1] Building static site...
Dashboard\venv\Scripts\python Dashboard\builder.py
Dashboard\venv\Scripts\python Summariser\main.py build

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Build failed!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ========================================================
echo ✅ Build Successful!
echo 📂 Location: docs/index.html
echo ========================================================
echo.
echo Check the result in your browser before running deploy.bat
echo.
pause
