## Why

Agent 要完整访问 PyTorch 社区信息需同时加载 GitHub MCP（80+ tools）、Slack MCP（10 tools）、Discourse MCP（18 tools）及多个独立网络接口，总计 120+ 工具。这导致上下文膨胀、工具误选率高、返回格式不统一（JSON/Markdown/纯文本混杂）。我们需要一个领域专用 MCP Server，将散落在多平台的 PyTorch 社区信号聚合为 10-15 个语义清晰的高级工具，统一输出格式，让 Agent 更准确高效地获取社区情报。

## What Changes

- 新建 Python 项目 `pytorch-community-mcp`，基于 FastMCP 框架构建独立 MCP Server
- 直接依赖底层 SDK/HTTP（PyGithub、httpx、feedparser），不依赖其他 MCP Server
- 提供 ~10 个面向 PyTorch 社区的高级 tool，覆盖 PR、Issue、RFC、Slack 讨论、开发者论坛、官方活动、关键贡献者动态等
- 所有 tool 统一输出为 Markdown + 结构化摘要格式
- 支持通过环境变量注入各平台认证凭据（GitHub PAT、Slack xoxc/xoxd token、Discourse API key）

## Capabilities

### New Capabilities

- `github-data`: 从 GitHub API 获取 PyTorch PR、Issue、RFC 数据，支持时间范围和模块过滤
- `slack-data`: 从 Slack API 获取 PyTorch 社区频道的讨论线程，使用 xoxc/xoxd 浏览器 session token 认证
- `discourse-data`: 从 Discourse API 获取 discuss.pytorch.org 开发者论坛的帖子和讨论
- `events-data`: 从 PyTorch 官网 Events API（WordPress TEC REST）和 RSS 获取活动、博客信息
- `contributor-activity`: 跨平台聚合关键贡献者在 GitHub、Slack、Discourse 的活动
- `unified-output`: 所有 tool 的统一输出格式规范（Markdown + 结构化摘要 JSON）

### Modified Capabilities

（无既有 capability 需要修改）

## Impact

- **新增代码**：`src/` 目录下的 MCP Server 实现（server.py、tools/、clients/）
- **新增依赖**：mcp[cli]、PyGithub、httpx、feedparser
- **部署前置**：需要 GitHub PAT、Slack xoxc/xoxd token（通过 slack-token-extractor 提取）、Discourse API key
- **外部 API 约束**：GitHub Search API 30 次/分钟 rate limit；Slack xoxc/xoxd token 需定期刷新（数周~数月）；Discourse 搜索最多返回 50 条
- **运行方式**：标准 MCP Server，支持 stdio 传输，可被 Claude Code、OpenCode 等 MCP client 直接连接
