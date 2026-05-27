# LangGraph 讲解材料与代码运行说明

本目录包含 4 篇微信分享文档、对应 HTML，以及可运行 Python 示例代码。

## 目录结构

```text
output/courses/langgraph/
├── 01-install-quickstart-wechat.md
├── 01-install-quickstart-wechat.html
├── 02-graph-thinking-wechat.md
├── 02-graph-thinking-wechat.html
├── 03-workflows-agents-wechat.md
├── 03-workflows-agents-wechat.html
├── 04-local-server-wechat.md
├── 04-local-server-wechat.html
├── assets/                  # 分享文档使用的 SVG 图
└── code/                    # 可运行示例代码
    ├── .env.example
    ├── requirements.txt
    ├── common.py
    ├── 01_install_quickstart_calculator.py
    ├── 02_graph_api_state_edges.py
    ├── 03_thinking_email_agent.py
    ├── 04_workflows_agents_patterns.py
    ├── 05_test_local_server_client.py
    ├── test_openai_config.py
    └── local_server_demo/
```

## 建议阅读顺序

1. `01-install-quickstart-wechat.md`：安装、概念总览、计算器 Agent 快速入门。
2. `02-graph-thinking-wechat.md`：State / Node / Edge / Command / interrupt，以及客服邮件 Agent 思路。
3. `03-workflows-agents-wechat.md`：prompt chaining、parallelization、routing、evaluator-optimizer、agent 的适用场景。
4. `04-local-server-wechat.md`：LangGraph Local Server、Studio、本地 API 调用方式。

## Python 环境要求

- Python 3.11+ 推荐。
- Local Server 官方文档要求 Python >= 3.11。
- 如果只跑 `02_graph_api_state_edges.py` 和 `04_workflows_agents_patterns.py`，不需要真实模型 key。
- 如果跑 `01_install_quickstart_calculator.py` 或本地服务，需要填写 OpenAI 兼容模型环境变量。

## 安装依赖

在 `code` 目录中执行：

```bash
cd /Users/chao/Desktop/分享文档库/output/courses/langgraph/code
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 配置环境变量

复制示例文件：

```bash
cp .env.example .env
```

填写以下变量：

```bash
OPENAI_API_KEY=你的模型网关 key
OPENAI_BASE_URL=你的 OpenAI 兼容接口地址，例如 https://xxx/v1
OPENAI_MODEL=你的模型名，例如 gpt-4o-mini 或公司网关模型名
```

建议先做一次最小化测试，确认 `.env` 里的地址、key 和模型名可用：

```bash
python test_openai_config.py
```

如果看到 `MODEL_TEST=HTTP_ERROR 401` 或 `无效的令牌`，一般不是 `.env` 没生效，而是当前 `OPENAI_API_KEY` 没被该网关接受。请重新复制有效 key，并确认 `OPENAI_BASE_URL` 与 key 属于同一个模型网关。

可选 LangSmith：

```bash
LANGSMITH_API_KEY=你的 LangSmith key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=langgraph-course
```

## 运行示例

```bash
python 01_install_quickstart_calculator.py
python 02_graph_api_state_edges.py
python 03_thinking_email_agent.py
python 04_workflows_agents_patterns.py
```

## 使用 LangGraph Studio 可视化执行

在 `code` 目录启动本地服务：

```bash
bash start_studio.sh
```

启动后打开终端输出中的 Studio 地址，通常是：

```text
https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

注意：即使服务用 `--host 0.0.0.0` 启动，浏览器里的 `baseUrl` 也不要写 `http://0.0.0.0:2024`，请使用 `http://127.0.0.1:2024` 或 `http://localhost:2024`。

如果页面显示 `Failed to initialize Studio / TypeError: Failed to fetch`，先检查本地 API：

```bash
python check_studio_server.py
```

如果检查成功但浏览器仍然失败，通常是浏览器或网络策略阻止 LangSmith 页面访问本机 `localhost`，改用隧道模式：

```bash
bash start_studio.sh --tunnel
```

然后打开终端输出里的 tunnel Studio 地址。

当前 `langgraph.json` 已注册这些可视化图：

- `calculator_agent`：第一讲计算器 Agent，依赖真实模型网关。
- `ticket_router`：第二讲工单分类与条件路由，不依赖 LLM。
- `email_review_agent`：第三讲人工审核 interrupt 流程。
- `prompt_chain`：第四讲链式工作流。
- `parallel_writer`：第四讲并行工作流。
- `evaluator_optimizer`：第四讲评估优化循环。

也可以用客户端脚本触发一次执行，并在 Studio 中观察过程：

```bash
python 05_test_local_server_client.py
```

切换要运行的图：

```bash
LANGGRAPH_ASSISTANT=parallel_writer python 05_test_local_server_client.py
```

如果 `calculator_agent` 报 `502 Bad Gateway`，通常是模型网关临时不可用或模型名/key 与网关不匹配；可先用 `ticket_router`、`parallel_writer` 等无 LLM 示例验证 Studio 链路。

运行后，图结构会保存到：

```text
code/generated_graphs/
```

这些 `.mmd` 文件是 Mermaid 图源码，可以复制到支持 Mermaid 的 Markdown 编辑器中预览。

## 启动 LangGraph Local Server

进入本地服务示例：

```bash
cd /Users/chao/Desktop/分享文档库/output/courses/langgraph/code/local_server_demo
cp .env.example .env
pip install -e .
langgraph dev --tunnel --no-browser --no-reload --port 2024 --host 127.0.0.1
```

启动成功后通常会看到：

```text
API: http://127.0.0.1:2024
Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
API Docs: http://127.0.0.1:2024/docs
```

另开终端测试 API：

```bash
cd /Users/chao/Desktop/分享文档库/output/courses/langgraph/code
source .venv/bin/activate
python 05_test_local_server_client.py
```

## 常见问题

### 1. 为什么有些示例不用真实 LLM？

为了把 LangGraph 的骨架讲清楚。State、Node、Edge、Command、interrupt 这些机制不依赖具体模型。等结构跑通后，把示例里的规则函数替换成模型调用即可。

### 2. 为什么 interrupt 要 checkpointer？

因为暂停后必须知道“刚才执行到哪一步、状态是什么”。checkpointer 就是 LangGraph 的存档点。

### 3. Local Server 和普通 Python 脚本有什么区别？

普通脚本适合学习和本地调试；Local Server 会把图暴露成 HTTP API，并可接入 Studio 做可视化调试。

## 官方参考

- https://docs.langchain.com/oss/python/langgraph/install
- https://docs.langchain.com/oss/python/langgraph/quickstart
- https://docs.langchain.com/oss/python/langgraph/local-server
- https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph
- https://docs.langchain.com/oss/python/langgraph/workflows-agents
