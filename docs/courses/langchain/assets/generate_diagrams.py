# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math

OUT = Path(__file__).resolve().parent

FONT_PATHS = [
    '/System/Library/Fonts/PingFang.ttc',
    '/System/Library/Fonts/STHeiti Light.ttc',
    '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
]

def font(size, bold=False):
    for p in FONT_PATHS:
        if Path(p).exists():
            for kwargs in ({'index': 1 if bold else 0}, {}):
                try:
                    return ImageFont.truetype(p, size, **kwargs)
                except Exception:
                    pass
    return ImageFont.load_default()

PRIMARY = '#10213E'
ACCENT = '#5DB2E2'
SECONDARY = '#625D9C'
MUTED = '#64748B'
BG = '#F7FAFC'
SOFT = '#EEF7FF'
LINE = '#BFDDEE'
WHITE = '#FFFFFF'
GREEN = '#22C55E'
ORANGE = '#F59E0B'

TITLE = font(30, True)
SUB = font(18)
NODE = font(20, True)
SMALL = font(15)

def rounded(draw, box, fill=WHITE, outline=LINE, width=2, radius=22):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def text_center(draw, box, text, fnt, fill=PRIMARY, spacing=4):
    lines = text.split('\n')
    sizes = []
    for line in lines:
        bb = draw.textbbox((0, 0), line, font=fnt)
        sizes.append((bb[2] - bb[0], bb[3] - bb[1]))
    total_h = sum(h for _, h in sizes) + spacing * (len(lines) - 1)
    y = box[1] + (box[3] - box[1] - total_h) / 2
    for line, (w, h) in zip(lines, sizes):
        x = box[0] + (box[2] - box[0] - w) / 2
        draw.text((x, y), line, font=fnt, fill=fill)
        y += h + spacing

def arrow(draw, start, end, color=ACCENT, width=4):
    draw.line([start, end], fill=color, width=width)
    dx, dy = end[0] - start[0], end[1] - start[1]
    ang = math.atan2(dy, dx)
    L = 14
    A = 0.55
    p1 = (end[0] - L * math.cos(ang - A), end[1] - L * math.sin(ang - A))
    p2 = (end[0] - L * math.cos(ang + A), end[1] - L * math.sin(ang + A))
    draw.polygon([end, p1, p2], fill=color)

def header(draw, title, subtitle=None):
    draw.text((54, 36), title, font=TITLE, fill=PRIMARY)
    if subtitle:
        draw.text((56, 78), subtitle, font=SUB, fill=MUTED)

def save(img, name):
    img.save(OUT / name, quality=95)

def diagram_streaming():
    img = Image.new('RGB', (1200, 720), BG)
    d = ImageDraw.Draw(img)
    header(d, 'LangChain 流式传输三种模式', '同一次 Agent 运行，可以按不同视角把过程流出来')
    steps = [
        ('用户请求', '输入问题'),
        ('模型节点', '判断是否调用工具'),
        ('工具节点', '查询业务系统'),
        ('模型节点', '生成最终回答'),
    ]
    xs = [90, 360, 650, 930]
    y = 185
    boxes = []
    for x, (a, b) in zip(xs, steps):
        box = (x, y, x + 190, y + 92)
        boxes.append(box)
        rounded(d, box)
        text_center(d, box, f'{a}\n{b}', NODE)
    for b1, b2 in zip(boxes, boxes[1:]):
        arrow(d, (b1[2] + 8, (b1[1] + b1[3]) // 2), (b2[0] - 8, (b2[1] + b2[3]) // 2))
    lanes = [
        ('updates', '每一步状态更新\nmodel → tools → model', '#EAF4FF'),
        ('messages', '模型 token + metadata\n文本、工具调用片段、reasoning', '#F3F0FF'),
        ('custom', '工具内部主动汇报\n例如：已读取工单、已匹配规则', '#ECFDF5'),
    ]
    y0 = 365
    for i, (name, desc, fill) in enumerate(lanes):
        yy = y0 + i * 92
        rounded(d, (90, yy, 1110, yy + 64), fill=fill, outline='#D8E8F4')
        d.text((120, yy + 17), name, font=NODE, fill=SECONDARY if name != 'custom' else '#047857')
        d.text((300, yy + 13), desc, font=SMALL, fill=PRIMARY)
        arrow(d, (245, yy + 32), (285, yy + 32), color=SECONDARY if name != 'custom' else '#10B981', width=3)
    d.text((90, 660), '记法：updates 管步骤，messages 管文字，custom 管业务进度。', font=SUB, fill=PRIMARY)
    save(img, 'langchain-streaming-modes.png')

def diagram_structured():
    img = Image.new('RGB', (1200, 760), BG)
    d = ImageDraw.Draw(img)
    header(d, 'LangChain 结构化输出策略选择', 'response_format 负责告诉 Agent：最终要交一份可校验的数据')
    boxes = {
        'schema': (455, 130, 745, 218),
        'check': (455, 285, 745, 375),
        'provider': (115, 455, 425, 550),
        'tool': (775, 455, 1085, 550),
        'result': (455, 625, 745, 705),
    }
    rounded(d, boxes['schema'])
    text_center(d, boxes['schema'], '传入 schema\nPydantic / TypedDict / JSON Schema', NODE)
    arrow(d, (600, 218), (600, 285))
    rounded(d, boxes['check'], fill=SOFT)
    text_center(d, boxes['check'], 'LangChain 判断模型能力\n是否支持原生结构化输出', NODE)
    arrow(d, (530, 375), (300, 455), color=GREEN)
    arrow(d, (670, 375), (930, 455), color=ORANGE)
    rounded(d, boxes['provider'], fill='#ECFDF5', outline='#A7F3D0')
    text_center(d, boxes['provider'], 'ProviderStrategy\n模型 API 原生约束\n通常更可靠', NODE)
    rounded(d, boxes['tool'], fill='#FFF7ED', outline='#FED7AA')
    text_center(d, boxes['tool'], 'ToolStrategy\n通过工具调用生成结构\n兼容面更广，可重试', NODE)
    arrow(d, (425, 505), (455, 665), color=GREEN)
    arrow(d, (775, 505), (745, 665), color=ORANGE)
    rounded(d, boxes['result'])
    text_center(d, boxes['result'], 'structured_response\n可直接给程序消费', NODE)
    d.text((155, 405), '支持原生结构化输出', font=SMALL, fill='#047857')
    d.text((790, 405), '不支持或强制工具策略', font=SMALL, fill='#B45309')
    d.text((70, 715), '重点：结构化输出不是“请返回 JSON”，而是 schema、校验、错误反馈和结果捕获。', font=SUB, fill=PRIMARY)
    save(img, 'langchain-structured-output-strategy.png')

def diagram_agent_loop():
    img = Image.new('RGB', (1200, 700), BG)
    d = ImageDraw.Draw(img)
    header(d, 'Agent 核心循环', '对应 LangChain Middleware Overview 中的 core agent loop')
    coords = [
        ('用户输入', '业务问题进入 Agent', (95, 260, 285, 355)),
        ('调用模型', '判断下一步动作', (370, 160, 570, 255)),
        ('执行工具', '读取数据或执行动作', (690, 160, 890, 255)),
        ('最终回答', '没有更多工具调用时结束', (915, 260, 1110, 355)),
        ('工具结果', 'ToolMessage 回到模型', (530, 410, 760, 505)),
    ]
    for title, desc, box in coords:
        rounded(d, box)
        text_center(d, box, f'{title}\n{desc}', NODE)
    arrow(d, (285, 307), (370, 210))
    arrow(d, (570, 208), (690, 208))
    arrow(d, (890, 208), (1010, 260))
    arrow(d, (790, 255), (650, 410))
    arrow(d, (530, 455), (470, 255))
    d.text((385, 286), '模型决定要不要调用工具', font=SMALL, fill=MUTED)
    d.text((532, 535), '如果还需要工具：继续循环；如果不需要工具：输出最终答案。', font=SUB, fill=PRIMARY)
    save(img, 'langchain-agent-core-loop.png')

def diagram_middleware_hooks():
    img = Image.new('RGB', (1200, 760), BG)
    d = ImageDraw.Draw(img)
    header(d, '中间件插入 Agent 执行流程的位置', '对应 LangChain Middleware Overview：before/after 与 wrap hooks')
    stages = [
        ('before_agent', '代理启动前\n一次调用一次'),
        ('before_model', '每次模型调用前\n改提示词 / 过滤上下文'),
        ('模型调用', 'LLM 生成工具调用或答案'),
        ('after_model', '模型响应后\n检查输出 / HITL 审批'),
        ('工具执行', '执行 ToolCall'),
        ('after_agent', '代理结束后\n记录结果 / 清理状态'),
    ]
    x, y, w, h, gap = 80, 175, 160, 88, 30
    boxes = []
    for i, (a, b) in enumerate(stages):
        box = (x + i * (w + gap), y, x + i * (w + gap) + w, y + h)
        boxes.append(box)
        fill = '#F3F0FF' if 'model' in a or 'agent' in a else WHITE
        if a in ['模型调用', '工具执行']:
            fill = '#EAF4FF'
        rounded(d, box, fill=fill)
        text_center(d, box, f'{a}\n{b}', SMALL if a not in ['模型调用', '工具执行'] else NODE)
    for b1, b2 in zip(boxes, boxes[1:]):
        arrow(d, (b1[2] + 6, y + h // 2), (b2[0] - 6, y + h // 2), width=3)
    d.rounded_rectangle((405, 330, 645, 430), radius=18, fill='#FFF7ED', outline='#FDBA74', width=2)
    text_center(d, (405, 330, 645, 430), 'wrap_model_call\n包住模型调用\n可重试 / 回退 / 替换模型', SMALL)
    arrow(d, (525, 330), (525, 263), color=ORANGE, width=3)
    d.rounded_rectangle((785, 330, 1035, 430), radius=18, fill='#ECFDF5', outline='#86EFAC', width=2)
    text_center(d, (785, 330, 1035, 430), 'wrap_tool_call\n包住工具调用\n可重试 / 限流 / 监控', SMALL)
    arrow(d, (910, 330), (910, 263), color=GREEN, width=3)
    examples = [
        ('安全', 'PII 检测、人审、权限校验'),
        ('稳定', '模型回退、工具重试'),
        ('成本', '模型调用限制、工具调用限制'),
        ('上下文', '摘要、上下文裁剪'),
    ]
    for i, (a, b) in enumerate(examples):
        xx, yy = 125 + i * 270, 535
        rounded(d, (xx, yy, xx + 220, yy + 82))
        text_center(d, (xx, yy, xx + 220, yy + 82), f'{a}\n{b}', SMALL)
    d.text((80, 680), '重点：中间件不是替代业务工具，而是在 Agent 每个关键节点上加规则、加保护、加观测。', font=SUB, fill=PRIMARY)
    save(img, 'langchain-middleware-hooks.png')

if __name__ == '__main__':
    diagram_streaming()
    diagram_structured()
    diagram_agent_loop()
    diagram_middleware_hooks()
    print('generated', len(list(OUT.glob('*.png'))), 'png diagrams in', OUT)
