"""多模型对战离线测试；fake 模型只验证协议和规则，不声明线上模型胜率。"""

import json
import io
import os
import threading
import unittest
import urllib.error
import urllib.request
from contextlib import redirect_stdout
from http.server import HTTPServer, ThreadingHTTPServer
from unittest.mock import patch

from enhanced_match import Match, PlatformMoveError, platform_move
from enhanced_server import handler_for
from gomoku import BLACK, WHITE, move_id


def fake_jev(state, questions):
    options = questions["next_move"]["criteria"]
    cell = next(iter(options))
    return {"model": "fake-jev", "usage": {"input_tokens": 1}, "answers": {"next_move": {
        "type": "choice", "choice": cell, "confidence": 1.0,
        "probabilities": {key: float(key == cell) for key in options}}}}


def fake_qwen(board, color):
    return platform_move(board, color, transport=lambda body: {
        "model": "fake-qwen", "choices": [{"message": {"content": json.dumps({"move":
            "r07c07" if not board[7][7] else next(move_id(r,c) for r in range(15) for c in range(15) if not board[r][c])})}}],
        "usage": {"prompt_tokens": 2}})


class MatchTests(unittest.TestCase):
    def test_qwen_move_and_prompt(self):
        captured = []
        def transport(body):
            captured.append(body)
            return {"model": "fake", "choices": [{"message": {"content": '{"move":"r07c07"}'}}]}
        from gomoku import empty_board
        point, meta = platform_move(empty_board(), BLACK, transport)
        self.assertEqual((point, meta["source"]), ((7, 7), "platform"))
        self.assertEqual(captured[0]["model"], "qwen3.7-flash-non-thinking")
        self.assertIn('"move":"rXXcYY"', captured[0]["messages"][0]["content"])
        self.assertEqual(captured[0]["response_format"], {"type": "json_object"})
        self.assertIn("07 ...............", captured[0]["messages"][1]["content"])
        self.assertNotIn("Legal ids:", captured[0]["messages"][1]["content"])
        self.assertEqual(captured[0]["max_tokens"], 48)
        self.assertEqual(captured[0]["temperature"], 0)

    def test_first_and_later_turns_send_full_board_without_duplicate_ids(self):
        from gomoku import empty_board
        board = empty_board()
        board[7][7] = BLACK
        captured = []

        def respond(payload):
            captured.append(payload)
            return {"choices": [{"message": {"content": '{"move":"r00c00"}'}}]}

        platform_move(board, WHITE, respond)
        board[8][8] = WHITE
        board[6][6] = BLACK
        platform_move(board, WHITE, respond)
        for body in captured:
            self.assertEqual([m["role"] for m in body["messages"]], ["system", "user"])
            system, user = (item["content"] for item in body["messages"])
            self.assertIn("15x15 Gomoku", system)
            self.assertIn("zero-based", system)
            self.assertNotIn("Legal ids:", user)
            self.assertEqual(len(user.split("Board (each row labelled 00..14):\n")[1].splitlines()), 15)
            self.assertLess(len(json.dumps(body).encode()), 1100)
        self.assertIn("07 .......X.......", captured[0]["messages"][1]["content"])
        self.assertIn("08 ........O......", captured[1]["messages"][1]["content"])

    def test_explicit_json_mode_opt_out_for_incompatible_gateway(self):
        from gomoku import empty_board
        with patch.dict(os.environ, {"PLATFORM_JSON_MODE": "0"}):
            def capture(body):
                self.assertNotIn("response_format", body)
                return {"choices": [{"message": {"content": '{"move":"r07c07"}'}}]}
            self.assertEqual(platform_move(empty_board(), BLACK, capture)[0], (7, 7))

    def test_json_mode_does_not_create_final_answer_when_reasoning_exhausts_budget(self):
        from gomoku import empty_board
        with patch.dict(os.environ, {"PLATFORM_MODEL": "origin-deepseek-v4-flash"}):
            def exhausted(body):
                self.assertEqual(body["response_format"], {"type": "json_object"})
                return {"choices": [{"finish_reason": "length", "message": {
                    "content": "", "reasoning_content": "intermediate reasoning"}}]}
            with self.assertRaisesRegex(PlatformMoveError, "content 为空"):
                platform_move(empty_board(), BLACK, exhausted)

    def test_invalid_json_mode_configuration_is_rejected(self):
        from gomoku import empty_board
        with patch.dict(os.environ, {"PLATFORM_JSON_MODE": "maybe"}):
            with self.assertRaisesRegex(ValueError, "PLATFORM_JSON_MODE"):
                platform_move(empty_board(), BLACK, lambda _: None)

    def test_thinking_model_alias_routes_to_non_thinking_but_custom_id_is_preserved(self):
        from gomoku import empty_board
        observed = []
        def capture(body):
            observed.append(body["model"])
            return {"choices": [{"message": {"content": '{"move":"r07c07"}'}}]}
        with patch.dict(os.environ, {"PLATFORM_MODEL": "qwen3.7-flash"}):
            platform_move(empty_board(), BLACK, capture)
        with patch.dict(os.environ, {"PLATFORM_MODEL": "my-custom-model"}):
            platform_move(empty_board(), BLACK, capture)
        self.assertEqual(observed, ["qwen3.7-flash-non-thinking", "my-custom-model"])

    def test_deepseek_output_budget_and_final_coordinate_formats(self):
        from gomoku import empty_board
        sent = []
        for content in ('{"move":"r07c07"}', ' { "move" : "r07c07" } '):
            def transport(body):
                sent.append(body)
                return {"choices": [{"finish_reason": "stop", "message": {
                    "content": content, "reasoning_content": "other guesses r00c00"}}]}
            with patch.dict(os.environ, {"PLATFORM_MODEL": "origin-deepseek-v4-flash"}):
                point, _ = platform_move(empty_board(), BLACK, transport)
            self.assertEqual(point, (7, 7))
        self.assertTrue(all(body["max_tokens"] == 2048 for body in sent))
        self.assertTrue(all(body["model"] == "origin-deepseek-v4-flash" for body in sent))

    def test_deepseek_reasoning_only_or_truncation_never_plays_guess(self):
        from gomoku import empty_board
        with patch.dict(os.environ, {"PLATFORM_MODEL": "origin-deepseek-v4-flash"}):
            for content in (None, ""):
                with self.subTest(content=content), self.assertRaisesRegex(PlatformMoveError, "输出预算耗尽.*max_tokens=2048.*content 为空"):
                    platform_move(empty_board(), BLACK, lambda _: {"choices": [{
                        "finish_reason": "length", "message": {"content": content, "reasoning_content": "r07c07"}}]})

    def test_exhausted_at_max_budget_does_not_suggest_raising_to_same_limit(self):
        from gomoku import empty_board
        with patch.dict(os.environ, {"PLATFORM_MODEL": "origin-deepseek-v4-flash", "PLATFORM_MAX_TOKENS": "4096"}):
            def exhausted(body):
                self.assertEqual(body["max_tokens"], 4096)
                return {"choices": [{"finish_reason": "length", "message": {
                    "content": "", "reasoning_content": "intermediate thought"}}]}

            with self.assertRaises(PlatformMoveError) as raised:
                platform_move(empty_board(), BLACK, exhausted)
        message = str(raised.exception)
        self.assertIn("本次 max_tokens=4096", message)
        self.assertIn("不要重复调高预算", message)
        self.assertNotIn("可设置 PLATFORM_MAX_TOKENS=4096", message)

    def test_platform_budget_override_is_bounded(self):
        from gomoku import empty_board
        with patch.dict(os.environ, {"PLATFORM_MODEL": "origin-deepseek-v4-flash", "PLATFORM_MAX_TOKENS": "1024"}):
            def assert_budget(body):
                self.assertEqual(body["max_tokens"], 1024)
                return {"choices": [{"message": {"content": '{"move":"r07c07"}'}}]}
            self.assertEqual(platform_move(empty_board(), BLACK, assert_budget)[0], (7, 7))
        with patch.dict(os.environ, {"PLATFORM_MAX_TOKENS": "999999"}):
            with self.assertRaisesRegex(ValueError, "PLATFORM_MAX_TOKENS"):
                platform_move(empty_board(), BLACK, lambda _: None)

    def test_non_thinking_route_requires_explicit_selection(self):
        from gomoku import empty_board
        with patch.dict(os.environ, {"PLATFORM_MODEL": "deepseek-v4-flash-wot"}):
            def verify(body):
                self.assertEqual(body["model"], "deepseek-v4-flash-wot")
                self.assertEqual(body["max_tokens"], 2048)
                return {"choices": [{"message": {"content": '{"move":"r07c07"}'}}]}
            self.assertEqual(platform_move(empty_board(), BLACK, verify)[0], (7, 7))

    def test_real_http_diagnostic_includes_budget_but_never_key_or_reasoning(self):
        from gomoku import empty_board
        class FakeReply:
            def __enter__(self):
                return io.BytesIO(json.dumps({"model": "deepseek-v4-flash-202605",
                    "choices": [{"finish_reason": "length", "message": {
                        "content": "", "reasoning_content": "secret reasoning r07c07"}}],
                    "usage": {"completion_tokens": 2048,
                              "completion_tokens_details": {"reasoning_tokens": 2048}}}).encode())
            def __exit__(self, *_):
                return False
        captured = io.StringIO()
        with patch.dict(os.environ, {"PLATFORM_MODEL": "origin-deepseek-v4-flash",
                      "PLATFORM_API_KEY": "secret-test-placeholder",
                      "PLATFORM_BASE_URL": "https://example.invalid"}), \
             patch("urllib.request.urlopen", return_value=FakeReply()), \
             redirect_stdout(captured), self.assertRaisesRegex(PlatformMoveError, "max_tokens=2048"):
            platform_move(empty_board(), BLACK)
        logged = json.loads(captured.getvalue().split("PLATFORM_RESULT ", 1)[1].strip())
        self.assertEqual(logged["requested_max_tokens"], 2048)
        self.assertEqual(logged["requested_model"], "origin-deepseek-v4-flash")
        self.assertEqual(logged["reasoning_tokens"], 2048)
        self.assertNotIn("secret-test-placeholder", captured.getvalue())
        self.assertNotIn("secret reasoning", captured.getvalue())

    def test_real_http_request_shape_with_mock_network(self):
        from gomoku import empty_board
        class FakeReply:
            def __enter__(self):
                return io.BytesIO(b'{"model":"qwen3.7-flash-non-thinking","choices":[{"message":{"content":"{\\"move\\":\\"r07c07\\"}"}}]}')
            def __exit__(self, *_):
                return False
        captured = io.StringIO()
        with patch.dict(os.environ, {"PLATFORM_API_KEY": "test-placeholder",
                                  "PLATFORM_BASE_URL": "https://example.invalid"}), \
             patch("urllib.request.urlopen", return_value=FakeReply()) as send, \
             redirect_stdout(captured):
            move, _ = platform_move(empty_board(), BLACK)
        request = send.call_args.args[0]
        self.assertEqual(captured.getvalue().count("PLATFORM_REQUEST\n"), 1)
        self.assertEqual(request.full_url, "https://example.invalid/v1/chat/completions")
        self.assertEqual(request.headers["Authorization"], "Bearer test-placeholder")
        body = json.loads(request.data)
        self.assertEqual(body["model"], "qwen3.7-flash-non-thinking")
        self.assertFalse(body["stream"])
        self.assertEqual(body["max_tokens"], 48)
        self.assertEqual(body["temperature"], 0)
        self.assertEqual(move, (7, 7))

    def test_terminal_prints_exact_sent_json_body_without_authorization(self):
        from gomoku import empty_board
        class FakeReply:
            def __enter__(self):
                return io.BytesIO(b'{"choices":[{"message":{"content":"{\\"move\\":\\"r07c07\\"}"}}]}')
            def __exit__(self, *_):
                return False
        output = io.StringIO()
        with patch.dict(os.environ, {"PLATFORM_API_KEY": "never-print-this-key",
                      "PLATFORM_BASE_URL": "https://example.invalid"}), \
             patch("urllib.request.urlopen", return_value=FakeReply()) as send, \
             redirect_stdout(output):
            platform_move(empty_board(), BLACK)
        logged = output.getvalue()
        self.assertIn("PLATFORM_REQUEST\n{\n", logged)
        formatted = logged.split("PLATFORM_REQUEST\n", 1)[1].split("\nPLATFORM_RESPONSE ", 1)[0]
        self.assertEqual(json.loads(formatted), json.loads(send.call_args.args[0].data))
        self.assertEqual(logged.count("PLATFORM_REQUEST\n"), 1)
        self.assertIn("PLATFORM_RESULT ", logged)
        self.assertIn('\n  "messages": [\n', formatted)
        self.assertNotIn("never-print-this-key", logged)
        self.assertNotIn("Authorization", logged)

    def test_rejects_invalid_model_answer_without_progress(self):
        match = Match(fake_jev, lambda b,c: platform_move(b,c,lambda p: {
            "choices": [{"message": {"content": '{"move":"r99c99"}'}}]}))
        match.reset("human_qwen")
        match.human_move(7, 7)
        with self.assertRaises(ValueError):
            match.ai_step()
        self.assertEqual(match.snapshot()["next_actor"], "qwen")
        self.assertEqual(len(match.history), 1)

    def test_rejects_verbose_or_extra_json_fields(self):
        from gomoku import empty_board
        for content in ('r07c07', '```json\n{"move":"r07c07"}\n```',
                'I choose {"move":"r07c07"}',
                '{"move":"r07c07","explanation":"long"}'):
            with self.subTest(content=content):
                with self.assertRaises(ValueError):
                    platform_move(empty_board(), BLACK, lambda _: {"choices": [{"message": {"content": content}}]})

    def test_human_vs_both_providers(self):
        for mode in ("human_jev", "human_qwen"):
            match = Match(fake_jev, fake_qwen)
            match.reset(mode, human_first=False)
            self.assertEqual(match.snapshot()["next_actor"], "jev" if mode == "human_jev" else "qwen")
            match.ai_step()
            self.assertEqual(match.board[0][0] if mode == "human_jev" else match.board[7][7], BLACK)
            self.assertEqual(match.snapshot()["next_actor"], "human")

    def test_ai_vs_ai_order_and_steps(self):
        match = Match(fake_jev, fake_qwen)
        for jev_first in (True, False):
            match.reset("jev_qwen", jev_first=jev_first)
            first = match.snapshot()["next_actor"]
            match.ai_step()
            self.assertEqual(match.history[0]["actor"], first)
            self.assertEqual(match.history[0]["color"], BLACK)
            match.ai_step()
            self.assertEqual(match.history[1]["color"], WHITE)
            self.assertNotEqual(match.history[1]["actor"], first)

    def test_jev_vs_platform_prompt_names_opponent_not_human(self):
        observed = []

        def inspect(state, questions):
            observed.append(state)
            return fake_jev(state, questions)

        match = Match(inspect, fake_qwen)
        match.reset("jev_qwen", jev_first=False)
        match.ai_step()  # platform plays X, Jev plays O
        match.ai_step()
        self.assertEqual(len(observed), 1)
        self.assertEqual(observed[0]["roles"], {
            "you_ai": "O", "opponent": "X", "first_player": "opponent", "to_move": "O"})
        self.assertIn("fork", observed[0]["strategy"])
        self.assertNotIn("human", json.dumps(observed[0], ensure_ascii=False))


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), handler_for(Match(fake_jev, fake_qwen)))
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def post(self,path,payload,origin=None):
        req=urllib.request.Request(self.url+path,json.dumps(payload).encode(),method="POST",
              headers={"Origin":origin or self.url,"Content-Type":"application/json"})
        with urllib.request.urlopen(req) as response:
            return json.load(response)

    def test_dual_model_http_flow(self):
        with patch.dict(os.environ,{"PLATFORM_API_KEY":"fake-key","TYPESAFE_API_KEY":"fake-key"}):
            reset=self.post("/api/reset",{"mode":"jev_qwen","human_first":True,"jev_first":True})
            self.assertEqual(reset["next_actor"],"jev")
            self.assertEqual(reset["platform_model"], "qwen3.7-flash-non-thinking")
            self.assertEqual(self.post("/api/step",{})["next_actor"],"qwen")
            after_qwen = self.post("/api/step",{})
            self.assertEqual(after_qwen["next_actor"],"jev")
            self.assertEqual(after_qwen["platform_model"], "qwen3.7-flash-non-thinking")

    def test_second_platform_turn_reaches_model_with_updated_board(self):
        bodies = []

        def platform(board, color):
            def respond(body):
                bodies.append(body)
                cell = "r07c07" if len(bodies) == 1 else "r07c08"
                return {"choices": [{"message": {"content": json.dumps({"move": cell})}}]}
            return platform_move(board, color, respond)

        match = Match(fake_jev, platform)
        server = HTTPServer(("127.0.0.1", 0), handler_for(match))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"

        def post(path, data):
            req = urllib.request.Request(base + path, json.dumps(data).encode(), method="POST",
                headers={"Origin": base, "Content-Type": "application/json"})
            with urllib.request.urlopen(req) as response:
                return json.load(response)

        try:
            with patch.dict(os.environ, {"PLATFORM_API_KEY": "test-placeholder"}):
                post("/api/reset", {"mode": "human_qwen", "human_first": True, "jev_first": True})
                post("/api/move", {"row": 6, "col": 6})
                first = post("/api/step", {})
                self.assertEqual(first["next_actor"], "human")
                post("/api/move", {"row": 6, "col": 7})
                second = post("/api/step", {})
                self.assertEqual(second["next_actor"], "human")
                self.assertEqual(len(second["history"]), 4)
                self.assertEqual(len(bodies), 2)
                self.assertIn("07 .......O.......", bodies[1]["messages"][1]["content"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_state_remains_available_while_platform_response_is_slow(self):
        from enhanced_server import handler_for
        entered, release = threading.Event(), threading.Event()

        def slow_platform(board, color):
            entered.set()
            if not release.wait(5):
                raise RuntimeError("test gateway did not resume")
            return (7, 8), {"source": "platform", "model": "fake", "usage": None}

        server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(Match(fake_jev, slow_platform)))
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        base = f"http://127.0.0.1:{server.server_port}"

        def post(path, data):
            request = urllib.request.Request(base + path, json.dumps(data).encode(), method="POST",
                headers={"Origin": base, "Content-Type": "application/json"})
            with urllib.request.urlopen(request, timeout=3) as response:
                return json.load(response)

        result = []
        try:
            with patch.dict(os.environ, {"PLATFORM_API_KEY": "test-placeholder"}):
                post("/api/reset", {"mode": "human_qwen", "human_first": True, "jev_first": True})
                post("/api/move", {"row": 7, "col": 7})
                step = threading.Thread(target=lambda: result.append(post("/api/step", {})))
                step.start()
                self.assertTrue(entered.wait(3))
                with urllib.request.urlopen(base + "/api/state", timeout=2) as response:
                    state = json.load(response)
                self.assertEqual(state["next_actor"], "qwen")
                self.assertEqual(len(state["history"]), 1)
                release.set()
                step.join(3)
                self.assertFalse(step.is_alive())
                self.assertEqual(len(result[0]["history"]), 2)
        finally:
            release.set()
            server.shutdown()
            server.server_close()
            worker.join()

    def test_cross_origin_and_client_board_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.post("/api/reset",{},origin="http://evil.invalid")
        self.assertEqual(ctx.exception.code,403)
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.post("/api/reset",{"mode":"jev_qwen","board":[[1]]})
        self.assertEqual(ctx.exception.code,400)

    def test_safe_platform_error_reaches_browser_without_changing_board(self):
        match = Match(fake_jev, lambda board, color: platform_move(board, color,
            lambda _: {"choices": [{"finish_reason": "length", "message": {
                "content": None, "reasoning_content": "secret r00c00"}}]}))
        server = HTTPServer(("127.0.0.1", 0), handler_for(match))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        def post(path, body):
            req = urllib.request.Request(base + path, json.dumps(body).encode(), method="POST",
                headers={"Origin": base, "Content-Type": "application/json"})
            return urllib.request.urlopen(req)
        try:
            with patch.dict(os.environ, {"PLATFORM_API_KEY": "test-placeholder"}):
                with post("/api/reset", {"mode": "human_qwen", "human_first": True, "jev_first": True}):
                    pass
                with post("/api/move", {"row": 7, "col": 7}):
                    pass
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    post("/api/step", {})
                response = json.load(caught.exception)
                self.assertEqual(caught.exception.code, 502)
                self.assertIn("预算耗尽", response["error"])
                self.assertNotIn("secret", response["error"])
                self.assertEqual(response["state"]["next_actor"], "qwen")
                self.assertEqual(len(response["state"]["history"]), 1)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()