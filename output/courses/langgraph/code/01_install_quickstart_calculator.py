"""01：安装与快速入门 —— 一个最小计算器 Agent。

运行前：
1. 安装依赖：pip install -r requirements.txt
2. 复制 .env.example 为 .env，填写 OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL
3. 执行：python 01_install_quickstart_calculator.py

这个例子对应官方 quickstart 的核心结构：
- State：保存消息和调用次数
- Node：一个节点调用模型，一个节点执行工具
- Edge：如果模型要调工具，就去工具节点；否则结束
"""

from __future__ import annotations

import operator
from functools import lru_cache
from typing import Annotated, Literal

from langchain.messages import AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain.tools import tool
from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph

from common import explain_model_error, make_model, print_section, save_mermaid

from dotenv import load_dotenv

load_dotenv(".env", override=True)

@tool
def multiply(a: int, b: int) -> int:
    """Multiply a and b."""

    return a * b


@tool
def add(a: int, b: int) -> int:
    """Add a and b."""

    return a + b


@tool
def divide(a: int, b: int) -> float:
    """Divide a by b."""

    return a / b


# 大白话：State 就是“全流程共享的小本子”。每个节点都从这里读，也往这里写。
# Annotated[..., operator.add] 表示新消息不是覆盖旧消息，而是追加到列表后面。
class CalculatorState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int


tools = [add, multiply, divide]
tools_by_name = {t.name: t for t in tools}


@lru_cache(maxsize=1)
def get_model_with_tools():
    """延迟创建模型，让 Studio 启动时只加载图结构，不提前初始化模型。"""

    return make_model(temperature=0).bind_tools(tools)


def llm_call(state: CalculatorState) -> dict:
    """让模型决定：直接回答，还是先调用工具。

    大白话：这一步像“调度员”。它不自己算，而是决定要不要找工具帮忙。
    """

    response = get_model_with_tools().invoke(
        [
            SystemMessage(
                content=(
                    "You are a helpful calculator assistant. "
                    "Use tools for arithmetic and keep the final answer concise."
                )
            )
        ]
        + state["messages"]
    )
    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


def tool_node(state: CalculatorState) -> dict:
    """执行模型请求的工具调用，并把工具结果写回 messages。

    大白话：模型说“我要调用 add”，这里才真的运行 add 函数。
    """

    result: list[ToolMessage] = []
    last_message = state["messages"][-1]

    for tool_call in last_message.tool_calls:
        tool_fn = tools_by_name[tool_call["name"]]
        observation = tool_fn.invoke(tool_call["args"])
        result.append(
            ToolMessage(content=str(observation), tool_call_id=tool_call["id"])
        )

    return {"messages": result}


def should_continue(state: CalculatorState) -> Literal["tool_node", "__end__"]:
    """根据最后一条 AI 消息判断下一步。

    如果有 tool_calls：说明模型还需要工具结果，去 tool_node。
    如果没有 tool_calls：说明模型已经能给最终答案，结束。
    """

    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tool_node"
    return END


def build_graph():
    """组装并编译图。注意：LangGraph 图必须 compile 后才能运行。"""

    builder = StateGraph(CalculatorState)
    builder.add_node("llm_call", llm_call)
    builder.add_node("tool_node", tool_node)

    builder.add_edge(START, "llm_call")
    builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
    builder.add_edge("tool_node", "llm_call")

    return builder.compile()


# LangGraph Studio / langgraph dev 会通过 langgraph.json 读取这个变量。
# 大白话：脚本模式用 main()；可视化调试模式直接加载 graph。
graph = build_graph()


def main() -> None:
    mermaid_path = save_mermaid(graph, "01_calculator_agent.mmd")

    print_section("图结构已保存")
    print(mermaid_path)

    print_section("执行 Agent")
    try:
        result = graph.invoke(
            {
                "messages": [
                    HumanMessage(
                        content="先计算 7 乘以 8，再把结果加 6，最后除以 2。"
                    )
                ],
                "llm_calls": 0,
            }
        )
    except Exception as error:
        print_section("模型配置或调用失败")
        print(explain_model_error(error))
        raise SystemExit(1) from error

    print_section("完整消息轨迹")
    for message in result["messages"]:
        message.pretty_print()

    print_section("LLM 调用次数")
    print(result["llm_calls"])


if __name__ == "__main__":
    main()
