# 学习资料库 output 目录规范

`output` 目录现在作为“可学习、可发布、可扩展”的内容产物库使用。

## 推荐结构

```text
output/
├── index.html                    # 学习门户首页，左侧目录 + 右侧内容预览
├── README.md                     # 当前目录规范
├── assets/                       # 跨课程复用素材
│   └── shared/
└── courses/                      # 按领域组织的课程/文章
    ├── langgraph/                # LangGraph 系列
    ├── langchain/                # LangChain 系列
    ├── fine-tuning/              # 微调系列
    ├── agents/                   # Agent 工具、Harness、Skills 等
    └── engineering-standards/    # 工程规范
```

## 新增内容放置规则

### 1. 新增一个完整课程

放到：

```text
output/courses/<domain>/<course-name>/
```

建议包含：

```text
README.md
article-01.md
article-01.html
assets/
code/
```

### 2. 新增单篇文章

放到对应领域目录：

```text
output/courses/langchain/xxx-wechat.md
output/courses/langchain/xxx-wechat.html
```

### 3. 新增代码

放到对应课程内的 `code/`：

```text
output/courses/langgraph/code/
```

### 4. 新增 Notebook

放到领域下的 `notebooks/`：

```text
output/courses/fine-tuning/notebooks/
```

### 5. 新增通用素材

如果只服务于某个课程，放课程自己的 `assets/`。
如果多个课程共用，放：

```text
output/assets/shared/
```

## 门户页维护

门户页位于：

```text
output/index.html
```

新增 HTML 内容后，在 `index.html` 的 `catalog` 数组里增加一条记录即可。

## 兼容说明

为了避免旧路径失效，保留了：

```text
output/langgraph -> output/courses/langgraph
```

这是软链接，后续新内容请优先使用 `output/courses/langgraph`。
