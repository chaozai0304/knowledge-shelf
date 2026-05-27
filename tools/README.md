# DOCX 转 Markdown 工具

这个目录提供了一个可直接在当前工作区使用的 `.docx -> .md` 转换工具。

## 快速使用

在工作区根目录执行：

- `./tools/docx2md "你的文件.docx"`
- `./tools/docx2md "你的文件.docx" --wechat`
- `./tools/docx2md "你的文件.docx" -o output/result.md --wechat --frontmatter`

## 支持能力

- 使用 `pandoc` 转换 `.docx` 为 Markdown
- 自动提取 Word 内嵌图片
- 自动清理常见 HTML 表格/图片残留
- 支持 WeChat 友好的轻量清洗
- 可选生成 YAML frontmatter

## 说明

- `--wechat`：适合用于公众号或知识库场景的轻量整理，不等于“完全自动改写”
- 如果原始 Word 使用了大量复杂表格、文本框或特殊样式，建议在生成后再人工检查一遍
