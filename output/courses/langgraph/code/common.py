"""LangGraph 讲解示例的公共工具。

这个文件故意写得啰嗦一点：
- 读 .env：方便你把自己的模型地址和 key 填进去。
- 创建模型：统一使用 OpenAI 兼容接口，很多国产/私有网关都支持这种格式。
- 保存 Mermaid：不用额外依赖浏览器，也能看到图结构。
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from openai import AuthenticationError


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")


def make_model(temperature: float = 0) -> ChatOpenAI:
    """创建一个 OpenAI 兼容 Chat 模型。

    大白话：LangGraph 不绑定某一家模型。这里用 ChatOpenAI 只是因为
    OpenAI 兼容协议最常见。你把 OPENAI_BASE_URL 换成自己的网关即可。
    """

    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    if not api_key:
        raise RuntimeError(
            "缺少 OPENAI_API_KEY。请复制 code/.env.example 为 code/.env 后填写。"
        )

    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url or None,
        temperature=temperature,
    )


def explain_model_error(error: Exception) -> str:
    """把模型网关报错翻译成更容易排查的中文提示。"""

    if isinstance(error, AuthenticationError):
        return (
            "模型网关返回 401：API Key/令牌无效。\n"
            "这通常说明 code/.env 已经被读取到了，但 OPENAI_API_KEY 不是当前网关认可的有效 key。\n"
            "请检查：\n"
            "1. OPENAI_API_KEY 是否复制完整，没有多余空格或引号；\n"
            "2. OPENAI_BASE_URL 是否和这个 key 属于同一个模型网关；\n"
            "3. OPENAI_MODEL 是否是该网关支持的模型名；\n"
            "4. 可先运行 python test_openai_config.py 做最小化连通性测试。"
        )

    return (
        f"模型调用失败：{type(error).__name__}: {error}\n"
        "建议先运行 python test_openai_config.py，确认 .env 中的模型地址、key 和模型名可用。"
    )


def save_mermaid(graph, filename: str) -> Path:
    """把图结构保存为 Mermaid 文本文件。

    大白话：Mermaid 就像“流程图源码”。很多 Markdown/文档工具都能渲染它。
    这里不强依赖 PNG 渲染，保证示例在普通终端也能跑。
    """

    out = ROOT / "generated_graphs"
    out.mkdir(exist_ok=True)
    path = out / filename
    path.write_text(graph.get_graph(xray=True).draw_mermaid(), encoding="utf-8")
    return path


def print_section(title: str) -> None:
    """打印一个清晰的小标题，方便看终端输出。"""

    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)
