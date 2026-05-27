#!/usr/bin/env python3
"""OCR AIDD PPT photos with macOS Vision and write structured JSON."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from Foundation import NSURL
from PIL import Image
from PIL.ExifTags import TAGS
from Vision import VNImageRequestHandler, VNRecognizeTextRequest, VNRequestTextRecognitionLevelAccurate

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".webp"}
LANGUAGES = ["zh-Hans", "zh-Hant", "en-US"]


def image_time(path: Path) -> str:
    try:
        with Image.open(path) as img:
            exif = img.getexif()
            for key, value in exif.items():
                if TAGS.get(key) in {"DateTimeOriginal", "DateTimeDigitized", "DateTime"} and value:
                    try:
                        dt = datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S")
                        return dt.isoformat(sep=" ")
                    except ValueError:
                        return str(value)
    except Exception:
        pass
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(sep=" ", timespec="seconds")


def recognize(path: Path) -> list[dict[str, Any]]:
    request = VNRecognizeTextRequest.alloc().init()
    request.setRecognitionLevel_(VNRequestTextRecognitionLevelAccurate)
    request.setRecognitionLanguages_(LANGUAGES)
    request.setUsesLanguageCorrection_(True)

    url = NSURL.fileURLWithPath_(str(path))
    handler = VNImageRequestHandler.alloc().initWithURL_options_(url, {})
    ok, err = handler.performRequests_error_([request], None)
    if not ok:
        raise RuntimeError(f"Vision OCR failed for {path}: {err}")

    rows: list[dict[str, Any]] = []
    for obs in request.results() or []:
        candidates = obs.topCandidates_(1)
        if not candidates:
            continue
        text = str(candidates[0].string()).strip()
        if not text:
            continue
        box = obs.boundingBox()
        rows.append(
            {
                "text": text,
                "confidence": float(candidates[0].confidence()),
                "x": float(box.origin.x),
                "y": float(box.origin.y),
                "w": float(box.size.width),
                "h": float(box.size.height),
            }
        )
    # Vision coordinates are bottom-left origin. Sort visually: top-to-bottom, left-to-right.
    rows.sort(key=lambda r: (-round(r["y"], 2), round(r["x"], 2)))
    return rows


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: ocr_aidd_images.py <image_dir> <output_json>", file=sys.stderr)
        return 2

    image_dir = Path(sys.argv[1]).expanduser().resolve()
    output_json = Path(sys.argv[2]).expanduser().resolve()
    images = sorted([p for p in image_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS], key=lambda p: (image_time(p), p.name))

    records = []
    for i, path in enumerate(images, 1):
        print(f"[{i}/{len(images)}] OCR {image_dir.name}/{path.name}", file=sys.stderr)
        try:
            lines = recognize(path)
            text = "\n".join(line["text"] for line in lines)
            records.append(
                {
                    "file": path.name,
                    "time": image_time(path),
                    "preview": " | ".join(line["text"] for line in lines[:12]),
                    "text": text,
                    "lines": lines,
                }
            )
        except Exception as exc:
            records.append({"file": path.name, "time": image_time(path), "error": str(exc), "text": "", "lines": []})

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {output_json} ({len(records)} images)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
