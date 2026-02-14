@echo off
chcp 65001 > nul
cd /d "%~dp0"

set OLD_TASK_NAME="MorningNewsSummary"
set NEW_TASK_NAME="CommitKim_DailyJob"
set RUN_FILE="%~dp0scheduled_job.bat"

:: Read schedule time from config.py
for /f "delims=" %%i in ('Dashboard\venv\Scripts\python.exe -c "import config; print(config.DAILY_JOB_TIME)"') do set SCHEDULE_TIME=%%i

echo.
echo ========================================================
echo 📅 작업 스케줄러 설정 마법사
echo ========================================================
echo.

:: 1. Delete Old Task
echo [1/2] 기존 Summariser 작업(%OLD_TASK_NAME%) 삭제 중...
schtasks /delete /tn %OLD_TASK_NAME% /f >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 기존 작업 삭제 완료.
) else (
    echo ℹ️ 기존 작업이 없거나 이미 삭제되었습니다.
)

:: 2. Create New Task
echo.
echo [2/2] 새 통합 작업(%NEW_TASK_NAME%) 등록 중...
echo 실행 파일: %RUN_FILE%
echo 실행 시간: 매일 %SCHEDULE_TIME%

:: Register new task
schtasks /create /tn %NEW_TASK_NAME% /tr %RUN_FILE% /sc daily /st %SCHEDULE_TIME% /f

if %errorlevel% neq 0 (
    echo.
    echo ❌ 등록 실패!
    echo ⚠️ '관리자 권한'으로 실행해주세요.
    pause
    exit /b 1
)

echo.
echo ========================================================
echo ✅ 등록 성공!
echo ========================================================
echo 이제 매일 아침 9시에 전체 프로젝트 자동화가 실행됩니다.
echo (뉴스 수집 -> 사이트 빌드 -> 배포)
echo ========================================================
pause
