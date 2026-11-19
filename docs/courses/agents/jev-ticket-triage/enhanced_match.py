"""五子棋多模型对战：代码判规则，Jev Choice / New API Chat 各选自己的合法落点。"""

import json
import os
import re
import time
import urllib.error
import urllib.request

from gomoku import BLACK, WHITE, SIZE, candidates, choose_move, empty_board, is_win, move_id, winning_moves
from triage import call_jev

PLATFORM_BASE = "http://自己的模型ip:端口"
PLATFORM_MODEL = "qwen3.7-flash-non-thinking"
MODES = {"human_jev", "human_qwen", "jev_qwen"}


def platform_model():
    """网关已提供专用非思考路由；旧启动命令中的原模型名也走该路由。"""
    selected = os.environ.get("PLATFORM_MODEL", PLATFORM_MODEL)
    return PLATFORM_MODEL if selected == "qwen3.7-flash" else selected


class PlatformMoveError(ValueError):
    """不含原始输出或凭据的可安全展示错误。"""


def output_budget(model):
    # 推理模型的 max_tokens 包含隐藏思考；实测 origin-deepseek-v4-flash 在 512 时
    # reasoning_tokens=512、content_length=0，因此不能用小预算要求它返回坐标。
    default = 48 if model == PLATFORM_MODEL else 2048
    setting = os.environ.get("PLATFORM_MAX_TOKENS")
    if setting is None:
        return default
    if not setting.isdecimal() or not 32 <= int(setting) <= 4096:
        raise ValueError("PLATFORM_MAX_TOKENS must be between 32 and 4096")
    return int(setting)


def json_mode_enabled():
    setting = os.environ.get("PLATFORM_JSON_MODE", "1")
    if setting not in ("0", "1"):
        raise ValueError("PLATFORM_JSON_MODE must be 0 or 1")
    return setting == "1"


def parse_move(content, finish_reason, legal, budget=None):
    """只解析唯一、可验证的最终坐标；绝不从 reasoning_content 猜测落点。"""
    if not isinstance(content, str) or not content.strip():
        if finish_reason == "length":
            hint = f"（本次 max_tokens={budget}）" if budget is not None else ""
            next_step = (
                "已达到本程序 4096 的输出上限；不要重复调高预算。请切换已验证可用的非思考模型路由，"
                "或在网关确认该模型支持关闭思考后再试"
                if budget is not None and budget >= 4096 else
                "若需继续使用此推理模型，可设置 PLATFORM_MAX_TOKENS=4096 并重启；"
                "更快的选择是切换已验证可用的非思考模型路由"
            )
            raise PlatformMoveError(
                "模型输出预算耗尽" + hint + "，最终 content 为空；棋盘未推进。"
                + next_step
            )
        raise PlatformMoveError("模型返回了空的最终 content；棋盘未推进")
    try:
        data = json.loads(content.strip())
    except ValueError as error:
        raise PlatformMoveError("模型最终 content 不是 JSON 对象；棋盘未推进") from error
    if not isinstance(data, dict) or set(data) != {"move"}:
        raise PlatformMoveError("模型返回的 JSON 必须仅含 move 字段；棋盘未推进")
    selected = data["move"]
    if not isinstance(selected, str) or not re.fullmatch(r"r\d{2}c\d{2}", selected):
        raise PlatformMoveError("模型返回的坐标格式无效；棋盘未推进")
    if selected not in legal:
        raise PlatformMoveError("模型选择了占用或越界的格子；棋盘未推进")
    return selected


def platform_move(board, player, transport=None):
    """选择 Qwen 落点；必胜/必防由确定性规则完成并明确标注。"""
    opponent = WHITE if player == BLACK else BLACK
    wins = winning_moves(board, player)
    blocks = winning_moves(board, opponent)
    if wins or blocks:
        move = sorted(wins or blocks)[0]
        return move, {"source": "rule_win" if wins else "rule_block", "model": None,
                      "confidence": None, "usage": None, "reason": "代码一步必胜/必防"}
    options = candidates(board)
    if not options:
        raise ValueError("no legal moves")
    symbol = "X" if player == BLACK else "O"
    other = "O" if player == BLACK else "X"
    rows = "\n".join(f"{r:02d} {''.join('.XO'[cell] for cell in line)}" for r, line in enumerate(board))
    messages = [
        {"role": "system", "content": (
            "15x15 Gomoku. X is black and moves first; O is white. Five in a row wins. "
            "Choose exactly one empty cell (.) on the board. The final answer MUST be one JSON object "
            '{"move":"rXXcYY"} where XX and YY are zero-based row and column 00..14. '
            "No extra fields, prose or markdown."
        )},
        {"role": "user", "content": (
            f"You are {symbol}; opponent is {other}. Select one empty cell for your next move. "
            "Board (each row labelled 00..14):\n" + rows)},
    ]
    model = platform_model()
    budget = output_budget(model)
    body = {"model": model, "messages": messages, "stream": False,
            "temperature": 0, "max_tokens": budget}
    if json_mode_enabled():
        body["response_format"] = {"type": "json_object"}
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    key = os.environ.get("PLATFORM_API_KEY")
    if transport is None:
        if not key:
            raise RuntimeError("PLATFORM_API_KEY is not configured")
        base = os.environ.get("PLATFORM_BASE_URL", PLATFORM_BASE).rstrip("/")
        if not base.startswith(("https://", "http://127.0.0.1:", "http://自己服务器地址:")):
            raise ValueError("PLATFORM_BASE_URL must be HTTPS or the configured local gateway")
        request = urllib.request.Request(base + "/v1/chat/completions", payload,
            headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"}, method="POST")
        # 只打印实际发送的 body；Authorization 头和 API Key 不在 body 中。
        print("PLATFORM_REQUEST\n" + json.dumps(body, ensure_ascii=False, indent=2), flush=True)
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=60) as stream:
                result = json.load(stream)
        except (urllib.error.URLError, OSError, ValueError) as error:
            # 网关可能在连接/读取时超时；不要打印异常文本（URL/响应中可能有敏感数据）。
            print("PLATFORM_FAILURE " + json.dumps({
                "model": model, "elapsed_seconds": round(time.monotonic() - started, 2),
                "error_type": type(error).__name__,
                "http_status": error.code if isinstance(error, urllib.error.HTTPError) else None,
            }, ensure_ascii=False), flush=True)
            raise
        print("PLATFORM_RESPONSE " + json.dumps({
            "model": model, "elapsed_seconds": round(time.monotonic() - started, 2),
        }, ensure_ascii=False), flush=True)
    else:
        result = transport(json.loads(payload))
    try:
        choice = result["choices"][0]
        content = choice["message"].get("content")
    except (KeyError, IndexError, TypeError, AttributeError):
        raise PlatformMoveError("网关响应中缺少 choices[0].message；棋盘未推进") from None
    if transport is None:
        usage = result.get("usage") or {}
        print("PLATFORM_RESULT " + json.dumps({
            "model": result.get("model", model), "requested_model": model,
            "requested_max_tokens": budget, "finish_reason": choice.get("finish_reason"),
            "content_length": len(content) if isinstance(content, str) else None,
            "reasoning_present": bool(choice["message"].get("reasoning_content")),
            "completion_tokens": usage.get("completion_tokens"),
            "reasoning_tokens": (usage.get("completion_tokens_details") or {}).get("reasoning_tokens"),
        }, ensure_ascii=False), flush=True)
    selected = parse_move(content, choice.get("finish_reason"), {move_id(*pos) for pos in options}, budget)
    move = next(pos for pos in options if move_id(*pos) == selected)
    return move, {"source": "platform", "model": result.get("model", platform_model()),
                  "confidence": None, "usage": result.get("usage"), "reason": "Qwen chat returned a legal cell"}


class Match:
    def __init__(self, jev=call_jev, platform=platform_move):
        self.jev = jev
        self.platform = platform
        self.reset()

    def reset(self, mode="human_jev", human_first=True, jev_first=True):
        if mode not in MODES or type(human_first) is not bool or type(jev_first) is not bool:
            raise ValueError("invalid match configuration")
        self.mode = mode
        if mode == "jev_qwen":
            self.actors = {BLACK: "jev" if jev_first else "qwen",
                           WHITE: "qwen" if jev_first else "jev"}
        else:
            opponent = "jev" if mode == "human_jev" else "qwen"
            self.actors = {BLACK: "human" if human_first else opponent,
                           WHITE: opponent if human_first else "human"}
        self.board = empty_board()
        self.next_color = BLACK
        self.winner = None
        self.history = []
        return self.snapshot()

    def snapshot(self):
        return {"board": self.board, "actors": self.actors, "mode": self.mode,
                "next_color": self.next_color if not self.winner else None,
                "next_actor": self.actors[self.next_color] if not self.winner else None,
                "winner": self.winner, "history": self.history}

    def _commit(self, row, col, actor, meta):
        if self.winner or self.board[row][col]:
            raise ValueError("illegal move")
        self.board[row][col] = self.next_color
        self.history.append({"actor": actor, "color": self.next_color, "row": row, "col": col, **meta})
        if is_win(self.board, row, col, self.next_color):
            self.winner = actor
        elif len(self.history) == SIZE * SIZE:
            self.winner = "draw"
        else:
            self.next_color = WHITE if self.next_color == BLACK else BLACK
        return self.snapshot()

    def human_move(self, row, col):
        if (self.winner or self.actors[self.next_color] != "human" or
                type(row) is not int or type(col) is not int or
                not (0 <= row < SIZE and 0 <= col < SIZE) or self.board[row][col]):
            raise ValueError("not a legal human move")
        return self._commit(row, col, "human", {"source": "human", "model": None})

    def ai_step(self):
        if self.winner:
            raise ValueError("match finished")
        actor = self.actors[self.next_color]
        if actor == "human":
            raise ValueError("waiting for human")
        if actor == "jev":
            move, info = choose_move(self.board, self.jev, self.next_color)
        else:
            move, info = self.platform(self.board, self.next_color)
        # Only commit after a valid provider answer; errors leave the board unchanged.
        return self._commit(*move, actor, info)