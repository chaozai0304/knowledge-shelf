"""02：Graph API 基础 —— State、Node、Edge、条件路由。

这个例子不调用真实大模型，方便你先理解 LangGraph 的“骨架”。

业务场景：把用户工单分成 billing / bug / question 三类，并走不同处理节点。
运行：python 02_graph_api_state_edges.py
"""

from __future__ import annotations

import operator
from typing import Annotated, Literal

from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph

from common import print_section, save_mermaid

from dotenv import load_dotenv

load_dotenv(".env", override=True)

class TicketState(TypedDict):
    # 原始输入
    ticket: str
    # 分类结果。默认 reducer 是覆盖：后写入的值替换旧值。
    category: str
    # 处理轨迹。用 operator.add 表示每个节点追加日志，而不是覆盖日志。
    steps: Annotated[list[str], operator.add]
    # 最终回复
    answer: str


def classify_ticket(state: TicketState) -> dict:
    """分类节点：根据关键词模拟一次意图识别。

    大白话：真实项目里这里通常会调用 LLM 或分类模型；
    但节点本质上仍然只是一个 Python 函数。
    """

    text = state["ticket"].lower()
    if any(word in text for word in ["charged", "invoice", "billing", "refund", "付款", "扣费"]):
        category = "billing"
    elif any(word in text for word in ["crash", "bug", "error", "报错", "崩溃"]):
        category = "bug"
    else:
        category = "question"

    return {"category": category, "steps": [f"分类为：{category}"]}


def route_by_category(state: TicketState) -> Literal["billing_node", "bug_node", "question_node"]:
    """条件边的路由函数：只决定下一站，不修改状态。"""

    if state["category"] == "billing":
        return "billing_node"
    if state["category"] == "bug":
        return "bug_node"
    return "question_node"


def billing_node(state: TicketState) -> dict:
    return {
        "steps": ["进入账单处理流程"],
        "answer": "我会先核对账单记录，并为你创建退款/复核工单。",
    }


def bug_node(state: TicketState) -> dict:
    return {
        "steps": ["进入缺陷处理流程"],
        "answer": "我会收集复现步骤、环境信息，并同步给研发排查。",
    }


def question_node(state: TicketState) -> dict:
    return {
        "steps": ["进入普通问答流程"],
        "answer": "我会从知识库检索相关说明，并整理成简短回复。",
    }


def build_graph():
    builder = StateGraph(TicketState)
    builder.add_node("classify_ticket", classify_ticket)
    builder.add_node("billing_node", billing_node)
    builder.add_node("bug_node", bug_node)
    builder.add_node("question_node", question_node)

    builder.add_edge(START, "classify_ticket")
    builder.add_conditional_edges("classify_ticket", route_by_category)
    builder.add_edge("billing_node", END)
    builder.add_edge("bug_node", END)
    builder.add_edge("question_node", END)
    return builder.compile()


# LangGraph Studio / langgraph dev 会通过 langgraph.json 读取这个变量。
# 这个示例不依赖 LLM，很适合先用 Studio 观察条件路由的完整执行过程。
graph = build_graph()


def main() -> None:
    mermaid_path = save_mermaid(graph, "02_state_edges.mmd")

    print_section("图结构已保存")
    print(mermaid_path)

    samples = [
        "I was charged twice for my subscription.",
        "导出 PDF 的时候系统崩溃了。",
        "How do I reset my password?",
    ]

    for ticket in samples:
        print_section(f"处理工单：{ticket}")
        result = graph.invoke({"ticket": ticket, "category": "", "steps": [], "answer": ""})
        print("分类：", result["category"])
        print("轨迹：", " -> ".join(result["steps"]))
        print("回复：", result["answer"])


if __name__ == "__main__":
    main()
