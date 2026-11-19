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