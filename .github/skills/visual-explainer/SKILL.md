---
name: visual-explainer
description: "Use when: 生成信息图、文章插图、流程图、对比图、架构说明图、HTML/CSS 可截图配图。负责把复杂观点转成高颜值、可发布、可复用的视觉解释图。"
argument-hint: "<要解释的概念/流程/对比关系>"
user-invocable: true
metadata:
  author: chao
---

# Visual Explainer

`visual-explainer` 是知识库的信息图生成器。它把复杂概念、流程、对比关系和系统结构转成可截图的 HTML 视觉说明图。

## 适用场景

- 用户要求“生成插图”“制作信息图”“画一张图解释”。
- 文章中有复杂流程、模型、对比关系、架构关系。
- 普通表格不够直观，需要视觉化表达。
- 需要生成 HTML 后截图为图片。

## 图形类型

- **流程型**：步骤、管道、工作流、转化路径。
- **对比型**：旧方式 vs 新方式、工具对比、能力差异。
- **矩阵型**：四象限、二维评估、策略选择。
- **架构型**：模块、层级、依赖、数据流。
- **摘要型**：一页纸概括文章核心观点。

## 工作流程

1. **抽象关系**：先判断这是流程、对比、矩阵还是架构。
2. **压缩信息**：每张图只表达一个核心观点。
3. **生成 HTML**：用 CSS/SVG/Tailwind/Lucide 构造自包含页面。
4. **截图导出**：使用配套脚本把 HTML 转成图片。
5. **回填文档**：将图片路径写回 Markdown，并确保发布 HTML 能嵌入。

## 自动截图

如果需要把 HTML 转成图片，可运行：

```bash
node .github/skills/visual-explainer/scripts/capture.js <input-html>
```

## 质量标准

- 图能独立表达观点，不依赖长段解释。
- 信息层级清楚，主标题、模块、说明文字有明显优先级。
- 不把所有内容塞进一张图。
- 图形风格与 chao 知识库一致：克制、科技感、干净。

## 配套资源

- 基础模板：`./assets/base_template.html`
- 截图脚本：`./scripts/capture.js`
- 示例：`./examples/demo.html`
