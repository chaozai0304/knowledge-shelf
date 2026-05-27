---
name: content-catalog-curator
description: "Use when: 整理 Frontmatter、维护文章元数据、规划知识库目录、更新 output/index.html、检查新增内容入口、为文档补标题摘要标签。负责让内容可检索、可浏览、可维护。"
argument-hint: "<文档路径/目录/新增内容说明>"
user-invocable: true
metadata:
  author: chao
---

# Content Catalog Curator

`content-catalog-curator` 是知识库目录策展器。它负责元数据、分类、首页入口和内容可发现性，让新增文档不是散落在文件夹里，而是进入知识库导航体系。

## 适用场景

- 新增了 Markdown 或 HTML，需要补充首页入口。
- 文档缺少 title、summary、tags、author、date。
- 需要整理一组文档的分组和阅读顺序。
- 需要检查 `output/index.html` 中路径是否存在。
- 用户要求“整理目录”“更新首页”“补 Frontmatter”。

## 工作内容

### 1. Frontmatter 整理

为 Markdown 补齐或规范：

- `title`
- `author`
- `date`
- `tags`
- `summary`
- `cover`

### 2. 首页入口维护

更新 `output/index.html` 的 `catalog`：

- 选择合适分组。
- 写清楚标题和简介。
- 使用相对于 `output/index.html` 的路径。
- 一组配套文档要分别挂入口。

### 3. 目录策展

为专题或课程设计阅读顺序：

- 入门
- 核心概念
- 实战案例
- 进阶手册
- 参考资料

### 4. 自检

- 路径是否存在。
- 首页是否可见。
- 点击是否能打开。
- 文档标题和简介是否准确。

## 自动识别边界

可以用脚本辅助发现新文件，但不要完全依赖文件名生成首页目录。分组、标题、简介和阅读顺序需要语义判断。

## 与其他 skill 的配合

- 发布 HTML 使用 `knowledge-page-publisher`。
- 写文章使用 `article-architect`。
- 清理文本使用 `clean-tone-editor`。
