"""测试当前 .env 中的 OpenAI 兼容模型配置。

不会打印 API Key，只检查是否已设置，并调用一次 /chat/completions。
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from dotenv import load_dotenv

load_dotenv(".env", override=True)

base = os.getenv("OPENAI_BASE_URL", "").rstrip("/")
key = os.getenv("OPENAI_API_KEY", "")
model = os.getenv("OPENAI_MODEL", "")

print("OPENAI_API_KEY=", "SET" if key else "MISSING")
print("OPENAI_BASE_URL=", base)
print("OPENAI_MODEL=", model)

if not (base and key and model):
    raise SystemExit("缺少 OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL 中的一项")

payload = {
    "model": model,
    "messages": [{"role": "user", "content": "请只回答：LangGraph OK"}],
    "temperature": 0,
    "max_tokens": 20,
}

request = urllib.request.Request(
    base + "/chat/completions",
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Authorization": "Bearer " + key,
        "Content-Type": "application/json",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.loads(response.read().decode("utf-8"))
    content = data["choices"][0]["message"]["content"]
    print("MODEL_TEST=OK")
    print("MODEL_RESPONSE=", content.replace("\n", " ")[:200])
except urllib.error.HTTPError as error:
    body = error.read().decode("utf-8", errors="replace")[:500]
    print("MODEL_TEST=HTTP_ERROR", error.code)
    print(body)
    if error.code == 401:
        print(
            "说明：.env 已被读取，但模型网关拒绝了当前 OPENAI_API_KEY。"
            "请检查 key 是否有效、是否属于当前 OPENAI_BASE_URL 对应的网关。"
        )
    raise SystemExit(1)
except Exception as error:
    print("MODEL_TEST=FAILED", type(error).__name__, str(error))
    raise SystemExit(1)
