---
title: Jev × Qwen Flash 非思考模式五子棋对战：本机启动与实现
author: chao
date: 2026-09-23
tags:
  - Jev
  - Qwen
  - 五子棋
  - 模型对战
summary: 本地网页切换人类对 Jev、人类对 Qwen，以及 Jev 对 Qwen；介绍网关、密钥设置、服务端调用与验证边界。
cover: gomoku-cover.svg
---

## 能做什么

新增的增强对战网页是一个**需要本地服务的 HTML 页面**，与旧的 Jev 单模型五子棋页面并存。支持三种模式：人类 vs Jev、人类 vs 平台模型、Jev vs 平台模型。平台默认改用 `qwen3.7-flash-non-thinking`：你的模型广场将它单独列为可用模型；这是通过模型路由关闭思考，而不是在提示词里请求“不要思考”。前两种可选择人类或模型执黑；最后一种可选择 Jev 或平台模型执黑。**黑棋永远先行**，页面标签会显示实际使用的模型 ID。

TypeSafe 的 Jev 使用其 System One `Choice` 接口，在所有合法空格中选择；平台模型使用 **enjoy API / New API** 网关的 OpenAI 兼容 `POST /v1/chat/completions`。平台请求默认带 `response_format: {"type":"json_object"}`，提示词要求最终回复仅为 `{"move":"r07c07"}`；服务端只接受**唯一 `move` 字段的 JSON 对象**，并核实该坐标为空位；纯坐标、说明文字和代码围栏都不会落子。`qwen3.7-flash-non-thinking` 默认 `max_tokens=48`；其它模型默认 2048。**JSON 模式只约束最终回答格式，不能阻止推理模型在隐藏 reasoning 阶段用完预算**；如果 `finish_reason=length` 且最终内容为空，依然不会落子。模型不支持该模式时可在启动前设置 `PLATFORM_JSON_MODE=0`，但仍须返回单字段 JSON。网关支持此字段的规范不代表每条上游模型路由都支持，需按实际调用验证。

> 已核实：[你的模型广场](http://自己的模型ip:端口/pricing?search=qwen3.7-flash)分别列出 `qwen3.7-flash` 和 `qwen3.7-flash-non-thinking`；[New API 官方文档](https://docs.newapi.pro/zh/docs/api/ai-model/chat/openai/createchatcompletion)确认 Chat Completions 的 `model`、`messages`、Bearer 认证和 `choices[0].message.content`。通用文档未证实这个网关会透传 `enable_thinking: false`，因此采用明确的非思考模型 ID。**Qwen 在线调用及双模型真实对局未在此修改中实测**；本地测试使用模拟返回，不能当作实测延迟或棋力。网关为内网 HTTP，只适合可信网络。

## 启动：由你在本机设置两把 Key

1. 在 Bash 终端切换仓库：`cd 自己本地仓库地址`。
2. **只玩人类 vs Qwen** 时，仅配置 `PLATFORM_API_KEY`；如需 Jev 或双模型对战，还需 `TYPESAFE_API_KEY`。以下命令会在终端**隐藏输入**，不要把真实 Key 写到命令行参数、网页或文档中：

```sh
read -rs -p '输入平台 API Key: ' PLATFORM_API_KEY; echo
export PLATFORM_API_KEY
# 如需 Jev，再执行：
read -rs -p '输入轮换后的 TypeSafe API Key: ' TYPESAFE_API_KEY; echo
export TYPESAFE_API_KEY
python3 docs/courses/agents/jev-ticket-triage/enhanced_server.py
```

3. 浏览器打开 `http://127.0.0.1:8767/`（不是直接双击静态 `arena.html`），选择模式并点击“开始新局”。人机模式点击空格，网页自动请求模型应手；双模型模式点击“AI 走一步”逐手查看，或点“自动对战”连续运行。自动对战会调用**两个付费模型**，注意用量。
4. 结束时在终端按 Ctrl+C，并用 `unset PLATFORM_API_KEY TYPESAFE_API_KEY` 清除当前终端的环境变量。服务只监听 `127.0.0.1`，不会将 Key 发往浏览器。不要对外暴露端口。你之前在聊天里披露过 TypeSafe Key，建议先在控制台轮换。

默认网关为 `http://自己的模型ip:端口`，默认模型 ID **`qwen3.7-flash-non-thinking`**。若旧启动命令中已有 `PLATFORM_MODEL=qwen3.7-flash`，为避免继续走思考版，服务端也会将它映射到 `qwen3.7-flash-non-thinking`。若设置其它 `PLATFORM_MODEL`（包括其它厂商模型），会原样使用其 ID，**不能保证那种模型也关闭思考**；请为其配置明确的非思考模型路由。服务支持 `PLATFORM_BASE_URL` 指向可信的 HTTPS 反代。修改环境变量后须**重启 Python 服务**，仅刷新网页不能更换已启动进程的模型设置。

### 从 DeepSeek 推理模型切到非思考模型

你平台的[模型广场](http://自己的模型ip:端口/pricing?search=non-thinking)列有 `qwen3.7-flash-non-thinking` 和 `qwen3.6-flash-non-thinking`。**优先试前者**：它是本程序默认的平台模型。先在正在运行服务的终端按 Ctrl+C 停止，再启动新进程：

```sh
# 先在当前终端安全配置好 PLATFORM_API_KEY；若要 Jev 对战，还需 TYPESAFE_API_KEY。
cd '自己本地仓库地址'
PLATFORM_MODEL='qwen3.7-flash-non-thinking' python3 docs/courses/agents/jev-ticket-triage/enhanced_server.py
```

不要在同一启动命令中继续写 `PLATFORM_MODEL='origin-deepseek-v4-flash'`，也**不要保留 `PLATFORM_MAX_TOKENS=8096`**：程序只允许 32～4096。若此前已在终端 `export PLATFORM_MAX_TOKENS`，先运行 `unset PLATFORM_MAX_TOKENS`，以恢复非思考模型默认的 48。`qwen3.7-flash-non-thinking` 是否对你的平台 Key 开放，仍以调用返回为准；若返回权限或模型不可用，再试 `qwen3.6-flash-non-thinking`。切换后在浏览器“开始新局”，查看右侧实际平台模型 ID 和终端的 `PLATFORM_RESULT`。

### `origin-deepseek-v4-flash` 返回了却不落子？

你提供的那次日志为 `finish_reason=length`、`content_length=0`、`completion_tokens=512`、`reasoning_tokens=512`。**确定的事实是：那次请求的 512 个输出 token 全部用于推理，未产生可落子的最终 `message.content`**；不是网页漏画，也不能从 `reasoning_content` 猜坐标。当前源码已经给其它平台模型默认 `max_tokens=2048`，但你的 512 日志可能来自旧进程或设置过 `PLATFORM_MAX_TOKENS=512`；仅凭该日志**不能断言 2048 也不够**。必须停止旧进程并重启后观察新的 `PLATFORM_RESULT` 中 `requested_model`、`requested_max_tokens`、`finish_reason`、`reasoning_tokens` 与 `content_length`（不包含 Key、回复正文或推理内容）。新版出现输出耗尽时，网页会显示本次实际预算和重试建议。若在 2048 时仍耗尽，再考虑加到 4096：

**后续回合更慢是否是提示词变长？**沿相同请求构造路径重放：改动前，首手请求约 2819 字节（224 个空位 ID），后续一个 3 子局面约 2805 字节（222 个空位 ID）。输入并未随回合增长；旧提示中重复列出了整盘棋与全部空位坐标，还要求“强力进攻/防守”，可能鼓励推理模型花更多 token 推演。已将平台模型请求缩为**15 行棋盘 + 简明规则 + 单字段 JSON 输出约束**，不再重复 200 多个空位 ID；相同两种局面请求均约 **818 字节**。服务端仍独立验空位、四方向成五及必胜/必防。缩短输入不保证关闭模型的隐藏推理；**新版第二手尚未在你平台完成在线实测**，需重启服务后检查 `PLATFORM_RESULT` 的实际数值。

```sh
# 两把 Key 请在本机终端安全设置，下面只展示非敏感配置。
PLATFORM_MODEL='origin-deepseek-v4-flash' PLATFORM_MAX_TOKENS=4096 python3 docs/courses/agents/jev-ticket-triage/enhanced_server.py
```

**如果在 4096 仍出现 `finish_reason=length`、最终 `content` 为空**：这表示该次请求在 4096 的预算内没有生成最终坐标，不能再照旧提示“把预算调到 4096”。新版提示会明确告知已经到程序上限。请结合终端的 `PLATFORM_RESULT` 核对 `reasoning_tokens`：若接近或等于 `completion_tokens=4096`，说明本次额度主要被隐藏推理占用；仅凭网页错误**不能断言两者必定相等**。不要从 `reasoning_content` 抽坐标替代最终答案。优先尝试可调用的非思考模型路由，或让网关管理员确认该模型是否提供可靠的关闭思考能力；修改模型后停止旧服务并重新启动。

`PLATFORM_MAX_TOKENS` 仅允许 32～4096；调高可能增加费用与延迟，仍不保证得到坐标。模型广场也列有 `deepseek-v4-flash-wot`；如果想试这条 DeepSeek 路由，可以在重启服务前显式设置模型 ID，但**平台没有说明 `wot` 的行为，不要把它当成已经验证的非思考模型**：

**只要一个 JSON 坐标时，为何生成量还会变大？**`max_tokens` 和账单里的 completion tokens 可包含看不见的 `reasoning_tokens`。新版请求使用 `response_format=json_object` + 单字段提示词；若终端的 `reasoning_tokens` 仍接近 `completion_tokens`，说明并非最终 JSON 变长，而是上游推理模式持续消耗额度。应切换非思考路由或请网关管理员验证关闭思考的支持情况，不能用提示词保证关停。

```sh
# 已在当前终端安全设置 PLATFORM_API_KEY（以及需要时的 TYPESAFE_API_KEY）后：
PLATFORM_MODEL='deepseek-v4-flash-wot' python3 docs/courses/agents/jev-ticket-triage/enhanced_server.py
```

这会**切换模型路由**，不是仍使用 `origin-deepseek-v4-flash`；你的 Key 能否调用，以及该路由是否真正省掉推理，仍须观察返回的 `reasoning_tokens` 和延迟。请先停止旧服务再重启，刷新网页不会更新运行中的 Python 代码；若已有一盘黑子，可在新服务里重新开局。切勿从 `reasoning_content` 取坐标，它可能仅是中间推理。

## 发给两个模型的内容

Jev 侧沿用 `gomoku.py` 的 `choose_move()`：`state` 携带 `. / X / O` 的完整 15 行棋盘、动态黑白身份、当前轮次和完整的**本游戏规则**：黑先白后、每手仅能下一个空位、不可移子/吃子、横竖和两条斜线连续至少五子即胜（长连也胜）、满盘无胜为和棋、无禁手及无开局限制，说明坐标从 0 起而候选文字从 1 起。`state.strategy` 另外说明活三/活四、断点连线、多方向双威胁与攻防取舍，强调局部连续线提示不等于搜索或胜负保证；即使对手是平台模型也不会错误地称为“人类”。`questions.next_move.criteria` 包含**全部空位**及代码计算的最长连续线/开放端提示。一步必胜与必防由代码直接处理，不伪装成 Jev 的决策；其他回合模型返回选点和全量概率分布，落点仍由服务端校验。修改提示词后需重启本地 Python 服务才能生效；战术说明更完整不等于已经证明棋力提高。

**要看实际发给自有平台的完整 body：**重新启动 `enhanced_server.py` 后，在网页让平台模型走一步，启动服务的终端会先输出 `PLATFORM_REQUEST`，下一段就是**缩进格式化的完整 JSON 请求体**（包含实际 `model`、`messages`、`max_tokens` 和 `response_format`）；返回后再输出 `PLATFORM_RESULT` 的非敏感摘要。打印的 body 与真正 POST 的字节内容来自同一个对象，已在模拟 HTTP 测试中逐字段核对。**不会打印 Bearer 令牌或请求头。**棋盘和 system/user 提示词本身会完整出现在终端，请不要在提示中放真实用户数据，也不要直接分享含敏感数据的终端截图。程序规则直接必胜/必防的回合不调用平台，因此不会打印 `PLATFORM_REQUEST`。

Qwen 侧的主要请求逻辑在 `enhanced_match.py`，下面是页面内直接可读的核心代码（省略了异常与校验分支，不能单独运行）：

```python
rows = "\n".join(f"{r:02d} {''.join('.XO'[cell] for cell in line)}"
                 for r, line in enumerate(board))
messages = [
  {"role": "system", "content": "15x15 Gomoku: X is black and moves first; O is white. Five in a row wins. Choose one empty cell (.) on the board. Reply only with JSON {\"move\":\"rXXcYY\"} using zero-based row and column 00..14."},
  {"role": "user", "content": f"You are {symbol}; opponent is {other}. Select one empty cell for your next move. Board (each row labelled 00..14):\n{rows}"},
]
body = {"model": "qwen3.7-flash-non-thinking", "messages": messages,
  "stream": False, "temperature": 0, "max_tokens": 48,
  "response_format": {"type": "json_object"}}  # 其他模型默认 2048
# 后端向 {PLATFORM_BASE_URL}/v1/chat/completions POST，授权头为 Bearer $PLATFORM_API_KEY。
# 仅接受单字段 JSON {"move":"rXXcYY"}，且必须是当前空位。
```

模型对战不是让一个模型在提示里模拟另一个模型：**每回合依据执黑/执白调用对应的真实 Provider**。重要的调用链：

```python
match.reset(mode="jev_qwen", jev_first=True)
match.ai_step()  # Jev（黑）通过 System One Choice 选一步
match.ai_step()  # Qwen（白）通过你平台的 Chat Completions 选一步
```

配套可运行文件在同目录：`enhanced_match.py`（双模型规则与调用）、`enhanced_server.py`（本地 HTTP 服务）、`arena.html`、`arena.js`、`arena.css`、既有的 `gomoku.py`、`triage.py`。文章中的代码展示关键请求形状；**要启动 HTML 游戏需要完整源码文件**。两个 Key 只从服务端环境变量读取，服务端返回网页的是模型落点、置信度（仅 Jev Choice 提供）、token 用量与胜负状态。

## 验证边界

使用标准库，无需安装额外 Python 包。运行项目全部本地测试：

```sh
python3 -m unittest discover -s docs/courses/agents/jev-ticket-triage -p 'test_*.py'
```

离线测试覆盖三种模式、双方先手、非法坐标、HTTP 跨站请求和模型失败不推进棋盘。**不要把通过模拟接口的测试说成你的平台已经联通**；实际调用成功与成本需在你设置平台 Key 后，在浏览器观察返回。如果出现错误，请先确认平台 Key 可调用 `qwen3.7-flash-non-thinking`，以及本机能访问 `自己的模型ip:端口`。