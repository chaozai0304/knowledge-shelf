"""01：Deep Agents 官方快速入门增强版 —— Tavily 资料研究员。

官方 quickstart 的核心流程是：
1. 安装 deepagents 和 tavily-python。
2. 配置模型 provider 的 API key，以及 TAVILY_API_KEY。
3. 创建 internet_search 搜索工具。
4. 用 create_deep_agent 创建研究 Agent。
5. 调用 agent.invoke(...) 运行，并观察规划、搜索、文件系统和子智能体能力。

为了方便学习，本脚本默认 RUN_AGENT=false，只演示工具和结构，不会真实调用模型。
当你在 .env 中配置好真实 key 后，把 RUN_AGENT=true 即可运行完整 Agent。
"""

from __future__ import annotations

import os
from typing import Any, Literal

from langchain.tools import tool

from common import explain_dry_run, model_for_deepagents, print_section, require_runtime, safe_preview, should_run_agent

from dotenv import load_dotenv

load_dotenv(".env", override=True)

# 本地迷你知识库：当没有 Tavily key 或不想联网时，仍然可以先理解工具调用流程。
LOCAL_KB = {
    "deep agents": "Deep Agents 是构建长任务智能体的 LangChain 套件，内置规划、文件系统、子智能体、上下文管理等 Harness 能力。",
    "langgraph": "LangGraph 提供图执行、持久化、interrupt、人机协同、流式输出和部署能力，是 Deep Agents 的底座。",
    "context engineering": "上下文工程关注输入上下文、运行时上下文、压缩、隔离和长期记忆，让长任务不会被上下文窗口拖垮。",
}


def has_real_tavily_key() -> bool:
    """检查是否配置了真实 Tavily key。

    Tavily 是官方 quickstart 使用的搜索服务。
    如果这里返回 False，internet_search 会自动退回本地知识库，避免新手第一次运行就失败。
    """
    # 结构演示模式下强制不联网，避免新手未安装 tavily-python 或不想消耗 Tavily 调用时失败。
    if not should_run_agent():
        return False

    key = os.getenv("TAVILY_API_KEY", "")
    return bool(key) and not key.startswith("请替换") and not key.startswith("你的")


def search_local_knowledge_base(query: str) -> dict[str, Any]:
    """在本地知识库里做一个极简搜索。

    这个函数模拟 Tavily 返回结构：包含 query 和 results。
    这样无论是否联网，Agent 都能收到一致格式的工具结果。
    """
    query_lower = query.lower()
    results = []

    # 小白提示：真实搜索引擎会做分词、排序、召回；这里为了教学只做包含匹配。
    for title, content in LOCAL_KB.items():
        if title in query_lower or query_lower in title:
            results.append({"title": title, "content": content, "url": "local://course-kb"})

    return {
        "query": query,
        "source": "local_fallback",
        "results": results or [{"title": "未命中", "content": "没有命中本地知识库，请换一个关键词。", "url": "local://empty"}],
    }


@tool
def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
) -> dict[str, Any]:
    """运行互联网搜索，优先使用 Tavily，未配置 key 时退回本地知识库。

    参数说明：
    - query：搜索关键词。
    - max_results：最多返回几条结果。
    - topic：Tavily 支持的搜索主题，官方示例包含 general/news/finance。
    - include_raw_content：是否返回网页原始正文；新手建议先用 False，避免上下文过大。
    """
    if not has_real_tavily_key():
        return search_local_knowledge_base(query)

    # 延迟导入 Tavily：只有真实联网搜索时才需要加载这个依赖。
    try:
        from tavily import TavilyClient  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        return {
            "query": query,
            "source": "missing_dependency_fallback",
            "results": [
                {
                    "title": "缺少 tavily-python",
                    "content": "请先执行 pip install deepagents tavily-python，或安装 requirements.txt。当前先返回本地演示结果。",
                    "url": "local://missing-tavily",
                }
            ],
        }

    tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    result = tavily_client.search(
        query=query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )
    print("--------搜索结果---------")
    print(result)
    return result


# 这个提示词直接对应官方 quickstart：让 Agent 成为“研究员”，并告诉它必须善用搜索工具。
RESEARCH_INSTRUCTIONS = """
你是一个专业资料研究员。你的工作是先做充分研究，再写出结构清晰、证据充分的中文报告。

你可以使用 `internet_search` 作为主要资料来源。

## `internet_search`

用它搜索给定问题。你可以指定 max_results、topic，以及是否包含 raw content。

工作要求：
1. 先规划研究步骤，不要急着下结论。
2. 至少调用一次 internet_search 获取证据。
3. 如果搜索结果很多，可以把中间材料写入虚拟文件系统，再提炼结论。
4. 最终回答必须包含：结论、关键证据、下一步建议。
""".strip()


def build_research_agent():
    """创建 Deep Agent。

    create_deep_agent 会自动给 Agent 注入 Harness 能力：
    - write_todos：让 Agent 维护任务计划。
    - 虚拟文件系统：让 Agent 读写中间材料。
    - task：默认通用子智能体，用于委派复杂子任务。
    - 上下文管理：长任务时自动压缩和隔离上下文。
    """
    from deepagents import create_deep_agent

    return create_deep_agent(
        model=model_for_deepagents(),
        tools=[internet_search],
        system_prompt=RESEARCH_INSTRUCTIONS,
    )


def preview_search_tool() -> None:
    """先单独试跑搜索工具，帮助新手确认工具输入输出。"""
    print_section("搜索工具试跑")
    result = internet_search.invoke({"query": "deep agents是什么", "max_results": 3})
    print(safe_preview(result, limit=10000))


def run_real_agent() -> None:
    """真实调用 Deep Agent。

    注意：这里会请求模型供应商 API，也可能调用 Tavily 搜索 API。
    如果 key 或模型名错误，错误通常来自模型网关，而不是 Deep Agents 代码本身。
    """
    require_runtime()
    agent = build_research_agent()
    try:
        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "请研究 Deep Agents 和 LangGraph以及langchain 的关系，并给我一份 5 行以内的学习路线。",
                    }
                ]
            }
        )
    except Exception as exc:
        print_section("模型调用失败")
        print(type(exc).__name__)
        print(str(exc))
        print("\n排查建议：")
        print("1. 如果你使用 OpenAI 兼容网关，确认 .env 中 DEEPAGENTS_USE_RESPONSES_API=false。")
        print("2. 确认 OPENAI_BASE_URL、OPENAI_API_KEY、DEEPAGENTS_MODEL 属于同一个网关。")
        print("3. 如果仍然 502，通常是网关后端模型临时不可用或不支持该模型名。")
        return

    print_section("最终回答")
    print(safe_preview(result["messages"][-1].content, limit=2000))


def main() -> None:
    """脚本入口：先展示工具，再根据 RUN_AGENT 决定是否真实调用 Agent。"""
    # preview_search_tool()

    if not should_run_agent():
        explain_dry_run("01_quickstart_research_agent.py")
        print_section("官方 quickstart 对应命令")
        print("pip install deepagents tavily-python")
        print("export TAVILY_API_KEY='your-tavily-api-key'")
        print("export GOOGLE_API_KEY='your-api-key'  # 如果使用 google_genai:* 模型")
        return

    run_real_agent()


if __name__ == "__main__":
    main()
