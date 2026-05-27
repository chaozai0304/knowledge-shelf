#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

PYTHON_BIN="${PYTHON_BIN:-/Users/chao/.pyenv/versions/3.11.0/bin/python}"
LANGGRAPH_BIN="${LANGGRAPH_BIN:-/Users/chao/.pyenv/versions/3.11.0/bin/langgraph}"
HOST="${LANGGRAPH_HOST:-127.0.0.1}"
PORT="${LANGGRAPH_PORT:-2024}"

echo "当前目录: $PWD"
echo "API 地址: http://127.0.0.1:${PORT}"
echo "Studio 地址: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:${PORT}"
echo
echo "注意：浏览器里不要使用 baseUrl=http://0.0.0.0:${PORT}。"
echo "如果 Studio 仍然 Failed to fetch，请改用：bash start_studio.sh --tunnel"
echo

exec "$LANGGRAPH_BIN" dev --no-browser --no-reload --port "$PORT" --host "$HOST" "$@"