"""03：上下文工程、后端、记忆与 Skills。

本例重点不是让模型多聪明，而是展示 Deep Agents 如何把文件系统、长期记忆和技能组合起来。
"""

from __future__ import annotations

from common import explain_dry_run, model_for_deepagents, print_section, require_runtime, should_run_agent

MEMORY_FILES = {
    "/memories/preferences.md": """# 用户偏好\n- 回答用中文。\n- 先给结论，再给步骤。\n""",
    "/skills/order-helpers/SKILL.md": """---\nname: order-helpers\ndescription: 当需要对订单记录进行清洗、按状态分组、统计金额或生成订单摘要时使用。\nmodule: index.ts\n---\n\n# order-helpers\n使用 index.ts 中的 groupByStatus 和 summarizeOrders 处理订单。\n""",
}


def build_agent():
    """创建一个同时启用 Memory、Skills 和解释器的 Deep Agent。

    StateBackend 是默认线程内虚拟文件系统；这里显式创建，是为了让 skills_backend
    和 agent backend 指向同一个地方，解释器才能读取 skill 里的模块文件。
    """
    from deepagents import create_deep_agent
    from deepagents.backends import StateBackend  # type: ignore[import-not-found]
    from langchain_quickjs import CodeInterpreterMiddleware  # type: ignore[import-not-found]

    # backend 决定 /memories/、/skills/ 这些虚拟路径背后的存储位置。
    backend = StateBackend()
    return create_deep_agent(
        model=model_for_deepagents(),
        backend=backend,
        memory=["/memories/preferences.md"],
        skills=["/skills/"],
        middleware=[CodeInterpreterMiddleware(skills_backend=backend)],
    )


def main() -> None:
    """演示上下文分层，并在真实运行时把 memory/skill 文件注入虚拟文件系统。"""
    print_section("上下文分层")
    print("1. system_prompt：稳定角色与任务规则")
    print("2. runtime context：本次请求的用户、组织、权限等")
    print("3. filesystem：短期草稿、资料、报告")
    print("4. memory：跨会话长期偏好或知识")
    print("5. skills：按需加载的大块流程知识")

    print_section("本例会注入的虚拟文件")
    for path, content in MEMORY_FILES.items():
        print(f"{path}: {content.splitlines()[0]}")

    if not should_run_agent():
        explain_dry_run("03_context_backends_memory_skills.py")
        return

    require_runtime()
    from deepagents.backends.utils import create_file_data  # type: ignore[import-not-found]

    agent = build_agent()
    # create_file_data 是 Deep Agents 要求的文件包装格式；不要直接传原始字符串。
    files = {path: create_file_data(content) for path, content in MEMORY_FILES.items()}
    result = agent.invoke(
        {
            "messages": [{"role": "user", "content": "根据我的偏好，解释 Deep Agents 的 memory 和 skills 有什么区别。"}],
            "files": files,
        },
        config={"configurable": {"thread_id": "context-backend-demo"}},
    )
    print_section("最终回答")
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
