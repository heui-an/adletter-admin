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

# ── SFTP 설정 ──────────────────────────────────────────
SFTP_HOST     = "121.254.171.47"
SFTP_USER     = "img"
SFTP_PASSWORD = "ehdtkimg!"
SFTP_DIR      = "/home/img/www/dongascience/letter/claude_an"
PUBLIC_URL    = "http://img.dongascience.com/letter/claude_an"
# ────────────────────────────────────────────────────────

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

    return f"{PUBLIC_URL}/{filename}"


class Handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

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
            content_type = self.headers.get("Content-Type", "")
            if "multipart/form-data" not in content_type:
                raise ValueError("multipart/form-data 형식으로 전송해야 합니다.")

            # multipart 파싱
            environ = {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": content_type,
                "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
            }
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ=environ
            )

            if "file" not in form:
                raise ValueError("파일이 없습니다.")

            file_item = form["file"]
            filename = os.path.basename(file_item.filename)
            data = file_item.file.read()

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
