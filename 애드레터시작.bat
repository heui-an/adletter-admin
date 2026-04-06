@echo off
cd /d "%~dp0"

REM 포트 5000 사용 중인 프로세스 종료
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":5000 " ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)

REM PowerShell로 서버 백그라운드 실행 (로그 기록)
start "" /b powershell -ExecutionPolicy Bypass -File "%~dp0server.ps1" > "%~dp0server.log" 2>&1

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
