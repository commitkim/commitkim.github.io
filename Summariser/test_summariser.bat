@echo off
chcp 65001 > nul
echo 🧪 Running Summariser Integration Test...
echo (Gemini API를 사용하여 실제 요약을 수행합니다)
echo.

..\Dashboard\venv\Scripts\python tests\test_integration.py

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Summariser Test Failed!
    exit /b 1
) else (
    echo ✅ Summariser Test Passed!
)
pause
