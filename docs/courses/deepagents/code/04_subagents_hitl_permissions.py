"""04：子智能体、人机协同与权限。

演示：
- 用 subagents 把审查任务隔离给专家角色
- 用 interrupt_on 给敏感工具加人工审批
- 用 FilesystemPermission 限制文件读写范围
"""

from __future__ import annotations

from langchain.tools import tool

from common import explain_dry_run, model_for_deepagents, print_section, require_runtime, safe_preview, should_run_agent


@tool
def publish_report(title: str, body: str) -> str:
    """发布报告到内部知识库。这是敏感操作，需要审批。

    在 build_agent() 里，publish_report 被配置到 interrupt_on，
    因此真实运行时模型提出调用它之前，会先触发人工审核。
    """
    return f"已发布：《{title}》，正文长度 {len(body)} 字。"


@tool
def read_policy(topic: str) -> str:
    """读取内部政策摘要。

    这是低风险只读工具，所以 interrupt_on 中把它设置为 False。
    """
    return f"{topic} 政策摘要：禁止泄露客户隐私；涉及外部发布必须人工审批。"


PERMISSIONS_EXPLANATION = [
    "允许读取 /workspace/**",
    "允许写入 /workspace/drafts/**",
    "拒绝读写 /workspace/.env",
    "拒绝写入 /memories/**，把共享记忆设为只读",
]


SUBAGENTS = [
    {
        "name": "compliance-reviewer",
        "description": "审查报告是否包含隐私、合规和未经批准的承诺。",
        "system_prompt": "你是合规审查员。只输出风险、证据和修改建议。",
        "tools": [read_policy],
    }
]


def build_agent():
    """创建带子智能体、HITL 和文件系统权限的 Deep Agent。"""
    from deepagents import FilesystemPermission, create_deep_agent
    from langgraph.checkpoint.memory import MemorySaver

    return create_deep_agent(
        model=model_for_deepagents(),
        tools=[publish_report, read_policy],
        subagents=SUBAGENTS,
        interrupt_on={
            # publish_report 风险高：允许人工通过、修改参数或拒绝执行。
            "publish_report": {"allowed_decisions": ["approve", "edit", "reject"]},
            # read_policy 只是读政策摘要，不需要打断用户。
            "read_policy": False,
        },
        permissions=[
            # first-match-wins：更具体的规则要放在更宽泛规则前面。
            FilesystemPermission(operations=["read", "write"], paths=["/workspace/.env"], mode="deny"),
            FilesystemPermission(operations=["write"], paths=["/memories/**"], mode="deny"),
            FilesystemPermission(operations=["read", "write"], paths=["/workspace/**"], mode="allow"),
            FilesystemPermission(operations=["read", "write"], paths=["/**"], mode="deny"),
        ],
        checkpointer=MemorySaver(),
    )


def main() -> None:
    """展示安全策略；真实运行时观察 interrupt 或最终执行结果。"""
    print_section("权限规则设计")
    for item in PERMISSIONS_EXPLANATION:
        print(f"- {item}")

    print_section("敏感工具策略")
    print("publish_report：approve / edit / reject")
    print("read_policy：无需审批")

    if not should_run_agent():
        explain_dry_run("04_subagents_hitl_permissions.py")
        return

    require_runtime()
    agent = build_agent()
    # HITL 恢复必须使用同一个 thread_id，因为中断现场保存在 checkpointer 里。
    config = {"configurable": {"thread_id": "hitl-permission-demo"}}
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "审查并发布一份关于客户案例的简短报告。"}]},
        config=config,
        version="v2",
    )
    print_section("执行结果或中断")
    print(safe_preview(result))
    if getattr(result, "interrupts", None):
        print("检测到 interrupt：请根据 action_requests 提供 approve/edit/reject 后用 Command 恢复。")


if __name__ == "__main__":
    main()
