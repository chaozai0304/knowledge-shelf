# -*- coding: utf-8 -*-
"""整理学习资料库目录结构。

该脚本是一次性整理脚本：
- 根目录原始文章进入 content/
- output 下的成品按领域进入 output/courses/
- 保留 output/langgraph 软链接兼容旧路径
"""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path("/Users/chao/Desktop/分享文档库")


def ensure(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def move(src_rel: str, dst_rel: str) -> None:
    src = ROOT / src_rel
    dst = ROOT / dst_rel
    if not src.exists() and not src.is_symlink():
        return
    ensure(dst.parent)
    if dst.exists() or dst.is_symlink():
        print(f"SKIP exists: {dst_rel}")
        return
    shutil.move(str(src), str(dst))
    print(f"MOVED {src_rel} -> {dst_rel}")


def main() -> None:
    # 根目录原始文章与素材归档到 content/
    move("AI Agent 浪潮汹涌：一周内重磅更新，智能体正加速重塑未来！.md", "content/articles/ai-agent-weekly/article.md")
    move("AI Agent 浪潮汹涌：一周内重磅更新，智能体正加速重塑未来！_assets", "content/articles/ai-agent-weekly/assets")
    move("GPT-6 震撼发布！代号“土豆”，性能暴涨40%，200万Token开启AI“交响乐”时代.md", "content/articles/gpt-6-spud/article.md")
    move("GPT-6 震撼发布！代号“土豆”，性能暴涨40%，200万Token开启AI“交响乐”时代_assets", "content/articles/gpt-6-spud/assets")
    move("AIAgent.docx", "content/sources/docx/AIAgent.docx")
    move("GPT.docx", "content/sources/docx/GPT.docx")
    move("【agent工具】SKILL学习笔记.docx", "content/sources/docx/skill-study-note.docx")
    move("harness-agent", "content/assets/harness-agent")

    # output 重新归类为 courses/assets/index
    move("output/langgraph", "output/courses/langgraph")
    move("output/langchain-lecture-assets", "output/courses/langchain/assets")

    for name in [
        "langchain-middleware-wechat",
        "langchain-streaming-wechat",
        "langchain-structured-output-wechat",
        "langchain-third-wechat",
    ]:
        move(f"output/{name}.md", f"output/courses/langchain/{name}.md")
        move(f"output/{name}.html", f"output/courses/langchain/{name}.html")

    move("output/fine-tuning-intro-wechat.md", "output/courses/fine-tuning/fine-tuning-intro-wechat.md")
    move("output/fine-tuning-intro-wechat.html", "output/courses/fine-tuning/fine-tuning-intro-wechat.html")
    move("output/微调", "output/courses/fine-tuning/notebooks")

    move("output/harness-agents-wechat.md", "output/courses/agents/harness-agents/harness-agents-wechat.md")
    move("output/harness-agents-wechat.html", "output/courses/agents/harness-agents/harness-agents-wechat.html")

    for name in ["skill-study-pro", "skill-study-wechat", "skill-study-final"]:
        move(f"output/{name}.md", f"output/courses/agents/skills/{name}.md")
        move(f"output/{name}.html", f"output/courses/agents/skills/{name}.html")
        move(f"output/{name}.docx", f"output/courses/agents/skills/{name}.docx")
    move("output/skill-study-final_assets", "output/courses/agents/skills/skill-study-final_assets")

    move("output/乐享开发规范.md", "output/courses/engineering-standards/lexiang-dev-standard.md")
    move("output/乐享开发规范 副本.docx", "output/courses/engineering-standards/lexiang-dev-standard.docx")
    move("output/乐享开发规范 副本_assets", "output/courses/engineering-standards/lexiang-dev-standard_assets")

    move("output/ChatGPT Image 2026年4月30日 14_39_05.png", "output/assets/shared/chatgpt-image-2026-04-30.png")

    # 保留旧路径兼容：output/langgraph -> output/courses/langgraph
    legacy = ROOT / "output/langgraph"
    target = ROOT / "output/courses/langgraph"
    if not legacy.exists() and not legacy.is_symlink() and target.exists():
        legacy.symlink_to(Path("courses/langgraph"))
        print("SYMLINK output/langgraph -> output/courses/langgraph")


if __name__ == "__main__":
    main()
