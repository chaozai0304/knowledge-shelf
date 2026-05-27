#!/usr/bin/env python3
"""Convert a .docx file to Markdown and extract embedded media.

Features:
- Uses pandoc for reliable .docx -> Markdown conversion
- Extracts embedded images to a sibling assets directory
- Performs light cleanup on common HTML-heavy output produced by Word docs
- Optional WeChat-friendly cleanup mode for easier article publishing

Examples:
- ./tools/docx_to_md.py notes.docx
- ./tools/docx_to_md.py notes.docx -o output/notes.md --wechat
- ./tools/docx_to_md.py notes.docx --title "我的文章标题" --frontmatter
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import sys
from pathlib import Path


LANGUAGE_LABELS = {
    "bash": "bash",
    "shell": "bash",
    "zsh": "bash",
    "json": "json",
    "javascript": "javascript",
    "js": "javascript",
    "typescript": "typescript",
    "ts": "typescript",
    "css": "css",
    "html": "html",
    "markdown": "markdown",
    "md": "markdown",
    "yaml": "yaml",
    "yml": "yaml",
    "python": "python",
    "plain text": "text",
    "text": "text",
}

HEADING_PATTERNS = [
    (re.compile(r"^(\d+)\\\.\s+\*\*(.+?)\*\*\s*$"), 2),
    (re.compile(r"^(\d+\.\d+)\s+\*\*(.+?)\*\*\s*$"), 3),
    (re.compile(r"^(\d+\.\d+\.\d+)\s+\*\*(.+?)\*\*\s*$"), 4),
    (re.compile(r"^(\d+\.\d+\.\d+\.\d+)\s+\*\*(.+?)\*\*\s*$"), 5),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert DOCX to Markdown with extracted images.")
    parser.add_argument("input", help="Path to the .docx file")
    parser.add_argument("-o", "--output", help="Path to the output markdown file")
    parser.add_argument(
        "--media-dir",
        help="Directory for extracted media (default: <output_stem>_assets beside the markdown file)",
    )
    parser.add_argument("--title", help="Override the Markdown title")
    parser.add_argument(
        "--wechat",
        action="store_true",
        help="Apply additional cleanup for easier WeChat article editing",
    )
    parser.add_argument(
        "--frontmatter",
        action="store_true",
        help="Add simple YAML frontmatter to the generated Markdown",
    )
    return parser.parse_args()


def fail(message: str) -> "NoReturn":
    print(f"错误：{message}", file=sys.stderr)
    raise SystemExit(1)


def require_pandoc() -> str:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        fail("未找到 pandoc，请先安装 pandoc 后再运行。")
    return pandoc


def resolve_paths(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        fail(f"输入文件不存在：{input_path}")
    if input_path.suffix.lower() != ".docx":
        fail("当前工具只支持 .docx 文件。")

    if args.output:
        output_path = Path(args.output).expanduser().resolve()
    else:
        output_path = input_path.with_suffix(".md")

    if args.media_dir:
        media_dir = Path(args.media_dir).expanduser().resolve()
    else:
        media_dir = output_path.parent / f"{output_path.stem}_assets"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    media_dir.mkdir(parents=True, exist_ok=True)
    return input_path, output_path, media_dir


def run_pandoc(pandoc: str, input_path: Path, output_path: Path, media_dir: Path) -> None:
    command = [
        pandoc,
        str(input_path),
        "-f",
        "docx",
        "-t",
        "gfm",
        "--wrap=none",
        f"--extract-media={media_dir}",
        "-o",
        str(output_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        fail(result.stderr.strip() or "pandoc 转换失败")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def normalize_image_paths(text: str, output_path: Path, media_dir: Path) -> str:
    relative_media = media_dir.relative_to(output_path.parent) if media_dir.is_relative_to(output_path.parent) else media_dir
    normalized_root = str(relative_media).replace("\\", "/")

    def replace_markdown_image(match: re.Match[str]) -> str:
        alt_text = match.group(1)
        src = match.group(2).replace("\\", "/")
        filename = src.split("/")[-1]
        if "/media/" in src:
            return f"![{alt_text}]({normalized_root}/media/{filename})"
        return f"![{alt_text}]({src})"

    def replace_html_image(match: re.Match[str]) -> str:
        src = match.group(1).replace("\\", "/")
        filename = src.split("/")[-1]
        if "/media/" in src:
            return f"![]({normalized_root}/media/{filename})"
        return f"![]({src})"

    text = re.sub(r"!\[(.*?)\]\(([^)]+)\)", replace_markdown_image, text)
    text = re.sub(r"<img\s+[^>]*src=\"([^\"]+)\"[^>]*>", replace_html_image, text, flags=re.IGNORECASE)
    return text


def strip_simple_tags(text: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?(p|strong|em|code|pre|tbody|thead|tr|td|table|colgroup|col|span)[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"</?a[^>]*>", "", text, flags=re.IGNORECASE)
    return html.unescape(text)


def convert_single_cell_table(block: str) -> str:
    cells = re.findall(r"<td[^>]*>(.*?)</td>", block, flags=re.IGNORECASE | re.DOTALL)
    if not cells:
        return block
    if len(cells) == 1:
        content = strip_simple_tags(cells[0]).strip()
        lines = [line.rstrip() for line in content.splitlines()]
        non_empty = [line for line in lines if line.strip()]
        if not non_empty:
            return ""
        first = non_empty[0].strip().lower()
        if first in LANGUAGE_LABELS and len(non_empty) >= 2:
            language = LANGUAGE_LABELS[first]
            body = "\n".join(non_empty[1:]).strip()
            return f"```{language}\n{body}\n```"
        return "\n".join(non_empty)

    image_sources = re.findall(r"<img\s+[^>]*src=\"([^\"]+)\"[^>]*>", block, flags=re.IGNORECASE)
    if image_sources:
        return "\n\n".join(f"![]({src})" for src in image_sources)

    cleaned_cells = [strip_simple_tags(cell).strip() for cell in cells]
    cleaned_cells = [cell for cell in cleaned_cells if cell]
    return "\n\n".join(cleaned_cells)


def convert_html_tables(text: str) -> str:
    return re.sub(
        r"<table[^>]*>.*?</table>",
        lambda match: convert_single_cell_table(match.group(0)),
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )


def cleanup_blockquotes(text: str) -> str:
    text = re.sub(r"^>\s*!\[", "![", text, flags=re.MULTILINE)
    text = re.sub(r"^>\s*$", "", text, flags=re.MULTILINE)
    return text


def normalize_headings(text: str) -> str:
    new_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        converted = False
        for pattern, level in HEADING_PATTERNS:
            match = pattern.match(stripped)
            if match:
                title = match.group(2).strip()
                new_lines.append(f"{'#' * level} {title}")
                converted = True
                break
        if converted:
            continue
        if re.fullmatch(r"\*\*.+\*\*", stripped):
            new_lines.append(f"## {stripped.strip('* ')}")
            continue
        new_lines.append(line)
    return "\n".join(new_lines)


def cleanup_markdown(text: str, output_path: Path, media_dir: Path, wechat: bool) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = normalize_image_paths(text, output_path, media_dir)
    text = convert_html_tables(text)
    text = strip_simple_tags(text)
    text = cleanup_blockquotes(text)
    text = normalize_headings(text)

    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)

    if wechat:
        text = re.sub(r"^\s*点击图片可查看完整电子表格\s*$", "> 提示：如果原图是长图或表格，建议在公众号后台上传高清版后再替换。", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*测试\s*$", "## 效果测试", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*实战\s*$", "## 实战示例", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*安装skill工具\s*$", "## 安装与管理 Skills", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*生成agents\.md【技能目录】\s*$", "### 生成技能目录", text, flags=re.MULTILINE)

    return text.strip() + "\n"


def inject_title(text: str, title: str | None) -> str:
    if not title:
        return text
    lines = text.splitlines()
    if lines and lines[0].startswith("# "):
        lines[0] = f"# {title}"
    else:
        lines.insert(0, f"# {title}")
        lines.insert(1, "")
    return "\n".join(lines)


def remove_duplicate_leading_heading(text: str, title: str) -> str:
    lines = text.splitlines()
    result: list[str] = []
    skipped = False

    for index, line in enumerate(lines):
        stripped = line.strip()
        if index <= 1:
            result.append(line)
            continue
        if not skipped and stripped == f"## {title}":
            skipped = True
            continue
        result.append(line)

    return "\n".join(result)


def add_frontmatter(text: str, title: str) -> str:
    frontmatter = "\n".join(
        [
            "---",
            f'title: "{title}"',
            "source: docx-to-md",
            "tags:",
            "  - docx",
            "  - markdown",
            "---",
            "",
        ]
    )
    return frontmatter + text


def main() -> None:
    args = parse_args()
    pandoc = require_pandoc()
    input_path, output_path, media_dir = resolve_paths(args)

    run_pandoc(pandoc, input_path, output_path, media_dir)

    text = read_text(output_path)
    text = cleanup_markdown(text, output_path, media_dir, args.wechat)

    title = args.title or input_path.stem
    text = inject_title(text, title)
    text = remove_duplicate_leading_heading(text, title)
    if args.frontmatter:
        text = add_frontmatter(text, title)

    write_text(output_path, text)

    print("转换完成")
    print(f"- Markdown: {output_path}")
    print(f"- Media: {media_dir}")


if __name__ == "__main__":
    main()
