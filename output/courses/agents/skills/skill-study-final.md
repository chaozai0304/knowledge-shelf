---
title: "把 Claude / VS Code Skills 用起来：从安装、创建到实战，一篇讲明白"
source: "【agent工具】SKILL学习笔记.docx"
created: 2026-04-12
tags:
  - Claude
  - VS Code
  - Skills
  - AI工具
  - 微信公众号
---

# 把 Claude / VS Code Skills 用起来：从安装、创建到实战，一篇讲明白

如果你已经在用 Claude、GitHub Copilot 或 VS Code Agent 功能，那你迟早会遇到一个关键词：**Skills**。

很多人第一次接触 Skills，会觉得它像“提示词模板”；但真正用起来你会发现，它更像是**把经验、流程、工具和最佳实践打包成可复用能力模块**。一旦配好，后面很多复杂任务都能直接一句话调用，效率非常夸张。

这篇文章基于原始学习笔记重新整理，做了三件事：

- 修正原文里的错别字、术语不统一和部分过时表达
- 按公众号阅读习惯重构结构，适合直接分享或二次排版
- 保留关键截图，方便你边看边照着操作

---

## 一、Skills 到底是什么？

一句话理解：

> **Skill 就是一个带说明书的能力包。**

它通常是一个目录，最核心的文件叫做 `SKILL.md`。这个文件里会写清楚：

- 这个 Skill 叫什么
- 适合在什么场景下使用
- 该怎么执行任务
- 需要参考哪些模板、脚本或资料

一个典型的 Skill 目录长这样：

```text
my-skill/
├── SKILL.md        # 必需：说明书 + 元数据
├── scripts/        # 可选：脚本
├── references/     # 可选：参考资料
└── assets/         # 可选：模板、资源文件
```

也就是说，**Skill 不是一句孤立的 Prompt，而是一套完整的工作方法封装**。

---

## 二、先在 VS Code 里把 Skills 打开

如果你准备在 VS Code 里使用 Agent / Skills，第一步通常是先启用相关开关。

### 1）打开相关设置

在设置里启用 `Use Agent Skills`。

![](skill-study-final_assets/media/image1.png)

### 2）创建或选择一个智能体

原始笔记里这一段是多张连续截图，我这里合并理解一下：核心就是先把 Agent 功能准备好，再让它具备调用 Skills 的能力。

![](skill-study-final_assets/media/image2.png)

![](skill-study-final_assets/media/image3.png)

![](skill-study-final_assets/media/image4.png)

![](skill-study-final_assets/media/image5.png)

> 小提醒：不同版本的 VS Code、Copilot Chat 或 Claude Code，界面名称可能略有差异，但思路基本一致——**先打开 Agent 能力，再让 Agent 能读取并使用 Skills**。

---

## 三、一个 Skill 的核心文件：`SKILL.md`

原始笔记这部分信息很重要，但排版比较散。我帮你归纳成最关键的 3 点。

### 1）`SKILL.md` 一定要有元数据

通常最少要包含：

```yaml
---
name: pdf-processing
description: Extract text and tables from PDF files, fill forms, merge documents.
---
```

其中：

- `name`：Skill 的唯一标识，尽量短、清晰、可搜索
- `description`：告诉 Agent **什么时候应该使用这个 Skill**

### 2）正文部分就是“操作说明书”

元数据下面通常就是 Markdown 正文，用来告诉 Agent：

- 遇到什么问题时触发
- 执行步骤是什么
- 输出格式是什么
- 需要调用哪些脚本、模板或资料

### 3）为什么 Skill 这么有用？

因为它同时具备这几个优点：

- **自解释**：别人直接看 `SKILL.md` 就知道这个 Skill 干什么
- **可扩展**：既能只写文字说明，也能配脚本、模板、参考资料
- **可移植**：本质上就是文件夹，便于版本控制和共享

---

## 四、最小可用示例：一个代码审查 Skill

原始笔记里给了一个非常长的 `code-reviewer` 示例。它的价值不在于“字多”，而在于它展示了一个成熟 Skill 应该包含哪些结构。

一个好用的代码审查 Skill，至少应该写清楚：

- 输入是什么
- 输出是什么
- 评分维度有哪些
- 审查流程怎么走
- 报告格式如何生成

比如下面这种结构就很标准：

```yaml
---
name: code-reviewer
description: 用于代码审查、质量分析、风险识别和报告生成。
---
```

正文里再补充：

- 审查重点：代码质量 / 安全性 / 性能 / 可维护性
- 输出格式：文本报告 + HTML 报告
- 严重度分级：Critical / Medium / Minor
- 报告落地方式：保存文件并自动预览

### 为什么这个例子值得参考？

因为它说明了一件事：

> **真正强的 Skill，不是“你帮我看看代码”，而是“把任务流程、评分标准、输出模板全部固定下来”。**

这样一来，后续你每次只要说一句“帮我审查这段代码”，Agent 就能稳定地产出你想要的格式和质量。

---

## 五、测试效果：Skill 不是纸上谈兵

原始笔记里放了测试截图，这部分其实是在证明：Skill 配好之后，Agent 输出会更稳定，也更接近你想要的工作流。

![](skill-study-final_assets/media/image6.png)

![](skill-study-final_assets/media/image7.png)

如果你之前觉得 AI 工具“有时聪明、有时跑偏”，那大概率不是模型不行，而是**你没有把任务流程标准化**。Skill 的意义，正是在这里。

---

## 六、怎么安装和管理 Skills？

这一段原文混用了 `openskills` 和 `npx skills` 两套写法。为了避免误导，我这里做一个更稳妥的修正：

- **如果你使用的是当前较新的 Skills CLI，优先参考 `npx skills` 系列命令**
- 原笔记中的 `openskills` 写法更像早期/旁支方案，是否适用请以你当前环境为准

### 1）原笔记记录过的安装方式

```bash
npm i -g openskills
cd skill-group
openskills install anthropics/skills
```

对应截图如下：

![](skill-study-final_assets/media/image8.png)

![](skill-study-final_assets/media/image9.png)

### 2）生成技能目录

原笔记里提到可以生成 `agents.md` 之类的目录索引：

```bash
openskills sync
```

![](skill-study-final_assets/media/image10.png)

### 3）更推荐记住的通用思路

如果你使用的是较新的 Skills CLI，常见命令通常是：

```bash
npx skills find react
npx skills add <包名或仓库地址>
npx skills check
npx skills update
```

这里最重要的不是某一个命令，而是理解这件事：

> **Skills 可以像“能力插件”一样被查找、安装、更新和复用。**

---

## 七、实战：直接让 Skill 帮你生成页面

原始笔记给的实战指令非常有代表性：

```text
根据 .claude/skills/frontend-design 的 skill，
生成一个贪吃蛇的前端页面游戏，要足够炫酷高大上，功能齐全。
```

![](skill-study-final_assets/media/image11.png)

这类场景特别适合 Skill，因为它对输出质量要求很高：

- 不只是“能跑”
- 还要有设计感
- 还要有完成度
- 还要符合某种风格

如果没有 Skill，AI 很容易给你一个“能交差但不惊艳”的结果；
如果有像 `frontend-design` 这种明确审美导向的 Skill，输出质量通常会明显提升。

---

## 八、`skill-creator`：自己动手做一个 Skill

如果说前面是在“使用别人的 Skill”，那 `skill-creator` 的意义就是：**把你自己的经验沉淀成 Skill。**

这一步非常关键，因为真正能拉开效率差距的，往往不是下载了多少 Skill，而是你有没有把自己的工作方法产品化。

### 1）在 Claude Code 里安装 `skill-creator`

打开 Claude Code，在对话框中执行类似命令：

```bash
npx skills add https://github.com/anthropics/skills --skill skill-creator
```

![](skill-study-final_assets/media/image12.png)

![](skill-study-final_assets/media/image13.png)

### 2）让它帮你创建第一个 Skill

你可以直接这样说：

```text
使用 skill-creator 帮我创建一个新的 Claude Skill。
目标是：写清楚我想让这个 Skill 解决什么问题。
```

原笔记中的示例是：

```text
使用 skill-creator 帮我创建一个新的 Claude Skill。
目标是：使用 Three.js 通过手势控制网页上的内容。
```

![](skill-study-final_assets/media/image14.png)

![](skill-study-final_assets/media/image15.png)

### 3）什么时候该自己写 Skill？

当你发现某类任务反复出现，并且你总要重复解释这些内容时，就该写一个 Skill 了。比如：

- 固定风格的代码审查
- 固定模板的周报 / 汇报 / 方案文档
- 固定流程的数据清洗与分析
- 固定风格的页面生成
- 固定规范的接口设计或测试生成

换句话说：

> **凡是你会重复做 3 次以上的高价值任务，都值得考虑做成 Skill。**

---

## 九、开源 Skills 资源从哪里找？

原始笔记后面整理了一批开源 Skills 项目，还提到了一些聚合站和电子表格。

这里我建议你分两类看：

### 第一类：官方或核心能力

![](skill-study-final_assets/media/image16.png)

### 第二类：实战型 Skills 清单

![](skill-study-final_assets/media/image17.png)

如果你只是刚开始接触 Skills，不要一上来就收藏几百个。**先找 3 个最贴近你工作流的 Skill，用熟再扩展。**

比如：

- 前端设计类：`frontend-design`
- 代码整理类：`code-simplifier`
- 自动化开发流程类：`ralph-loop`

---

## 十、几个常见误区，顺手帮你避坑

### 误区 1：Skill = 高级 Prompt

不完全对。

Prompt 更像一句临时指令；Skill 更像一个**可复用的工作系统**，里面可以包含：

- 触发场景
- 执行步骤
- 输出格式
- 参考资料
- 脚本和模板

### 误区 2：Skill 越长越好

也不对。

好的 Skill 不是越长越好，而是：

- 触发条件明确
- 指令边界清晰
- 输出格式稳定
- 示例足够有代表性

### 误区 3：装得越多越强

也不是。

Skills 的关键不是数量，而是**是否贴合你的日常工作**。真正有效的，一般都是高频、刚需、可复用的那几个。

### 误区 4：所有旧命令都依然通用

不一定。

AI 工具和 CLI 变化很快。看到旧笔记里的安装命令时，最好做两件事：

1. 先看官方当前文档
2. 再确认你本机环境是否支持

这样可以避免因为版本差异白白折腾半天。

---

## 十一、我建议你现在就做的 3 件事

如果你读到这里，最实用的落地动作其实只有 3 个：

### 1）先启用 Skills 功能

把入口打开，比收藏十篇教程更重要。

### 2）先安装 1~3 个最常用的 Skill

别贪多，先选与你最相关的：

- 写代码多：装代码审查、代码简化、测试生成相关 Skill
- 做前端多：装设计、美化、交互类 Skill
- 写文档多：装总结、改写、结构化输出类 Skill

### 3）把你最常重复的一件事，做成自己的 Skill

这是收益最高的一步。

只要你做成一个真正可复用的 Skill，后面的时间节省会是指数级的。

---

## 结语

过去我们总把 AI 当成“会聊天的工具”；
但当你开始使用 Skills 之后，它更像是一个**会按你的工作方式办事的协作系统**。

这也是为什么越来越多高效团队开始重视 Skills：
它不是让 AI 更会说，而是让 AI **更稳定地做事**。

如果你准备把 AI 真正用进工作流，Skills 是非常值得尽快补上的一课。

> 如果你愿意，下一步最值得做的不是继续看教程，而是：**亲手写出你的第一个 Skill。**

---

## 附：本文顺手修正了哪些原始问题？

为了方便后续引用，我把这次整理中做过的修正也列一下：

- 把原文中大量零散截图说明，重构为按场景拆分的可读结构
- 修正了 `skill / Skill / Skills` 大小写混用问题
- 修正了部分错别字、病句和术语表述不统一的问题
- 把不适合公众号阅读的 HTML 表格、碎片段落改成了自然段与代码块
- 对 `openskills` 与 `npx skills` 的关系做了风险提示，避免直接照抄旧命令
- 删除了部分未经验证、容易引起误解的表达，保留更稳妥的通用结论
