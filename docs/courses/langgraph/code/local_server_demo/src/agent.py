"""LangGraph Local Server 最小应用。

langgraph.json 会读取这里的 graph 变量：
    "agent": "src.agent:graph"

大白话：本地 Server 并不是重新写一套 Agent，它只是把你编译好的 graph
包装成 HTTP API 和 Studio 可调试的服务。
"""

from __future__ import annotations

import os
from typing import Annotated

from dotenv import load_dotenv
from langchain.messages import AnyMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

load_dotenv()


class State(TypedDict):
    # add_messages 比 operator.add 更适合聊天：它能按消息 ID 更新已有消息。
    messages: Annotated[list[AnyMessage], add_messages]


def make_model() -> ChatOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("请在 local_server_demo/.env 中填写 OPENAI_API_KEY")

    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=api_key,
        base_url=os.getenv("OPENAI_BASE_URL") or None,
        temperature=0,
    )


def call_model(state: State) -> dict:
    """本地服务暴露的单节点 Agent。"""

    model = make_model()
    response = model.invoke(
        [SystemMessage(content="你是一个简洁、准确的 LangGraph 助教。")]
        + state["messages"]
    )
    return {"messages": [response]}


builder = StateGraph(State)
builder.add_node("call_model", call_model)
builder.add_edge(START, "call_model")
builder.add_edge("call_model", END)

graph = builder.compile()
