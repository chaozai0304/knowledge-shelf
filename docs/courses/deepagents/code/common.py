"""Deep Agents 课程示例公共工具。

这些脚本默认以“结构演示模式”运行，不会直接消耗模型调用。
如需真实调用 deep agent，请在 .env 中设置 RUN_AGENT=true，并配置可用模型。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
# override=True 很重要：如果终端里残留旧的 OPENAI_API_KEY / OPENAI_BASE_URL，
# 这里强制以当前课程目录的 .env 为准，避免“明明改了 .env 但运行仍用旧配置”。
load_dotenv(ROOT / ".env", override=True)


def print_section(title: str) -> None:
    """用统一样式打印章节标题，方便初学者阅读终端输出。"""
    print(f"\n{'=' * 18} {title} {'=' * 18}")


def should_run_agent() -> bool:
    """判断是否真的调用模型。

    课程默认是结构演示模式：RUN_AGENT=false。
    只有你确认 key、模型名和网关可用后，再把 RUN_AGENT 改成 true。
    """
    return os.getenv("RUN_AGENT", "false").lower() in {"1", "true", "yes", "y"}


def model_spec() -> str:
    """返回 Deep Agents 支持的 provider:model 模型字符串。"""
    return os.getenv("DEEPAGENTS_MODEL", "openai:gpt-4o-mini")


def openai_model_name() -> str:
    """把 Deep Agents 的 openai:model 写法转换为 ChatOpenAI 需要的模型名。

    例如：
    - openai:gpt-4o -> gpt-4o
    - gpt-4o -> gpt-4o
    """
    model = model_spec()
    return model.split(":", 1)[1] if model.startswith("openai:") else model


def use_responses_api() -> bool:
    """是否使用 OpenAI Responses API。

    很多 OpenAI 兼容网关只实现了 /chat/completions，没有实现 /responses。
    因此课程默认 false；如果你直连官方 OpenAI 且确认要用 Responses API，可在 .env 中设置：
    DEEPAGENTS_USE_RESPONSES_API=true
    """
    return os.getenv("DEEPAGENTS_USE_RESPONSES_API", "false").lower() in {"1", "true", "yes", "y"}


def model_for_deepagents() -> Any:
    """返回传给 create_deep_agent 的模型对象或模型字符串。

    - 对 openai:*：显式创建 ChatOpenAI，并默认 use_responses_api=False。
      这样更兼容公司内部网关、LiteLLM、One API 等 OpenAI-compatible 服务。
    - 对 google_genai:*、anthropic:* 等：保留 provider:model 字符串，让 Deep Agents/LangChain 自动解析。
    """
    model = model_spec()
    if not model.startswith("openai:"):
        return model

    from langchain_openai import ChatOpenAI
    import httpx

    # trust_env=False：不读取系统代理变量，避免内网 OpenAI-compatible 网关被代理劫持。
    http_client = httpx.Client(trust_env=False, timeout=60)
    http_async_client = httpx.AsyncClient(trust_env=False, timeout=60)

    return ChatOpenAI(
        model=openai_model_name(),
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL") or None,
        temperature=0,
        max_retries=1,
        timeout=60,
        use_responses_api=use_responses_api(),
        http_client=http_client,
        http_async_client=http_async_client,
    )


def require_runtime() -> None:
    """在真实调用前做最小检查，避免把占位 key 发给网关。"""
    if not should_run_agent():
        raise RuntimeError("当前 RUN_AGENT=false；脚本只展示结构，不真实调用模型。")

    model = model_spec()
    if model.startswith("openai:"):
        key = os.getenv("OPENAI_API_KEY", "")
        if not key or key.startswith("请替换") or key.startswith("你的"):
            raise RuntimeError("请先在 .env 中填写真实 OPENAI_API_KEY。")

    if model.startswith("google_genai:"):
        key = os.getenv("GOOGLE_API_KEY", "")
        if not key or key.startswith("请替换") or key.startswith("你的"):
            raise RuntimeError("请先在 .env 中填写真实 GOOGLE_API_KEY。")


def safe_preview(value: Any, limit: int = 800) -> str:
    """把长对象转成短文本预览，避免终端输出被大结果刷屏。"""
    text = str(value)
    if len(text) <= limit:
        return text
    return text[:limit] + "...<已截断>"


def explain_dry_run(script_name: str) -> None:
    print_section("结构演示模式")
    print(f"{script_name} 已加载成功。")
    print("当前 RUN_AGENT=false，因此不会真实调用模型。")
    print("如需真实运行：复制 .env.example 为 .env，填写 key，并设置 RUN_AGENT=true。")
    print(f"当前模型配置：{model_spec()}")
    if model_spec().startswith("openai:"):
        print(f"OpenAI Responses API：{use_responses_api()}（兼容网关建议保持 false）")
