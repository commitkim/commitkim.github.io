@echo off
cd /d %~dp0
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

echo. >> execute_log.txt
echo ======================================================== >> execute_log.txt
echo [%date% %time%] 뉴스 요약 + 정적사이트 빌드 시작 >> execute_log.txt

rem 전체 파이프라인 실행 (수집 -> 요약 -> 빌드 -> 카톡 -> 배포)
.\venv\Scripts\python main.py run >> execute_log.txt 2>&1

echo [%date% %time%] 작업 종료 >> execute_log.txt
echo ======================================================== >> execute_log.txt
