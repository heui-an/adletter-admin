@echo off
cd /d "%~dp0"

REM server.exe 없으면 GitHub에서 자동 다운로드
if not exist "server.exe" (
    echo 처음 실행 시 서버 파일을 다운로드합니다. 잠시 기다려주세요...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/heui-an/adletter-admin/releases/latest/download/server.exe' -OutFile 'server.exe'"
    if not exist "server.exe" (
        echo 다운로드 실패. 인터넷 연결을 확인하거나 관리자에게 문의하세요.
        pause
        exit /b 1
    )
    echo 다운로드 완료!
)

REM 포트 5000 사용 중인 프로세스 종료
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":5000 " ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)

REM 서버 백그라운드 실행 (로그 기록)
start "" /b cmd /c ""%~dp0server.exe" > "%~dp0server.log" 2>&1"

REM 포트 5000이 실제로 열릴 때까지 대기 (최대 20초)
set /a count=0
:wait_loop
netstat -an | findstr ":5000" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 goto server_ready
set /a count+=1
if %count% geq 20 (
    echo 서버 시작 실패. server.log 파일을 확인해주세요.
    pause
    exit /b 1
)
timeout /t 1 /nobreak >nul
goto wait_loop

:server_ready
REM 관리자 페이지 열기
start https://heui-an.github.io/adletter-admin/
exit
