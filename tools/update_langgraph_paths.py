# -*- coding: utf-8 -*-
from pathlib import Path

base = Path('/Users/chao/Desktop/分享文档库/output/courses/langgraph')
for path in list(base.glob('*.md')) + [base / 'README.md']:
    if not path.exists():
        continue
    text = path.read_text(encoding='utf-8')
    text = text.replace('output/langgraph', 'output/courses/langgraph')
    text = text.replace('/Users/chao/Desktop/分享文档库/output/langgraph', '/Users/chao/Desktop/分享文档库/output/courses/langgraph')
    path.write_text(text, encoding='utf-8')
    print('updated', path)
