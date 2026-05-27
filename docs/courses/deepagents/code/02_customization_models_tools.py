"""02：模型、工具、提示词与结构化输出定制。

本例展示 create_deep_agent 的常用定制面：
- provider:model 模型字符串
- 自定义工具
- system_prompt
- response_format
- 自定义 subagent
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from langchain.tools import tool

from common import explain_dry_run, model_for_deepagents, model_spec, print_section, require_runtime, safe_preview, should_run_agent


class CampaignBrief(BaseModel):
    """结构化输出 schema。

    Deep Agents 会把模型生成的结构化结果校验成这个对象，
    适合后端继续保存、展示或传给下一步流程。
    """

    title: str = Field(description="活动标题")
    audience: str = Field(description="目标受众")
    channels: list[str] = Field(description="推荐渠道")
    risks: list[str] = Field(description="主要风险")


@tool
def estimate_channel_fit(channel: str, audience: str) -> str:
    """评估某个投放渠道与目标受众的匹配程度。

    这是一个教学用工具：真实业务里可以把这里替换成数据库查询、BI 指标、广告平台 API。
    模型会根据函数名、参数和 docstring 判断什么时候调用它。
    """
    scores = {
        "公众号": "高：适合深度内容和已有粉丝触达",
        "小红书": "中高：适合种草和轻量转化",
        "知乎": "中：适合专业解释和搜索长尾",
        "B站": "中：适合教程型视频和品牌认知",
    }
    return f"{channel} 面向 {audience} 的匹配度：{scores.get(channel, '未知：需要补充渠道数据')}"


SYSTEM_PROMPT = """
你是一个增长策略顾问。回答前先拆解目标受众，再调用工具评估渠道。
最后输出一个结构化 CampaignBrief，不要编造不存在的数据。
""".strip()


SUBAGENTS = [
    {
        "name": "risk-reviewer",
        "description": "检查营销方案中的合规、预算和执行风险。",
        "system_prompt": "你是谨慎的风险审查员，只输出风险和缓解建议。",
        # "tools": [internet_search],
        # "model": "openai:gpt-4o",
    }
]


def build_agent():
    """组装一个带工具、子智能体和结构化输出的 Deep Agent。"""
    from deepagents import create_deep_agent

    return create_deep_agent(
        model=model_for_deepagents(),
        tools=[estimate_channel_fit],
        system_prompt=SYSTEM_PROMPT,
        subagents=SUBAGENTS,
        response_format=CampaignBrief,
    )


def main() -> None:
    """脚本入口：先展示配置和工具效果，再按 RUN_AGENT 决定是否真实调用。"""
    print_section("当前定制项")
    print(f"模型：{model_spec()}")
    print(f"工具：{estimate_channel_fit.name}")
    print(f"结构化输出：{CampaignBrief.__name__}")
    print(f"子智能体：{SUBAGENTS[0]['name']}")
    print_section("工具试跑")
    print(estimate_channel_fit.invoke({"channel": "公众号", "audience": "企业 AI 产品经理"}))

    if not should_run_agent():
        explain_dry_run("02_customization_models_tools.py")
        return

    require_runtime()
    agent = build_agent()
    # 用户问题进入 messages；Deep Agents 会根据 system_prompt 决定是否调用工具或子智能体。
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "为企业 AI Agent 课程设计一个低预算获客活动。"}]}
    )
    print_section("最终回答")
    # 官方 structured output 会把校验后的结果放在 structured_response。
    print(safe_preview(result.get("structured_response", result)))


if __name__ == "__main__":
    main()
