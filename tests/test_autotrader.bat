@echo off
chcp 65001 > nul
echo 🧪 Testing Auto Trader Strategy...
call "%~dp0..\Dashboard\venv\Scripts\python" "%~dp0test_autotrader_strategy.py"
if %errorlevel% neq 0 (
    echo ❌ Auto Trader Strategy Tests Failed!
    exit /b 1
)
echo ✅ Auto Trader Strategy Tests Passed!
exit /b 0
