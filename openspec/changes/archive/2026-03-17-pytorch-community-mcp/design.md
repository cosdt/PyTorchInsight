## Context

PyTorch 开源社区的信息分布在 GitHub（pytorch/pytorch、pytorch/rfcs 等）、Slack（pytorch.slack.com）、Discourse（discuss.pytorch.org）、官网 Events API 和 RSS 等多个平台。当前 Agent 需同时加载 120+ 个通用 MCP 工具来获取这些信息，导致上下文膨胀、误选率高、输出格式不统一。

本项目构建一个领域专用 MCP Server，直接调用各平台底层 SDK/API（非依赖其他 MCP Server），提供 ~10 个语义清晰的高级工具。

### 现有约束

- GitHub Search API：30 次/分钟 rate limit
- Slack `search.messages`：不支持 Bot Token，需要 User Token（xoxp-）或浏览器 session token（xoxc-/xoxd-）
- Discourse 搜索：单次最多 50 条结果
- Events API（`pytorch.org/wp-json/tec/v1/`）：GET 请求无需认证
- 项目定位：仅限内部使用，仅获取公开信息

## Goals / Non-Goals

**Goals:**

- 提供 ~10 个面向 PyTorch 社区情报的 MCP tool，覆盖 PR、Issue、RFC、Slack、论坛、活动、关键贡献者
- 所有 tool 统一输出 Markdown 格式，降低 Agent 解析负担
- 直接调底层 SDK/API，单进程部署，无需启动子 MCP Server
- 支持时间范围过滤、模块过滤等领域专属查询维度
- 内置 rate limit 感知与退避机制

**Non-Goals:**

- 不做通用 MCP gateway/proxy
- 不包含写操作（不发消息、不创建 Issue、不评论）
- 不做 Web UI 或 Dashboard
- 不做持久化存储或数据库
- 不处理用户认证/授权流程（token 通过环境变量注入）

## Decisions

### D1: 直接调 SDK 而非依赖子 MCP Server

**选择**: 模式 B — 直接用 PyGithub / httpx / feedparser 调各平台 API

**替代方案**: 模式 A — 在进程内作为 MCP Client 连接 GitHub MCP、Slack MCP 等子 Server

**理由**:
- 本项目是领域 MCP（语义封装 + 数据加工），不是工具代理
- 单进程、纯 Python，部署极简（`pip install` 即可）
- 完全控制输出格式、错误处理、rate limit 策略
- 无需管理子进程生命周期或 Node.js 运行时

### D2: Slack 认证使用 xoxc/xoxd 浏览器 session token

**选择**: 支持 xoxc/xoxd token，通过 httpx 直接调 Slack API（带 Authorization + Cookie header）

**替代方案 A**: 用 Bot Token + conversations.history 逐频道拉取

**替代方案 B**: 用 OAuth User Token（xoxp-），需管理员审批

**理由**:
- `search.messages` 是 Slack 数据的核心能力，Bot Token 不支持
- xoxc/xoxd 无需管理员审批，slack-token-extractor 提供成熟的提取方案（9000+ 用户验证）
- 内部使用场景下合规风险可控
- 同时支持 xoxp- token 作为替代（如果用户能拿到）

### D3: HTTP 客户端统一使用 httpx

**选择**: Slack API、Discourse API、Events API 全部用 httpx（AsyncClient）

**替代方案**: Slack 用 slack_sdk，Discourse 用 pydiscourse

**理由**:
- xoxc/xoxd token 需要自定义 Cookie header，slack_sdk 不方便支持
- pydiscourse 功能有限，直接用 httpx 调 REST API 更灵活
- 统一 HTTP client 减少依赖，简化错误处理和重试逻辑
- GitHub 仍用 PyGithub（其搜索语法封装有独立价值）

### D4: FastMCP 作为 MCP 框架

**选择**: 使用 jlowin/fastmcp（v2.x 稳定版）

**理由**:
- Python 生态最成熟的 MCP Server 框架
- `@mcp.tool` 装饰器，自动生成 schema 和验证
- 原生支持 async、stdio 传输
- 社区活跃，文档完善

### D5: 项目结构

```
pytorch-community-mcp/
├── pyproject.toml
├── src/
│   └── pytorch_community_mcp/
│       ├── __init__.py
│       ├── server.py           # FastMCP 入口 + tool 注册
│       ├── config.py           # 环境变量配置
│       ├── tools/              # MCP Tool 定义（业务逻辑层）
│       │   ├── __init__.py
│       │   ├── prs.py
│       │   ├── issues.py
│       │   ├── rfcs.py
│       │   ├── slack.py
│       │   ├── discussions.py
│       │   ├── events.py
│       │   ├── contributors.py
│       │   └── governance.py
│       ├── clients/            # API Client 封装（传输层）
│       │   ├── __init__.py
│       │   ├── github.py       # PyGithub wrapper + rate limit
│       │   ├── slack.py        # httpx → Slack API
│       │   ├── discourse.py    # httpx → discuss.pytorch.org
│       │   ├── events.py       # httpx → pytorch.org Events API
│       │   └── rss.py          # feedparser wrapper
│       └── formatter.py        # 统一输出格式化
└── tests/
```

## Risks / Trade-offs

**[Slack xoxc/xoxd token 过期]** → Token 寿命数周~数月，过期后需重新提取。缓解：MCP Server 检测 401 时在返回中提示用户刷新 token；部署文档说明刷新流程。

**[GitHub Search API rate limit]** → 30 次/分钟可能在密集查询场景不够用。缓解：内置 rate limit 感知 + 指数退避；考虑对相同查询条件做短期缓存；后续可评估 GraphQL API。

**[Discourse 搜索分页限制]** → 单次搜索最多 50 条。缓解：对于"最近 N 天热门讨论"场景已够用；必要时用 `/latest.json` + 客户端过滤补充。

**[Slack session token 合规灰色地带]** → 使用浏览器 session 非 Slack 官方推荐路径。缓解：项目仅限内部使用、仅获取公开频道信息；同时支持 xoxp- token 作为正规替代。

**[多平台 API 变更]** → 各平台 API 可能变更或下线。缓解：clients/ 层隔离 API 调用细节，变更时只需修改对应 client。
