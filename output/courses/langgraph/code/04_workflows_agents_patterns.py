"""04：常见工作流模式 —— 链式、并行、路由、评估优化。

为了降低运行门槛，本文件不用真实 LLM，而用普通 Python 函数模拟“生成”。
你可以把 generate_* 函数替换成模型调用，图结构不变。

运行：python 04_workflows_agents_patterns.py
"""

from __future__ import annotations

import operator
from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from common import print_section, save_mermaid

from dotenv import load_dotenv

load_dotenv(".env", override=True)

class ChainState(TypedDict):
    topic: str
    draft: str
    improved: str
    final: str


def write_draft(state: ChainState) -> dict:
    return {"draft": f"关于 {state['topic']} 的第一版说明：先解释概念，再给例子。"}


def improve_draft(state: ChainState) -> dict:
    return {"improved": state["draft"] + " 补充一句：复杂流程要画成图。"}


def polish_draft(state: ChainState) -> dict:
    return {"final": state["improved"] + " 最后用检查清单收尾。"}


def build_prompt_chain():
    builder = StateGraph(ChainState)
    builder.add_node("write_draft", write_draft)
    builder.add_node("improve_draft", improve_draft)
    builder.add_node("polish_draft", polish_draft)
    builder.add_edge(START, "write_draft")
    builder.add_edge("write_draft", "improve_draft")
    builder.add_edge("improve_draft", "polish_draft")
    builder.add_edge("polish_draft", END)
    return builder.compile()


class ParallelState(TypedDict):
    topic: str
    joke: str
    story: str
    poem: str
    combined: str


def write_joke(state: ParallelState) -> dict:
    return {"joke": f"一个关于 {state['topic']} 的小笑话。"}


def write_story(state: ParallelState) -> dict:
    return {"story": f"一个关于 {state['topic']} 的短故事。"}


def write_poem(state: ParallelState) -> dict:
    return {"poem": f"一首关于 {state['topic']} 的小诗。"}


def aggregate(state: ParallelState) -> dict:
    return {"combined": f"故事：{state['story']}\n笑话：{state['joke']}\n诗：{state['poem']}"}


def build_parallel():
    builder = StateGraph(ParallelState)
    builder.add_node("write_joke", write_joke)
    builder.add_node("write_story", write_story)
    builder.add_node("write_poem", write_poem)
    builder.add_node("aggregate", aggregate)
    builder.add_edge(START, "write_joke")
    builder.add_edge(START, "write_story")
    builder.add_edge(START, "write_poem")
    builder.add_edge("write_joke", "aggregate")
    builder.add_edge("write_story", "aggregate")
    builder.add_edge("write_poem", "aggregate")
    builder.add_edge("aggregate", END)
    return builder.compile()


class EvalState(TypedDict):
    topic: str
    attempt: int
    draft: str
    feedback: str


def generate_answer(state: EvalState) -> dict:
    attempt = state.get("attempt", 0) + 1
    if attempt == 1:
        draft = f"{state['topic']} 很重要。"
    else:
        draft = f"{state['topic']} 很重要，因为它把状态、节点和边组合成可恢复的执行流。"
    return {"attempt": attempt, "draft": draft}


def evaluate_answer(state: EvalState) -> dict:
    if "因为" in state["draft"]:
        return {"feedback": "accepted"}
    return {"feedback": "too vague"}


def route_eval(state: EvalState) -> Literal["generate_answer", "__end__"]:
    if state["feedback"] == "accepted":
        return END
    return "generate_answer"


def build_evaluator_optimizer():
    builder = StateGraph(EvalState)
    builder.add_node("generate_answer", generate_answer)
    builder.add_node("evaluate_answer", evaluate_answer)
    builder.add_edge(START, "generate_answer")
    builder.add_edge("generate_answer", "evaluate_answer")
    builder.add_conditional_edges("evaluate_answer", route_eval, ["generate_answer", END])
    return builder.compile()


class LogState(TypedDict):
    # 这个状态演示 reducer：多个并行节点都写 logs，最终会合并。
    logs: Annotated[list[str], operator.add]


# LangGraph Studio / langgraph dev 会通过 langgraph.json 读取这些变量。
# 一个文件里可以暴露多个图，分别观察链式、并行、评估优化三种执行模式。
prompt_chain_graph = build_prompt_chain()
parallel_graph = build_parallel()
evaluator_optimizer_graph = build_evaluator_optimizer()


def main() -> None:
    examples = [
        ("Prompt chaining", prompt_chain_graph, {"topic": "LangGraph", "draft": "", "improved": "", "final": ""}, "04_prompt_chain.mmd"),
        ("Parallelization", parallel_graph, {"topic": "LangGraph", "joke": "", "story": "", "poem": "", "combined": ""}, "04_parallel.mmd"),
        ("Evaluator optimizer", evaluator_optimizer_graph, {"topic": "LangGraph", "attempt": 0, "draft": "", "feedback": ""}, "04_evaluator_optimizer.mmd"),
    ]

    for name, graph, inputs, filename in examples:
        print_section(name)
        print("图结构：", save_mermaid(graph, filename))
        print(graph.invoke(inputs))


if __name__ == "__main__":
    main()
