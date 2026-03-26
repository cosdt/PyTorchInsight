## Why

Slack 信源在当前 MCP 服务中已完全不再使用。保留它增加了不必要的维护负担（token 提取、Playwright 可选依赖、Chrome profile 管理）和代码复杂度。现在安全地移除它，简化代码库和配置。

## What Changes

- **BREAKING**: 移除 `get-slack-threads` MCP tool
- **BREAKING**: 移除 Slack 相关环境变量支持（`SLACK_XOXC_TOKEN`、`SLACK_XOXD_TOKEN`、`SLACK_XOXP_TOKEN`）
- 移除 `SlackClient` 客户端和 `SlackConfig` 配置
- 移除 `token_extractor.py` 整个模块（Playwright-based Chrome token 提取）
- 移除 CLI 子命令 `extract-slack-tokens`
- 移除 `playwright` 可选依赖和 `slack-auto` 依赖组
- 从 `get-key-contributors-activity` tool 中移除 Slack 数据源聚合
- 移除所有 Slack 相关测试文件
- 归档 Slack 相关 specs（`slack-data`、`auto-token-extraction`）
- 更新文档（README.md、docs/setup.md、docs/mcp.md）

## Capabilities

### New Capabilities

（无新增能力）

### Modified Capabilities

- `contributor-activity`: 移除 Slack 作为数据源，从三平台（GitHub + Slack + Discourse）变为两平台（GitHub + Discourse）
- `unified-output`: 如果输出格式中有 Slack 特有的格式标记（如 `[Slack]` 前缀），需要确认并清理

## Impact

- **代码**: 删除 `clients/slack.py`、`tools/slack.py`、`token_extractor.py`；修改 `config.py`、`server.py`、`__init__.py`、`tools/contributors.py`
- **测试**: 删除 `test_slack_retry.py`、`test_slack_config.py`、`test_token_extractor.py`；修改 `test_clients.py`、`test_contributors_tool.py`、`test_integration.py`、`test_e2e.py`、`test_formatter.py`
- **依赖**: 移除 `playwright` 可选依赖，更新 `pyproject.toml` 和 `uv.lock`
- **配置**: MCP client 配置中不再需要 Slack token 环境变量
- **文档**: README、setup.md、mcp.md 需更新
- **Specs**: `slack-data` 和 `auto-token-extraction` specs 整体归档
