"""Render an explicitly synthetic human-vs-Jev replay; never calls the live API.

Requires Pillow only for regenerating the GIF: python3 render_gomoku_demo.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from gomoku import BLACK, WHITE, Gomoku, move_id


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "gomoku-human-jev-demo.gif"
HUMAN_MOVES = [(7, 7), (8, 7), (6, 6), (9, 6), (6, 9)]
FIXTURE_JEV_MOVES = [(7, 8), (8, 8), (9, 8), (6, 8)]
FONT_PATH = "/System/Library/Fonts/STHeiti Medium.ttc"


def font(size):
    return ImageFont.truetype(FONT_PATH, size)


def replay():
    """Use the production game engine; the fixture supplies choices, not probabilities from Jev."""
    fixture = iter(FIXTURE_JEV_MOVES)

    def choose_fixture(state, questions):
        cell = move_id(*next(fixture))
        options = questions["next_move"]["criteria"]
        assert cell in options
        return {"model": "synthetic-fixture-not-jev", "answers": {"next_move": {
            "type": "choice", "choice": cell, "confidence": 1.0,
            "probabilities": {key: float(key == cell) for key in options},
        }}}

    game = Gomoku(ask=choose_fixture)
    moves = []
    for row, col in HUMAN_MOVES:
        game.human_move(row, col)
        moves.append((row, col, BLACK, "human"))
        game.ai_move()
        decision = game.turns[-1]
        moves.append((decision["row"], decision["col"], WHITE, decision["source"]))
    assert game.status == "JEV_WON"
    assert moves[-1][3] == "rule_win"
    return moves


def frame(moves, count):
    image = Image.new("RGB", (840, 704), "#f2f5fb")
    d = ImageDraw.Draw(image)
    d.rounded_rectangle((22, 20, 818, 682), radius=24, fill="#ffffff")
    d.text((54, 42), "人类 × Jev  五子棋", font=font(29), fill="#122742")
    d.text((54, 88), "模拟复盘 · 非在线 Jev 对局", font=font(18), fill="#945400")

    left, top, step = 76, 172, 29
    d.rounded_rectangle((left - 34, top - 34, left + 14 * step + 34, top + 14 * step + 34),
                        radius=16, fill="#d8b988")
    for i in range(15):
        x, y = left + i * step, top + i * step
        d.line((x, top, x, top + 14 * step), fill="#8c6d48", width=2)
        d.line((left, y, left + 14 * step, y), fill="#8c6d48", width=2)
    for row, col in ((3, 3), (3, 11), (7, 7), (11, 3), (11, 11)):
        x, y = left + col * step, top + row * step
        d.ellipse((x - 4, y - 4, x + 4, y + 4), fill="#715538")

    for index, (row, col, color, _) in enumerate(moves[:count]):
        x, y = left + col * step, top + row * step
        fill = "#172840" if color == BLACK else "#f8fafc"
        d.ellipse((x - 12, y - 12, x + 12, y + 12), fill=fill,
                  outline="#566272" if color == WHITE else "#172840", width=2)
        if index == count - 1:
            d.ellipse((x - 4, y - 4, x + 4, y + 4), fill="#ffad52" if color == BLACK else "#256ad4")

    x = 552
    d.text((x, 174), "对局进度", font=font(24), fill="#152d4e")
    d.text((x, 216), f"{count:02d} / {len(moves):02d} 手", font=font(25), fill="#3561ad")
    d.rounded_rectangle((x, 266, 782, 277), radius=5, fill="#e2eafa")
    if count:
        d.rounded_rectangle((x, 266, x + 230 * count // len(moves), 277), radius=5, fill="#4c77d5")
        row, col, color, source = moves[count - 1]
        d.text((x, 315), "人类 · 黑棋" if color == BLACK else "Jev · 白棋", font=font(22), fill="#172840")
        d.text((x, 356), f"落点：第 {row + 1} 行 {col + 1} 列", font=font(18), fill="#344b66")
        label = "固定测试响应" if source == "jev" else "规则引擎直接必胜" if source == "rule_win" else "玩家落子"
        d.text((x, 396), label, font=font(17), fill="#786036")
    else:
        d.text((x, 315), "人类执黑先手", font=font(22), fill="#172840")
        d.text((x, 355), "演示棋盘 15 × 15", font=font(18), fill="#344b66")
    if count == len(moves):
        d.rounded_rectangle((x - 6, 458, 784, 516), radius=12, fill="#e6f3ed")
        d.text((x + 8, 472), "白棋五连 · 演示结束", font=font(18), fill="#195844")
    d.text((54, 648), "常规 Jev 落点来自离线夹具；最后一步由代码识别必胜，并非模型实测。",
           font=font(16), fill="#52627b")
    return image


def main():
    moves = replay()
    frames = [frame(moves, i).quantize(colors=128, method=Image.Quantize.FASTOCTREE)
              for i in range(len(moves) + 1)]
    frames[0].save(OUTPUT, save_all=True, append_images=frames[1:], loop=0,
                   duration=[1200] + [900] * (len(frames) - 2) + [2600], optimize=True)
    print(f"Saved {OUTPUT} ({len(frames)} frames; {len(moves)} moves)")


if __name__ == "__main__":
    main()