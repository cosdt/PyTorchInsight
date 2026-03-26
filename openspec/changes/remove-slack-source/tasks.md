## 1. 移除 Slack 引用（先改引用方，再删被引用方）

- [x] 1.1 修改 `src/pytorch_community_mcp/server.py`：移除 `SlackClient` 导入、`slack_client` 实例化、`get_slack_threads` tool 注册、传给 `get_key_contributors_activity` 的 `slack_client` 参数；更新 `FastMCP(instructions=...)` 字符串移除 Slack 引用；更新 `get_key_contributors_activity` 的 docstring 移除 Slack 引用
- [x] 1.2 修改 `src/pytorch_community_mcp/tools/contributors.py`：移除 `slack_client` 参数、`_fetch_slack_activity` 函数、Slack 相关 import 和 platform notes 处理
- [x] 1.3 修改 `src/pytorch_community_mcp/config.py`：移除 `SlackConfig` 类及 `Config.from_env()` 中的 Slack 配置
- [x] 1.4 修改 `src/pytorch_community_mcp/__init__.py`：移除 `extract-slack-tokens` 子命令和 `_extract_slack_tokens()` 函数

## 2. 删除纯 Slack 文件（引用已清除，安全删除）

- [x] 2.1 删除 `src/pytorch_community_mcp/clients/slack.py`
- [x] 2.2 删除 `src/pytorch_community_mcp/tools/slack.py`
- [x] 2.3 删除 `src/pytorch_community_mcp/token_extractor.py`

## 3. 修改测试

- [x] 3.1 删除 `tests/test_slack_retry.py`
- [x] 3.2 删除 `tests/test_slack_config.py`
- [x] 3.3 删除 `tests/test_token_extractor.py`
- [x] 3.4 修改 `tests/test_clients.py`：移除 SlackClient 相关测试
- [x] 3.5 修改 `tests/test_contributors_tool.py`：移除 `_fetch_slack_activity` 测试和 Slack 相关 fixture/断言
- [x] 3.6 修改 `tests/test_integration.py`：移除 `get_slack_threads` 工具注册和 schema 测试，移除 `SlackConfig` 引用；更新 `EXPECTED_TOOLS` 集合（移除 `get_slack_threads`）并将 `assert len(tools) == 11` 改为 `== 10`
- [x] 3.7 修改 `tests/test_e2e.py`：移除 `TestGetSlackThreads` 测试类和 `slack_client` fixture
- [x] 3.8 修改 `tests/test_formatter.py`：替换或移除 `test_format_error` 中以 `slack-token-extractor` 为示例数据的测试用例（改的是测试数据，formatter 本身无 Slack 逻辑）

## 4. 更新依赖配置

- [x] 4.1 修改 `pyproject.toml`：从主 `dependencies` 列表中移除 `playwright>=1.58.0`（第19行），移除整个 `slack-auto` optional dependency group，移除 coverage omit 中的 `token_extractor.py`
- [x] 4.2 执行 `uv lock` 重新生成 `uv.lock`

## 5. 归档 Specs

- [x] 5.1 删除 `openspec/specs/slack-data/` 目录
- [x] 5.2 删除 `openspec/specs/auto-token-extraction/` 目录

## 6. 更新文档

- [x] 6.1 修改 `README.md`：移除 Slack 相关 tool 说明、环境变量、auto-extraction 描述
- [x] 6.2 修改 `docs/setup.md`：移除 Slack 认证配置说明和环境变量
- [x] 6.3 修改 `docs/mcp.md`：移除 Slack 数据源引用和架构图中的 Slack 依赖

## 7. 验证

- [x] 7.1 运行全量测试 `uv run pytest` 确保通过
- [x] 7.2 全局搜索 "slack"/"Slack" 确认无残留代码引用（archive 目录除外）
