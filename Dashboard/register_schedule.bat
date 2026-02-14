@echo off
chcp 65001 > nul
cd /d %~dp0

set TASK_NAME="MorningNewsSummary"
set RUN_FILE="%~dp0run_auto.bat"

rem config.py에서 시간 가져오기
for /f "delims=" %%i in ('call .\venv\Scripts\python.exe -c "import config; print(config.DAILY_JOB_TIME)"') do set SCHEDULE_TIME=%%i

echo.
echo ========================================================
echo 📅 윈도우 작업 스케줄러 등록 마법사
echo ========================================================
echo.
echo [1] 기존 작업 삭제 중...
rem 기존 작업 강제 삭제 (오류 무시)
schtasks /delete /tn %TASK_NAME% /f >nul 2>&1

echo [2] 새 작업 등록 중...
echo 작업 이름: %TASK_NAME%
echo 실행 파일: %RUN_FILE%
echo 실행 시간: 매일 %SCHEDULE_TIME% (config.py 설정)
echo.

rem 새 작업 등록
schtasks /create /tn %TASK_NAME% /tr %RUN_FILE% /sc weekly /d MON,TUE,WED,THU,FRI /st %SCHEDULE_TIME% /f

if %errorlevel% neq 0 goto :error

:success
echo.
echo ========================================================
echo ✅ 등록 성공!
echo ========================================================
echo 이제 터미널을 켜두지 않아도 됩니다.
echo PC가 켜져 있다면 매일 %SCHEDULE_TIME%에 백그라운드에서 실행됩니다.
echo (실행 기록은 execute_log.txt에서 확인할 수 있습니다)
echo ========================================================
goto :end

:error
echo.
echo ========================================================
echo ❌ 등록 실패!
echo ========================================================
echo ⚠️ '관리자 권한'으로 이 파일을 실행해주세요.
echo (파일 우클릭 -> 관리자 권한으로 실행)
echo ========================================================

:end
pause
