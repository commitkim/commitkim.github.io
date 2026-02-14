@echo off
chcp 65001 > nul
cd /d "%~dp0"

set TASK_NAME_MORNING="CommitKim_Morning"
set TASK_NAME_EVENING="CommitKim_Evening"
set RUN_FILE="%~dp0scheduled_job.bat"

:: Read schedule times from config.py
for /f "delims=" %%i in ('Dashboard\venv\Scripts\python.exe -c "import config; print(config.MORNING_JOB_TIME)"') do set MORNING_TIME=%%i
for /f "delims=" %%i in ('Dashboard\venv\Scripts\python.exe -c "import config; print(config.EVENING_JOB_TIME)"') do set EVENING_TIME=%%i

echo.
echo ========================================================
echo 📅 작업 스케줄러 설정 마법사 (듀얼 스케줄)
echo ========================================================
echo.

:: 1. Delete Existing Tasks (Cleanup)
echo [1/2] 기존 작업(%TASK_NAME_MORNING%, %TASK_NAME_EVENING%) 정리 중...
schtasks /delete /tn %OLD_TASK_NAME% /f >nul 2>&1
schtasks /delete /tn %NEW_TASK_NAME% /f >nul 2>&1
schtasks /delete /tn %TASK_NAME_MORNING% /f >nul 2>&1
schtasks /delete /tn %TASK_NAME_EVENING% /f >nul 2>&1
echo ✅ 기존 작업 정리 완료.

:: 2. Create New Tasks
echo.
echo [2/2] 새 통합 작업 등록 중...
echo.
echo 🌅 [모닝루틴]
echo    작업명: %TASK_NAME_MORNING%
echo    실행 시간: 평일 %MORNING_TIME%
schtasks /create /tn %TASK_NAME_MORNING% /tr "%RUN_FILE% morning" /sc weekly /d MON,TUE,WED,THU,FRI /st %MORNING_TIME% /f

echo.
echo 🌇 [퇴근요정]
echo    작업명: %TASK_NAME_EVENING%
echo    실행 시간: 평일 %EVENING_TIME%
schtasks /create /tn %TASK_NAME_EVENING% /tr "%RUN_FILE% evening" /sc weekly /d MON,TUE,WED,THU,FRI /st %EVENING_TIME% /f

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
echo 모닝루틴(%MORNING_TIME%)과 퇴근요정(%EVENING_TIME%)이 등록되었습니다.
echo 데이터 수집 -^> 사이트 빌드 -^> 테스트 -^> 배포
echo ========================================================
pause
