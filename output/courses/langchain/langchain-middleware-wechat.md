---
title: "LangChain 第六讲：中间件，Agent 不是只会调用工具，还要能被管住"
source: "参考 LangChain 官方 JavaScript Middleware Overview / Built-in Middleware / Custom Middleware 文档，并结合 LangChain v1 Python 中文文档整理"
author: "GitHub Copilot"
date: 2026-05-09
created: 2026-05-09
tags:
  - LangChain
  - Middleware
  - Agent
  - Python
  - 微信公众号
summary: "一篇面向公众号分享的 LangChain 第六讲，重点讲清楚预置中间件、自定义中间件、hook、重试、限流、PII、人工审批等机制，并给出完整 Python 示例。"
---

第五讲解决的是“模型输出怎么稳定进入系统”。

第六讲继续往工程里走一步：**当 Agent 真的开始调用模型和工具时，怎么管住它的执行过程**。

前面学 Agent，大家通常先盯着两件事：

- 模型够不够聪明
- 工具接得够不够多

但真到业务现场，你很快会遇到另一类问题：

- 模型会不会无限循环调用工具？
- 工具失败了要不要重试？
- 用户输入里有手机号、邮箱，要不要脱敏？
- 发送邮件、执行 SQL 这种高风险动作，要不要人工审批？
- 对话太长了，要不要自动总结？
- 每次模型调用前，能不能动态塞一点用户上下文？

这些问题靠 prompt 很难管住。

LangChain 的中间件，就是用来处理这些“Agent 运行过程中的管控问题”。

> **工具让 Agent 能干活，中间件让 Agent 干活时别乱来。**

---

## 中间件到底是什么？

大白话讲，中间件就是插在 Agent 执行流程里的“拦截器”。

Agent 的核心循环一般是：

```text
调用模型
  ↓
模型决定是否调用工具
  ↓
执行工具
  ↓
把工具结果交回模型
  ↓
模型继续判断或输出最终答案
```

![Agent 核心循环](langchain-lecture-assets/langchain-agent-core-loop.png)

这张图对应官方 Middleware Overview 里的核心 Agent loop：模型先判断是否需要工具，工具执行后把结果交回模型；如果模型还要继续调用工具，就继续循环；如果不再调用工具，就输出最终答案。

中间件可以插在这些位置前后，做一些横切能力：

- 打日志
- 改提示词
- 限制调用次数
- 检查敏感信息
- 自动重试
- 模型回退
- 人工审批
- 上下文裁剪
- 长对话摘要

它不一定改变业务逻辑，但会改变 Agent 的运行边界。

这就像给一个新人配工作规范：

- 什么事能自己处理
- 什么事要找主管
- 一件事最多尝试几次
- 哪些信息不能直接发出去
- 太长的历史记录怎么归纳

这就是中间件的意义。

![中间件插入 Agent 执行流程的位置](langchain-lecture-assets/langchain-middleware-hooks.png)

这张图对应官方 Middleware Overview 里的第二张流程图：中间件不是替代模型或工具，而是在模型调用前后、工具调用前后、Agent 启动和结束等位置增加 hook，用来做日志、校验、重试、审批、上下文管理等控制。

---

## 官网里的两类中间件

LangChain 官方文档主要分两类：

| 类型 | 作用 | 适合谁 |
|---|---|---|
| 预置中间件 | 官方已经写好的常用能力 | 大多数项目直接用 |
| 自定义中间件 | 自己写 hook 控制 Agent 流程 | 有特殊业务规则的项目 |

我建议先用预置中间件，别一上来就自己写。

因为很多能力官方已经给了：

- `SummarizationMiddleware`
- `HumanInTheLoopMiddleware`
- `ModelCallLimitMiddleware`
- `ToolCallLimitMiddleware`
- `ModelFallbackMiddleware`
- `PIIMiddleware`
- `TodoListMiddleware`
- `LLMToolSelectorMiddleware`
- `ToolRetryMiddleware`
- `ContextEditingMiddleware`

这些名字看起来多，但可以按用途分成四组：

| 用途 | 对应能力 |
|---|---|
| 控成本 | 模型调用限制、工具调用限制、工具选择 |
| 控风险 | PII 检测、人工审批、上下文编辑 |
| 提稳定性 | 工具重试、模型回退、模型重试 |
| 管上下文 | 摘要、上下文裁剪、待办规划 |

---

## 预置中间件：生产里最常用的几个

### 1. 摘要中间件：长对话别硬塞上下文

长对话里最常见的问题是上下文越来越长。

如果每一轮都把完整历史塞给模型，成本会上去，效果也不一定更好。

摘要中间件会在接近 token 阈值时，把旧消息压缩成摘要，同时保留最近消息。

适合：

- 客服多轮对话
- 长周期项目助手
- 内部知识问答助手

### 2. 人在回路中：高风险工具别自动跑

官方 Human-in-the-loop 文档讲得很清楚：某些工具调用前，Agent 可以暂停，等人工批准、编辑或拒绝。

比如：

- 发邮件
- 执行 SQL
- 删除文件
- 提交退款
- 修改合同状态

这类操作不能让模型“觉得可以”就直接执行。

### 3. 调用次数限制：防止 Agent 跑飞

`ModelCallLimitMiddleware` 和 `ToolCallLimitMiddleware` 很适合生产环境。

因为 Agent 一旦陷入循环，消耗的不只是时间，还有钱。

比如一次用户请求最多：

- 调模型 5 次
- 调搜索工具 3 次
- 调数据库工具 2 次

这类上限最好写进系统，而不是写在 prompt 里。

### 4. PII 检测：敏感信息别乱进模型和日志

`PIIMiddleware` 可以检测邮箱、信用卡、IP、URL 等，也支持自定义正则。

常见策略包括：

- `redact`：替换成 `[REDACTED]`
- `mask`：部分隐藏
- `hash`：转成哈希
- `block`：直接阻止

对企业系统来说，这不是锦上添花。

这是合规底线。

### 5. 工具重试：外部系统不稳定时别立刻失败

很多工具背后都是 HTTP API、数据库、搜索服务。

临时失败很正常。

`ToolRetryMiddleware` 可以用指数退避重试，避免一次网络抖动就让整个 Agent 失败。

---

## 自定义中间件：什么时候需要自己写？

当预置中间件不够时，再写自定义中间件。

官方文档里提到两种 hook 风格：

| 风格 | Python 常见名字 | 适合干什么 |
|---|---|---|
| Node-style hooks | `before_agent`、`before_model`、`after_model`、`after_agent` | 打日志、验证、状态更新 |
| Wrap-style hooks | `wrap_model_call`、`wrap_tool_call` | 重试、缓存、短路、动态替换模型或工具 |

大白话：

- `before_*` / `after_*` 像门口检查
- `wrap_*` 像把整个调用包起来，你可以决定调用一次、多次，甚至不调用

如果只是记录日志，用 node-style。

如果要控制执行，比如重试、回退、改模型，用 wrap-style。

---

## 中间件执行顺序要注意

官方 JS 文档里有一个很实用的规则：

- `before_*`：按中间件列表从前到后执行
- `after_*`：反过来执行
- `wrap_*`：像洋葱一样嵌套，列表前面的包住后面的

这意味着顺序不是小事。

比如你有三个中间件：

```text
PII 检测 -> 限流 -> 日志
```

和：

```text
日志 -> 限流 -> PII 检测
```

效果可能完全不同。

因为第一种可以先把敏感信息挡掉，第二种可能已经把原文打进日志了。

我的建议：

> **安全类中间件尽量靠前，日志类中间件要避免记录未脱敏内容。**

---

## 一个自己写的业务示例：合同审批助手

这次我们写一个企业内部合同审批助手。

它能做几件事：

1. 读取合同摘要
2. 检查合同风险
3. 对高风险条款要求人工复核
4. 对敏感邮箱做脱敏
5. 限制模型和工具调用次数
6. 对外部工具失败做重试
7. 用自定义中间件记录模型调用前后的信息

这比官网里的简单示例更接近真实业务。

---

## 完整 Python 代码

> 运行前建议安装：`langchain`、`langchain-openai`、`langgraph`、`python-dotenv`。项目根目录已有 `.env` 时，把 `OPENAI_API_KEY` 写进去即可。

```python
"""
LangChain 中间件完整示例：合同审批助手

这个脚本演示：
1. 预置中间件：PII、模型调用限制、工具调用限制、工具重试
2. 可选高风险能力：HumanInTheLoopMiddleware（需要 checkpointer）
3. 自定义中间件：before_model、after_model、wrap_model_call、dynamic_prompt
4. 一个更贴近企业业务的合同审批 Agent

注意：
- 不同 LangChain 版本的中间件导入路径可能略有差异，请以当前安装版本为准。
- 人在回路中中间件需要 checkpointer，生产环境建议换成持久化 checkpointer。
"""

from __future__ import annotations

import os
import random
import time
from typing import Any, Callable, Literal

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import (
    AgentState,
    HumanInTheLoopMiddleware,
    ModelCallLimitMiddleware,
    ModelRequest,
    ModelResponse,
    PIIMiddleware,
    ToolCallLimitMiddleware,
    ToolRetryMiddleware,
    after_model,
    before_model,
    dynamic_prompt,
    wrap_model_call,
)
from langchain.messages import AIMessage
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.runtime import Runtime
from pydantic import BaseModel, Field


load_dotenv()


CONTRACTS = {
    "CT-2026-001": {
        "customer": "杭州某制造企业",
        "owner_email": "li.chen@example.com",
        "amount": 320000,
        "payment_terms": "验收后 90 天付款",
        "liability_cap": "无明确责任上限",
        "auto_renewal": True,
    },
    "CT-2026-002": {
        "customer": "深圳某零售企业",
        "owner_email": "wang.min@example.com",
        "amount": 48000,
        "payment_terms": "签署后 30 天付款",
        "liability_cap": "责任上限为合同金额",
        "auto_renewal": False,
    },
}


class ContractInput(BaseModel):
    contract_id: str = Field(description="合同编号，例如 CT-2026-001")


@tool(args_schema=ContractInput)
def read_contract_summary(contract_id: str) -> str:
    """读取合同摘要，包括金额、付款条款、责任上限和自动续约信息。"""

    contract = CONTRACTS.get(contract_id)
    if contract is None:
        return f"未找到合同 {contract_id}。"

    return (
        f"合同编号：{contract_id}\n"
        f"客户：{contract['customer']}\n"
        f"负责人邮箱：{contract['owner_email']}\n"
        f"合同金额：{contract['amount']} 元\n"
        f"付款条款：{contract['payment_terms']}\n"
        f"责任上限：{contract['liability_cap']}\n"
        f"是否自动续约：{contract['auto_renewal']}"
    )


class RiskInput(BaseModel):
    amount: int = Field(description="合同金额，单位为元")
    payment_terms: str = Field(description="付款条款")
    liability_cap: str = Field(description="责任上限条款")
    auto_renewal: bool = Field(description="是否自动续约")


@tool(args_schema=RiskInput)
def evaluate_contract_risk(
    amount: int,
    payment_terms: str,
    liability_cap: str,
    auto_renewal: bool,
) -> str:
    """根据合同金额和关键条款评估风险等级。"""

    # 模拟外部风控服务偶发抖动，方便观察 ToolRetryMiddleware 的价值。
    if random.random() < 0.15:
        raise RuntimeError("临时风控服务超时，请稍后重试")

    risk_points: list[str] = []

    if amount >= 200000:
        risk_points.append("合同金额较高")
    if "90 天" in payment_terms or "90天" in payment_terms:
        risk_points.append("付款周期较长")
    if "无明确" in liability_cap:
        risk_points.append("缺少明确责任上限")
    if auto_renewal:
        risk_points.append("存在自动续约条款")

    if len(risk_points) >= 3:
        level = "high"
    elif len(risk_points) >= 1:
        level = "medium"
    else:
        level = "low"

    return f"风险等级：{level}\n风险点：{'；'.join(risk_points) if risk_points else '未发现明显风险'}"


@tool(args_schema=ContractInput)
def submit_contract_review(contract_id: str) -> str:
    """提交合同审批。高风险操作，通常需要人工审批。"""

    # 真实场景里这里可能会写数据库、发起 OA 流程或调用审批 API。
    return f"合同 {contract_id} 已提交审批流程。"


@before_model
def log_before_model(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """模型调用前打印消息数量，适合调试 Agent 是否陷入过长上下文。"""

    print(f"[before_model] 即将调用模型，当前消息数：{len(state['messages'])}")
    return None


@after_model(can_jump_to=["end"])
def block_forbidden_output(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """模型调用后做一次简单输出检查，必要时提前结束。"""

    last_message = state["messages"][-1]
    content = getattr(last_message, "content", "")

    if isinstance(content, str) and "直接绕过审批" in content:
        return {
            "messages": [AIMessage("该请求涉及审批绕过，已停止处理。")],
            "jump_to": "end",
        }

    print("[after_model] 模型输出已通过基础检查")
    return None


@wrap_model_call
def retry_model_call(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """一个简单的模型调用重试包装器。"""

    max_retries = 2
    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return handler(request)
        except Exception as exc:
            last_error = exc
            if attempt == max_retries:
                raise
            wait_seconds = 1.5 * (attempt + 1)
            print(f"[wrap_model_call] 模型调用失败，{wait_seconds} 秒后重试：{exc}")
            time.sleep(wait_seconds)

    raise RuntimeError(f"模型调用失败：{last_error}")


@dynamic_prompt
def add_runtime_prompt(request: ModelRequest) -> str:
    """根据运行时上下文动态生成系统提示词。"""

    # 如果调用方传了 context，可以在这里读取用户角色、租户、区域等信息。
    reviewer_role = request.runtime.context.get("reviewer_role", "普通审批人")

    return (
        "你是企业合同审批助手。"
        f"当前审批人角色：{reviewer_role}。"
        "请优先检查付款周期、责任上限、自动续约和大额合同风险。"
        "涉及提交审批、修改合同、对外发送信息时，必须谨慎。"
    )


def build_agent(enable_human_review: bool = False):
    """创建带中间件的合同审批 Agent。"""

    model_name = os.getenv("MODEL_NAME", "openai:gpt-4o-mini")

    middleware = [
        # 先处理敏感信息，避免邮箱等内容直接进入后续日志或模型上下文。
        PIIMiddleware("email", strategy="redact", apply_to_input=True, apply_to_tool_results=True),

        # 限制一次运行最多调用模型 6 次，防止 Agent 跑飞。
        ModelCallLimitMiddleware(run_limit=6, exit_behavior="end"),

        # 限制工具调用次数。也可以为某个工具单独配置 tool_name。
        ToolCallLimitMiddleware(run_limit=8, exit_behavior="end"),

        # 工具失败时自动重试，适合外部 API 偶发抖动。
        ToolRetryMiddleware(
            max_retries=2,
            initial_delay=1.0,
            backoff_factor=2.0,
            jitter=True,
        ),

        # 自定义中间件：日志、输出检查、模型重试、动态提示词。
        log_before_model,
        block_forbidden_output,
        retry_model_call,
        add_runtime_prompt,
    ]

    if enable_human_review:
        middleware.append(
            HumanInTheLoopMiddleware(
                interrupt_on={
                    # 提交审批是写操作，这里要求人工批准或拒绝。
                    "submit_contract_review": {
                        "allowed_decisions": ["approve", "reject"],
                        "description": "提交合同审批前需要人工确认",
                    },
                    # 读取摘要和风险评估可以自动执行。
                    "read_contract_summary": False,
                    "evaluate_contract_risk": False,
                }
            )
        )

    return create_agent(
        model=model_name,
        tools=[read_contract_summary, evaluate_contract_risk, submit_contract_review],
        middleware=middleware,
        # Human-in-the-loop 需要 checkpointer 才能暂停并恢复。
        checkpointer=InMemorySaver() if enable_human_review else None,
    )


def run_without_human_review() -> None:
    """普通运行：展示中间件如何约束 Agent。"""

    agent = build_agent(enable_human_review=False)

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "请检查合同 CT-2026-001 的风险，"
                        "说明是否建议提交审批，并给出理由。"
                    ),
                }
            ]
        },
        context={"reviewer_role": "法务复核人"},
    )

    print("\n=== 最终回复 ===")
    print(result["messages"][-1].content)


def run_with_human_review() -> None:
    """带人工审批的运行示意。"""

    agent = build_agent(enable_human_review=True)

    # 同一个 thread_id 用来暂停和恢复同一条执行线程。
    config = {"configurable": {"thread_id": "contract-review-demo-001"}}

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "请检查 CT-2026-001，如果风险较高就提交审批。",
                }
            ]
        },
        config=config,
        context={"reviewer_role": "合同审批主管"},
    )

    print("\n=== 可能出现的中断信息 ===")
    print(result.get("__interrupt__"))

    # 如果真的触发了中断，生产系统里通常会把 result["__interrupt__"] 展示给人工审核页面。
    # 审核人确认后，再用 Command 恢复执行。
    # from langgraph.types import Command
    # approved = agent.invoke(
    #     Command(resume={"decisions": [{"type": "approve"}]}),
    #     config=config,
    # )
    # print(approved["messages"][-1].content)


if __name__ == "__main__":
    run_without_human_review()

    # 如果想测试 HumanInTheLoopMiddleware，可以取消下面这一行注释。
    # run_with_human_review()
```

---

## 这段代码里每个中间件在干什么？

| 中间件 | 做什么 | 为什么有用 |
|---|---|---|
| `PIIMiddleware` | 脱敏邮箱等个人信息 | 避免敏感数据进入模型或日志 |
| `ModelCallLimitMiddleware` | 限制模型调用次数 | 防止 Agent 无限循环 |
| `ToolCallLimitMiddleware` | 限制工具调用次数 | 控制外部 API 成本和风险 |
| `ToolRetryMiddleware` | 工具失败自动重试 | 对抗临时网络抖动 |
| `HumanInTheLoopMiddleware` | 高风险工具执行前暂停 | 让人审关键动作 |
| `before_model` | 模型调用前执行 | 做日志、检查、状态更新 |
| `after_model` | 模型调用后执行 | 校验输出，必要时提前结束 |
| `wrap_model_call` | 包住模型调用 | 可重试、回退、替换模型 |
| `dynamic_prompt` | 动态生成系统提示词 | 按用户角色、租户、场景改提示词 |

如果你只记一件事：

> **中间件处理的是“每次都要做、但不该散落在业务代码里的事”。**

---

## 什么时候不要写中间件？

中间件很好，但别滥用。

下面几种情况，不一定要写中间件：

1. 只是一段一次性业务逻辑
2. 只服务一个工具，不会复用
3. 写进工具函数里更清楚
4. 只是 prompt 文案的小改动
5. 没有跨模型、跨工具、跨 Agent 的需求

如果一个逻辑只在某个工具内部有意义，放工具里就好。

如果一个逻辑要覆盖所有模型调用、所有工具调用、所有 Agent 运行，那就适合中间件。

---

## 常见设计建议

### 1. 安全类中间件靠前

PII、权限、合规检查尽量靠前。

不要等日志打完、模型调完，再说要脱敏。

那就晚了。

### 2. 成本类中间件必须有

生产 Agent 最怕跑飞。

模型调用限制和工具调用限制，建议早加。

哪怕阈值先放宽，也比完全没有强。

### 3. 高风险工具必须人工审批

只要工具会写数据、发消息、执行 SQL、动钱，就不要完全自动化。

Agent 可以起草，可以建议，可以准备参数。

但最后那一下，最好有人看一眼。

### 4. 自定义中间件保持单一职责

一个中间件只做一件事。

不要写一个万能中间件，又脱敏、又限流、又改 prompt、又打日志。

后面排查起来会很痛。

### 5. 先用预置，再写自定义

官方已经给了很多能力。

先用它们，把业务跑通。

只有当规则真的特殊，再写自己的 hook。

---

## 最后总结

LangChain 中间件解决的不是“让 Agent 更聪明”。

它解决的是另一个更工程化的问题：

> **当 Agent 开始真正干活时，我们怎么让它可控、可审、可恢复。**

没有中间件的 Agent，很容易像一个热情但没边界的新人：

- 工具能调就一直调
- 出错了就直接失败
- 敏感信息随手带出去
- 高风险动作也敢自动执行
- 长对话越堆越满

中间件的价值，就是给它加上工作规矩。

我会把它记成三句话：

> **工具决定 Agent 能做什么。**

> **记忆决定 Agent 能记住什么。**

> **中间件决定 Agent 做事时有没有边界。**

到了生产环境，第三句话往往最要命。

因为真正让系统稳定的，不只是能力，而是约束。
