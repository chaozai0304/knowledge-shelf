---
name: knowledge-page-publisher
description: "Use when: 新增分享文档、发布知识库页面、Markdown 转微信/知识库 HTML、公众号排版、发布课程页面、更新 output/index.html。负责把原创 Markdown 发布成 chao 风格 HTML，并同步维护首页入口。"
argument-hint: "<input markdown> [output html]"
user-invocable: true
metadata:
  author: chao
---

# Knowledge Page Publisher

`knowledge-page-publisher` 是知识库页面发布器。它负责把 Markdown 变成可浏览、可分享、可复制到公众号的 HTML，并确保新增页面能从 `output/index.html` 找到。

## 必须触发的场景

- 新增课程、分享稿、规范文档、案例库、实战手册。
- 用户要求“转 HTML”“公众号排版”“发布成网页”“加入知识库”。
- 在 `output/` 下新增可分享 HTML。
- 更新或新增知识库首页入口。

## 发布流程

1. **确认源稿**：找到 Markdown 源文件。
2. **确认输出路径**：优先与源文件同目录，命名清楚。
3. **生成 HTML**：运行发布脚本。

```bash
node .github/skills/knowledge-page-publisher/scripts/format.js <input-md> <output-html>
```

4. **同步首页**：如果输出在 `output/` 下，必须更新 `output/index.html` 的 `catalog`。
5. **验证可访问**：检查 HTML 存在、图片正常、首页入口可点击。

## 首页目录规则

每个入口至少包含：

- `group`：所属分组。
- `title`：短标题。
- `desc`：一句话说明价值。
- `path`：相对于 `output/index.html` 的路径。

如果新增的是一组文档，例如主文档、示例库、转化手册，应分别提供入口。

## 为什么不默认自动扫描

首页不是文件列表，而是学习路径。文件名无法判断内容分组、标题质量、阅读顺序和简介。当前以人工维护 `catalog` 为准；可以用脚本辅助校验路径存在，但不要用纯扫描替代策展。

## HTML 样式能力

发布脚本会处理：

- Markdown frontmatter：`title`、`author`、`date`、`cover`、`tags`。
- 图片 Base64 内嵌。
- 公众号友好的内联样式。
- 标题、段落、列表、引用、表格、代码块。
- chao 风格的蓝紫科技感排版。

## 验收清单

- Markdown 源文件存在。
- HTML 已生成。
- 图片能正常显示。
- `output/index.html` 已新增或更新入口。
- 从首页点击能打开目标页面。
