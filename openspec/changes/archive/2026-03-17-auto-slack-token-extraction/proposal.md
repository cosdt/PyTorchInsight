## Why

Slack token 配置是当前 MCP server 唯一需要手动干预的环节。用户必须通过浏览器扩展提取 xoxc/xoxd token，然后手动写入环境变量。这些 token 还会过期，导致反复操作。项目已有 `slack-token-extractor` (Playwright 版) 能从本地 Chrome 零交互提取 token，应该整合进 MCP server 启动流程。

## What Changes

- MCP server 启动时自动尝试获取 Slack token（检查已保存 token → 从本地 Chrome 提取 → 降级为手动配置）
- 将 `slack-token-extractor` 的核心提取逻辑整合为项目内部模块
- `SlackConfig` 支持运行时 token 刷新（token 过期时自动重新提取）
- 新增 `playwright` 可选依赖
- 统一 token 环境变量命名（`SLACK_MCP_XOXC_TOKEN` → `SLACK_XOXC_TOKEN`）

## Capabilities

### New Capabilities
- `auto-token-extraction`: MCP server 启动时自动从本地 Chrome 提取 Slack xoxc/xoxd token 的三阶段生命周期（saved → chrome → manual fallback），以及 token 过期时的运行时刷新

### Modified Capabilities
- `slack-data`: "No Slack token configured" 场景变更 — 不再直接报错，而是先尝试自动提取；认证失败场景增加自动刷新重试

## Impact

- **代码**: `config.py`（SlackConfig 增加动态 token 获取）、`server.py`（启动流程）、`clients/slack.py`（token 刷新重试）
- **新模块**: `token_extractor.py`（从 `playwright_extract.py` 整合的提取逻辑）
- **依赖**: 新增 `playwright` 为可选依赖（`pip install pytorch-community-mcp[slack-auto]`）
- **文件系统**: 读取 `~/.slack_tokens.env` 和 Chrome profile 目录
