"""03：用 LangGraph 思考 —— 客服邮件 Agent 的可暂停流程。

这个示例对应 thinking-in-langgraph：
1. 先把流程拆成节点
2. 再设计状态
3. 对复杂/高风险路径加 human-in-the-loop

运行：python 03_thinking_email_agent.py
"""

from __future__ import annotations

from typing import Literal, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from common import print_section, save_mermaid

from dotenv import load_dotenv

load_dotenv(".env", override=True)

class EmailClassification(TypedDict):
    intent: Literal["question", "bug", "billing", "feature", "complex"]
    urgency: Literal["low", "medium", "high", "critical"]
    topic: str
    summary: str


class EmailAgentState(TypedDict):
    # 原始邮件数据：原始事实应该放进 state，方便后续节点复用和审计。
    email_content: str
    sender_email: str
    email_id: str

    # 中间判断结果
    classification: EmailClassification | None
    search_results: list[str]
    draft_response: str

    # 人类审批结果
    approved: bool | None
    final_response: str


def read_email(state: EmailAgentState) -> dict:
    """读取邮件节点。

    大白话：这里示例里邮件已经在输入中；真实系统里可能是从邮箱、工单系统读取。
    """

    return {}


def classify_intent(state: EmailAgentState) -> Command[Literal["search_documentation", "human_review"]]:
    """分类并直接决定下一步。

    这里使用 Command，是因为我们既要写入 classification，又要根据分类结果路由。
    """

    content = state["email_content"].lower()
    if "charged" in content or "扣费" in content or "billing" in content:
        classification: EmailClassification = {
            "intent": "billing",
            "urgency": "critical",
            "topic": "账单异常",
            "summary": "用户反馈疑似重复扣费，需要人工确认。",
        }
    elif "crash" in content or "504" in content or "崩溃" in content:
        classification = {
            "intent": "bug",
            "urgency": "high",
            "topic": "产品缺陷",
            "summary": "用户遇到错误或稳定性问题，需要收集信息。",
        }
    else:
        classification = {
            "intent": "question",
            "urgency": "low",
            "topic": "普通问题",
            "summary": "用户提出产品使用问题，可先检索文档。",
        }

    # 高风险账单问题先交给人，不要让 Agent 自作主张。
    goto = "human_review" if classification["urgency"] in {"high", "critical"} else "search_documentation"
    return Command(update={"classification": classification}, goto=goto)


def search_documentation(state: EmailAgentState) -> dict:
    """文档检索节点。

    大白话：真实项目里可以接向量库、知识库、搜索 API。
    这里用静态结果模拟，重点是说明 search_results 应该保存原始结果，而不是保存拼好的 prompt。
    """

    topic = state["classification"]["topic"] if state["classification"] else "未知"
    return {"search_results": [f"知识库命中：{topic} 的处理说明", "建议回复保持简短，并给出下一步操作。"]}


def draft_response(state: EmailAgentState) -> dict:
    """生成草稿节点。"""

    classification = state["classification"] or {}
    docs = "；".join(state["search_results"])
    return {
        "draft_response": (
            f"你好，我们已收到你的反馈。问题类型：{classification.get('topic', '待确认')}。"
            f"参考信息：{docs} 我们会继续跟进。"
        )
    }


def human_review(state: EmailAgentState) -> Command[Literal["search_documentation", "send_reply", "__end__"]]:
    """人工审核节点。

    interrupt 会暂停图，把 payload 返回给调用方。恢复时，Command(resume=...) 的值会成为 review。
    注意：interrupt 前面的非幂等副作用会在恢复时重新执行，所以不要在这里先发邮件/写订单。
    """

    review = interrupt(
        {
            "question": "这封邮件是否允许 Agent 继续处理？",
            "classification": state["classification"],
            "email": state["email_content"],
            "expected_input": "approve / reject / send_now",
        }
    )

    if review == "reject":
        return Command(update={"approved": False, "final_response": "已转人工处理。"}, goto=END)
    if review == "send_now":
        return Command(update={"approved": True, "draft_response": "已确认，客服会优先处理该账单问题。"}, goto="send_reply")
    return Command(update={"approved": True}, goto="search_documentation")


def send_reply(state: EmailAgentState) -> dict:
    """发送回复节点。

    示例里不真的发邮件，只返回 final_response。真实项目中建议把发送动作做成单独节点，并加幂等键。
    """

    return {"final_response": state["draft_response"]}


def build_graph(checkpointer=None):
    builder = StateGraph(EmailAgentState)
    builder.add_node("read_email", read_email)
    builder.add_node("classify_intent", classify_intent)
    builder.add_node("search_documentation", search_documentation)
    builder.add_node("draft_response", draft_response)
    builder.add_node("human_review", human_review)
    builder.add_node("send_reply", send_reply)

    builder.add_edge(START, "read_email")
    builder.add_edge("read_email", "classify_intent")
    builder.add_edge("search_documentation", "draft_response")
    builder.add_edge("draft_response", "send_reply")
    builder.add_edge("send_reply", END)

    # Studio / LangGraph API 会自动接管持久化；普通脚本模式才传 InMemorySaver。
    return builder.compile(checkpointer=checkpointer)


# LangGraph Studio / langgraph dev 会通过 langgraph.json 读取这个变量。
# 这个图包含 interrupt，适合在 Studio 里观察“暂停 -> 人工输入 -> 恢复”的过程。
# 注意：这里不要传自定义 checkpointer，LangGraph API 会自动接管持久化。
graph = build_graph()


def main() -> None:
    graph = build_graph(checkpointer=InMemorySaver())
    mermaid_path = save_mermaid(graph, "03_email_agent.mmd")
    print_section("图结构已保存")
    print(mermaid_path)

    config = {"configurable": {"thread_id": "email-demo-1"}}
    initial_state: EmailAgentState = {
        "email_content": "I was charged twice for my subscription! Please help ASAP.",
        "sender_email": "customer@example.com",
        "email_id": "mail-001",
        "classification": None,
        "search_results": [],
        "draft_response": "",
        "approved": None,
        "final_response": "",
    }

    print_section("第一次运行：触发人工审核 interrupt")
    first = graph.invoke(initial_state, config=config)
    print(first)

    print_section("模拟人工批准后恢复")
    resumed = graph.invoke(Command(resume="approve"), config=config)
    print(resumed)


if __name__ == "__main__":
    main()
