---
name: share-doc-publisher
description: "Use when: 新增分享文档、生成知识库文章、Markdown 转微信/知识库 HTML、公众号排版、发布课程页面、更新 output/index.html 入口。This skill publishes original Markdown documents as chao-style shareable HTML and reminds agents to update the knowledge-base catalog."
argument-hint: "<input markdown> [output html]"
user-invocable: true
metadata:
  author: chao
---

# Share Doc Publisher Skill

本 skill 是 chao 知识库平台的分享文档发布工作流。它不只是把 Markdown 转成 HTML，还负责提醒 Agent 完成首页入口、资源路径和发布自检。

## 什么时候必须使用

当任务包含以下任意场景时，必须自动使用本 skill：

- 新增课程、文章、分享稿、规范文档、案例库、实战手册。
- 将 Markdown 转成微信/知识库友好的 HTML。
- 用户提到“公众号排版”“微信格式”“分享页”“HTML 成品页”。
- 在 `output/` 下新增可分享文件。
- 需要更新 `output/index.html` 首页目录。

## 输出目标

把一份原创 Markdown 文档发布成同时适合本地知识库浏览和微信公众号复制的 HTML：

- 标题、段落、列表、引用、代码块和表格都有统一样式。
- 图片会尽量转成 Base64，减少分享时的资源丢失。
- 默认作者为 `chao`，也支持从 Markdown frontmatter 读取 `title`、`author`、`date`、`cover`、`tags`。
- 输出页面遵循 chao 的科技蓝紫视觉风格。

## 标准流程

1. **确认源文件**：定位要发布的 `.md` 文件。
2. **确认输出路径**：HTML 通常与 Markdown 同目录，命名建议使用 `*-wechat.html` 或清晰的主题名。
3. **生成 HTML**：运行本 skill 的脚本。

   ```bash
   node .github/skills/share-doc-publisher/scripts/format.js <input-md> <output-html>
   ```

4. **同步首页**：如果输出文件位于 `output/` 下且是可分享文档，必须更新 `output/index.html` 的 `catalog`。
5. **自检入口**：确认 HTML 文件存在、图片正常、首页入口可见且能打开。

## `output/index.html` 更新规则

新增分享文档后，必须为每个可独立阅读的 HTML 添加入口：

- `group`：所属分组，例如 `LangGraph 系列`、`工程标准`、`Agent 工具与 Skills`。
- `title`：读者看到的标题，短而明确。
- `desc`：一句话说明读者能学到什么。
- `path`：相对于 `output/index.html` 的路径。

如果新增的是一组文档，例如主文档、示例库、实战手册，不要只添加总入口，应分别添加入口。

## 为什么不默认全自动扫描目录

文件名无法稳定表达分组、学习顺序和内容价值。当前以人工维护 `catalog` 为准；可以用脚本辅助检查文件是否存在，但不要用纯自动扫描替代目录策展。

## 原创与质量要求

- 输出必须是原创组织和原创表达，不拼贴、不搬运。
- 如果基于外部资料，要重组结构、转述观点，并保留必要来源。
- 面向学习者写作：先解释概念，再给操作步骤，最后给示例和避坑。
- 简单需求讲清楚，复杂场景拆开讲，不用空泛标题堆内容。

## 样式能力

脚本基于 `marked` 解析 Markdown，并注入内联样式：

- 容器：最大宽度 667px，适合微信公众号正文区域。
- 字体：优先使用 `MiSans` 与系统中文字体。
- 二级标题：渐变图标、柔和底色、强调色竖条。
- 三级标题：星形图标与渐变下划线。
- 四级标题：胶囊徽章样式。
- 段落：15px、较高行距，适合长文阅读。
- 引用：浅灰背景、蓝紫色左边框。
- 列表：自定义蓝色项目符号。
- 代码：深色代码块，适合技术文档。
- 标签：文章末尾标签胶囊。

## 验证清单

- HTML 文件已生成。
- 页面标题、作者、日期正确。
- 图片路径或 Base64 正常。
- `output/index.html` 已同步新增入口。
- 本地首页能打开新增页面。
