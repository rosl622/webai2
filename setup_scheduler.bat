@echo off
:: ============================================================
:: setup_scheduler.bat
:: 매일 오전 7시에 auto_fetch.py를 자동 실행하도록
:: Windows 작업 스케줄러에 등록합니다.
::
:: ▶ 사용법: 이 파일을 마우스 우클릭 → "관리자 권한으로 실행"
:: ============================================================

set TASK_NAME=EricNewsroomAutoFetch
set SCRIPT_DIR=%~dp0
set PYTHON_EXE=C:\Users\rosl6\AppData\Local\Python\pythoncore-3.14-64\python.exe
set SCRIPT_PATH=%SCRIPT_DIR%auto_fetch.py

:: 실행 시간 설정 (기본: 매일 오전 7시 00분)
:: HH:MM 형식으로 원하는 시간으로 변경하세요.
set RUN_TIME=07:00

echo 작업 스케줄러 등록 중...
echo.
echo  - 작업 이름  : %TASK_NAME%
echo  - 실행 시간  : 매일 %RUN_TIME%
echo  - 스크립트   : %SCRIPT_PATH%
echo.

schtasks /create ^
  /tn "%TASK_NAME%" ^
  /tr "\"%PYTHON_EXE%\" \"%SCRIPT_PATH%\"" ^
  /sc DAILY ^
  /st %RUN_TIME% ^
  /f ^
  /ru "%USERNAME%"

if %ERRORLEVEL% == 0 (
    echo.
    echo ✅ 등록 성공! 매일 %RUN_TIME%에 자동으로 뉴스 fetch가 실행됩니다.
    echo    로그는 auto_fetch.log 파일에서 확인할 수 있습니다.
) else (
    echo.
    echo ❌ 등록 실패. 관리자 권한으로 다시 실행해주세요.
)

echo.
pause
