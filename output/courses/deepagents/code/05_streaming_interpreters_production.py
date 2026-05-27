"""05：解释器、流式输出与生产化部署骨架。

展示三个生产化要点：
1. CodeInterpreterMiddleware 让 Agent 用代码整理中间结果。
2. stream / stream_events 让前端看到子智能体进度。
3. langgraph.json 把 agent 注册为可部署图。
"""

from __future__ import annotations

import json
from pathlib import Path

from langchain.tools import tool
from langgraph.config import get_stream_writer

from common import explain_dry_run, model_for_deepagents, print_section, require_runtime, should_run_agent


@tool
def analyze_orders(topic: str) -> str:
    """模拟一个会持续汇报进度的数据分析工具。

    get_stream_writer() 可以把工具内部进度作为 custom stream 发给前端，
    适合展示“开始分析 / 正在分组 / 已完成”这类进度条。
    """
    writer = get_stream_writer()
    writer({"status": "starting", "topic": topic, "progress": 0})
    writer({"status": "grouping", "progress": 50})
    writer({"status": "complete", "progress": 100})
    return "订单分析结论：退款集中在 pending 状态，建议优先检查支付回调链路。"


SUBAGENTS = [
    {
        "name": "data-analyst",
        "description": "分析订单、漏斗和运营数据，并汇报过程进度。",
        "system_prompt": "你是数据分析师。分析请求必须调用 analyze_orders 工具。",
        "tools": [analyze_orders],
    }
]


def build_agent():
    """创建带解释器和数据分析子智能体的 Deep Agent。"""
    from deepagents import create_deep_agent
    from langchain_quickjs import CodeInterpreterMiddleware  # type: ignore[import-not-found]

    return create_deep_agent(
        model=model_for_deepagents(),
        system_prompt="你是项目协调员。复杂分析任务先交给 data-analyst，再给出一句话结论。",
        subagents=SUBAGENTS,
        # ptc=["task"] 表示解释器中的 TypeScript 代码可以调用 task 工具委派子智能体。
        middleware=[CodeInterpreterMiddleware(ptc=["task"])],
    )


def write_langgraph_json() -> Path:
    """生成 LangGraph/Deep Agents 部署配置文件。

    LangGraph Platform 或 Studio 会通过这个文件找到 agent 变量。
    """
    path = Path(__file__).resolve().parent / "langgraph.json"
    data = {
        "dependencies": ["."],
        "graphs": {"deepagents_course_agent": "./05_streaming_interpreters_production.py:agent"},
        "env": ".env",
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


# 供 LangGraph Platform / Studio 按 langgraph.json 加载。
try:
    agent = build_agent()
except Exception:
    agent = None


def main() -> None:
    """脚本入口：写出部署配置，并演示 streaming 相关概念。"""
    config_path = write_langgraph_json()
    print_section("部署配置已写入")
    print(config_path)

    if not should_run_agent():
        explain_dry_run("05_streaming_interpreters_production.py")
        print_section("可观察的流")
        print("- stream_mode='updates'：看节点/子智能体进度")
        print("- stream_mode='messages'：看模型 token 和工具调用")
        print("- stream_mode='custom'：看工具内部自定义进度")
        print("- stream_events(version='v3')：新应用推荐的 typed projection API")
        return

    require_runtime()
    runtime_agent = build_agent()
    print_section("流式事件")
    for chunk in runtime_agent.stream(
        {"messages": [{"role": "user", "content": "分析订单异常，并展示过程进度。"}]},
        stream_mode=["updates", "custom"],
        subgraphs=True,
        version="v2",
    ):
        print(chunk)


if __name__ == "__main__":
    main()
