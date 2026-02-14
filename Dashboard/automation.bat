@echo off
chcp 65001 > nul
echo 📊 Running Dashboard Builder...

:: Use local venv
venv\Scripts\python builder.py

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Dashboard build failed!
    exit /b %ERRORLEVEL%
)
echo ✅ Dashboard build completed.
