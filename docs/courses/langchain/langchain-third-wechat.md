---
title: "LangChain 第三讲：工具 + 短时记忆，Agent 才算真的开始干活"
source: "以 LangChain 英文官网为主，结合中文文档对照整理：tools / short-term-memory / agents / middleware / persistence"
author: "GitHub Copilot"
date: 2026-04-30
created: 2026-04-30
tags:
  - LangChain
  - Agent
  - Tools
  - 短时记忆
  - Python
  - 微信公众号
summary: "一篇面向公众号分享的 LangChain 第三讲，重点讲清楚 Tools 和 Short-term Memory 在官方 v1 体系里分别负责什么、如何配合、为什么它们决定了 Agent 能不能进入真实工作流，并给出一组可运行、面向研发协作场景的原创 Python 示例。"
---

前两讲如果你已经把 LangChain 看成“让模型更会说话”的框架，那第三讲要补上的，是更关键的一层：

> **模型会不会干活，不取决于它会不会聊天，而取决于它能不能调用工具，以及能不能在一个线程里记住刚刚发生了什么。**

这也是为什么这次我不打算泛泛聊“Agent 很强”，而是直接盯住官方文档里最关键的两页：

- `Tools`
- `Short-term memory`

再往外补一圈英文官网的 `Agents`、`Middleware` 和 `Persistence`，你会发现 LangChain v1 其实已经把这件事讲得很清楚了：

- **Tools** 解决的是“Agent 能做什么”
- **Short-term memory** 解决的是“Agent 在这一轮工作线程里记得住什么”
- **Middleware** 解决的是“你如何控制它什么时候忘、什么时候裁剪、什么时候总结”
- **Persistence / Checkpointer** 解决的是“线程状态怎么存下来，怎么恢复”

如果只用模型、不接工具，那它更像顾问。
如果接了工具，但没有线程级短时记忆，那它像一个每轮都会“断片”的实习生。

真正能进入工作流的 Agent，必须两样都有。

---

## 为什么第三讲要把焦点放在这两个词上？

如果你最近看 Agent 文章看得有点多，可能会有一种感觉：

- 大家都在说 Agent
- 大家也都在说工作流
- 但真正落到代码层时，很多内容还是停留在“模型会调函数”

问题就在这里。

真正决定一个 Agent 能不能进入业务现场的，往往不是“模型够不够大”，而是下面两件事有没有打通：

1. **它能不能碰到真实系统能力**
2. **它能不能在当前线程里保留连续上下文**

前者对应 `Tools`，后者对应 `Short-term memory`。

如果只讲 Tool，不讲线程记忆，你会得到一个“每轮都像第一次接单”的 Agent。

如果只讲记忆，不讲 Tool，你会得到一个“记性不错、但基本不动手”的 Agent。

所以第三讲之所以重要，不是因为它终于开始讲 API 了，而是因为它开始解释：

> **Agent 从聊天助手走向工作助手，底层到底是靠什么拐过去的。**

---

## 如果你很忙，先看这 6 句话

第一，**Tool 不是“给模型多绑几个函数”这么简单**，它本质上是在给 Agent 接入真实系统能力。

第二，**短时记忆不是长期知识库**，它更像当前会话线程的工作上下文。

第三，LangChain 官方文档现在把短时记忆明确放进了 **agent state** 里，而不是一个独立的“记忆插件”。

第四，线程级记忆依赖 **checkpointer**，没有 `thread_id`，就谈不上恢复上下文。

第五，真正实用的工作流，不是“查天气”这种演示，而是像：

- 查发布窗口
- 读值班信息
- 记录故障上下文
- 生成升级通告
- 在长对话里保留关键状态

第六，**中文文档适合对照阅读，但英文官网要优先**。因为在 v1 体系里，像 `state_schema`、`ToolRuntime`、`SummarizationMiddleware` 这些能力，英文官网的信息更完整，也更新得更快。

先看一个最小可用示例，感受一下“工具”到底是什么意思：

```python
from langchain.tools import tool

CHANGE_REQUESTS = [
    {"id": "CR-1024", "service": "payment-api", "status": "approved", "window": "2026-05-01 20:00-21:00"},
    {"id": "CR-1038", "service": "order-api", "status": "pending", "window": "2026-05-01 21:00-22:00"},
    {"id": "CR-1042", "service": "payment-api", "status": "scheduled", "window": "2026-05-02 19:00-20:00"},
]

@tool
def search_change_requests(service: str, limit: int = 5) -> str:
    """Search approved or scheduled change requests for a service."""
    matched = [
        item for item in CHANGE_REQUESTS
        if service.lower() in item["service"].lower()
    ][:limit]

    if not matched:
        return f"No change requests found for {service}."

    lines = [
        f"{item['id']} | {item['service']} | {item['status']} | {item['window']}"
        for item in matched
    ]
    return "\n".join(lines)

if __name__ == "__main__":
    result = search_change_requests.invoke({"service": "payment-api", "limit": 2})
    print(result)
```

这段代码一点都不花哨，但它已经说明了一件事：

> **工具的意义不是“让模型更聪明”，而是“让模型能触达到真实数据”。**

如果你把这句话再往前推一步，其实就是：

> **模型负责判断，工具负责取数和动作。**

这是 Agent 和普通问答模型最实用的一条分界线。

---

## 一、官方到底怎么定义 Tool？先别把它理解浅了

LangChain 英文官网在 `Tools` 页里讲得很直白：

> Tools extend what agents can do — letting them fetch real-time data, execute code, query external databases, and take actions in the world.

翻成人话就是：

> **Tool 是 Agent 接触外部世界的手和脚。**

很多人第一次学 Tool，容易把它理解成“给大模型注册一个 Python 函数”。
这个理解不能说错，但太浅。

因为从实际工作流看，Tool 更像三层东西的结合：

1. **一个可调用函数**
2. **一份明确输入 schema**
3. **一段给模型看的使用说明**

也就是为什么官方一直强调两件事：

- 参数类型注解要清楚
- docstring 要短而准

来看一个更像企业内部研发场景的例子：

```python
from langchain.tools import tool

SERVICE_OWNERS = {
    "payment-api": {"owner": "支付中台", "oncall": "张宁", "slack": "#team-payment"},
    "order-api": {"owner": "交易平台", "oncall": "王哲", "slack": "#team-order"},
    "inventory-api": {"owner": "库存平台", "oncall": "李越", "slack": "#team-inventory"},
}

@tool("get_service_owner")
def lookup_service_owner(service_name: str) -> str:
    """Get owner team, on-call engineer, and notification channel for a backend service."""
    service = SERVICE_OWNERS.get(service_name)
    if service is None:
        return f"Service {service_name} is not registered."

    return (
        f"service={service_name}; owner={service['owner']}; "
        f"oncall={service['oncall']}; channel={service['slack']}"
    )

if __name__ == "__main__":
    print(lookup_service_owner.invoke({"service_name": "payment-api"}))
```

这里有几个细节特别值得注意：

- 我用了 `snake_case` 风格的工具名，这和官网建议一致
- docstring 不是随便写的，而是告诉模型 **什么时候该调用它**
- 返回值尽量结构清楚，方便模型下一步继续推理

如果你想让模型在工作里更稳定地选对工具，**工具描述写得准，比写得长更重要。**

这里再补一个很实际的经验：

- 工具名最好让人一眼知道用途
- docstring 最好直接写“何时用它”
- 返回值最好让模型容易继续消费

很多工具之所以在 demo 里能用、进业务就飘，问题并不在模型，而在于工具本身写得太“面向程序员”，没有“面向模型”。

---

## 二、Tool 的输入，不只是参数；它其实是在定义系统边界

英文官网里还有一个经常被忽略的点：**type hints are required**。

这不是语法洁癖，而是因为 Tool 的参数签名，本身就在定义模型能传什么。

如果你的输入复杂，就不要硬塞多个散乱参数，而要老老实实上 schema。

比如一个“查询发布窗口”的工具，现实里就不该只有一个 `service` 字符串。我们至少还会关心环境、日期、是否要看冻结窗口。

```python
from typing import Literal
from pydantic import BaseModel, Field
from langchain.tools import tool

DEPLOY_WINDOWS = {
    ("payment-api", "prod", "2026-05-01"): {
        "window": "20:00-21:00",
        "freeze": False,
        "risk": "medium",
    },
    ("order-api", "prod", "2026-05-01"): {
        "window": "21:00-22:00",
        "freeze": True,
        "risk": "high",
    },
}

class DeploymentWindowInput(BaseModel):
    service: str = Field(description="Target backend service name, for example payment-api")
    environment: Literal["test", "staging", "prod"] = Field(description="Deployment environment")
    date: str = Field(description="Business date in YYYY-MM-DD format")
    include_freeze_check: bool = Field(default=True, description="Whether to report freeze window status")

@tool(args_schema=DeploymentWindowInput)
def get_deployment_window(
    service: str,
    environment: str,
    date: str,
    include_freeze_check: bool = True,
) -> str:
    """Get the approved deployment window and freeze status for a service."""
    payload = DEPLOY_WINDOWS.get((service, environment, date))
    if payload is None:
        return f"No deployment window found for {service} in {environment} on {date}."

    result = [
        f"service={service}",
        f"environment={environment}",
        f"date={date}",
        f"window={payload['window']}",
        f"risk={payload['risk']}",
    ]

    if include_freeze_check:
        result.append(f"freeze={payload['freeze']}")

    return "; ".join(result)

if __name__ == "__main__":
    print(
        get_deployment_window.invoke(
            {
                "service": "order-api",
                "environment": "prod",
                "date": "2026-05-01",
                "include_freeze_check": True,
            }
        )
    )
```

这个例子背后的核心不是 Pydantic，而是：

> **你给 Tool 设计的 schema，决定了 Agent 能不能稳定地把自然语言需求翻译成系统动作。**

顺便补一个官网里的小坑位：

- `config`
- `runtime`

这两个参数名是保留字，不要拿来当普通业务参数名用。否则很容易在运行时翻车，属于那种“看起来没问题，真跑就出问题”的老六错误。

---

## 三、真正关键的一步：ToolRuntime 让工具拿到“当前线程上下文”

如果你只学到 `@tool`，其实还停留在 Tool 的初级阶段。

真正把 Tool 和 Agent 连起来的关键，是官方在 v1 文档里反复强调的 `ToolRuntime`。

它最有价值的地方是：

- 可以访问 **state**（短时记忆）
- 可以访问 **context**（本次调用的不可变上下文）
- 可以访问 **store**（跨线程持久信息）
- 还能拿到 **stream_writer / execution_info / tool_call_id** 这些运行期信息

先看一个更贴近实际工作的例子：同一个发布协调助手，在不同操作者上下文下，应该返回不同的值班视角。

```python
from dataclasses import dataclass
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime

ONCALL_ROTATION = {
    "u-1001": {"name": "陈工", "team": "支付中台", "shift": "20:00-08:00"},
    "u-1002": {"name": "赵工", "team": "交易平台", "shift": "08:00-20:00"},
}

@dataclass
class OperatorContext:
    operator_id: str

@tool
def get_my_oncall_info(runtime: ToolRuntime[OperatorContext]) -> str:
    """Get the current operator's on-call information."""
    operator_id = runtime.context.operator_id
    profile = ONCALL_ROTATION.get(operator_id)
    if profile is None:
        return f"No on-call profile found for operator {operator_id}."

    return (
        f"operator={operator_id}; name={profile['name']}; "
        f"team={profile['team']}; shift={profile['shift']}"
    )

if __name__ == "__main__":
    agent = create_agent(
        model="openai:gpt-4.1-mini",
        tools=[get_my_oncall_info],
        context_schema=OperatorContext,
        system_prompt="You are a release coordination assistant. Use tools before answering operational questions.",
    )

    result = agent.invoke(
        {
            "messages": [
                {"role": "user", "content": "我现在是谁值班，属于哪个团队？"}
            ]
        },
        context=OperatorContext(operator_id="u-1001"),
    )

    print(result["messages"][-1].content)
```

这里非常像真实企业系统：

- 用户并没有把 `operator_id` 明文说出来
- 这个信息来自调用上下文，而不是模型推理
- Tool 通过 `runtime.context` 拿到它

这很重要，因为它意味着：

> **Tool 可以安全地拿到“系统知道、但不一定需要让模型看见”的运行时信息。**

这类信息在实际工作里非常常见：

- 当前登录用户 ID
- 当前项目 ID
- 当前租户信息
- 本次会话所在的环境
- 功能开关与权限范围

也就是说，`ToolRuntime` 不是锦上添花，它是 Tool 真正工程化的入口。

换句话说，`ToolRuntime` 让 Tool 从“一个被模型调用的函数”，升级成“一个带运行时语义的系统节点”。

这层升级很重要，因为从这里开始，Tool 才真正接上：

- 当前线程状态
- 当前用户上下文
- 当前系统环境
- 当前执行身份

你也就终于不需要再把所有信息都塞进 prompt 里了。

---

## 四、官方说的短时记忆，到底是什么？

到了 `short-term memory` 这页，LangChain 官方其实给了一个非常清晰的定义：

> **短时记忆是线程级的记忆。**

注意这里不是“用户级”、不是“跨会话知识库”，而是 **thread-level persistence**。

这就决定了它适合保存什么：

- 当前对话刚提到的服务名
- 当前线程里的故障编号
- 这一轮工作流已经查过的中间结果
- 这个会话里刚确认过的偏好与约束

不适合拿来保存什么：

- 跨线程长期保留的用户画像
- 跨会话积累的业务知识
- 永久性的知识库事实

官方文档里还特别强调了一点：

> 短时记忆是 agent state 的一部分。

也就是说，在 LangChain v1 里，短时记忆已经不是“外挂插件思维”了，而是运行图状态本身。

先看一个最小可用版本：

```python
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(
    model="openai:gpt-4.1-mini",
    tools=[],
    checkpointer=InMemorySaver(),
    system_prompt="You are a concise release support assistant.",
)

config = {"configurable": {"thread_id": "release-thread-001"}}

first = agent.invoke(
    {
        "messages": [
            {"role": "user", "content": "我们正在处理 payment-api 的生产发布。"}
        ]
    },
    config,
)

second = agent.invoke(
    {
        "messages": [
            {"role": "user", "content": "刚才我说的是哪个服务？"}
        ]
    },
    config,
)

print(first["messages"][-1].content)
print(second["messages"][-1].content)
```

这个例子最关键的不是 `InMemorySaver()`，而是这个：

```python
{"configurable": {"thread_id": "release-thread-001"}}
```

因为没有 `thread_id`，就没有线程；没有线程，也就谈不上短时记忆。

所以短时记忆真正的底座其实是：

- **state**：存当前线程状态
- **checkpointer**：负责持久化这个状态
- **thread_id**：负责把多轮交互归到同一条线程里

这三样缺一不可。

这里建议你把概念彻底分开：

- `messages` 是最常见的短时记忆内容
- `state` 是短时记忆的容器
- `thread_id` 是这段记忆属于哪条线程的标识
- `checkpointer` 是这段记忆的存储机制

一旦这几个概念分清了，后面再看 `middleware`、`persistence`、`store`，基本都不会乱。

---

## 五、别只记住“能记住消息”，真正好用的是“能记住业务字段”

如果你只把短时记忆理解成消息历史，那还是有点保守。

官方在 `Customizing agent memory` 和 `Agents -> Memory` 里讲得很明确：

> 你可以扩展 `AgentState`，让 agent 在短时记忆里保存额外字段。

不过这里要特别提醒一句：

> **以英文官网为准，v1 里自定义 state 更推荐 TypedDict 风格。**

中文页里你可能还会看到一些更早期的写法，但如果你准备按官方当前思路落地，建议优先跟英文官网保持一致。

看一个更像故障协同线程的例子：

```python
from langchain.agents import create_agent, AgentState
from langgraph.checkpoint.memory import InMemorySaver
from typing_extensions import TypedDict

INCIDENT_DATABASE = {
    "INC-9001": {"service": "payment-api", "severity": "SEV-2", "summary": "third-party callback timeout"},
    "INC-9002": {"service": "order-api", "severity": "SEV-1", "summary": "checkout flow unavailable"},
}

class IncidentState(AgentState):
    current_incident_id: str
    current_service: str
    current_severity: str


def get_incident_snapshot(incident_id: str) -> str:
    incident = INCIDENT_DATABASE.get(incident_id)
    if incident is None:
        return f"Incident {incident_id} not found."
    return (
        f"incident_id={incident_id}; service={incident['service']}; "
        f"severity={incident['severity']}; summary={incident['summary']}"
    )

agent = create_agent(
    model="openai:gpt-4.1-mini",
    tools=[get_incident_snapshot],
    state_schema=IncidentState,
    checkpointer=InMemorySaver(),
    system_prompt="You are an incident coordination assistant.",
)

config = {"configurable": {"thread_id": "incident-thread-9001"}}

result = agent.invoke(
    {
        "messages": [{"role": "user", "content": "先处理 INC-9001，并记住这是当前故障。"}],
        "current_incident_id": "INC-9001",
        "current_service": "payment-api",
        "current_severity": "SEV-2",
    },
    config,
)

follow_up = agent.invoke(
    {
        "messages": [{"role": "user", "content": "给我总结当前故障级别和涉及服务。"}]
    },
    config,
)

print(result["messages"][-1].content)
print(follow_up["messages"][-1].content)
```

这背后的意义很大。

很多工作系统里，真正高价值的信息并不是自然语言消息本身，而是：

- 当前服务名
- 当前工单号
- 当前风险级别
- 当前审批状态
- 当前负责人

如果这些字段只存在于“文本里”，模型就要每次自己重新理解。
如果这些字段直接存在于 **state** 里，后续工具和中间件就都能稳定访问。

这就是短时记忆真正从“会话历史”走向“工作状态”的一步。

这也是为什么我特别建议在业务里优先存“字段”，而不是只存“对话”。

因为字段更稳定，也更容易被后续工具、中间件和判断逻辑复用。

---

## 六、工具不只是读系统，还能直接写入当前线程状态

这是我觉得官网里最容易被低估、但在真实项目里最有用的能力之一。

在 `Tools` 和 `Short-term memory` 两页里，官方都提到了这个模式：

> 工具可以通过返回 `Command` 来更新 state。

翻译成更工程化一点的话就是：

> **工具不只是拿数据回来给模型看，还可以把结果写入当前线程的“工作内存”。**

看一个完整一点的原创示例：先加载故障单，再生成升级通告。

```python
from dataclasses import dataclass
from langchain.agents import create_agent, AgentState
from langchain.messages import ToolMessage
from langchain.tools import ToolRuntime, tool
from langgraph.types import Command
from typing_extensions import TypedDict

INCIDENTS = {
    "INC-9001": {
        "service": "payment-api",
        "severity": "SEV-2",
        "summary": "third-party callback timeout causes delayed payment confirmation",
        "owner": "支付中台",
    },
    "INC-9002": {
        "service": "order-api",
        "severity": "SEV-1",
        "summary": "checkout flow unavailable for all users",
        "owner": "交易平台",
    },
}

class EscalationState(AgentState):
    incident_id: str
    service_name: str
    severity: str
    incident_summary: str
    owner_team: str

@dataclass
class EscalationContext:
    operator_name: str

@tool
def load_incident(
    incident_id: str,
    runtime: ToolRuntime[EscalationContext, EscalationState],
) -> Command:
    """Load incident details into the current thread state."""
    incident = INCIDENTS.get(incident_id)
    if incident is None:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content=f"Incident {incident_id} was not found.",
                        tool_call_id=runtime.tool_call_id,
                    )
                ]
            }
        )

    return Command(
        update={
            "incident_id": incident_id,
            "service_name": incident["service"],
            "severity": incident["severity"],
            "incident_summary": incident["summary"],
            "owner_team": incident["owner"],
            "messages": [
                ToolMessage(
                    content=f"Loaded incident {incident_id} into thread state.",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )

@tool
def draft_escalation_message(
    runtime: ToolRuntime[EscalationContext, EscalationState],
) -> str:
    """Draft an escalation message using incident details already stored in thread state."""
    operator = runtime.context.operator_name
    incident_id = runtime.state.get("incident_id")
    service_name = runtime.state.get("service_name")
    severity = runtime.state.get("severity")
    summary = runtime.state.get("incident_summary")
    owner_team = runtime.state.get("owner_team")

    if not all([incident_id, service_name, severity, summary, owner_team]):
        return "Incident details are incomplete. Call load_incident first."

    return (
        f"[升级通知] {incident_id} | 服务: {service_name} | 等级: {severity}\n"
        f"现象: {summary}\n"
        f"责任团队: {owner_team}\n"
        f"当前协调人: {operator}\n"
        "建议动作: 立即确认影响范围、回滚条件和下一次同步时间。"
    )

if __name__ == "__main__":
    agent = create_agent(
        model="openai:gpt-4.1-mini",
        tools=[load_incident, draft_escalation_message],
        state_schema=EscalationState,
        context_schema=EscalationContext,
        system_prompt="You are an incident escalation assistant. Load incident data before drafting escalation messages.",
    )

    result = agent.invoke(
        {"messages": [{"role": "user", "content": "请先加载 INC-9002，然后帮我生成升级通知。"}]},
        context=EscalationContext(operator_name="周宁"),
    )

    print(result["messages"][-1].content)
```

这个模式很像真正的工作流：

1. 工具先把故障单信息读回来
2. 然后把关键字段写进线程 state
3. 后续工具或提示直接读这些字段
4. 整个线程不需要一遍遍重新解析自然语言

这时候你会发现：

> **短时记忆不是“多记几句话”，而是“把工作线程里的关键变量保存下来”。**

这才是它真正值钱的地方。

如果你从系统设计角度去看，这一步其实很像把 Agent 从“即时问答”推进到了“状态机驱动的协作流程”。

它不再只是这一轮答了什么，而是开始关心：

- 当前线程现在处于什么阶段
- 哪些信息已经确认
- 哪些动作已经执行
- 下一步应该基于什么状态继续推进

---

## 七、为什么官方一直在讲 trim / delete / summarize？因为长线程一定会脏

一旦你真的把 Agent 接进工作流，就会遇到一个很现实的问题：

> **线程会越来越长。**

发布协调、故障排查、需求评审，这些事情不可能两轮对话结束。

而官方在 `short-term memory` 页面里给的答案非常明确，常见处理方式有四种：

- Trim messages
- Delete messages
- Summarize messages
- Custom strategies

### 1）Trim：保留最近有用的消息

这是最朴素、也最常用的办法。

```python
from typing import Any
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import before_model
from langchain.messages import RemoveMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.runtime import Runtime

@before_model
def trim_release_thread(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Keep the first instruction and the latest four messages."""
    messages = state["messages"]
    if len(messages) <= 5:
        return None

    first_message = messages[0]
    latest_messages = messages[-4:]

    return {
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),
            first_message,
            *latest_messages,
        ]
    }

agent = create_agent(
    model="openai:gpt-4.1-mini",
    tools=[],
    middleware=[trim_release_thread],
    checkpointer=InMemorySaver(),
)
```

这个策略很适合什么场景？

- 最开始那条系统性需求不能丢
- 最近上下文最重要
- 中间大量往返消息价值越来越低

对很多运维、发布、协同场景来说，够用了。

### 2）Delete：有些消息不是“压缩”，而是应该真正删掉

比如敏感输出、过期工具回执、重复确认消息。

```python
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import after_model
from langchain.messages import RemoveMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.runtime import Runtime

@after_model
def remove_sensitive_reply(state: AgentState, runtime: Runtime) -> dict | None:
    """Delete the latest assistant message if it leaks a forbidden word."""
    forbidden_words = ["password", "secret", "access_key"]
    last_message = state["messages"][-1]

    content = getattr(last_message, "content", "") or ""
    if any(word in content.lower() for word in forbidden_words):
        return {"messages": [RemoveMessage(id=last_message.id)]}

    return None

agent = create_agent(
    model="openai:gpt-4.1-mini",
    tools=[],
    middleware=[remove_sensitive_reply],
    checkpointer=InMemorySaver(),
)
```

这段代码的意义特别适合企业环境，因为很多时候你不是怕它“答错”，而是怕它“答了不该答的东西”。

### 3）Summarize：不是粗暴丢弃，而是把旧上下文压成摘要

这也是英文官网里我非常建议重点看的部分。

```python
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(
    model="openai:gpt-4.1-mini",
    tools=[],
    middleware=[
        SummarizationMiddleware(
            model="openai:gpt-4.1-mini",
            trigger=("tokens", 3000),
            keep=("messages", 12),
        )
    ],
    checkpointer=InMemorySaver(),
    system_prompt="You are a release review assistant. Keep long threads concise without losing key decisions.",
)
```

如果你问我企业里最值得优先试哪个，答案往往不是 delete，而是 summarize。

因为它更符合真实协作：

- 旧过程不能完全丢
- 但也不可能每轮都全量带上
- 所以最合理的办法是“保留决策、压缩过程”

这其实和人类团队协作很像：

> 开长会的人，最后都得有人写纪要。

`SummarizationMiddleware` 本质上就是在给 Agent 自动补这个动作。

如果你是在企业场景里落地，我会建议优先用这个顺序考虑：

1. **先 trim**：最省事，先解决上下文无限变长的问题
2. **再 summarize**：保证关键信息不丢
3. **最后才 delete**：用于处理敏感信息和明确该丢弃的内容

这样落地通常更稳，也更符合团队可接受的演进路径。

---

## 八、Tool 和短时记忆真正配起来，Agent 才像团队里的“在岗同事”

前面我们把工具和短时记忆分开讲，是为了看清楚边界。

但一旦进入真实业务，真正有价值的是它们配起来之后的效果。

我们写一个更完整、但仍然可运行的例子：

场景是这样的——

一位发布协调同学说：

> 帮我确认 `payment-api` 明晚能不能发版，顺便把风险说明写出来。

一个靠谱的 Agent，至少应该做这几件事：

1. 查发布窗口
2. 查服务负责人
3. 把关键结果写入当前线程
4. 再基于这些状态生成结论

看代码：

```python
from dataclasses import dataclass
from langchain.agents import create_agent, AgentState
from langchain.messages import ToolMessage
from langchain.tools import ToolRuntime, tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

DEPLOY_PLAN = {
    "payment-api": {"window": "2026-05-01 20:00-21:00", "freeze": False, "risk": "medium"},
    "order-api": {"window": "2026-05-01 21:00-22:00", "freeze": True, "risk": "high"},
}

TEAM_DIRECTORY = {
    "payment-api": {"owner": "支付中台", "oncall": "张宁"},
    "order-api": {"owner": "交易平台", "oncall": "王哲"},
}

class ReleaseState(AgentState):
    service_name: str
    deploy_window: str
    freeze_status: str
    risk_level: str
    owner_team: str
    oncall_engineer: str

@dataclass
class ReleaseContext:
    reviewer: str

@tool
def fetch_release_plan(
    service_name: str,
    runtime: ToolRuntime[ReleaseContext, ReleaseState],
) -> Command:
    """Load release plan details for a service into thread state."""
    plan = DEPLOY_PLAN.get(service_name)
    if plan is None:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content=f"No deploy plan found for {service_name}.",
                        tool_call_id=runtime.tool_call_id,
                    )
                ]
            }
        )

    return Command(
        update={
            "service_name": service_name,
            "deploy_window": plan["window"],
            "freeze_status": "frozen" if plan["freeze"] else "open",
            "risk_level": plan["risk"],
            "messages": [
                ToolMessage(
                    content=f"Loaded release plan for {service_name}.",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )

@tool
def fetch_team_owner(
    service_name: str,
    runtime: ToolRuntime[ReleaseContext, ReleaseState],
) -> Command:
    """Load owner team and on-call engineer for a service into thread state."""
    team = TEAM_DIRECTORY.get(service_name)
    if team is None:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content=f"No owner info found for {service_name}.",
                        tool_call_id=runtime.tool_call_id,
                    )
                ]
            }
        )

    return Command(
        update={
            "owner_team": team["owner"],
            "oncall_engineer": team["oncall"],
            "messages": [
                ToolMessage(
                    content=f"Loaded owner info for {service_name}.",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )

@tool
def generate_release_risk_note(
    runtime: ToolRuntime[ReleaseContext, ReleaseState],
) -> str:
    """Generate a release risk note from the current thread state."""
    service_name = runtime.state.get("service_name")
    deploy_window = runtime.state.get("deploy_window")
    freeze_status = runtime.state.get("freeze_status")
    risk_level = runtime.state.get("risk_level")
    owner_team = runtime.state.get("owner_team")
    oncall_engineer = runtime.state.get("oncall_engineer")
    reviewer = runtime.context.reviewer

    missing = [
        key for key, value in {
            "service_name": service_name,
            "deploy_window": deploy_window,
            "freeze_status": freeze_status,
            "risk_level": risk_level,
            "owner_team": owner_team,
            "oncall_engineer": oncall_engineer,
        }.items()
        if not value
    ]
    if missing:
        return f"Missing required release context: {', '.join(missing)}"

    decision = "可发布" if freeze_status == "open" and risk_level != "high" else "暂缓发布"

    return (
        f"【发布评审结论】\n"
        f"服务：{service_name}\n"
        f"发布窗口：{deploy_window}\n"
        f"冻结状态：{freeze_status}\n"
        f"风险等级：{risk_level}\n"
        f"责任团队：{owner_team}\n"
        f"值班同学：{oncall_engineer}\n"
        f"评审人：{reviewer}\n"
        f"建议：{decision}。若继续发布，请提前在群内同步回滚预案和观察指标。"
    )

if __name__ == "__main__":
    agent = create_agent(
        model="openai:gpt-4.1-mini",
        tools=[fetch_release_plan, fetch_team_owner, generate_release_risk_note],
        state_schema=ReleaseState,
        context_schema=ReleaseContext,
        checkpointer=InMemorySaver(),
        system_prompt=(
            "You are a release review assistant. "
            "Before giving a conclusion, fetch release plan and owner info, then generate a risk note."
        ),
    )

    config = {"configurable": {"thread_id": "release-review-payment-api"}}

    response = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "帮我确认 payment-api 明晚能不能发版，并给一段风险说明。",
                }
            ]
        },
        config,
        context=ReleaseContext(reviewer="刘洋"),
    )

    print(response["messages"][-1].content)
```

如果你认真看这个例子，会发现它其实已经很接近真实工作助手了：

- 工具不是摆设，而是在查系统状态
- 短时记忆不是聊天记录，而是当前评审线程里的关键变量
- 结论不是拍脑袋，而是依赖前面工具写入 state 后再生成

这时候，Agent 才从“对话模型”真正变成“线程化的工作协作者”。

如果你要用一句话向团队解释这段代码的价值，我会建议这么说：

> **前两个工具在收集状态，最后一个工具在消费状态；这就是 Agent 工作流最小闭环。**

这个闭环一旦跑通，很多场景都能自然迁移过去：

- 发布评审
- 故障协同
- 需求澄清
- 变更审批
- 代码评审

---

## 九、为什么我说“官网为主”尤其重要？因为有些细节真的会影响你写不写得对

这次看中英文文档，我有一个很强的感受：

> **中文文档很适合辅助理解，但真正准备写代码时，还是要回到英文官网确认。**

尤其是下面几个点：

### 1）`ToolRuntime` 的角色，在英文官网里讲得更完整

英文官网不仅讲了 `state`、`context`，还把这些运行期信息一起放进来了：

- `store`
- `stream_writer`
- `execution_info`
- `server_info`
- `tool_call_id`

比如你想给长任务加进度回写，就可以这么做：

```python
from langchain.tools import tool, ToolRuntime
import time

@tool
def rebuild_search_index(service_name: str, runtime: ToolRuntime) -> str:
    """Rebuild search index for a service and stream progress updates."""
    writer = runtime.stream_writer
    writer(f"Start rebuilding search index for {service_name}")
    time.sleep(1)
    writer("Downloaded latest documents")
    time.sleep(1)
    writer("Recomputed embeddings and updated index shards")
    return f"Search index rebuild finished for {service_name}."
```

这类能力在中文页里通常不会第一眼注意到，但在真实产品里很重要。

### 2）短时记忆和 persistence 的关系，在英文官网链路更顺

英文页把这几件事串得更清楚：

- state 在图里流动
- checkpointer 在每一步保存 checkpoint
- checkpoint 归属到 thread
- 后续可以恢复、重放、调试

你甚至可以顺着 persistence 页面继续往下看 `StateSnapshot`、`get_state_history()`、`replay`。

这对做可观测性和排障特别有帮助。

举个最小例子：

```python
from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from typing_extensions import TypedDict
from langchain_core.runnables import RunnableConfig

class State(TypedDict):
    service_name: str
    status: str


def mark_review_started(state: State):
    return {"status": f"review-started:{state['service_name']}"}


def mark_review_finished(state: State):
    return {"status": f"review-finished:{state['service_name']}"}

builder = StateGraph(State)
builder.add_node("start_review", mark_review_started)
builder.add_node("finish_review", mark_review_finished)
builder.add_edge(START, "start_review")
builder.add_edge("start_review", "finish_review")
builder.add_edge("finish_review", END)

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

config: RunnableConfig = {"configurable": {"thread_id": "graph-review-001"}}
graph.invoke({"service_name": "payment-api", "status": "pending"}, config)

latest_state = graph.get_state(config)
print(latest_state.values)
print(latest_state.metadata)
```

如果你后面要做“为什么这次 agent 的判断和上次不一样”的排查，这类能力会非常好用。

---

## 十、很多人会混淆的 4 个概念，这里一次讲清

如果你刚接触 LangChain v1，下面这几个词很容易在脑子里打架。

### 1）Tool 不是 MCP，也不是外部系统本身

Tool 是 Agent 可调用的能力抽象。

它背后可以连：

- API
- 数据库
- 文件系统
- 搜索服务
- 代码执行器

但 Tool 本身不是这些系统，而是它们暴露给 Agent 的调用接口。

### 2）Short-term memory 不是 long-term memory

短时记忆属于当前线程。
长期记忆属于跨线程、跨会话复用的信息。

最简单的判断方法是：

- **这条信息只对当前会话有用** → 放短时记忆
- **这条信息下次开新线程还要用** → 放长期记忆 / store

### 3）State 不是只有消息

`messages` 只是 state 里最常见的一部分。

真正业务里更有价值的，往往是：

- 当前服务
- 当前故障号
- 当前风险等级
- 当前审批状态
- 当前负责人

### 4）Checkpointer 不是长期知识库

它负责的是线程状态持久化，不是企业知识沉淀。

所以不要把 checkpointer 和 knowledge base 混为一谈。

它更像“当前工作现场的保存点”，而不是“组织记忆库”。

---

## 十一、从架构视角看，LangChain 在这里到底搭了什么？

如果把这篇内容抽象成一层更稳定的架构图，其实可以简化成 4 层：

### 1）模型层：负责理解、决策、生成

这一层决定 Agent 怎么判断下一步要不要调用工具、要不要结束、要不要继续追问。

### 2）工具层：负责接真实系统能力

这一层决定 Agent 能不能：

- 读数据
- 写状态
- 发动作
- 拿结果

### 3）状态层：负责维持线程内连续性

这一层让 Agent 不会每轮都“重新认识世界”。

### 4）控制层：负责裁剪、总结、治理

这一层通常由 middleware 和 persistence 相关能力支撑，用来控制：

- 消息什么时候裁剪
- 哪些信息需要保留
- 哪些输出要清理
- 状态如何恢复和追踪

如果你从工程角度看，LangChain v1 真正做的事，不只是“封装一下大模型调用”，而是在逐步把 Agent 变成一个有状态、有节点、有运行时约束的执行系统。

---

## 十二、企业里怎么用？我建议先抓 3 种最容易落地的模式

讲到这里，Tools 和短时记忆的边界应该已经比较清楚了。

最后我给你一个更偏实践的判断：

> **不要一上来就想做全能 Agent。先抓住三个能直接创造价值的工作模式。**

### 1）查询型助手：把系统信息拉到对话里

适合：

- 查发布窗口
- 查负责人
- 查值班表
- 查工单状态

示例骨架：

```python
from langchain.tools import tool

@tool
def query_ticket_status(ticket_id: str) -> str:
    """Query the latest status of an incident or request ticket."""
    mock_data = {
        "REQ-7001": "approved",
        "INC-9002": "mitigating",
    }
    return mock_data.get(ticket_id, "unknown")
```

### 2）线程型助手：把当前工作状态保留在 thread 里

适合：

- 一轮需求澄清
- 一次发布评审
- 一次故障处理
- 一次代码评审

示例骨架：

```python
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(
    model="openai:gpt-4.1-mini",
    tools=[],
    checkpointer=InMemorySaver(),
)

config = {"configurable": {"thread_id": "review-thread-req-7001"}}
```

### 3）状态驱动助手：工具把中间结果写回 state，后续步骤继续消费

适合：

- 先识别影响范围，再生成通知
- 先解析工单，再生成处理建议
- 先查服务拓扑，再生成排查路径

示例骨架：

```python
from langgraph.types import Command
from langchain.messages import ToolMessage
from langchain.tools import tool, ToolRuntime

@tool
def save_service_scope(service_name: str, runtime: ToolRuntime) -> Command:
    """Persist the current service scope into thread state."""
    return Command(
        update={
            "service_name": service_name,
            "messages": [
                ToolMessage(
                    content=f"Current scope set to {service_name}.",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )
```

如果你先把这三类跑通，已经能覆盖大多数团队最先会做的 Agent 场景了。

---

## 十三、如果你准备自己动手，我建议按这个顺序落地

这部分很适合拿去做团队内部分享，因为它回答的是另一个现实问题：

> 听懂了之后，第一步到底先做什么？

我建议按下面这个顺序来，而不是一上来就做“大而全智能体”。

### 第一步：先做只读工具

比如：

- 查发布窗口
- 查服务 owner
- 查故障状态

目的只有一个：

> 先让 Agent 真正能“碰到系统”。

### 第二步：再给它 thread 级记忆

让同一条线程里的多轮对话能接起来。

这时候你就能明显感受到：

- 它不会每轮都重新确认背景
- 它开始能沿着当前任务往下推进

### 第三步：再让工具写 state

这是从“能用”到“好用”的关键一步。

因为一旦工具能把关键结果写回 state，后续动作就能围绕同一套线程上下文继续展开。

### 第四步：最后再上 middleware

也就是：

- trim
- summarize
- guardrails
- 自定义 before / after hooks

这一步更像优化层，而不是起步层。

很多团队一开始最容易犯的错误，就是还没把前 3 步跑顺，就急着做复杂治理。结果系统复杂度上去了，业务价值还没出来。

---

## 十四、这一讲最重要的，不是 API 名字，而是这张脑图

如果让我把这一讲压缩成一张脑图，我会这样总结：

- **Tool**：给 Agent 接系统能力
- **ToolRuntime**：让工具拿到运行时上下文
- **State**：当前线程中的短时记忆
- **Checkpointer**：把线程状态存下来
- **Middleware**：控制线程怎么保留、裁剪、总结
- **Store**：跨线程长期保存信息（这不是这篇重点，但它和 state 要区分开）

再用一句最不容易忘的话来记：

> **Tool 决定 Agent 能不能动手，Short-term memory 决定 Agent 动手时会不会失忆。**

这两样一旦接起来，LangChain 才不只是“套了个 agent 外壳的大模型调用器”，而是真正开始变成工作流运行时。

---

## 十五、一个适合公众号结尾的判断

如果你今天还在把 Agent 理解成“会自己挑函数调用的大模型”，那大概率会低估 LangChain v1。

因为官方现在讲得已经不是简单的 tool calling 了，而是一整套线程化运行机制：

- 有工具
- 有状态
- 有中间件
- 有 checkpoint
- 有恢复与调试

从这个角度看，LangChain 真正值得学的，不是某一个 API，而是它在逐步把 Agent 从“会说话”推向“会执行、会记住、会续上”。

而你一旦理解了 Tools 和 Short-term memory 这两个点，后面的多智能体、长期记忆、Human-in-the-loop，其实都会顺很多。

如果你准备在团队里分享这一讲，我建议就用一句话做结尾：

> **没有工具，Agent 只是顾问；没有短时记忆，Agent 只是一个每轮都重新入职的顾问。**

如果还想再补一句更偏工程团队的话，我会这样说：

> **Tool 让 Agent 接上系统，Memory 让 Agent 接上流程。**

---

## 参考资料

### 英文官网（优先）

- `https://docs.langchain.com/oss/python/langchain/tools`
- `https://docs.langchain.com/oss/python/langchain/short-term-memory`
- `https://docs.langchain.com/oss/python/langchain/agents`
- `https://docs.langchain.com/oss/python/langchain/middleware`
- `https://docs.langchain.com/oss/python/langgraph/persistence`

### 中文对照

- `https://langchain-doc.cn/v1/python/langchain/tools.html`
- `https://langchain-doc.cn/v1/python/langchain/short-term-memory.html`

---

## 环境准备（给准备实操的人）

上面的代码示例都按 LangChain v1 的官方结构来写。准备本地实操时，可以先安装：

```bash
pip install -U langchain langgraph langchain-openai pydantic
```

如果你用 OpenAI 系列模型，准备好环境变量即可：

```bash
export OPENAI_API_KEY="your_api_key"
```

如果你喜欢 `.env` 方式，也可以在项目根目录放：

```dotenv
OPENAI_API_KEY=your_api_key
```

---

## 适合公众号封面的备选标题

如果你准备发公众号，下面这几个标题可以按风格选：

1. `LangChain 第三讲：为什么 Tool 和短时记忆，决定了 Agent 能不能进入工作流？`
2. `LangChain 第三讲：Tool 负责动手，Memory 负责不断片`
3. `LangChain 第三讲：把工具和线程记忆接起来，Agent 才不只是聊天机器人`
4. `LangChain 第三讲：官方文档里最值得细看的，其实是 Tools 和 Short-term Memory`
5. `LangChain 第三讲：没有工具和短时记忆，Agent 就很难真正干活`
