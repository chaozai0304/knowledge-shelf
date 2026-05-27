# chao AI 学习与分享知识库

这是 chao 用来沉淀 AI 工程、Agent、研发管理、需求工程和知识分享内容的本地知识库平台。仓库目标不是保存零散文件，而是持续产出可浏览、可分享、可复用、可维护的知识库资产。

## 快速入口

- 本地学习门户：`output/index.html`
- GitHub Pages 发布目录：`docs/`
- 最终发布产物：`output/`
- 创作源稿与素材：`content/`
- 文档处理工具：`tools/`
- Agent 工作规范：`AGENTS.md`、`CLAUDE.md`、`.github/copilot-instructions.md`
- 知识库生产 Skills：`.github/skills/`

## 目录结构

| 路径 | 用途 |
| --- | --- |
| `content/articles/` | 文章源稿、专题草稿和长期素材。 |
| `content/assets/` | 创作阶段使用的图片、素材和附件。 |
| `output/` | 最终可浏览、可分享、可发布的 HTML/Markdown 成品。 |
| `docs/` | GitHub Pages 发布目录，由 `output/` 同步生成。 |
| `output/courses/` | 系列课程、专题知识文档和实战手册。 |
| `output/assets/` | 发布产物共享资源。 |
| `tools/` | 文档转换、OCR、资料整理和校验脚本。 |
| `.github/skills/` | 面向 AI Agent 的项目级专业工作流能力。 |

## GitHub Pages 发布

当前仓库已采用 `docs/` 作为 GitHub Pages 发布目录。

你在 GitHub 仓库中将 Pages Source 设置为：

- Branch：`main`
- Folder：`/docs`

本地内容仍然以 `output/` 作为主产物目录；当 `output/` 更新后，执行下面的同步脚本即可刷新 GitHub Pages 发布目录：

```bash
bash tools/sync_docs.sh
```

同步完成后提交并推送：

```bash
git add docs README.md tools/sync_docs.sh
git commit -m "sync docs for GitHub Pages"
git push
```

## 新增文档流程

新增课程、文章、分享稿、规范、案例库或实战手册时，默认按以下流程处理：

1. 规划主题、读者和输出目录。
2. 生成或更新 Markdown 源文档。
3. 需要时补充封面、信息图、示例代码或配套资料。
4. 使用 `knowledge-page-publisher` 将 Markdown 发布为知识库/公众号友好的 HTML。
5. 如果新增内容位于 `output/`，同步更新 `output/index.html` 的 `catalog`。
6. 使用 `content-catalog-curator` 检查标题、分组、简介、路径和可访问性。

## Skills 能力体系

当前仓库内置 8 个原创 Skill：

- `media-insight-lens`：整理视频、播客、访谈、会议纪要等外部资料。
- `insight-forge`：通过追问和反证锻造深层洞察。
- `article-architect`：构建文章、课程和分享稿的结构与初稿。
- `clean-tone-editor`：去 AI 味，提升中文表达自然度和信息密度。
- `cover-art-studio`：生成知识库封面图和课程头图。
- `visual-explainer`：生成信息图、流程图和架构解释图。
- `knowledge-page-publisher`：发布 Markdown 为 chao 风格 HTML。
- `content-catalog-curator`：维护内容目录、Frontmatter 和首页入口。

详细说明见 `.github/skills/README.md`。

## 首页维护规则

`output/index.html` 是当前可靠的知识库导航入口，内部 `catalog` 是权威清单。新增 `output/` 下的可分享文档时，必须补齐：

- 分组
- 标题
- 简述
- 相对于 `output/index.html` 的访问路径

不建议纯靠文件扫描自动生成目录，因为分组、标题、简介和阅读顺序都需要语义判断。

## 内容标准

- 默认中文写作，表达自然、专业、克制。
- 保持原创表达；引用外部资料时要理解、转述并注明来源。
- 面向分享的内容应兼顾可读性、可操作性和后续维护。
- 不留下过期 skill 名称、错误作者信息或无法访问的入口。

---

Maintained by chao