"""05：测试本地 LangGraph Server / Studio 后端。

前置：在 code 目录执行 langgraph dev 启动服务。
然后另开终端执行：python 05_test_local_server_client.py

默认运行 ticket_router，因为它不依赖真实 LLM，最适合验证可视化执行链路。
也可以通过环境变量切换：LANGGRAPH_ASSISTANT=parallel_writer python 05_test_local_server_client.py
"""

from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv
from langgraph_sdk import get_client

load_dotenv(".env", override=True)


SAMPLE_INPUTS = {
    "calculator_agent": {
        "messages": [{"role": "human", "content": "先计算 7 乘以 8，再把结果加 6，最后除以 2。"}],
        "llm_calls": 0,
    },
    "ticket_router": {
        "ticket": "导出 PDF 的时候系统崩溃了。",
        "category": "",
        "steps": [],
        "answer": "",
    },
    "email_review_agent": {
        "email_content": "I was charged twice for my subscription! Please help ASAP.",
        "sender_email": "customer@example.com",
        "email_id": "mail-001",
        "classification": None,
        "search_results": [],
        "draft_response": "",
        "approved": None,
        "final_response": "",
    },
    "prompt_chain": {"topic": "LangGraph", "draft": "", "improved": "", "final": ""},
    "parallel_writer": {"topic": "LangGraph", "joke": "", "story": "", "poem": "", "combined": ""},
    "evaluator_optimizer": {"topic": "LangGraph", "attempt": 0, "draft": "", "feedback": ""},
}


async def main() -> None:
    url = os.getenv("LANGGRAPH_SERVER_URL", "http://127.0.0.1:2024")
    assistant = os.getenv("LANGGRAPH_ASSISTANT", "ticket_router")
    client = get_client(url=url)

    print(f"连接 LangGraph Server: {url}")
    print("当前可选 assistant：")
    assistants = await client.assistants.search()
    for item in assistants:
        print(f"- {item['graph_id']}")

    if assistant not in SAMPLE_INPUTS:
        raise SystemExit(f"未知 LANGGRAPH_ASSISTANT={assistant}，请从上面的列表中选择。")

    print(f"\n开始 threadless stream: {assistant}")
    print("提示：同时打开 Studio 页面，就能看到同一个图的节点结构和执行过程。")

    async for chunk in client.runs.stream(
        None,
        assistant,
        input=SAMPLE_INPUTS[assistant],
        stream_mode="updates",
    ):
        print(f"event={chunk.event}")
        print(chunk.data)
        print("-" * 60)


if __name__ == "__main__":
    asyncio.run(main())
