# chao 知识库 Skills

这是一套面向 chao AI 学习与分享知识库的原创内容生产能力体系。它不是零散工具箱，而是一条从“资料输入 → 洞察形成 → 长文写作 → 视觉表达 → HTML 发布 → 首页编目”的知识库流水线。

## 使用方式

本仓库已将项目级 Skills 放在 `.github/skills/` 下。支持 Skills 的 AI 助手加载工作区后，会自动识别每个子目录中的 `SKILL.md`。

你可以直接用自然语言触发，例如：

- “把这段会议纪要整理成可写文章的素材包。”
- “围绕企业 AI 落地做一次深度洞察挖掘。”
- “把这篇 Markdown 发布成知识库 HTML，并更新首页入口。”
- “给这篇课程文档生成一张 900x363 封面图。”

> 每个子目录内都有独立 `SKILL.md`，其中包含触发场景、工作流、质量标准和必要命令。

## Skills 清单

| Skill | 能力定位 | 常见用法 |
| --- | --- | --- |
| `media-insight-lens` | 多媒体资料洞察镜头 | 从视频、播客、访谈、会议纪要或文字稿中提炼观点、案例、金句和可引用素材。 |
| `insight-forge` | 洞察锻造器 | 对一个主题进行苏格拉底式追问，形成非共识观点、论证链和文章地基。 |
| `article-architect` | 文章架构师 | 将主题、素材或洞察地基扩展为结构清晰、可分享的文章、课程或长文。 |
| `clean-tone-editor` | 清爽中文编辑器 | 去掉 AI 味、翻译腔和空泛套话，让中文表达更自然、克制、有信息密度。 |
| `cover-art-studio` | 封面视觉工坊 | 生成 900x363 知识库封面、课程头图和分享头图，保持统一视觉风格。 |
| `visual-explainer` | 视觉解释器 | 生成流程图、架构图、信息图和 HTML/CSS 可截图配图，用图解释复杂概念。 |
| `knowledge-page-publisher` | 知识页发布器 | 将 Markdown 发布为 chao 风格 HTML，适配知识库阅读与公众号排版。 |
| `content-catalog-curator` | 内容目录策展人 | 维护 Frontmatter、内容分组、首页 `catalog`、路径校验和知识库导航。 |

## 推荐协作流程

1. `media-insight-lens`：先把外部资料拆成观点、案例和证据。
2. `insight-forge`：对核心主题进行追问，提炼真正值得写的洞察。
3. `article-architect`：把洞察组织成完整文章、课程或分享稿。
4. `clean-tone-editor`：压缩套话，统一中文语气和表达密度。
5. `visual-explainer`：为关键模型、流程或架构补充可传播图示。
6. `cover-art-studio`：为正式发布内容生成统一封面。
7. `knowledge-page-publisher`：输出微信/知识库友好的 HTML。
8. `content-catalog-curator`：把新内容加入 `output/index.html`，并校验可访问性。

## 维护约定

- 新增或改名 Skill 时，目录名必须与 `SKILL.md` frontmatter 中的 `name` 保持一致。
- 作者信息统一写入 `metadata.author: chao`，不要使用顶层 `author` 字段。
- 所有面向分享的内容都要同时考虑 Markdown 源稿、HTML 成品、视觉资源和首页入口。
- 不依赖纯文件名扫描生成首页目录；`output/index.html` 中的 `catalog` 是人工策展后的权威入口。

---

Maintained by chao
