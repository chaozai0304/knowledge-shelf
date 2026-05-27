# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from pathlib import Path

root = Path('/Users/chao/Desktop/分享文档库/output')
index = root / 'index.html'
text = index.read_text(encoding='utf-8')
paths = re.findall(r"path: '([^']+)'", text)
missing = [p for p in paths if not (root / p).exists()]
print(f'catalog paths: {len(paths)}')
if missing:
    print('missing:')
    for path in missing:
        print(path)
    raise SystemExit(1)
print('all catalog paths exist')

expected_dirs = [
    'courses/langgraph',
    'courses/langchain',
    'courses/fine-tuning',
    'courses/agents',
    'courses/engineering-standards',
    'assets/shared',
]
for rel in expected_dirs:
    path = root / rel
    print(rel, 'OK' if path.exists() else 'MISSING')
    if not path.exists():
        raise SystemExit(1)
