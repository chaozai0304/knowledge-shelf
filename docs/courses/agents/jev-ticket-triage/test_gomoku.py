"""五子棋胜负、策略、接口安全测试；fake 客户端不调用付费服务。"""

import json
import io
import os
import threading
import unittest
import urllib.error
import urllib.request
from contextlib import redirect_stdout
from http.server import HTTPServer
from unittest.mock import patch

from gomoku import Gomoku, HUMAN, JEV, BLACK, WHITE, candidates, choose_move, empty_board, is_win, line_peak, winning_moves
from gomoku_server import handler_for
from triage import call_jev


def fake_ask(state, questions):
    options = questions["next_move"]["criteria"]
    selected = next(iter(options))
    return {"model": "fake-test-only", "usage": {"input_tokens": 12, "output_tokens": 3},
            "answers": {"next_move": {"type": "choice", "choice": selected,
                "confidence": 1.0, "probabilities": {
                    name: float(name == selected) for name in options}}}}


class RulesTests(unittest.TestCase):
    def test_four_directions_and_full_board(self):
        for dr, dc in ((1, 0), (0, 1), (1, 1), (1, -1)):
            board = empty_board()
            points = [(5 + i*dr, 5 + i*dc) for i in range(5)]
            for r, c in points:
                board[r][c] = HUMAN
            self.assertTrue(is_win(board, *points[-1], HUMAN))

    def test_immediate_win_is_code_not_model(self):
        board = empty_board()
        for c in range(5, 9):
            board[7][c] = JEV
        def must_not_call(*args):
            self.fail("一步必胜应由代码处理")
        move, info = choose_move(board, must_not_call)
        self.assertEqual(info["source"], "rule_win")
        self.assertIn(move, winning_moves(board, JEV))

    def test_immediate_block_is_code_not_model(self):
        board = empty_board()
        for c in range(5, 9):
            board[7][c] = HUMAN
        move, info = choose_move(board, lambda *args: self.fail("不应调用模型"))
        self.assertEqual(info["source"], "rule_block")
        self.assertIn(move, winning_moves(board, HUMAN))

    def test_normal_move_is_actual_choice(self):
        board = empty_board()
        board[7][7] = HUMAN
        self.assertEqual(len(candidates(board)), 224)
        self.assertIn((0, 0), candidates(board))
        self.assertIn((14, 14), candidates(board))
        move, info = choose_move(board, fake_ask)
        self.assertEqual(info["source"], "jev")
        self.assertEqual(info["model"], "fake-test-only")
        self.assertEqual(len(info["candidates"]), 224)
        self.assertEqual(board[move[0]][move[1]], 0)

    def test_remote_empty_cell_is_a_real_choice(self):
        board = empty_board()
        board[7][7] = HUMAN

        def choose_corner(state, questions):
            options = questions["next_move"]["criteria"]
            self.assertEqual(set(options), {f"r{r:02d}c{c:02d}" for r, c in candidates(board)})
            self.assertNotIn("candidates", state)  # 不重复发送 224 项说明
            return {"model": "fake-test-only", "answers": {"next_move": {
                "type": "choice", "choice": "r00c00", "confidence": 1.0,
                "probabilities": {name: float(name == "r00c00") for name in options}}}}

        move, result = choose_move(board, choose_corner)
        self.assertEqual(move, (0, 0))
        self.assertEqual(result["source"], "jev")

    def test_all_empty_and_almost_full_boards(self):
        self.assertEqual(len(candidates(empty_board())), 225)
        board = [[HUMAN] * 15 for _ in range(15)]
        board[0][14] = 0
        self.assertEqual(candidates(board), [(0, 14)])

    def test_prompt_spells_out_rules_coordinates_and_open_ends(self):
        board = empty_board()
        board[7][7] = HUMAN
        self.assertEqual(line_peak(board, 7, 8, HUMAN), (2, 2))

        def inspect(state, questions):
            self.assertIn("five contiguous", state["rules"])
            self.assertIn("diagonally", state["rules"])
            self.assertIn("zero-based", state["rules"])
            self.assertIn("full board", state["rules"])
            self.assertIn("no forbidden", state["rules"])
            self.assertIn("overlines", state["rules"])
            self.assertIn("open three", state["strategy"])
            self.assertIn("open four", state["strategy"])
            self.assertIn("fork", state["strategy"])
            self.assertIn("immediate", state["strategy"])
            self.assertIn("not a full search", state["strategy"])
            self.assertEqual(state["roles"]["opponent"], "X")
            self.assertEqual(state["roles"]["first_player"], "opponent")
            self.assertNotIn("human", json.dumps(state, ensure_ascii=False))
            self.assertIn("stopping X", state["objective"])
            self.assertIn("open ends", questions["next_move"]["criteria"]["r07c08"])
            return fake_ask(state, questions)

        choose_move(board, inspect)

    def test_ai_first_prompt_is_black_and_full_board(self):
        def inspect(state, questions):
            self.assertEqual(state["roles"], {"you_ai": "X", "opponent": "O", "first_player": "ai", "to_move": "X"})
            self.assertIn("Black X always plays first", state["rules"])
            self.assertIn("horizontal", state["rules"])
            self.assertIn("vertical", state["rules"])
            self.assertIn("diagonal", state["rules"])
            self.assertIn("You play X; opponent plays O", questions["next_move"]["instructions"])
            self.assertEqual(len(questions["next_move"]["criteria"]), 225)
            self.assertIn("X line", questions["next_move"]["criteria"]["r07c07"])
            return fake_ask(state, questions)

        game = Gomoku(ask=inspect)
        game.reset("ai")
        self.assertEqual(game.status, "AI_PENDING")
        with self.assertRaises(ValueError):
            game.human_move(7, 7)
        game.ai_move()
        self.assertEqual(game.board[0][0], BLACK)
        self.assertEqual(game.snapshot()["next"], "human")
        game.human_move(7, 7)
        self.assertEqual(game.board[7][7], WHITE)

    def test_ai_first_failure_keeps_empty_board_for_retry(self):
        game = Gomoku(ask=lambda *args: (_ for _ in ()).throw(OSError("offline")))
        game.reset("ai")
        with self.assertRaises(OSError):
            game.ai_move()
        self.assertEqual(game.status, "AI_PENDING")
        self.assertEqual(sum(map(sum, game.board)), 0)
        game.ask = fake_ask
        game.ai_move()
        self.assertEqual(game.board[0][0], BLACK)

    def test_invalid_first_rejected(self):
        game = Gomoku(ask=fake_ask)
        with self.assertRaises(ValueError):
            game.reset("robot")
        self.assertEqual(game.first, "human")

    def test_dynamic_colors_for_win_and_rule_block(self):
        board = empty_board()
        for c in range(4, 8):
            board[5][c] = BLACK
        move, info = choose_move(board, lambda *a: self.fail("应走必胜规则"), ai_player=BLACK)
        self.assertIn(move, winning_moves(board, BLACK))
        self.assertEqual(info["source"], "rule_win")
        game = Gomoku(ask=fake_ask)
        game.reset("ai")
        game.board = board
        game.ai_move()
        self.assertEqual(game.status, "JEV_WON")

    def test_logging_only_json_body_and_response_without_bearer(self):
        class FakeHTTP:
            def __enter__(self):
                return io.BytesIO(b'{"answers":{"next_move":{"choice":"r00c00"}},"model":"test"}')

            def __exit__(self, *_):
                return False

        captured = io.StringIO()
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": "secret-test-placeholder"}), \
             patch("urllib.request.urlopen", return_value=FakeHTTP()) as urlopen, \
             redirect_stdout(captured):
            call_jev({"board": ["X"]}, {"next_move": {"type": "choice"}}, log_io=True)
        self.assertIn("Bearer secret-test-placeholder", urlopen.call_args.args[0].headers["Authorization"])
        lines = captured.getvalue().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("JEV_REQUEST "))
        self.assertTrue(lines[1].startswith("JEV_RESPONSE "))
        self.assertEqual(json.loads(lines[0].removeprefix("JEV_REQUEST "))["state"]["board"], ["X"])
        self.assertEqual(json.loads(lines[1].removeprefix("JEV_RESPONSE "))["model"], "test")
        self.assertNotIn("secret-test-placeholder", captured.getvalue())
        self.assertNotIn("Authorization", captured.getvalue())

    def test_illegal_moves_and_failed_ai_never_fake_result(self):
        game = Gomoku(ask=lambda *args: (_ for _ in ()).throw(OSError("simulated failure")))
        with self.assertRaises(ValueError):
            game.human_move(True, 7)
        game.human_move(7, 7)
        with self.assertRaises(ValueError):
            game.human_move(7, 8)
        with self.assertRaises(OSError):
            game.ai_move()
        self.assertEqual(game.status, "AI_PENDING")
        self.assertEqual(len(game.turns), 0)


class WebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), handler_for(Gomoku(ask=fake_ask)))
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def post(self, path, data, origin=None):
        request = urllib.request.Request(self.base + path, json.dumps(data).encode(), method="POST",
            headers={"Content-Type": "application/json", "Origin": origin or self.base})
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def test_serves_ui_without_secrets(self):
        with urllib.request.urlopen(self.base + "/") as response:
            html = response.read().decode()
        self.assertIn("五子棋", html)
        self.assertNotIn("apikey_", html)

    def test_player_move_triggers_model_and_rejects_replay(self):
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": "test-placeholder"}):
            self.post("/api/reset", {})
            result = self.post("/api/move", {"row": 7, "col": 7})
            self.assertEqual(result["board"][7][7], HUMAN)
            self.assertEqual(result["turns"][-1]["source"], "jev")
            self.assertEqual(result["status"], "PLAYING")
            with self.assertRaises(urllib.error.HTTPError) as caught:
                self.post("/api/move", {"row": 7, "col": 7})
            self.assertEqual(caught.exception.code, 400)

    def test_reset_to_ai_first_and_human_first(self):
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": "test-placeholder"}):
            first = self.post("/api/reset", {"first": "ai"})
            self.assertEqual((first["first"], first["ai_color"], first["board"][0][0]), ("ai", BLACK, BLACK))
            self.assertEqual(first["turns"][0]["source"], "jev")
            self.assertEqual(first["next"], "human")
            human = self.post("/api/move", {"row": 7, "col": 7})
            self.assertEqual(human["board"][7][7], WHITE)
            reset = self.post("/api/reset", {"first": "human"})
            self.assertEqual(reset["first"], "human")
            self.assertEqual(reset["turns"], [])
            self.assertEqual(reset["board"][0][0], 0)

    def test_invalid_first_http_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.post("/api/reset", {"first": "robot"})
        self.assertEqual(caught.exception.code, 400)

    def test_rejects_cross_site_and_client_board(self):
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.post("/api/move", {"row": 7, "col": 7}, origin="https://example.invalid")
        self.assertEqual(caught.exception.code, 403)
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": "test-placeholder"}):
            with self.assertRaises(urllib.error.HTTPError) as caught:
                self.post("/api/move", {"board": [[2]]})
            self.assertEqual(caught.exception.code, 400)


if __name__ == "__main__":
    unittest.main()