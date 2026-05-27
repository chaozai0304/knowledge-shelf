"""03B：持久 memory 版 —— 用 FilesystemBackend 把记忆真正保存到磁盘。

和原版 03_context_backends_memory_skills.py 的区别：
1. 原版使用 StateBackend，并把 memory/skill 文件通过 invoke(files=...) 临时注入。
2. 本版使用 FilesystemBackend，memory/skill 文件会真实落盘到本地目录。
3. 因此，只要文件被修改，下次再运行脚本时仍然存在，这才是真正的“持久 memory”。

默认行为：
- 如果磁盘上还没有初始文件，脚本会自动创建。
- 如果磁盘上已经有文件，脚本不会覆盖，避免把你之前积累的记忆抹掉。

建议学习顺序：
1. 先运行一次，看看它把文件创建到了哪里。
2. 打开真实文件手动改一行，再运行一次，观察 Agent 读取到的内容变化。
3. 如果你想观察 Agent 自动写回 memory，可以把下方用户问题改成“请在 preferences.md 里新增一条偏好”。
"""

from __future__ import annotations

from pathlib import Path

from common import explain_dry_run, model_for_deepagents, print_section, require_runtime, should_run_agent


# 持久化根目录：所有 memory 和 skills 都真实保存在这里。
PERSISTENT_ROOT = Path(__file__).resolve().parent / "persistent_memory_demo"
MEMORY_FILE = PERSISTENT_ROOT / "memories" / "preferences.md"
SKILL_DIR = PERSISTENT_ROOT / "skills" / "order-helpers"
SKILL_FILE = SKILL_DIR / "SKILL.md"
SKILL_MODULE = SKILL_DIR / "index.ts"

INITIAL_MEMORY = """# 用户偏好
- 回答用中文。
- 先给结论，再给步骤。
- 代码示例请带清晰注释。
"""

INITIAL_SKILL_MD = """---
name: order-helpers
description: 当需要对订单记录进行清洗、按状态分组、统计金额或生成订单摘要时使用。
module: index.ts
---

# order-helpers

这是一个可被解释器按需加载的 Skill。

适用场景：
- 订单记录很多，模型不适合手写分组逻辑时
- 需要稳定、可复用的分组和汇总函数时

在解释器中导入：

```typescript
const { groupByStatus, summarizeOrders } = await import("@/skills/order-helpers");
```
"""

INITIAL_SKILL_TS = """interface Order {
  id: string;
  status: string;
  amount: number;
}

export function groupByStatus(orders: Order[]) {
  return orders.reduce<Record<string, Order[]>>((acc, order) => {
    acc[order.status] = acc[order.status] ?? [];
    acc[order.status].push(order);
    return acc;
  }, {});
}

export function summarizeOrders(orders: Order[]) {
  const total = orders.reduce((sum, order) => sum + order.amount, 0);
  const byStatus = groupByStatus(orders);
  return {
    count: orders.length,
    total,
    statusCounts: Object.fromEntries(
      Object.entries(byStatus).map(([status, rows]) => [status, rows.length]),
    ),
  };
}
"""


def ensure_persistent_files_exist() -> None:
    """确保磁盘上的初始 memory 和 skill 文件存在。

    关键点：
    - 只在文件不存在时创建。
    - 已有文件绝不覆盖，这样你之前积累的记忆就能保留下来。
    """
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    SKILL_DIR.mkdir(parents=True, exist_ok=True)

    if not MEMORY_FILE.exists():
        MEMORY_FILE.write_text(INITIAL_MEMORY, encoding="utf-8")

    if not SKILL_FILE.exists():
        SKILL_FILE.write_text(INITIAL_SKILL_MD, encoding="utf-8")

    if not SKILL_MODULE.exists():
        SKILL_MODULE.write_text(INITIAL_SKILL_TS, encoding="utf-8")


def read_memory_snapshot() -> str:
    """读取当前磁盘上的 memory 文件内容，方便运行前后对比。"""
    return MEMORY_FILE.read_text(encoding="utf-8")


def build_agent():
    """创建使用 FilesystemBackend 的 Deep Agent。

    FilesystemBackend 会把虚拟路径映射到真实磁盘目录：
    - /memories/preferences.md -> persistent_memory_demo/memories/preferences.md
    - /skills/order-helpers/SKILL.md -> persistent_memory_demo/skills/order-helpers/SKILL.md

    这意味着：如果 Agent 或你手动修改这些文件，改动都会保留到下次运行。
    """
    from deepagents import create_deep_agent
    from deepagents.backends import FilesystemBackend  # type: ignore[import-not-found]
    from langchain_quickjs import CodeInterpreterMiddleware  # type: ignore[import-not-found]

    backend = FilesystemBackend(root_dir=PERSISTENT_ROOT)
    return create_deep_agent(
        model=model_for_deepagents(),
        backend=backend,
        memory=["/memories/preferences.md"],
        skills=["/skills/"],
        middleware=[CodeInterpreterMiddleware(skills_backend=backend)],
    )


def main() -> None:
    """脚本入口：创建真实文件、展示落盘位置，再运行 Agent。"""
    ensure_persistent_files_exist()

    print_section("真实落盘位置")
    print(f"memory 文件：{MEMORY_FILE}")
    print(f"skill 文件：{SKILL_FILE}")
    print(f"skill 模块：{SKILL_MODULE}")

    print_section("当前 memory 快照")
    print(read_memory_snapshot())

    if not should_run_agent():
        explain_dry_run("03b_persistent_memory_filesystem.py")
        print_section("怎么验证它是持久的")
        print("1. 打开上面打印出来的 preferences.md，手动新增一行偏好。")
        print("2. 再次运行本脚本。")
        print("3. 你会看到新的内容仍然存在，因为它已经真实保存在磁盘上。")
        return

    require_runtime()
    agent = build_agent()
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "请先读取我的 memory 和 skills，"
                        "再用中文解释 Deep Agents 的 memory 和 skills 有什么区别。"
                        "这次只解释，不要修改任何文件。"
                    ),
                }
            ]
        },
        config={"configurable": {"thread_id": "persistent-memory-demo"}},
    )

    print_section("最终回答")
    print(result["messages"][-1].content)

    print_section("运行后 memory 快照")
    print(read_memory_snapshot())


if __name__ == "__main__":
    main()
