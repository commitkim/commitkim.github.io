@echo off
chcp 65001 > nul
echo.
echo ========================================================
echo 🧹 이전 작업 스케줄러 정리 (퇴근요정 추가 전 구버전)
echo ========================================================
echo.

:: Old task names to be removed
set OLD_TASK_1="MorningNewsSummary"
set OLD_TASK_2="CommitKim_DailyJob"

echo [%OLD_TASK_1%] 제거 시도 중...
schtasks /delete /tn %OLD_TASK_1% /f >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ %OLD_TASK_1% 제거 완료.
) else (
    echo ℹ️ %OLD_TASK_1% 작업이 이미 없거나 제거할 수 없습니다.
)

echo.
echo [%OLD_TASK_2%] 제거 시도 중...
schtasks /delete /tn %OLD_TASK_2% /f >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ %OLD_TASK_2% 제거 완료.
) else (
    echo ℹ️ %OLD_TASK_2% 작업이 이미 없거나 제거할 수 없습니다.
)

echo.
echo ========================================================
echo ✨ 정리가 완료되었습니다.
echo 'setup_schedule.bat'를 실행하여 새 작업을 등록해 주세요.
echo ========================================================
pause
