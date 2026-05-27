# OpenAI 兼容接口测试结果

测试脚本：`test_openai_config.py`

## 当前结果

- `OPENAI_BASE_URL`：已规范为 `/v1` 结尾。
- `OPENAI_MODEL`：已读取到配置。
- `OPENAI_API_KEY`：已读取到配置，但测试返回 `401 Unauthorized`。
- 网关错误信息：`无效的令牌`。

## 结论

当前网络地址和接口路径可以发起请求，但 key 未通过网关认证。请替换为有效 key 后重新运行：

```bash
cd /Users/chao/Desktop/分享文档库/output/courses/langgraph/code
python test_openai_config.py
```

如果你启用 LangSmith，请填写真实 `LANGSMITH_API_KEY`；否则保持：

```bash
LANGSMITH_TRACING=false
```
