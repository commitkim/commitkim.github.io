@echo off
echo ========================================================
echo 🧪 Running LIVE Integration Test (Real API Calls)
echo ========================================================
"%~dp0..\Dashboard\venv\Scripts\python.exe" "%~dp0test_summariser_live.py"
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Live Test Failed!
    pause
    exit /b 1
)
echo ✅ Live Test Passed!
pause
