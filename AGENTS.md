# 分享文档库 Agent 工作规范

本仓库是 chao 的 AI 学习与分享知识库平台。所有 Agent 在本仓库工作时，目标不是只生成一个孤立文件，而是产出可沉淀、可浏览、可分享、可继续维护的知识库内容。

## 核心原则

- 默认使用中文输出，表达要清楚、克制、专业，优先给结论和可执行建议。
- 新增内容必须优先保持原创表达；引用外部信息时要转述、消化、注明来源，不直接搬运长段原文。
- 所有可分享文档都要同时考虑 Markdown 源文件、HTML 分享页、图片资源、首页入口和后续维护。
- 不为了炫技引入复杂自动化。目录入口以 `output/index.html` 的 `catalog` 为权威清单。

## 文档发布强制流程

当新增、改写或发布任何面向分享的文档时，包括课程、分享稿、规范、报告、案例库、实战手册、HTML 成品页，必须执行以下流程：

1. 规划输出位置，优先放在 `output/courses/`、`output/assets/`、`content/articles/` 等已有结构下。
2. 生成或更新 Markdown 源文档。
3. 自动触发 `.github/skills/knowledge-page-publisher` skill，将 Markdown 转成适合微信/知识库浏览的 HTML。
4. 如果新增了 `output/` 下的可分享文档，必须同步更新 `output/index.html` 的 `catalog`。
5. 若新增的是一组配套文档，必须分别在首页提供入口，不只挂一个总入口。
6. 自检 HTML 文件存在、相对路径可访问、首页能打开对应页面。

## `output/index.html` 维护规则

- `output/index.html` 是知识库首页和导航入口，新增分享文档后必须更新。
- 每个入口至少包含：`group`、`title`、`desc`、`path`。
- 自动扫描文件名无法可靠判断分组、标题和简介，因此不要用纯自动发现替代人工维护 `catalog`。
- 如果未来新增脚本辅助生成目录，也必须先保留人工可读、可审查的 `catalog` 结构。

## Skill 使用约定

- 文档新增、文档排版、微信公众号 HTML、分享页生成、知识库发布任务，都必须优先使用 `.github/skills/knowledge-page-publisher`。
- 首页分组、Frontmatter、路径校验和内容编目任务，优先使用 `.github/skills/content-catalog-curator`。
- 当前原创 skill 体系包括：`article-architect`、`clean-tone-editor`、`insight-forge`、`media-insight-lens`、`cover-art-studio`、`visual-explainer`、`knowledge-page-publisher`、`content-catalog-curator`。
- 旧版 skill 名称已废弃；后续不要再创建、引用或恢复旧目录。

## 验证要求

- 修改 Markdown/HTML/JS 后，至少检查相关文件是否存在且无明显语法错误。
- 修改 `output/index.html` 后，应打开页面或检查 DOM，确认新增分组和入口可见。
- 新增路径必须使用相对于 `output/index.html` 的相对路径。

## 文件组织建议

- `content/`：创作源稿、文章素材和长期内容资产。
- `output/`：最终可分享、可浏览、可发布的产物。
- `output/assets/`：跨文档共用资源。
- `output/courses/`：课程、专题、系列化知识文档。
- `.github/skills/`：面向 Agent 的专业工作流能力。
