"""15×15 人机五子棋：规则用代码，非强制落点由 Jev 的 Choice 选择。"""

import math

from triage import _probability, call_jev

SIZE = 15
BLACK, WHITE = 1, 2
# 保留原有调用者的默认色值；实际执棋颜色由 Gomoku.first 决定。
HUMAN, JEV = BLACK, WHITE
DIRECTIONS = ((1, 0), (0, 1), (1, 1), (1, -1))


def empty_board():
    return [[0] * SIZE for _ in range(SIZE)]


def run_length(board, row, col, player, dr, dc):
    count = 1
    for sign in (-1, 1):
        r, c = row + sign * dr, col + sign * dc
        while 0 <= r < SIZE and 0 <= c < SIZE and board[r][c] == player:
            count += 1
            r += sign * dr
            c += sign * dc
    return count


def is_win(board, row, col, player):
    return any(run_length(board, row, col, player, dr, dc) >= 5 for dr, dc in DIRECTIONS)


def winning_moves(board, player):
    result = []
    for row in range(SIZE):
        for col in range(SIZE):
            if board[row][col] == 0:
                board[row][col] = player
                won = is_win(board, row, col, player)
                board[row][col] = 0
                if won:
                    result.append((row, col))
    return result


def line_peak(board, row, col, player):
    """若该方在此落子，最长连续线及其两端仍为空的数量。"""
    best = (0, 0)
    for dr, dc in DIRECTIONS:
        length, open_ends = 1, 0
        for sign in (-1, 1):
            r, c = row + sign * dr, col + sign * dc
            while 0 <= r < SIZE and 0 <= c < SIZE and board[r][c] == player:
                length += 1
                r += sign * dr
                c += sign * dc
            if 0 <= r < SIZE and 0 <= c < SIZE and board[r][c] == 0:
                open_ends += 1
        best = max(best, (length, open_ends))
    return best


def candidates(board):
    """返回棋盘所有空格，不再按邻近程度或代码评分裁剪 Jev 的选择。"""
    return [(row, col) for row in range(SIZE) for col in range(SIZE)
            if board[row][col] == 0]


def move_id(row, col):
    return f"r{row:02d}c{col:02d}"


def choose_move(board, ask=call_jev, ai_player=WHITE):
    """依据当前 AI 执棋颜色选择落点；必胜/必防由代码执行。"""
    if ai_player not in (BLACK, WHITE):
        raise ValueError("invalid AI color")
    opponent = WHITE if ai_player == BLACK else BLACK
    ai_symbol = "X" if ai_player == BLACK else "O"
    opponent_symbol = "O" if ai_player == BLACK else "X"
    immediate = winning_moves(board, ai_player)
    blocks = winning_moves(board, opponent)
    if immediate or blocks:
        selected = sorted(immediate or blocks)[0]
        return selected, {"source": "rule_win" if immediate else "rule_block",
                          "reason": "代码检测到一步成五" if immediate else "代码检测到对手下一步可成五",
                          "candidates": [move_id(*p) for p in (immediate or blocks)],
                          "model": None, "probabilities": {}, "confidence": None, "usage": None}

    choices = candidates(board)
    if not choices:
        raise ValueError("board is full")
    criteria = {}
    for r, c in choices:
        (own, own_open) = line_peak(board, r, c, ai_player)
        (theirs, their_open) = line_peak(board, r, c, opponent)
        criteria[move_id(r, c)] = (
            f"{ai_symbol} at row {r+1}, column {c+1}: {ai_symbol} line {own}, open ends {own_open}; "
            f"occupying this cell denies {opponent_symbol} line {theirs}, open ends {their_open}."
        )
    state = {"rules": (
                "15x15 Gomoku, no forbidden-move restrictions. The full board has 15 rows and 15 columns, "
                "top to bottom and left to right. '.' is empty, X is black, O is white. Black X always plays first. "
                "Players strictly alternate, placing exactly one stone on an empty cell per turn; "
                "stones stay in place and cannot be captured or moved. "
                "First to form at least five contiguous own stones horizontally, vertically, or diagonally "
                "(along either diagonal) wins; "
                "overlines (six or more) also win. Only uninterrupted stones count: empty or opponent stones break a line. "
                "If the full board has no winner, it is a draw. No opening restrictions, forbidden moves or special captures. "
                "An open end is the empty cell immediately beyond a contiguous line; two open ends allow growth both ways. "
                "Option ids r00c00 through r14c14 use zero-based row and column; option text uses one-based numbers. "
                "Only keys listed under criteria are legal moves; never select an occupied cell."
             ),
             "roles": {"you_ai": ai_symbol, "opponent": opponent_symbol,
                       "first_player": "ai" if ai_player == BLACK else "opponent",
                       "to_move": ai_symbol},
             "board": ["".join(".XO"[cell] for cell in row) for row in board],
             "objective": (
                 f"You control {ai_symbol}; the opponent controls {opponent_symbol}. "
                 f"Build five {ai_symbol} in a row while stopping {opponent_symbol}. "
                 f"Block open-ended {opponent_symbol} threats and build open {ai_symbol} lines. "
                 "Choose only among empty cells; consider the full board rather than option order."
             ),
             "strategy": (
                 "Code already plays any immediate winning move or blocks an opponent's immediate win before asking you. "
                 "For other positions, compare attack and defense: a contiguous open four (four stones with empty cells "
                 "at both ends) threatens a win on either end; a closed four has only one such end. "
                 "An open three can become an open four; watch for broken lines too, where an empty gap could connect "
                 "separate groups. Give priority to urgent opponent threats over slow attacks unless your move creates "
                 "a stronger immediate threat. Look for forks: a single move that creates two distinct threats in "
                 "different directions, which may be impossible to stop with one reply. Prefer moves that both defend "
                 "and extend your own lines, and consider likely opponent replies. "
                 "The per-cell line length/open ends in criteria are local hints, not a full search or proof that a "
                 "move is safe: inspect the actual board, gaps, crossings, edges and both colors before deciding."
             )}
    response = ask(state, {"next_move": {
        "type": "choice", "instructions": (
            f"It is {ai_symbol}'s turn. You play {ai_symbol}; opponent plays {opponent_symbol}. "
            f"Which single listed empty cell is the best move for {ai_symbol}? "
            "Use the rules, strategy, entire board and criteria; prevent opponent threats and build "
            "your own open lines rather than relying on option order or one local score."
        ),
        "criteria": criteria}})
    answer = response["answers"]["next_move"]
    distribution = answer["probabilities"]
    selected_id = answer["choice"]
    if (answer["type"] != "choice" or set(distribution) != set(criteria)
            or selected_id not in criteria or not _probability(answer["confidence"])
            or any(not _probability(p) for p in distribution.values())
            or not math.isclose(sum(distribution.values()), 1, abs_tol=0.02)
            or distribution[selected_id] != max(distribution.values())):
        raise ValueError("invalid Jev move response")
    selected = next(pos for pos in choices if move_id(*pos) == selected_id)
    return selected, {"source": "jev", "reason": "Jev Choice 从全部空位中选择",
                      "candidates": list(criteria), "probabilities": distribution,
                      "confidence": answer["confidence"], "model": response.get("model"),
                      "usage": response.get("usage")}


class Gomoku:
    def __init__(self, ask=call_jev):
        self.ask = ask
        self.reset()

    def reset(self, first="human"):
        if first not in ("human", "ai"):
            raise ValueError("first must be human or ai")
        self.first = first
        self.ai_color = BLACK if first == "ai" else WHITE
        self.human_color = WHITE if first == "ai" else BLACK
        self.board = empty_board()
        self.status = "AI_PENDING" if first == "ai" else "PLAYING"
        self.turns = []

    def snapshot(self):
        return {"board": self.board, "status": self.status, "turns": self.turns,
                "size": SIZE, "first": self.first, "ai_color": self.ai_color,
                "human_color": self.human_color,
                "next": "human" if self.status == "PLAYING" else
                        "ai" if self.status == "AI_PENDING" else None}

    def human_move(self, row, col):
        if (self.status != "PLAYING" or type(row) is not int or type(col) is not int
                or not (0 <= row < SIZE and 0 <= col < SIZE) or self.board[row][col]):
            raise ValueError("illegal or finished move")
        self.board[row][col] = self.human_color
        if is_win(self.board, row, col, self.human_color):
            self.status = "HUMAN_WON"
        elif all(cell for line in self.board for cell in line):
            self.status = "DRAW"
        else:
            self.status = "AI_PENDING"

    def ai_move(self):
        if self.status != "AI_PENDING":
            raise ValueError("not AI turn")
        (row, col), decision = choose_move(self.board, self.ask, self.ai_color)
        self.board[row][col] = self.ai_color
        if is_win(self.board, row, col, self.ai_color):
            self.status = "JEV_WON"
        elif all(cell for line in self.board for cell in line):
            self.status = "DRAW"
        else:
            self.status = "PLAYING"
        self.turns.append({"row": row, "col": col, "color": self.ai_color, **decision})
        return self.snapshot()