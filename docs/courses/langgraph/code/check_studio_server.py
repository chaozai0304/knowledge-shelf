"""检查 LangGraph Studio 本地服务是否可访问。

用途：
1. 先确认 http://127.0.0.1:2024/ok 是否返回 {"ok": true}。
2. 再列出当前 langgraph.json 注册的 assistant / graph。

如果这个脚本成功，但 Studio 页面仍显示 Failed to fetch，通常是浏览器侧访问
localhost 被拦截或页面打开得太早；刷新页面，或改用 langgraph dev --tunnel。
"""

from __future__ import annotations

import json
import urllib.request


BASE_URL = "http://127.0.0.1:2024"


def main() -> None:
    with urllib.request.urlopen(f"{BASE_URL}/ok", timeout=5) as response:
        print("SERVER_OK", response.status, response.read().decode("utf-8"))

    request = urllib.request.Request(
        f"{BASE_URL}/assistants/search",
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        assistants = json.loads(response.read().decode("utf-8"))

    print("ASSISTANT_COUNT", len(assistants))
    for assistant in sorted(assistants, key=lambda item: item["graph_id"]):
        print(f"- {assistant['graph_id']}  {assistant['assistant_id']}")


if __name__ == "__main__":
    main()