#!/usr/bin/env python3
"""Download AiDD Shanghai 2026 downloadable documents into speaker-title folders."""
from __future__ import annotations

import csv
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit, quote

import requests

DOC_EXTS = (".pdf", ".ppt", ".pptx", ".doc", ".docx", ".zip")
INVALID_CHARS = '<>:"/\\|?*\n\r\t'


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attrs_dict = dict(attrs)
        href = attrs_dict.get("href")
        if href:
            self.links.append(href)


def safe_name(name: str, max_len: int = 120) -> str:
    name = unquote(name).strip()
    name = re.sub(f"[{re.escape(INVALID_CHARS)}]", " ", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name[:max_len].strip(" .") or "未命名"


def quote_url(url: str) -> str:
    parts = urlsplit(url)
    path = quote(unquote(parts.path), safe="/%")
    query = quote(unquote(parts.query), safe="=&%?/:,+")
    return urlunsplit((parts.scheme, parts.netloc, path, query, parts.fragment))


def extract_doc_links(page_url: str) -> list[str]:
    response = requests.get(page_url, timeout=30)
    response.raise_for_status()
    html = response.content.decode("utf-8", "replace")

    parser = LinkParser()
    parser.feed(html)

    seen: set[str] = set()
    docs: list[str] = []
    for href in parser.links:
        absolute = urljoin(page_url, href)
        clean = absolute.split("#", 1)[0]
        path = unquote(urlsplit(clean).path).lower()
        if not path.endswith(DOC_EXTS):
            continue
        if clean not in seen:
            seen.add(clean)
            docs.append(clean)
    return docs


def folder_and_file(url: str) -> tuple[str, str, str, str]:
    filename = safe_name(Path(unquote(urlsplit(url).path)).name, max_len=180)
    stem = Path(filename).stem
    ext = Path(filename).suffix or ".pdf"
    if "-" in stem:
        speaker, title = stem.split("-", 1)
    else:
        speaker, title = "未知分享人", stem
    speaker = safe_name(speaker, max_len=40)
    title = safe_name(title, max_len=100)
    folder = safe_name(f"{speaker}-{title}", max_len=140)
    return folder, filename, speaker, title


def download_file(session: requests.Session, url: str, dest: Path) -> int:
    encoded_url = quote_url(url)
    with session.get(encoded_url, stream=True, timeout=120) as response:
        response.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        total = 0
        with tmp.open("wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 256):
                if not chunk:
                    continue
                file.write(chunk)
                total += len(chunk)
        tmp.replace(dest)
        return total


def write_manifest(rows: Iterable[dict[str, str]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["speaker", "title", "folder", "file", "url", "status", "bytes"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    page_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.aidd.vip/dhrc-sh2026"
    output_dir = Path(sys.argv[2]).expanduser().resolve() if len(sys.argv) > 2 else Path("aidd分享图片/AiDD上海2026可下载资料").resolve()

    docs = extract_doc_links(page_url)
    print(f"Found {len(docs)} downloadable documents")

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 AiDD downloader",
            "Referer": page_url,
            "Accept": "application/pdf,application/vnd.ms-powerpoint,application/vnd.openxmlformats-officedocument.presentationml.presentation,*/*",
        }
    )

    rows: list[dict[str, str]] = []
    for index, url in enumerate(docs, 1):
        folder, filename, speaker, title = folder_and_file(url)
        dest = output_dir / folder / filename
        print(f"[{index}/{len(docs)}] {folder}/{filename}")
        try:
            if dest.exists() and dest.stat().st_size > 0:
                size = dest.stat().st_size
                status = "exists"
            else:
                size = download_file(session, url, dest)
                status = "downloaded"
            rows.append({"speaker": speaker, "title": title, "folder": folder, "file": filename, "url": url, "status": status, "bytes": str(size)})
        except Exception as exc:
            rows.append({"speaker": speaker, "title": title, "folder": folder, "file": filename, "url": url, "status": f"failed: {exc}", "bytes": "0"})
            print(f"  FAILED: {exc}", file=sys.stderr)

    write_manifest(rows, output_dir / "manifest.csv")
    ok = sum(1 for row in rows if row["status"] in {"downloaded", "exists"})
    failed = len(rows) - ok
    print(f"Done. ok={ok}, failed={failed}")
    print(f"Output: {output_dir}")
    print(f"Manifest: {output_dir / 'manifest.csv'}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
