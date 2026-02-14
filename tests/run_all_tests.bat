@echo off
chcp 65001 > nul
echo ========================================================
echo 🧪 CommitKim Project Test Suite
echo ========================================================

echo.
echo [1/2] Testing Summariser...
call "%~dp0test_summariser.bat"
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Summariser Test Failed!
    exit /b 1
)

echo.
echo [2/2] Testing Dashboard Builder...
call "%~dp0test_dashboard.bat"
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Dashboard Test Failed!
    exit /b 1
)

echo.
echo ========================================================
echo ✅ All Tests Passed!
echo ========================================================
pause
