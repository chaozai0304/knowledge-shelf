# Deep Agents 讲解材料与代码运行说明

本目录包含 5 篇 Deep Agents 微信分享文档、对应 HTML、SVG 图，以及可运行 Python 示例代码。

## 目录结构

```text
output/courses/deepagents/
├── 01-quickstart-harness-wechat.md
├── 02-customization-models-tools-wechat.md
├── 03-context-backends-memory-skills-wechat.md
├── 04-subagents-hitl-permissions-wechat.md
├── 05-interpreters-streaming-production-wechat.md
├── assets/                  # 分享文档使用的 SVG 图
└── code/                    # 可运行示例代码
    ├── .env.example
    ├── .env                 # 自动创建的占位配置，请替换真实 key
    ├── requirements.txt
    ├── common.py
    ├── 01_quickstart_research_agent.py
    ├── 02_customization_models_tools.py
    ├── 03_context_backends_memory_skills.py
    ├── 03b_persistent_memory_filesystem.py
    ├── 04_subagents_hitl_permissions.py
    ├── 05_streaming_interpreters_production.py
    └── skills/order-helpers/
```

## 建议阅读顺序

1. `01-quickstart-harness-wechat.md`：Deep Agents 的定位、Harness 心智模型、快速入门。
2. `02-customization-models-tools-wechat.md`：模型、工具、提示词、结构化输出和 profile。
3. `03-context-backends-memory-skills-wechat.md`：上下文工程、Backend、Memory 和 Skills。
    - 如果你想看“真正持久保存到磁盘”的版本，请运行 `03b_persistent_memory_filesystem.py`。
4. `04-subagents-hitl-permissions-wechat.md`：子智能体、人机协同、权限和 sandbox。
5. `05-interpreters-streaming-production-wechat.md`：解释器、流式输出和生产化部署。

## 官方文档覆盖关系

本系列按官方 Deep Agents 文档重新核对过，核心内容覆盖如下：

| 官方页面 | 覆盖章节 |
| --- | --- |
| quickstart | 第 1 讲：安装、Tavily、搜索工具、create_deep_agent、invoke、streaming |
| harness | 第 1 讲：planning、filesystem、subagents、context、HITL、skills、memory |
| customization | 第 2 讲：model、tools、system_prompt、middleware、subagents、backends、HITL、skills、memory、profiles、structured output |
| models | 第 2 讲：provider:model、tool calling、模型参数、运行时模型选择 |
| context-engineering | 第 3 讲：输入上下文、运行时上下文、压缩、隔离、长期记忆 |
| backends | 第 3 讲：StateBackend、StoreBackend、CompositeBackend、虚拟文件系统 |
| memory | 第 3 讲：长期记忆、用户作用域、组织作用域、只读/可写、后台 consolidation |
| skills | 第 3 讲：SKILL.md、progressive disclosure、interpreter skills |
| subagents / async-subagents | 第 4 讲：同步子智能体、异步任务、上下文隔离 |
| human-in-the-loop | 第 4 讲：interrupt_on、approve/edit/reject/respond、checkpointer |
| permissions | 第 4 讲：FilesystemPermission、first-match-wins、子智能体权限 |
| sandboxes | 第 4 讲：execute、隔离边界、文件传输、安全注意事项 |
| interpreters | 第 5 讲：QuickJS、CodeInterpreterMiddleware、PTC、interpreter skills |
| profiles | 第 2 / 5 讲：HarnessProfile、ProviderProfile、按模型调优 |
| streaming / event-streaming | 第 5 讲：stream v2、stream_events v3、subagents projection |
| going-to-production / comparison | 第 5 讲：Thread、User、Assistant、langgraph.json、部署与治理 |

## Python 环境要求

- Python 3.11+。
- 真实调用需要一个支持 tool calling 的模型。
- 官方 quickstart 使用 `deepagents` + `tavily-python`，并要求配置模型 provider key 与 `TAVILY_API_KEY`。
- 示例默认使用 OpenAI 兼容配置，也可以替换为其他 `provider:model`，例如 `google_genai:gemini-3.5-flash`。

## 安装依赖

官方 quickstart 的最小安装命令是：

```bash
pip install deepagents tavily-python
```

本课程为了覆盖模型、LangGraph、解释器、结构化输出等后续内容，建议直接安装完整依赖：

```bash
cd /Users/chao/Desktop/分享文档库/output/courses/deepagents/code
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 配置环境变量

当前已自动创建 `.env` 占位文件。请把里面的 key 替换为真实值：

```bash
DEEPAGENTS_MODEL=openai:gpt-4o-mini
OPENAI_API_KEY=你的模型网关 key
OPENAI_BASE_URL=https://你的模型网关/v1
TAVILY_API_KEY=你的 Tavily 搜索 key
RUN_AGENT=true
```

如果使用官方 quickstart 里的 Gemini 模型，请改成：

```bash
DEEPAGENTS_MODEL=google_genai:gemini-3.5-flash
GOOGLE_API_KEY=你的 Google API key
TAVILY_API_KEY=你的 Tavily 搜索 key
RUN_AGENT=true
```

如果 `RUN_AGENT=false`，脚本只做结构演示，不会真实调用模型。

## OpenAI 兼容网关排障

如果运行 `01_quickstart_research_agent.py` 时搜索成功，但模型调用报错，例如：

- `openai.InternalServerError: Error code: 502`
- `APIConnectionError: Connection error`
- 栈里出现 `responses.with_raw_response.create`

通常不是 Deep Agents 逻辑问题，而是模型网关兼容性问题。很多 OpenAI-compatible 网关只实现了 `/chat/completions`，不支持 OpenAI 新的 `/responses` 接口。

本课程代码已经做了兼容处理：

1. `DEEPAGENTS_USE_RESPONSES_API=false`：默认禁用 Responses API。
2. 对 `openai:*` 模型显式创建 `ChatOpenAI`，走 Chat Completions。
3. `load_dotenv(..., override=True)`：强制以当前代码目录 `.env` 为准，避免终端残留旧环境变量。
4. `httpx.Client(trust_env=False)`：忽略系统代理环境，避免内网网关被代理影响。

如果仍然失败，可以先用最小模型测试脚本确认网关本身可用，再运行 Deep Agents 示例。

## 运行示例

```bash
python 01_quickstart_research_agent.py
python 02_customization_models_tools.py
python 03_context_backends_memory_skills.py
python 04_subagents_hitl_permissions.py
python 05_streaming_interpreters_production.py
```

## 官方参考

- https://docs.langchain.com/oss/python/deepagents/quickstart
- https://docs.langchain.com/oss/python/deepagents/customization
- https://docs.langchain.com/oss/python/deepagents/comparison
- https://docs.langchain.com/oss/python/deepagents/going-to-production
- https://docs.langchain.com/oss/python/deepagents/harness
- https://docs.langchain.com/oss/python/deepagents/models
- https://docs.langchain.com/oss/python/deepagents/context-engineering
- https://docs.langchain.com/oss/python/deepagents/backends
- https://docs.langchain.com/oss/python/deepagents/subagents
- https://docs.langchain.com/oss/python/deepagents/async-subagents
- https://docs.langchain.com/oss/python/deepagents/human-in-the-loop
- https://docs.langchain.com/oss/python/deepagents/permissions
- https://docs.langchain.com/oss/python/deepagents/memory
- https://docs.langchain.com/oss/python/deepagents/skills
- https://docs.langchain.com/oss/python/deepagents/sandboxes
- https://docs.langchain.com/oss/python/deepagents/interpreters
- https://docs.langchain.com/oss/python/deepagents/profiles
- https://docs.langchain.com/oss/python/deepagents/event-streaming
- https://docs.langchain.com/oss/python/deepagents/streaming
