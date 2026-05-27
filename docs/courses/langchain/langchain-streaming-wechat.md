---
title: "LangChain 第四讲：流式传输，别让用户盯着空白页等模型"
source: "参考 LangChain 官方 JavaScript Streaming / Event Streaming 文档，并结合 LangChain v1 Python 中文文档整理"
author: "GitHub Copilot"
date: 2026-05-09
created: 2026-05-09
tags:
  - LangChain
  - Streaming
  - Agent
  - Python
  - 微信公众号
summary: "一篇面向公众号分享的 LangChain 第四讲，重点讲清楚 updates、messages、custom 三种流模式，以及如何用 Python 写一个可运行的业务型流式 Agent。"
---

第三讲聊完工具和短时记忆之后，第四讲要补上的，是 Agent 的另一个关键体验层：**流式传输**。

如果说普通调用像是在餐厅等菜：你只知道自己点了什么，但不知道厨房在忙什么。

那流式传输更像开放式厨房：

- 模型开始想了，你能看到
- 工具开始查了，你能看到
- 中间状态变了，你能看到
- 最终答案还没回来，用户也不会觉得系统卡死了

LangChain 官方文档里把这件事讲得很清楚：Streaming 不是单纯“一个字一个字吐出来”，它更像是把 Agent 运行过程拆成可观察的实时信号。

这篇只讲一件事：**怎么把 LangChain Agent 的运行过程实时展示出来。**

---

## 先说结论：流式传输解决的不是炫技，而是等待感

大模型应用最容易让人焦虑的地方，不是慢。

而是**不知道它是不是还活着**。

尤其是 Agent 场景，它不只是生成文本，还可能经历：

1. 模型判断要不要调用工具
2. 工具开始执行
3. 工具返回结果
4. 模型读工具结果
5. 模型组织最终答案

如果你只用普通 `invoke`，用户看到的就是一段漫长沉默。

如果你用 streaming，用户看到的是：

- “正在识别问题类型”
- “正在查询工单系统”
- “已读取退款记录”
- “正在生成处理建议”

这就是体验上的差别。

> **流式传输不是让模型更快，而是让用户更早知道系统正在认真工作。**

---

## 官网里最重要的三个模式

LangChain 官方 JavaScript 文档里讲的是 `streamMode`，Python 里对应的是 `stream_mode`。

别被名字绕住，核心就三类：

| 模式 | Python 写法 | 适合看什么 | 大白话解释 |
|---|---|---|---|
| 代理进度 | `stream_mode="updates"` | Agent 每一步状态 | 看 Agent 走到哪一步了 |
| 模型 token | `stream_mode="messages"` | LLM 逐段输出 | 看模型正在吐哪些字、哪些工具调用片段 |
| 自定义更新 | `stream_mode="custom"` | 工具内部自己发的状态 | 工具边干活边汇报进度 |

官方 JS 文档还提到 Event Streaming，也就是 `streamEvents(..., version="v3")` 这种更偏前端和生产 UI 的做法。它会把 messages、tool calls、state、final output 做成 typed projections。

但如果你刚开始学，我建议先掌握这三个基础模式：

```text
updates  看流程
messages 看文本和工具调用 token
custom   看你自己定义的业务进度
```

这三个吃透了，再上 Event Streaming 会顺很多。

![LangChain 流式传输三种模式](langchain-lecture-assets/langchain-streaming-modes.png)

这张图对应官方文档里的三个基础流模式：`updates` 看 Agent 步骤，`messages` 看模型输出片段，`custom` 看工具或节点主动发出的业务进度。

---

## 第一种：updates，看 Agent 当前走到哪一步

`updates` 最适合展示“流程进度”。

比如一个售后助手收到用户问题后，可能会先调用查询工具，再生成回复。

你不一定关心每一个 token，但你很关心它有没有真的去查系统。

这时就用：

```python
for chunk in agent.stream(input_payload, stream_mode="updates"):
    ...
```

它通常会告诉你类似这样的节点变化：

```text
model -> tools -> model
```

翻译成人话就是：

```text
模型先判断要查工具
工具查完返回结果
模型再基于结果回答
```

这对于后台日志、运维排查、前端进度条都很有用。

---

## 第二种：messages，看模型逐段输出

`messages` 更像我们平时理解的“打字机效果”。

但它不只是文本。

官方文档里强调，`messages` 会流式输出来自图里任意 LLM 节点的 token 和 metadata。也就是说，它也可能包含：

- 普通文本块
- 工具调用片段
- reasoning / thinking 内容块（如果模型和配置支持）
- 当前来自哪个 LangGraph 节点的元信息

Python 里常见写法是：

```python
for token, metadata in agent.stream(input_payload, stream_mode="messages"):
    print(metadata["langgraph_node"])
    print(token.content_blocks)
```

这里有个小提醒：

> 不要默认每个 chunk 都是自然语言文本。它也可能是工具调用参数的一小段。

所以生产里最好先判断 `content_blocks` 的类型，再决定怎么展示。

---

## 第三种：custom，让工具自己汇报进度

这是我觉得最容易被低估的一种。

`custom` 不是模型吐出来的内容，而是你在工具内部主动写出来的业务进度。

比如：

- “正在读取工单”
- “正在检查退款规则”
- “正在匹配历史处理记录”
- “已生成建议草稿”

在 Python 里，工具内部可以用：

```python
from langgraph.config import get_stream_writer

writer = get_stream_writer()
writer("正在读取工单")
```

这非常适合真实系统。

因为很多时候，用户不关心模型每个 token。他更关心：

> **系统到底查到哪一步了。**

---

## 多模式一起开：流程和进度都要

官方文档支持一次传多个模式。

Python 中可以这样写：

```python
for mode, chunk in agent.stream(
    input_payload,
    stream_mode=["updates", "custom"],
):
    print(mode, chunk)
```

这时返回的是 `(mode, chunk)`。

大白话就是：

- `updates` 告诉你 Agent 走到哪个节点
- `custom` 告诉你业务工具正在干什么

如果你做的是管理后台、客服工作台、内部运维助手，我会更推荐这种组合。

---

## 和官网内容对齐的一张速查表

| 官方 JS 文档 | Python 对应理解 | 用法重点 |
|---|---|---|
| `streamMode: "updates"` | `stream_mode="updates"` | 每个 Agent 步骤后的状态更新 |
| `streamMode: "messages"` | `stream_mode="messages"` | LLM token 与 metadata |
| `streamMode: "custom"` | `stream_mode="custom"` | 工具或节点主动发出的业务事件 |
| `streamMode: ["updates", "messages"]` | `stream_mode=["updates", "messages"]` | 同时看多种事件 |
| `streamEvents(..., version="v3")` | 更偏事件流和前端投影 | 适合复杂 UI 和生产系统 |
| `contentBlocks` | `content_blocks` | 标准化内容块，可能是 text、tool_call、reasoning 等 |

这张表够用了。

先别急着把所有流式能力都塞进项目。第一步只要回答一个问题：

> **你的用户最需要看到什么进度？**

---

## 一个自己写的业务示例：售后退款助手

下面这个例子不照搬官网的天气查询。

我们写一个更接近企业内部系统的场景：客服同学输入退款工单号，Agent 会：

1. 查询工单基本信息
2. 检查退款规则
3. 给出处理建议
4. 在工具内部流式输出业务进度

我们会同时演示：

- `updates`
- `messages`
- `custom`
- 多模式组合

---

## 完整 Python 代码

> 运行前建议安装：`langchain`、`langchain-openai`、`langgraph`、`python-dotenv`。项目根目录已有 `.env` 时，把 `OPENAI_API_KEY` 写进去即可。

```python
"""
LangChain 流式传输完整示例：售后退款助手

这个脚本演示四件事：
1. stream_mode="updates"：查看 Agent 走到了 model 还是 tools 节点
2. stream_mode="messages"：查看模型逐段输出的 token / content_blocks
3. stream_mode="custom"：查看工具内部主动发出的业务进度
4. stream_mode=["updates", "custom"]：同时观察流程和业务进度

注意：
- 示例中的数据是内存里的假数据，方便你直接理解逻辑。
- 真接入业务时，把 REFUND_TICKETS / REFUND_POLICIES 换成数据库或 HTTP API 即可。
"""

from __future__ import annotations

import os
from typing import Literal

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langgraph.config import get_stream_writer
from pydantic import BaseModel, Field


# 读取 .env 中的 OPENAI_API_KEY、MODEL_NAME 等配置。
load_dotenv()


# 这里用内存数据模拟真实工单系统。
REFUND_TICKETS = {
    "RF-1001": {
        "customer": "华东区 A 公司",
        "amount": 12800,
        "reason": "重复扣款",
        "days_since_payment": 3,
        "risk_level": "low",
    },
    "RF-1002": {
        "customer": "北京 B 公司",
        "amount": 88000,
        "reason": "合同终止争议",
        "days_since_payment": 46,
        "risk_level": "high",
    },
}

REFUND_POLICIES = {
    "low": "低风险退款：金额小于 20000 且付款 7 天内，可由客服主管审批。",
    "medium": "中风险退款：需要财务复核，并保留合同与付款凭证。",
    "high": "高风险退款：必须由法务、财务和业务负责人共同确认。",
}


class RefundTicketInput(BaseModel):
    """查询退款工单时需要的输入。"""

    ticket_id: str = Field(description="退款工单号，例如 RF-1001")
    include_policy: bool = Field(
        default=True,
        description="是否同时返回对应退款规则",
    )


@tool(args_schema=RefundTicketInput)
def lookup_refund_ticket(ticket_id: str, include_policy: bool = True) -> str:
    """查询退款工单，并根据风险等级返回处理规则。"""

    # get_stream_writer 只能在 LangGraph / Agent 执行上下文里使用。
    # 它发出的内容会出现在 stream_mode="custom" 的输出里。
    writer = get_stream_writer()

    writer(f"开始读取退款工单：{ticket_id}")
    ticket = REFUND_TICKETS.get(ticket_id)

    if ticket is None:
        writer("没有找到对应工单，准备返回空结果")
        return f"未找到退款工单 {ticket_id}。请确认工单号是否正确。"

    writer("已读取工单基础信息")

    result = [
        f"工单号：{ticket_id}",
        f"客户：{ticket['customer']}",
        f"金额：{ticket['amount']} 元",
        f"原因：{ticket['reason']}",
        f"付款距今：{ticket['days_since_payment']} 天",
        f"风险等级：{ticket['risk_level']}",
    ]

    if include_policy:
        writer("正在匹配退款审批规则")
        policy = REFUND_POLICIES.get(ticket["risk_level"], "未找到匹配规则")
        result.append(f"审批规则：{policy}")
        writer("已匹配退款审批规则")

    return "\n".join(result)


class SuggestionInput(BaseModel):
    """生成客服建议时需要的输入。"""

    risk_level: Literal["low", "medium", "high"] = Field(description="退款风险等级")
    amount: int = Field(description="退款金额，单位为元")


@tool(args_schema=SuggestionInput)
def build_refund_reply_suggestion(risk_level: str, amount: int) -> str:
    """根据退款风险和金额生成客服处理建议。"""

    writer = get_stream_writer()
    writer("开始生成客服处理建议")

    if risk_level == "high" or amount >= 50000:
        writer("识别为高风险或大额退款，需要升级处理")
        return (
            "建议回复：该退款涉及较高金额或争议风险，建议先收集合同、付款记录、"
            "沟通截图，并升级给财务、法务和业务负责人共同确认。"
        )

    if risk_level == "medium":
        writer("识别为中风险退款，需要财务复核")
        return "建议回复：该退款需要财务复核，请客户补充付款凭证和退款原因说明。"

    writer("识别为低风险退款，可走快速审批")
    return "建议回复：该退款符合快速审批条件，可提交客服主管审批。"


def build_agent():
    """创建一个带工具的退款处理 Agent。"""

    model_name = os.getenv("MODEL_NAME", "openai:gpt-4o-mini")

    return create_agent(
        model=model_name,
        tools=[lookup_refund_ticket, build_refund_reply_suggestion],
        system_prompt=(
            "你是一个企业售后退款助手。"
            "回答前必须先查询退款工单；"
            "如果涉及高风险或大额退款，要提醒升级给财务、法务和业务负责人。"
            "回复要简洁、稳妥、可执行。"
        ),
    )


def build_input(ticket_id: str) -> dict:
    """构造 Agent 输入。"""

    return {
        "messages": [
            {
                "role": "user",
                "content": f"请帮我处理退款工单 {ticket_id}，给出客服回复建议。",
            }
        ]
    }


def demo_updates(agent, ticket_id: str) -> None:
    """演示 updates：看 Agent 运行步骤。"""

    print("\n=== stream_mode='updates'：查看 Agent 步骤 ===")
    for chunk in agent.stream(build_input(ticket_id), stream_mode="updates"):
        # chunk 通常类似：{"model": {...}} 或 {"tools": {...}}
        for step_name, step_data in chunk.items():
            print(f"\n[步骤] {step_name}")
            last_message = step_data["messages"][-1]
            print(last_message.content_blocks)


def demo_messages(agent, ticket_id: str) -> None:
    """演示 messages：看模型 token 和工具调用片段。"""

    print("\n=== stream_mode='messages'：查看模型输出片段 ===")
    for token, metadata in agent.stream(build_input(ticket_id), stream_mode="messages"):
        node_name = metadata.get("langgraph_node")
        blocks = getattr(token, "content_blocks", [])

        if not blocks:
            continue

        print(f"\n[节点] {node_name}")
        for block in blocks:
            block_type = block.get("type")

            if block_type == "text":
                print(block.get("text", ""), end="", flush=True)
            else:
                # 工具调用片段、reasoning 片段等会走这里。
                print(f"\n[非文本内容块] {block}")

    print()


def demo_custom(agent, ticket_id: str) -> None:
    """演示 custom：看工具内部主动发出的业务进度。"""

    print("\n=== stream_mode='custom'：查看业务进度 ===")
    for chunk in agent.stream(build_input(ticket_id), stream_mode="custom"):
        print(f"[业务进度] {chunk}")


def demo_multiple_modes(agent, ticket_id: str) -> None:
    """演示多模式：同时查看 Agent 步骤和业务进度。"""

    print("\n=== stream_mode=['updates', 'custom']：同时查看流程和业务进度 ===")
    for mode, chunk in agent.stream(
        build_input(ticket_id),
        stream_mode=["updates", "custom"],
    ):
        if mode == "custom":
            print(f"[custom] {chunk}")
        elif mode == "updates":
            print(f"[updates] {list(chunk.keys())}")


if __name__ == "__main__":
    refund_agent = build_agent()

    # 可以换成 RF-1001 看低风险退款，也可以用 RF-1002 看高风险退款。
    target_ticket_id = "RF-1002"

    demo_updates(refund_agent, target_ticket_id)
    demo_messages(refund_agent, target_ticket_id)
    demo_custom(refund_agent, target_ticket_id)
    demo_multiple_modes(refund_agent, target_ticket_id)
```

---

## 这段代码最值得看的几个点

第一，`updates` 看的是 Agent 运行节点。

它适合回答：

> Agent 到底有没有调用工具？卡在哪一步？

第二，`messages` 看的是模型输出片段。

它适合回答：

> 最终答案能不能一边生成一边展示？工具调用参数是不是也在流里出现？

第三，`custom` 看的是工具主动发出的业务事件。

它适合回答：

> 工具内部执行到哪了？数据库查完了吗？审批规则匹配了吗？

这三个问题，其实就是大模型应用从 demo 走到产品时最常见的三个问题。

---

## 什么时候该用哪种模式？

| 场景 | 推荐模式 | 原因 |
|---|---|---|
| 聊天窗口逐字展示 | `messages` | 用户需要看到文字逐步出现 |
| 后台任务进度条 | `updates` + `custom` | 既要流程节点，也要业务进度 |
| 调试 Agent 工具调用 | `updates` | 看模型、工具、模型的往返过程 |
| 展示工具内部进度 | `custom` | 进度来自工具，不来自模型 |
| 复杂前端应用 | Event Streaming | 更适合 typed projections 和 UI 状态管理 |

如果你只做一个简单聊天框，`messages` 就够。

如果你做企业内部助手，我更建议从 `updates + custom` 开始。

---

## 常见坑：别把所有流都当文本处理

很多同学第一次接 streaming，最容易写出这样的代码：

```python
for token, metadata in agent.stream(payload, stream_mode="messages"):
    print(token.content)
```

这能跑，但不够稳。

因为 Agent 场景里，流出来的内容不一定都是普通文本，可能还有工具调用 chunk。

更稳的做法是看 `content_blocks`：

- `type == "text"`：展示给用户
- `type == "tool_call_chunk"`：可以展示为“正在准备调用工具”
- `type == "reasoning"`：如果产品允许，再考虑展示
- 其他类型：先记录日志，不要直接拼到正文里

> **流式输出不是字符串拼接问题，而是事件分流问题。**

这句话很重要。

---

## 最后总结

LangChain 的流式传输，真正有价值的地方不是“让字一个个冒出来”。

它让 Agent 的运行过程变得可见。

如果用户只是等一个答案，`invoke` 也许够用。

但只要进入真实业务场景，用户就会在意：

- 系统有没有开始处理
- 有没有查真实数据
- 查到了哪一步
- 是模型在生成，还是工具在执行
- 中间有没有触发高风险动作

这时 streaming 就不再是体验优化，而是产品基本功。

我个人会这样记：

> **messages 管文字，updates 管步骤，custom 管业务进度。**

三者配好，一个 Agent 才不再像黑盒。

它开始有了工作时的“呼吸感”。
