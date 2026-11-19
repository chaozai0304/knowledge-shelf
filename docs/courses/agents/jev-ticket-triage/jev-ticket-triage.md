---
title: Jev 模型知识与实战：企业工单的可信分流
author: chao
date: 2026-09-23
tags:
  - Jev
  - TypeSafe
  - System One
  - 工单分流
  - 概率决策
summary: 从 Jev 的 Choice、Score、Noul 三种原语出发，构建一个带不确定性复核和密钥保护的企业 SaaS 工单分流案例。
cover: ticket-triage-cover.svg
---

> **证据边界（2026-09-23）：**TypeSafe 控制台首页需要登录，接口与能力依据[公开文档](https://docs.typesafe.ai/introduction/quickstart)和[模型说明](https://docs.typesafe.ai/models)核对。本文已用授权密钥实际调用 Jev 接口，实测返回值、token 和耗时见下文；工单正文是**教程构造的样本**，不是客户数据或生产运行记录。另有[五子棋实时对战与源码](gomoku-guide.html)。密钥不会写进源文件或发布页面。

## 一句话结论：让 Jev 判断，让代码负责执行

当客服工单同时涉及账单、技术故障和人工诉求时，按关键词路由容易误判；让聊天模型生成一大段建议，又很难控制实际会执行什么。Jev 更适合把**范围明确的语义判断**变为软件可用的值：先回答“归谁管”“影响程度”“是否明确要求人工”，再由代码按风险阈值选路由。这个案例只**分流工单**，不自动退款、不改账户、不向客户发送未经审核的承诺。

## 先认清 Jev 的边界

TypeSafe 将 Jev 称为首个 System One 模型。API 接收 `state`（字符串或结构化文本状态）和多道 `questions`，单次请求返回每道题的结构化答案；各题独立评估。它不是写文章或生成客服回复的模型。[来源：官方简介](https://docs.typesafe.ai/)；[API 文档](https://docs.typesafe.ai/api)。

| 原语 | 想问的问题 | 返回值 | 在本文中的任务 |
| --- | --- | --- | --- |
| `Choice` | 多个固定选项，选哪个？ | `choice`、各选项 `probabilities`、`confidence` | 技术 / 账单 / 商务 / 其他，选首要团队 |
| `Score` | 在有文字定义的等级中，处于哪里？ | `score`、各等级 `probabilities`、`confidence` | 判断业务功能受损程度 |
| `Noul` | 某个明确命题是否成立？ | 0～1 的 `noul` 值 | 是否明确提出转人工 |

![示意图：一张匿名工单进入 Choice、Score、Noul 三类独立判断，形成结构化结果](../../../assets/generated-images/jev-triage-three-questions-20260924-145502.png)

*图 1｜三问一次请求：选首接团队、评估影响程度、判断是否明确要求人工。插图仅示意结构，不表示实际返回值。*

这里的 `confidence` 是 **Choice/Score 答案分布的集中程度**，不是“这次一定正确”的保证；`Noul` 没有单独的 `confidence` 字段。一个模型返回了合法类型，也不代表业务结论无误。来源：[Choice](https://docs.typesafe.ai/primitives/choice)、[Score](https://docs.typesafe.ai/primitives/score)、[Noul](https://docs.typesafe.ai/primitives/noul)、[Confidence](https://docs.typesafe.ai/confidence)。

截至查阅时，官方[模型页](https://docs.typesafe.ai/models)列出 `jev-1.13.0`；`jev-latest` 当前指向该版本但会变动。官网给出的输入价格是每百万 token 约 **$0.042**，输出 token 免费；这是公开标价，**不是本文测得成本**。官网介绍中的速度与竞品比较属于厂商所选工作流条件下的实验结果，不应移植成自己场景的 SLA。该模型目前仅接收文本（包括 JSON 文本结构），不直接接收图片、语音、视频；英文训练优势更明显，**中文工单必须另做回归测试**。[限制说明](https://docs.typesafe.ai/model-jaggedness/jev-1.13)提醒它不擅长精确数学、日期比较、长篇无关上下文和生成文字，还可能受到对抗性内容干扰。

## 场景：企业 SaaS 工单谁先接、什么时候要人工

下面三条是**为教程编写的模拟工单**，不是来自真实客服平台：

| ID | 工单摘要 | 我们希望核对的路由（人工标注） |
| --- | --- | --- |
| T-101 | 账单重复扣费，同时明确要求人工核查 | 转人工；退款动作仍需系统校验与授权 |
| T-102 | 今日无法登录、团队无法处理订单、无备用账号 | 技术团队，高优先级 |
| T-103 | 询问企业版报价与套餐 | 商务团队，普通优先级 |

真实业务的重点不是“模型选中了哪个队”，而是**出现两种诉求、缺少信息或置信度不够时不误自动化**。如果工单同时投诉接口故障与重复扣款，`Choice` 的首要团队只是候选分流，不应当丢掉次要问题；生产版可增加一组独立 `Noul` 检查多标签，再创建协作任务。

### 决策契约：三问一次请求，规则留在代码

代码将工单作为 `state.ticket`，并一次发送三题：

1. `department` 是带有 `other` 兜底选项的 `Choice`；只定首接团队。
2. `impact` 是三级 `Score`，等级写出具体情形。**不**让模型计算受影响订单数、金额或截止日期。
3. `wants_human` 是“是否明确要求真人”的 `Noul`，不用“语气是否不满”来替代人工诉求。

本文的**自定示例策略**（并非 TypeSafe 官方阈值）：明确要人工且 `noul ≥ 0.8` 则转人工；`0.2 < noul < 0.8` 或选中 `other` 则复核；低于 `0.2` 且团队 `confidence ≥ 0.7`、所选团队概率 `≥ 0.8`、影响程度 `confidence ≥ 0.65` 才允许自动分流。最高影响等级概率 `≥ 0.8` 则标记高优先级。任何 API 错误或响应格式异常都转人工复核。**阈值只有经过本团队标注数据集校准后，才适合上线。**

![示意图：工单判断结果经代码决策网关，分流到人工复核或团队队列](../../../assets/generated-images/jev-triage-decision-boundary-20260924-145611.png)

*图 2｜模型负责提供结构化判断，确定性代码决定是否放行；高风险或不确定的结果进入人工复核。图形不代表已经自动执行退款等操作。*

> 注意：严重程度问题的“没有说明可用替代方案”不等于“确定没有替代方案”。这个措辞偏保守，但上线前需用真实数据检验误报与漏报。影响等级高且置信度低的样本应优先人工复核，而不是凭一个数触发生产事故升级。

## 实战：离线规则测试 + 在线真实调用

下面直接提供完整可运行的 `triage.py` 和 `test_triage.py` 源码，复制文章到其他平台时不依赖本站文件链接。将两段代码分别保存为同名文件、放在同一个目录。运行需要 Python 3.10+，**仅使用标准库**；在线接口为官方文档的 `POST https://api.typesafe.ai/v1/systemone`，使用 `Authorization: Bearer`，模型设为 `jev-latest`，单次请求中混合三种原语。[官方 Quick Start](https://docs.typesafe.ai/introduction/quickstart)。

以下请求仅示意协议形状，**并非逐字实发的请求**；实际发给 Jev 的问题措辞已完整写在下方源码的 `QUESTIONS` 中：

```json
{
  "model": "jev-latest",
  "state": {"ticket": "账单扣了两次款，请安排人工客服帮我核查退款。"},
  "questions": {
    "department": {"type": "choice", "instructions": "首要团队？", "criteria": {"technical": "系统故障", "billing": "账单问题", "sales": "商务咨询", "other": "均不适用"}},
    "impact": {"type": "score", "instructions": "功能受损程度？", "criteria": ["无功能受损", "有替代方案", "关键功能无法使用"]},
    "wants_human": {"type": "noul", "instructions": "是否明确要求人工客服？"}
  }
}
```

### `triage.py`：完整可执行源码

```python
"""Jev 工单分流示例：离线校验策略，在线调用时才读取环境变量密钥。"""

import argparse
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request

ENDPOINT = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"
DEPARTMENTS = {
  "technical": "系统错误、登录失败、接口或集成故障",
  "billing": "扣费、发票、退款咨询或账单问题",
  "sales": "产品报价、套餐和商务咨询",
  "other": "不属于以上任何团队或信息不足",
}
QUESTIONS = {
  "department": {
    "type": "choice",
    "instructions": "工单主要应由哪个团队先接手？仅判断首要归属，不执行操作。",
    "criteria": DEPARTMENTS,
  },
  "impact": {
    "type": "score",
    "instructions": "工单描述的业务功能受影响程度如何？仅根据明确描述判断。",
    "criteria": [
      "仅外观或咨询，没有功能受损",
      "功能受损，但明确存在可用替代方案",
      "关键功能无法使用，且未说明可用替代方案",
    ],
  },
  "wants_human": {
    "type": "noul",
    "instructions": "客户是否明确要求人工客服或真人联系？",
    "criteria": {
      "true": "明确要求人工、真人或客服人员联系",
      "false": "没有明确提出人工联系请求",
    },
  },
}
TICKETS = {
  "T-101": "账单扣了两次款，请安排人工客服帮我核查退款。",
  "T-102": "账号今天一直无法登录，团队无法处理订单，也没有备用账号。",
  "T-103": "请介绍企业版的报价与套餐区别。",
}


def _probability(value):
  return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value) and 0 <= value <= 1


def assess(response):
  """所有检查失败都转人工；仅返回白名单字段，不输出原始请求或响应。"""
  try:
    answers = response["answers"]
    department, impact, wants_human = (answers[k] for k in QUESTIONS)
    probabilities = department["probabilities"]
    levels = impact["probabilities"]
    if (department["type"] != "choice" or impact["type"] != "score"
        or wants_human["type"] != "noul"
        or set(probabilities) != set(DEPARTMENTS)
        or set(levels) != {"0", "1", "2"}
        or department["choice"] not in DEPARTMENTS
        or any(not _probability(p) for p in probabilities.values())
        or any(not _probability(p) for p in levels.values())
        or not math.isclose(sum(probabilities.values()), 1, abs_tol=0.02)
        or not math.isclose(sum(levels.values()), 1, abs_tol=0.02)
        or not _probability(department["confidence"])
        or not _probability(impact["confidence"])
        or not _probability(wants_human["noul"])
        or probabilities[department["choice"]] != max(probabilities.values())):
      raise ValueError("invalid answer shape")

    human = wants_human["noul"]
    priority = "high" if levels["2"] >= 0.8 else "normal"
    if human >= 0.8:
      route, reason = "human", "明确请求人工"
    elif human > 0.2 or department["choice"] == "other":
      route, reason = "review", "诉求或归属不明确"
    elif (department["confidence"] < 0.7
        or probabilities[department["choice"]] < 0.8
        or impact["confidence"] < 0.65):
      route, reason = "review", "分类或影响程度不确定"
    else:
      route, reason = department["choice"], "自动分流（不执行退款等操作）"
    return {"route": route, "priority": priority, "reason": reason,
        "model": response.get("model", "unknown")}
  except (KeyError, TypeError, ValueError, AttributeError):
    return {"route": "review", "priority": "unknown", "reason": "响应无效，禁止自动分流",
        "model": "unknown"}


def call_jev(state, questions, log_io=False):
  """调用 Jev。log_io 只记录 JSON body/返回值，绝不记录授权头。"""
  key = os.environ.get("TYPESAFE_API_KEY")
  if not key:
    raise RuntimeError("未设置 TYPESAFE_API_KEY；请在本机环境变量中配置")
  payload = json.dumps({"model": MODEL, "state": state,
              "questions": questions}, ensure_ascii=False).encode("utf-8")
  if log_io:
    print("JEV_REQUEST " + payload.decode("utf-8"), flush=True)
  request = urllib.request.Request(
    ENDPOINT, data=payload, method="POST",
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
  )
  # 单次尝试；429/529 交给上层队列延后重试，不做无界同步重试。
  try:
    with urllib.request.urlopen(request, timeout=15) as result:
      response = json.load(result)
  except urllib.error.HTTPError as error:
    if log_io:
      print(f"JEV_ERROR HTTP {error.code}", flush=True)
    raise
  except (urllib.error.URLError, TimeoutError) as error:
    if log_io:
      print(f"JEV_ERROR {type(error).__name__}", flush=True)
    raise
  if log_io:
    print("JEV_RESPONSE " + json.dumps(response, ensure_ascii=False), flush=True)
  return response


def evaluate(ticket):
  return call_jev({"ticket": ticket}, QUESTIONS)


def evidence(response):
  """真实返回值的审计视图：只选择已知非敏感字段。"""
  answers = response["answers"]
  return {
    "department": {field: answers["department"][field]
             for field in ("choice", "probabilities", "confidence")},
    "impact": {field: answers["impact"][field]
           for field in ("score", "probabilities", "confidence")},
    "wants_human": answers["wants_human"]["noul"],
    "usage": {field: response.get("usage", {}).get(field)
          for field in ("input_tokens", "output_tokens")},
  }


def demo_answer(ticket_id):
  """手工合成的协议形状，用来演练策略；并非 Jev 的预测。"""
  samples = {
    "T-101": ("billing", 0.95, 0.94, [0.02, 0.88, 0.10]),
    "T-102": ("technical", 0.97, 0.04, [0.01, 0.09, 0.90]),
    "T-103": ("sales", 0.98, 0.03, [0.96, 0.03, 0.01]),
  }
  team, peak, human, levels = samples[ticket_id]
  probabilities = {name: (peak if name == team else (1 - peak) / 3)
           for name in DEPARTMENTS}
  return {"model": "synthetic-fixture", "answers": {
    "department": {"type": "choice", "choice": team, "confidence": peak,
             "probabilities": probabilities},
    "impact": {"type": "score", "confidence": 0.9,
           "probabilities": {str(i): p for i, p in enumerate(levels)}},
    "wants_human": {"type": "noul", "noul": human},
  }}


def main():
  parser = argparse.ArgumentParser(description="Jev 工单路由：--live 调真实 API，否则只演示规则")
  parser.add_argument("--live", action="store_true", help="逐条调用真实 Jev API，会产生费用")
  parser.add_argument("--evidence", action="store_true", help="打印经白名单过滤的真实概率、用量与耗时")
  args = parser.parse_args()
  if args.evidence and not args.live:
    parser.error("--evidence 只能与 --live 一起使用")
  if not args.live:
    print("离线规则演示（内部输入为合成概率，非 Jev 返回值）")
  for ticket_id, ticket in TICKETS.items():
    if not args.live:
      decision = assess(demo_answer(ticket_id))
    else:
      try:
        started = time.monotonic()
        response = evaluate(ticket)
        decision = assess(response)
        if args.evidence:
          decision["evidence"] = evidence(response)
          decision["elapsed_ms"] = round((time.monotonic() - started) * 1000)
      except (urllib.error.URLError, OSError, KeyError, TypeError, ValueError, RuntimeError) as error:
        # 避免打印请求头、密钥、工单正文或服务端响应体。
        decision = {"route": "review", "priority": "unknown", "reason": "API 不可用或未配置：" + type(error).__name__, "model": "unknown"}
    print(json.dumps({"ticket_id": ticket_id, **decision}, ensure_ascii=False))
  return 0


if __name__ == "__main__":
  sys.exit(main())
```

### `test_triage.py`：完整离线回归测试

```python
"""仅测试业务路由规则，网络调用需使用 --live 单独验证。"""

import unittest

from triage import assess


def answer(team="billing", confidence=0.95, human=0.05, impact=None):
  impact = impact or {"0": 0.0, "1": 0.95, "2": 0.05}
  probabilities = {"technical": 0.01, "billing": 0.95, "sales": 0.02, "other": 0.02}
  if team == "technical":
    probabilities = {"technical": 0.95, "billing": 0.01, "sales": 0.02, "other": 0.02}
  return {"model": "test-fixture", "answers": {
    "department": {"type": "choice", "choice": team, "confidence": confidence,
             "probabilities": probabilities},
    "impact": {"type": "score", "confidence": 0.9, "probabilities": impact},
    "wants_human": {"type": "noul", "noul": human},
  }}


class PolicyTests(unittest.TestCase):
  def test_high_confidence_routes_but_never_refunds(self):
    self.assertEqual(assess(answer())["route"], "billing")

  def test_explicit_human_request(self):
    self.assertEqual(assess(answer(human=0.95))["route"], "human")

  def test_ambiguous_or_low_confidence_escalates(self):
    self.assertEqual(assess(answer(human=0.45))["route"], "review")
    self.assertEqual(assess(answer(confidence=0.5))["route"], "review")

  def test_critical_impact_priority(self):
    result = assess(answer(team="technical", impact={"0": 0.01, "1": 0.09, "2": 0.9}))
    self.assertEqual((result["route"], result["priority"]), ("technical", "high"))

  def test_invalid_response_fails_closed(self):
    self.assertEqual(assess({"answers": {}})["route"], "review")
    bad = answer()
    bad["answers"]["wants_human"]["noul"] = float("nan")
    self.assertEqual(assess(bad)["route"], "review")


if __name__ == "__main__":
  unittest.main()
```

先在本地执行，不需要密钥，也**不会发起网络请求**：

```sh
python3 -m unittest discover -s docs/courses/agents/jev-ticket-triage -p 'test_*.py'
python3 docs/courses/agents/jev-ticket-triage/triage.py
```

本地离线执行结果：工单策略的 5 个测试通过；**合成的概率输入**按策略得到 T-101 → `human`、T-102 → `technical/high`、T-103 → `sales/normal`。它们只是测试夹具，不能代替下面的真实接口调用。随游戏代码更新，目录下测试数量会变化，应以实际运行输出为准。

### 实测环境与命令

2026-09-23，以 Python 标准库 `urllib.request` 向 `https://api.typesafe.ai/v1/systemone` 提交三次 HTTPS POST，每条中文样本工单发送相同的三个问题。密钥仅在运行时进入进程环境，不作为代码或文档内容。复现前自行安全设置 `TYPESAFE_API_KEY`，然后运行：

```sh
python3 docs/courses/agents/jev-ticket-triage/triage.py --live --evidence
```

`--evidence` 输出经过白名单过滤的真实概率、等级、用量和客户端墙钟耗时（含网络，不是模型纯推理耗时）。下面是该次实际运行的逐条摘要，不是模拟 JSON：

| 工单 | 实际模型 | `department`（所选概率 / confidence） | `impact`（各等级概率 / confidence） | `wants_human` | 策略结果 | input / output tokens | 本地耗时 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T-101 重复扣费、请求人工 | `jev-1.13.0` | billing 1.00 / 1.00 | 0:0.30，1:0.49，2:0.21 / **0.24** | 0.99 | `human`，普通优先级 | 606 / 78 | 1363 ms |
| T-102 登录故障、无备用账号 | `jev-1.13.0` | technical 1.00 / 1.00 | 0:0，1:0，2:1.00 / 1.00 | 0.05 | `technical`，**高优先级** | 612 / 78 | 1047 ms |
| T-103 企业版报价 | `jev-1.13.0` | sales 1.00 / 1.00 | 0:1.00，1:0，2:0 / 1.00 | 0.03 | `sales`，普通优先级 | 599 / 78 | 874 ms |

例如 T-101 的真实返回证据（只摘选关键信息；`impact.score=0.92` 并不表示 92% 严重）：

```json
{
  "model": "jev-1.13.0",
  "department": {"choice": "billing", "probabilities": {"technical": 0.0, "billing": 1.0, "other": 0.0, "sales": 0.0}, "confidence": 1.0},
  "impact": {"score": 0.92, "probabilities": {"0": 0.30, "1": 0.49, "2": 0.21}, "confidence": 0.24},
  "wants_human": 0.99,
  "usage": {"input_tokens": 606, "output_tokens": 78},
  "route": "human"
}
```

这里 `department`、`impact`、`wants_human` 和 `usage` 来自实际 API 响应，`route` 则是**本地 `assess()` 的计算结果**，不是服务端字段。`impact.score=0.92` 与表内显示的两位小数概率乘加略有差异，不能拿展示精度做精确反推。T-101 的 `impact.confidence` 只有 **0.24**，说明在本问法下它对影响等级并不确定；人工请求 `0.99` 触发了转人工，这次低影响置信度并未转化成错误的自动分流。三条样本恰好都符合人工预期，**样本量太小，不证明中文工单准确率或性能指标**。三次请求合计 1817 输入 token、234 输出 token，按当时官网输入标价估算约 **$0.000076**（非实际账单）。

不要把密钥写进代码、终端历史里的 `export ...` 字面量、网页或 Git 仓库。脚本只在 `--live` 时读取环境变量；`--evidence` 不打印密钥和工单正文。调用会产生 API 费用；若请求失败则走 `review`，不会伪造成功结果。密钥已在聊天中披露，建议**立即到 TypeSafe 控制台轮换**；密钥也可能进入终端/会话记录，应依照团队安全规范清理。

## 结果怎么看：有结构，不等于有事实

收到在线响应时，先核查 `answers.department.choice` 是否在团队白名单、`probabilities` 是否覆盖全部选项且合计约为 1；`impact.probabilities` 是否覆盖三级；`wants_human.noul` 是否在 0～1。脚本将异常/缺字段默认送 `review`。真实工单要把模型实际返回的版本 ID 和策略版本一起记录进受控审计系统，但**避免日志落盘用户正文、姓名、支付信息和密钥**。

`Score.score` 是等级的概率加权位置，不是损失金额；`Noul=0.8` 也不表示“80% 用户满意度”。人工放行之后仍要在业务系统核实订单、金额、操作权限和审批链。对金融、医疗、合规等高风险动作，仅凭模型概率不应直接执行。

## 上线前的验收门槛（作者建议，不是厂商保证）

![示意图：匿名样本、人工标注与误差分析、影子运行、小流量发布及回滚](../../../assets/generated-images/jev-triage-shadow-validation-20260924-145718.png)

*图 3｜从数据标注到影子运行，再到可回滚的小流量上线；示意流程不等于已完成生产验收。*

1. 收集本域中文工单，按时间分出训练/调阈值集与独立回归集，至少覆盖混合诉求、否定句、口语、转人工、长文本和提示注入。
2. 人工标注：首接团队、第二团队、严重程度、人工诉求；对分歧样本双人复核。用混淆矩阵查看错分和高风险漏报，而不是只看整体准确率。
3. 对多版本分别统计自动分流覆盖率、错分率、人工复核量、高优先级召回、中文性能、延迟 P95 和单工单成本；先影子运行，再小流量开放自动分流。
4. 用固定版本 ID 和可回滚的阈值策略部署。遇到模型升级、`429`/`529` 限流、网络超时或模型答案变更，暂停自动化，走可追溯的人工队列。官方[API 错误说明](https://docs.typesafe.ai/api#errors)规定了限流等状态；本例故意不在请求线程里无限重试。
5. 查阅[隐私政策](https://typesafe.ai/legal/privacy-policy)和团队的数据处理要求：厂商表示不以客户 Input 训练模型，但输入会按其服务条款处理；不要把“不会用于训练”理解为“默认零留存”或“可以直接上传敏感数据”。

**适用边界：**Jev 适合被拆成有限选项的语义判断；需要回复客户的自然语言答复、复杂证据链推理、金额计算与最终退款执行，都应由其他经授权的组件承担。用确定性代码守住执行边界，让不确定性留给人工。

**动手玩一遍：**本站另有 Jev 五子棋对战案例；它与本文工单示例是独立项目，复制本文到其他平台不影响上述工单代码的阅读和运行。

## 官方资料

- [TypeSafe 开发者文档与 Quick Start](https://docs.typesafe.ai/introduction/quickstart)
- [API 接口及响应协议](https://docs.typesafe.ai/api)
- [Jev 模型版本、价格、输入及语言限制](https://docs.typesafe.ai/models)
- [Choice、Score、Noul 与 confidence](https://docs.typesafe.ai/primitives)
- [Jev 1.13 已知弱项（最后审阅 2026-09-17）](https://docs.typesafe.ai/model-jaggedness/jev-1.13)
- [TypeSafe 官方发布文章（厂商声明与评测适用条件）](https://typesafe.ai/blog/introducing-system-one-models-and-jev)
- [TypeSafe 隐私政策](https://typesafe.ai/legal/privacy-policy)