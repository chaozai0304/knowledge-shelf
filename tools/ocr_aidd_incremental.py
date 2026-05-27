#!/usr/bin/env python3
"""Incremental OCR for an image directory using macOS Vision."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from ocr_aidd_images import IMAGE_EXTS, image_time, recognize


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: ocr_aidd_incremental.py <image_dir> <output_json>", file=sys.stderr)
        return 2

    image_dir = Path(sys.argv[1]).expanduser().resolve()
    output_json = Path(sys.argv[2]).expanduser().resolve()
    images = sorted([p for p in image_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS], key=lambda p: (image_time(p), p.name))

    existing = []
    done = set()
    if output_json.exists():
        existing = json.loads(output_json.read_text(encoding="utf-8"))
        done = {item.get("file") for item in existing}

    records = existing
    for i, path in enumerate(images, 1):
        if path.name in done:
            print(f"[{i}/{len(images)}] Skip {path.name}", file=sys.stderr)
            continue
        print(f"[{i}/{len(images)}] OCR {image_dir.name}/{path.name}", file=sys.stderr)
        try:
            lines = recognize(path)
            text = "\n".join(line["text"] for line in lines)
            record = {
                "file": path.name,
                "time": image_time(path),
                "preview": " | ".join(line["text"] for line in lines[:12]),
                "text": text,
                "lines": lines,
            }
        except Exception as exc:
            record = {"file": path.name, "time": image_time(path), "error": str(exc), "text": "", "lines": []}
        records.append(record)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {output_json} ({len(records)} images) at {datetime.now().isoformat(timespec='seconds')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
