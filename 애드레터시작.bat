@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM Python 실행 파일 찾기 (python 우선, 없으면 py 런처)
set PYTHON=
where python >nul 2>&1 && set PYTHON=python
if not defined PYTHON (
    where py >nul 2>&1 && set PYTHON=py
)
if not defined PYTHON (
    echo.
    echo [오류] Python이 설치되어 있지 않습니다.
    echo https://www.python.org/downloads/ 에서 Python 3.x를 설치하세요.
    echo 설치 시 "Add Python to PATH" 옵션을 반드시 체크하세요.
    echo.
    pause
    exit /b 1
)

REM paramiko 패키지 없으면 자동 설치
%PYTHON% -c "import paramiko" >nul 2>&1
if errorlevel 1 (
    echo paramiko 패키지 설치 중...
    %PYTHON% -m pip install paramiko -q
    if errorlevel 1 (
        echo.
        echo [오류] paramiko 설치에 실패했습니다.
        echo.
        pause
        exit /b 1
    )
)

REM 포트 5000 사용 중인 프로세스 종료
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":5000 " ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)

REM Python 서버 백그라운드 실행 (로그 기록)
start "" /b %PYTHON% "%~dp0server.py" > "%~dp0server.log" 2>&1

REM 포트 5000이 열릴 때까지 최대 15초 대기
set /a count=0
:wait_loop
netstat -an | findstr ":5000" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 goto server_ready
set /a count+=1
if %count% geq 15 goto server_failed
timeout /t 1 /nobreak >nul
goto wait_loop

:server_failed
echo.
echo [오류] 서버가 시작되지 않았습니다. server.log 파일을 확인해주세요.
echo.
start https://heui-an.github.io/adletter-admin/
pause
exit /b 1

:server_ready
REM 관리자 페이지 열기
start https://heui-an.github.io/adletter-admin/
exit
