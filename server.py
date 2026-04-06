#!/usr/bin/env python3
"""
애드레터 이미지 업로드 서버
실행: python3 server.py
"""

import os
import paramiko
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import cgi
import io

# ── SFTP 설정 (config.py 또는 환경변수에서 읽기) ──────────
try:
    import config
    SFTP_HOST     = config.SFTP_HOST
    SFTP_USER     = config.SFTP_USER
    SFTP_PASSWORD = config.SFTP_PASSWORD
    SFTP_DIR      = config.SFTP_DIR
    PUBLIC_URL    = config.PUBLIC_URL
except ImportError:
    SFTP_HOST     = os.environ.get("SFTP_HOST", "")
    SFTP_USER     = os.environ.get("SFTP_USER", "")
    SFTP_PASSWORD = os.environ.get("SFTP_PASSWORD", "")
    SFTP_DIR      = os.environ.get("SFTP_DIR", "")
    PUBLIC_URL    = os.environ.get("PUBLIC_URL", "")
# ────────────────────────────────────────────────────────────

PORT = 5000


def upload_to_sftp(filename: str, data: bytes) -> str:
    """파일을 SFTP 서버에 업로드하고 public URL 반환"""
    transport = paramiko.Transport((SFTP_HOST, 22))
    transport.connect(username=SFTP_USER, password=SFTP_PASSWORD)
    sftp = paramiko.SFTPClient.from_transport(transport)

    # 대상 디렉토리 확인 및 생성
    try:
        sftp.stat(SFTP_DIR)
    except FileNotFoundError:
        sftp.mkdir(SFTP_DIR)

    remote_path = f"{SFTP_DIR}/{filename}"
    sftp.putfo(io.BytesIO(data), remote_path)
    sftp.close()
    transport.close()

    # 업로드 후 SSH로 sync_img 실행
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SFTP_HOST, username=SFTP_USER, password=SFTP_PASSWORD)
    _, stdout, _ = ssh.exec_command("/usr/local/bin/sync_img")
    stdout.channel.recv_exit_status()
    ssh.close()

    return f"{PUBLIC_URL}/{filename}"


class Handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    def do_POST(self):
        if self.path != "/upload":
            self.send_response(404)
            self.end_headers()
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            body   = self.rfile.read(length)
            payload = json.loads(body)
            filename = os.path.basename(payload["filename"])
            data     = __import__("base64").b64decode(payload["data"])

            url = upload_to_sftp(filename, data)

            body = json.dumps({"ok": True, "url": url}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_cors()
            self.end_headers()
            self.wfile.write(body)

        except Exception as e:
            body = json.dumps({"ok": False, "error": str(e)}).encode()
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_cors()
            self.end_headers()
            self.wfile.write(body)


if __name__ == "__main__":
    print(f"애드레터 업로드 서버 시작 — http://localhost:{PORT}")
    print(f"업로드 경로: {SFTP_DIR}")
    print(f"공개 URL:    {PUBLIC_URL}/")
    print("종료: Ctrl+C\n")
    HTTPServer(("", PORT), Handler).serve_forever()
