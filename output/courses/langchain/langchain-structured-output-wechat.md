---
title: "LangChain 第五讲：结构化输出，别再从一大段话里抠 JSON 了"
source: "参考 LangChain 官方 JavaScript Structured Output / Models 文档，并结合 LangChain v1 Python 中文文档整理"
author: "GitHub Copilot"
date: 2026-05-09
created: 2026-05-09
tags:
  - LangChain
  - Structured Output
  - Agent
  - Python
  - 微信公众号
summary: "一篇面向公众号分享的 LangChain 第五讲，重点讲清楚 response_format、ProviderStrategy、ToolStrategy、schema 校验和错误重试，并给出完整 Python 示例。"
---

第四讲聊的是流式传输，也就是怎么让 Agent 的过程被用户看见。

第五讲换一个更偏工程落地的问题：**模型输出怎么稳定进入系统**。

很多大模型应用，一开始都喜欢这么干：

> 让模型“请用 JSON 返回”。

然后你会得到各种惊喜：

- 前面多一句“当然可以”
- 后面补一句“希望对你有帮助”
- JSON 少个逗号
- 字段名突然换成中文
- 数字变成字符串
- 数组里混进解释性文本

这不是模型坏。

是你把“应用需要的数据结构”，交给了“自然语言约定”。

LangChain 的结构化输出，就是为了解决这个问题。

它的核心价值很简单：

> **别再从一大段自然语言里抠字段，让 Agent 直接返回可验证的数据对象。**

---

## 结构化输出到底是什么？

大白话讲，结构化输出就是：

> 你先告诉模型“我要什么格式”，模型最后必须尽量按这个格式交卷。

在 LangChain Agent 里，这个格式会通过 `response_format` 传进去。

Python 文档里对应的是：

```python
create_agent(
    ...,
    response_format=YourSchema,
)
```

最终结果会放在：

```python
result["structured_response"]
```

JavaScript 官方文档里叫：

```ts
result.structuredResponse
```

名字不一样，意思一样。

它不是“让模型口头承诺返回 JSON”，而是让 LangChain 接管：

- schema 定义
- 输出捕获
- 结果校验
- 错误反馈
- 必要时重试

这就比纯 prompt 稳得多。

---

## 为什么这件事重要？

如果只是聊天，模型返回自然语言没问题。

但一旦进入业务系统，后端通常需要的是字段，而不是散文。

比如客服质检系统需要：

```json
{
  "sentiment": "negative",
  "risk_level": "high",
  "need_human_review": true
}
```

合同审核系统需要：

```json
{
  "risk_items": [...],
  "missing_clauses": [...],
  "overall_score": 72
}
```

销售线索系统需要：

```json
{
  "company_name": "...",
  "budget_level": "medium",
  "next_action": "schedule_demo"
}
```

这些都不能靠“你帮我返回 JSON”糊弄过去。

因为下游系统会直接消费这些字段。

字段错了，不只是回答不好看，而是流程会走错。

---

## 官网里最关键的三件事

LangChain 官方文档把结构化输出拆成几层：

| 关键词 | 大白话解释 | 适合记什么 |
|---|---|---|
| `response_format` | 告诉 Agent 最终要什么结构 | 入口参数 |
| `ProviderStrategy` | 使用模型提供商原生结构化输出 | 优先选，通常更稳 |
| `ToolStrategy` | 用工具调用模拟结构化输出 | 兼容面更广 |
| `structured_response` | 最终拿到的结构化结果 | Python 返回字段 |
| schema validation | 按字段类型和约束校验 | 防止脏数据进系统 |
| error handling | 出错后给模型反馈并重试 | 让模型自己修正格式 |

一句话总结：

> **ProviderStrategy 靠模型 API 原生保证格式，ToolStrategy 靠工具调用和校验机制保证格式。**

---

## ProviderStrategy 和 ToolStrategy 怎么选？

官方文档里有一个很重要的判断：

当你直接传 schema，LangChain 会根据模型能力自动选择策略。

如果模型支持原生结构化输出，就用 ProviderStrategy。

如果不支持，就退回 ToolStrategy。

大白话就是：

- 模型原生会填表，就让它原生填
- 模型原生不会填表，就让它通过工具调用来填

| 策略 | 优点 | 注意点 |
|---|---|---|
| ProviderStrategy | 通常更可靠，由模型提供商强约束 | 依赖模型支持 |
| ToolStrategy | 兼容大多数支持工具调用的模型 | 可能出现工具调用错误，需要重试 |
| 直接传 schema | 写法最省心 | 需要理解背后自动选择逻辑 |

我的建议很简单：

> 新项目先直接传 Pydantic schema；如果你明确要强制工具调用，再显式用 `ToolStrategy`。

![LangChain 结构化输出策略选择](langchain-lecture-assets/langchain-structured-output-strategy.png)

这张图和官方文档的逻辑保持一致：`response_format` 先接住 schema，LangChain 再根据模型能力选择 ProviderStrategy 或 ToolStrategy，最终把校验后的结果放到 `structured_response` 里。

---

## schema 不是类型体操，是业务边界

很多人写结构化输出时，只把 schema 当类型定义。

但在业务里，schema 其实是在定义边界。

比如“风险等级”不是随便一个字符串，而应该限制成：

```python
Literal["low", "medium", "high"]
```

“评分”不应该是任意数字，而应该限制在：

```python
Field(ge=0, le=100)
```

“是否需要人工复核”不应该让模型写成“建议需要”，而应该是：

```python
bool
```

这不是洁癖。

这是在告诉系统：

> **哪些东西能流入后续流程，哪些东西必须挡在门外。**

---

## 一个自己写的业务示例：客户投诉分流

这次不用官网里的联系方式提取，也不用产品评论分析。

我们写一个更常见的企业场景：**客户投诉分流**。

用户输入一段投诉内容，Agent 要返回一个结构化结果：

- 客户情绪
- 问题类别
- 风险等级
- 是否需要人工介入
- 建议转交团队
- 客服回复要点

这类结果非常适合直接进入 CRM、工单系统或客服质检系统。

---

## 完整 Python 代码

> 运行前建议安装：`langchain`、`langchain-openai`、`pydantic`、`python-dotenv`。项目根目录已有 `.env` 时，把 `OPENAI_API_KEY` 写进去即可。

```python
"""
LangChain 结构化输出完整示例：客户投诉分流助手

这个脚本演示：
1. 用 Pydantic 定义业务 schema
2. 直接把 schema 传给 create_agent 的 response_format
3. 显式使用 ToolStrategy，并自定义错误提示
4. 从 result["structured_response"] 里拿到可直接入库的数据

注意：
- 示例重点是结构化输出，不是客服话术本身。
- 真接入业务时，可以把 structured_response 写入 CRM、工单系统或质检系统。
"""

from __future__ import annotations

import os
from typing import Literal

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from pydantic import BaseModel, Field


load_dotenv()


class ComplaintRoutingResult(BaseModel):
    """客户投诉分流结果。"""

    customer_emotion: Literal["calm", "anxious", "angry"] = Field(
        description="客户当前情绪：calm=平静，anxious=焦虑，angry=愤怒"
    )
    issue_category: Literal[
        "refund",
        "delivery",
        "product_quality",
        "contract",
        "technical_support",
        "other",
    ] = Field(description="投诉问题类别")
    risk_level: Literal["low", "medium", "high"] = Field(
        description="投诉风险等级，涉及金额大、公开投诉、合同争议时通常更高"
    )
    urgency_score: int = Field(
        ge=0,
        le=100,
        description="紧急程度评分，0 表示完全不紧急，100 表示必须立刻处理",
    )
    need_human_review: bool = Field(
        description="是否需要人工介入复核。高风险、强情绪、合同争议通常需要"
    )
    suggested_team: Literal[
        "customer_success",
        "finance",
        "legal",
        "logistics",
        "engineering",
        "quality_team",
    ] = Field(description="建议转交的团队")
    reply_key_points: list[str] = Field(
        min_length=2,
        max_length=5,
        description="客服回复时必须覆盖的关键点，每条用简短中文表达",
    )
    short_summary: str = Field(
        max_length=80,
        description="80 字以内概括投诉内容，方便写入工单标题或摘要",
    )


def build_auto_strategy_agent():
    """直接传 Pydantic schema，让 LangChain 自动选择 ProviderStrategy 或 ToolStrategy。"""

    model_name = os.getenv("MODEL_NAME", "openai:gpt-4o-mini")

    return create_agent(
        model=model_name,
        tools=[],
        response_format=ComplaintRoutingResult,
        system_prompt=(
            "你是企业客服投诉分流助手。"
            "你需要把客户投诉内容整理成结构化字段。"
            "不要夸大风险，但遇到退款、合同、公开投诉、强烈情绪时要谨慎。"
        ),
    )


def build_tool_strategy_agent():
    """显式使用 ToolStrategy，适合想控制错误处理文案的场景。"""

    model_name = os.getenv("MODEL_NAME", "openai:gpt-4o-mini")

    return create_agent(
        model=model_name,
        tools=[],
        response_format=ToolStrategy(
            schema=ComplaintRoutingResult,
            # 当模型返回的结构不符合 schema 时，LangChain 会把这段话作为反馈，要求模型修正。
            handle_errors=(
                "请严格按 schema 返回：urgency_score 必须是 0-100 的整数，"
                "risk_level 只能是 low、medium、high，reply_key_points 必须是 2-5 条。"
            ),
            # 这个内容会出现在结构化输出工具消息里，方便日志阅读。
            tool_message_content="投诉分流结果已结构化生成。",
        ),
        system_prompt=(
            "你是企业客服投诉分流助手。"
            "输出必须稳定、克制、适合进入工单系统。"
        ),
    )


def analyze_complaint(agent, complaint_text: str) -> ComplaintRoutingResult:
    """调用 Agent，并返回结构化结果。"""

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "请分析下面这段客户投诉，并输出结构化分流结果：\n\n"
                        f"{complaint_text}"
                    ),
                }
            ]
        }
    )

    # LangChain 会把结构化结果放在 structured_response 中。
    structured = result["structured_response"]

    # 如果 response_format 使用的是 Pydantic 模型，这里通常就是 ComplaintRoutingResult 实例。
    return structured


def print_routing_result(result: ComplaintRoutingResult) -> None:
    """把结构化结果打印出来，方便人工查看。"""

    print("\n=== 客户投诉分流结果 ===")
    print(f"情绪：{result.customer_emotion}")
    print(f"问题类别：{result.issue_category}")
    print(f"风险等级：{result.risk_level}")
    print(f"紧急评分：{result.urgency_score}")
    print(f"是否需要人工复核：{result.need_human_review}")
    print(f"建议转交团队：{result.suggested_team}")
    print(f"摘要：{result.short_summary}")
    print("回复要点：")
    for index, point in enumerate(result.reply_key_points, start=1):
        print(f"  {index}. {point}")


def to_ticket_payload(result: ComplaintRoutingResult) -> dict:
    """把 Pydantic 对象转成可写入工单系统的 dict。"""

    return {
        "title": result.short_summary,
        "category": result.issue_category,
        "risk_level": result.risk_level,
        "urgency_score": result.urgency_score,
        "need_human_review": result.need_human_review,
        "assigned_team": result.suggested_team,
        "reply_key_points": result.reply_key_points,
        "customer_emotion": result.customer_emotion,
    }


if __name__ == "__main__":
    complaint = (
        "我们公司上周已经申请退款，到现在没有任何进展。"
        "客户成功说让等财务，财务又说合同条款要确认。"
        "这笔钱金额不小，如果今天还没人处理，我们会把情况发到行业群里。"
    )

    print("\n--- 自动策略：让 LangChain 根据模型能力选择 ProviderStrategy 或 ToolStrategy ---")
    auto_agent = build_auto_strategy_agent()
    auto_result = analyze_complaint(auto_agent, complaint)
    print_routing_result(auto_result)
    print("可入库 payload：")
    print(to_ticket_payload(auto_result))

    print("\n--- 显式 ToolStrategy：自定义错误处理和工具消息 ---")
    tool_agent = build_tool_strategy_agent()
    tool_result = analyze_complaint(tool_agent, complaint)
    print_routing_result(tool_result)
```

---

## 这段代码在做什么？

第一，`ComplaintRoutingResult` 是业务 schema。

它不是给人看的作文要求，而是给系统消费的数据合同。

第二，`response_format=ComplaintRoutingResult` 是最省心的写法。

LangChain 会根据模型能力自动选择合适策略。

第三，`ToolStrategy(...)` 适合你想更细控制错误处理的时候。

比如你希望模型输出错了以后，收到更明确的重试提示。

第四，最终结果不是从文本里解析出来的，而是从：

```python
result["structured_response"]
```

直接拿。

这就是结构化输出最舒服的地方。

---

## 字段设计的几个实用建议

### 1. 能枚举就不要自由文本

不要这样：

```python
risk_level: str
```

更推荐：

```python
risk_level: Literal["low", "medium", "high"]
```

因为自由文本会出现：

- “较高”
- “严重”
- “偏高”
- “high risk”

系统处理起来就麻烦了。

### 2. 分数一定要限制范围

不要只写：

```python
score: int
```

要写：

```python
score: int = Field(ge=0, le=100)
```

否则模型可能给你一个 120。

### 3. 给字段写清楚 description

description 不是装饰。

它会影响模型怎么填字段。

比如：

```python
need_human_review: bool = Field(
    description="是否需要人工介入复核。高风险、强情绪、合同争议通常需要"
)
```

这比只写一个布尔值强很多。

### 4. 输出结构不要一次设计太大

很多人一上来就写 40 个字段。

结果模型不是漏字段，就是字段质量不稳定。

我的建议是：

- 第一版控制在 5-10 个关键字段
- 跑真实样本
- 看坏例子
- 再逐步加字段

结构化输出不是字段越多越专业。

字段越多，校验和稳定性成本也越高。

---

## 错误处理为什么重要？

官方文档里提到两类典型错误：

1. 模型一次返回多个结构化输出
2. 输出字段不符合 schema 校验

这两个在业务里都很常见。

比如你只想要一个投诉分流结果，模型却同时返回“投诉结果”和“合同风险结果”。

或者你要求 `urgency_score` 在 0-100，它给了 120。

LangChain 的价值在于：

> 它不是默默吞掉错误，而是把错误反馈给模型，让模型按 schema 修正。

这比你自己写一堆 JSON 修复逻辑要稳得多。

---

## 和 prompt-only JSON 的差别

| 做法 | 优点 | 问题 |
|---|---|---|
| Prompt 里写“请返回 JSON” | 快，容易上手 | 格式不稳定，校验靠自己 |
| 手写正则解析 | 看似可控 | 边界情况很多，很脆 |
| `json.loads` + try/except | 比正则好 | 只能校验 JSON，不懂业务字段 |
| LangChain 结构化输出 | schema、校验、错误反馈一体化 | 要先设计好 schema |

如果只是 demo，prompt-only JSON 也许够。

但只要结构化结果要进入数据库、工作流、审批系统，就建议别偷懒。

---

## 最后总结

结构化输出的核心，不是“让模型返回 JSON”。

它是在告诉模型和系统：

> **这次回答不是一段话，而是一份可以被程序接住的数据。**

这件事一旦想清楚，很多设计都会变得更自然：

- schema 是业务边界
- 字段描述是模型指令
- 枚举是流程约束
- 校验是质量门槛
- 错误重试是稳定性保障

我的建议是：

> **凡是要进入系统的模型输出，都尽量结构化；凡是只给人看的解释，再交给自然语言。**

不要让后端从一段漂亮话里抠字段。

那不是工程，那是考古。
