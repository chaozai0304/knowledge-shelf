# CLAUDE.md

本文件为 Claude / Claude Code 在本仓库中的工作约定。这里是 chao 的 AI 学习与分享知识库平台，所有工作都应服务于“可沉淀、可浏览、可分享、可复用”。

## 项目定位

- 这是一个以 AI 工程、Agent、研发管理、需求工程和知识分享为核心的内容型知识库。
- `output/index.html` 是本地学习门户，负责承载最终可访问入口。
- 生成内容时不要只写草稿，要同时考虑发布形态、目录入口和读者学习路径。

## 必须遵守

- 默认中文写作，风格自然、专业、信息密度高，避免空泛套话。
- 保持原创表达；对外部资料进行理解、重组和转述，不复制大段原文。
- 用户提供 URL 时，必须先读取网页内容，再基于资料进行整理。
- 新增可分享文档时，必须同步更新 `output/index.html`。
- 新增文档默认需要生成微信/知识库友好的 HTML 成品页。

## 文档新增流程

当用户要求新增课程、文章、分享稿、规范文档、案例库或实战手册时：

1. 明确文档所属主题和输出目录。
2. 生成 Markdown 源文档，必要时补充图片、图表或示例代码。
3. 使用 `.github/skills/knowledge-page-publisher` 中的发布流程生成 HTML。
4. 在 `output/index.html` 的 `catalog` 中新增入口。
5. 验证新增 HTML 文件存在，并能从首页打开。

## 关于首页目录

- `output/index.html` 的 `catalog` 是当前可靠的导航来源。
- 不建议纯靠文件扫描自动生成目录，因为标题、分组和简介需要人工语义判断。
- 如果新增一组配套文档，例如主文档、示例库、转化手册，应分别添加入口。

## 发布 Skill

- 当前发布 skill 名称：`knowledge-page-publisher`。
- 路径：`.github/skills/knowledge-page-publisher/SKILL.md`。
- 首页目录与内容编目 skill：`content-catalog-curator`，路径为 `.github/skills/content-catalog-curator/SKILL.md`。
- 任何“生成文档 / 格式化文档 / 转 HTML / 公众号排版 / 新增分享页 / 更新知识库入口”任务，都应触发对应 skill。
- 旧版 skill 名称不再使用，避免恢复旧目录或旧引用。

## 验收标准

- 内容完整，读者能直接学习和使用。
- Markdown 与 HTML 路径清晰。
- 首页入口可见、可点击、路径正确。
- 不留下过期 skill 名称或错误作者信息。
