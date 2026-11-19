"""仅在 127.0.0.1 提供五子棋网页；TypeSafe 密钥永不下发到浏览器。"""

import argparse
import json
import os
from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from gomoku import Gomoku
from triage import call_jev

HERE = Path(__file__).resolve().parent
ASSETS = {"gomoku.html": "text/html", "gomoku.js": "text/javascript",
          "gomoku.css": "text/css", "gomoku-turn.css": "text/css", "gomoku.py": "text/plain",
          "gomoku_server.py": "text/plain", "triage.py": "text/plain",
          "test_gomoku.py": "text/plain"}


def handler_for(game):
    class Handler(BaseHTTPRequestHandler):
        def send_bytes(self, status, data, mime):
            self.send_response(status)
            self.send_header("Content-Type", mime + "; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(data)

        def send_json(self, status, data):
            self.send_bytes(status, json.dumps(data, ensure_ascii=False, allow_nan=False).encode(), "application/json")

        def snapshot(self):
            return {**game.snapshot(), "key_configured": bool(os.environ.get("TYPESAFE_API_KEY"))}

        def valid_host(self):
            return self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}"

        def do_GET(self):
            if not self.valid_host():
                self.send_json(403, {"error": "仅限本机访问"})
            elif self.path in ("/", "/api/state"):
                if self.path == "/api/state":
                    self.send_json(200, self.snapshot())
                else:
                    self.send_bytes(200, (HERE / "gomoku.html").read_bytes(), "text/html")
            elif self.path.removeprefix("/") in ASSETS:
                name = self.path.removeprefix("/")
                self.send_bytes(200, (HERE / name).read_bytes(), ASSETS[name])
            else:
                self.send_json(404, {"error": "没有此页面"})

        def do_POST(self):
            origin = f"http://127.0.0.1:{self.server.server_port}"
            if not self.valid_host() or self.headers.get("Origin") != origin:
                self.send_json(403, {"error": "拒绝跨站请求"})
                return
            if self.path not in ("/api/move", "/api/retry", "/api/reset"):
                self.send_json(404, {"error": "没有此操作"})
                return
            size = self.headers.get("Content-Length", "")
            if (self.headers.get("Content-Type") != "application/json" or not size.isdecimal()
                    or not 2 <= int(size) <= 128):
                self.send_json(400, {"error": "请求格式不正确"})
                return
            try:
                payload = json.loads(self.rfile.read(int(size)))
            except (ValueError, UnicodeDecodeError):
                self.send_json(400, {"error": "JSON 不正确"})
                return
            if self.path == "/api/reset":
                if not isinstance(payload, dict) or set(payload) - {"first"} or payload.get("first", "human") not in ("human", "ai"):
                    self.send_json(400, {"error": "只能选择 human 或 ai 先手"})
                    return
                first = payload.get("first", "human")
                if first == "ai" and not os.environ.get("TYPESAFE_API_KEY"):
                    self.send_json(503, {"error": "请先配置 TYPESAFE_API_KEY 再让 Jev 先手"})
                    return
                game.reset(first)
                if first == "human":
                    self.send_json(200, self.snapshot())
                    return
            if not os.environ.get("TYPESAFE_API_KEY"):
                self.send_json(503, {"error": "请在启动服务的终端安全配置 TYPESAFE_API_KEY"})
                return
            if self.path == "/api/move":
                if not isinstance(payload, dict) or set(payload) != {"row", "col"}:
                    self.send_json(400, {"error": "只接受 row、col 坐标"})
                    return
                try:
                    game.human_move(payload["row"], payload["col"])
                except ValueError:
                    self.send_json(400, {"error": "棋盘位置无效或对局已结束", "state": self.snapshot()})
                    return
            elif self.path == "/api/retry" and payload != {}:
                self.send_json(400, {"error": "重试无需参数"})
                return
            if game.status == "AI_PENDING":
                try:
                    game.ai_move()
                except (OSError, ValueError, KeyError, TypeError, RuntimeError):
                    # 人类落子保留，但 AI 尚未落子；可以重试，不凭空代替模型下棋。
                    self.send_json(502, {"error": "Jev 调用失败：你的落子已保留，可点击重试", "state": self.snapshot()})
                    return
            self.send_json(200, self.snapshot())

        def log_message(self, format, *args):
            pass

    return Handler


def main():
    parser = argparse.ArgumentParser(description="Jev 五子棋，本机网页人机对战")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    with HTTPServer(("127.0.0.1", args.port), handler_for(Gomoku(ask=partial(call_jev, log_io=True)))) as server:
        print(f"浏览器打开 http://127.0.0.1:{server.server_port}/ ，Ctrl+C 停止；终端打印每次 JEV_REQUEST / JEV_RESPONSE（不含密钥）。", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()