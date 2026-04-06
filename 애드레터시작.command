#!/bin/zsh
cd "$(dirname "$0")"

# paramiko 없으면 자동 설치
python3 -c "import paramiko" 2>/dev/null || pip3 install paramiko -q

# 이미 실행 중이면 종료
lsof -ti:5000 | xargs kill -9 2>/dev/null
sleep 1

# 서버 백그라운드 실행 (터미널 종료 후에도 유지)
nohup python3 server.py > server.log 2>&1 &

# 서버 뜰 때까지 대기
sleep 2

# 관리자 페이지 열기
open https://heui-an.github.io/adletter-admin/
