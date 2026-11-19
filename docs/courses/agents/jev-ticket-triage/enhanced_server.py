"""本机多模型五子棋服务。令牌留在服务端，不回传浏览器。"""

import argparse
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from enhanced_match import Match, PlatformMoveError, platform_model
from triage import call_jev

ROOT = Path(__file__).resolve().parent
ASSETS = {"arena.html": "text/html", "arena-guide.html": "text/html",
          "arena.css": "text/css", "arena.js": "text/javascript",
          "gomoku.css": "text/css", "enhanced_match.py": "text/plain", "enhanced_server.py": "text/plain"}


def handler_for(match):
    match_lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def reply(self, code, data):
            raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(raw)

        def own_origin(self):
            base = f"127.0.0.1:{self.server.server_port}"
            return self.headers.get("Host") == base

        def snapshot(self):
            return {**match.snapshot(), "platform_model": platform_model(),
                "available": {"jev": bool(os.environ.get("TYPESAFE_API_KEY")),
                "qwen": bool(os.environ.get("PLATFORM_API_KEY"))}}

        def do_GET(self):
            if not self.own_origin():
                self.reply(403, {"error": "仅限本机访问"})
                return
            if self.path == "/api/state":
                self.reply(200, self.snapshot())
                return
            name = "arena.html" if self.path == "/" else self.path.removeprefix("/")
            if name not in ASSETS:
                self.reply(404, {"error": "Not found"})
                return
            raw = (ROOT / name).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", ASSETS[name] + "; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(raw)

        def do_POST(self):
            # 一个对局只能依次落子；GET /api/state 不应被慢速模型请求阻塞。
            with match_lock:
                self.handle_post()

        def handle_post(self):
            if not self.own_origin() or self.headers.get("Origin") != f"http://127.0.0.1:{self.server.server_port}":
                self.reply(403, {"error": "跨站请求被拒绝"})
                return
            if self.path not in ("/api/reset", "/api/move", "/api/step"):
                self.reply(404, {"error": "Not found"})
                return
            length = self.headers.get("Content-Length", "")
            if (self.headers.get("Content-Type") != "application/json" or not length.isdecimal()
                    or not 2 <= int(length) <= 150):
                self.reply(400, {"error": "无效请求"})
                return
            try:
                data = json.loads(self.rfile.read(int(length)))
                if not isinstance(data, dict):
                    raise ValueError("expected object")
                if self.path == "/api/reset":
                    if set(data) != {"mode", "human_first", "jev_first"}:
                        raise ValueError("invalid configuration")
                    result = match.reset(**data)
                elif self.path == "/api/move":
                    if set(data) != {"row", "col"}:
                        raise ValueError("invalid coordinates")
                    result = match.human_move(**data)
                else:
                    if data:
                        raise ValueError("step expects empty object")
                    actor = match.snapshot()["next_actor"]
                    key = "TYPESAFE_API_KEY" if actor == "jev" else "PLATFORM_API_KEY"
                    if actor not in ("jev", "qwen") or not os.environ.get(key):
                        self.reply(503, {"error": "轮到的模型未配置 API Key", "state": self.snapshot()})
                        return
                    try:
                        result = match.ai_step()
                    except PlatformMoveError as error:
                        self.reply(502, {"error": str(error), "state": self.snapshot()})
                        return
                    except (ValueError, TypeError, KeyError, IndexError, OSError, RuntimeError):
                        self.reply(502, {"error": "模型接口失败或落点无效，棋盘未推进；可重试", "state": self.snapshot()})
                        return
            except (ValueError, TypeError, KeyError) as error:
                self.reply(400, {"error": type(error).__name__ + ": 非法操作或模型响应", "state": self.snapshot()})
                return
            self.reply(200, {**result, "platform_model": platform_model(),
                             "available": self.snapshot()["available"]})

        def log_message(self, *_):
            pass

    return Handler


def main():
    parser = argparse.ArgumentParser(description="Jev / Qwen 五子棋增强对战")
    parser.add_argument("--port", type=int, default=8767)
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.port), handler_for(Match())) as server:
        print(f"本地对战 http://127.0.0.1:{server.server_port}/ ；Ctrl+C 停止", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()