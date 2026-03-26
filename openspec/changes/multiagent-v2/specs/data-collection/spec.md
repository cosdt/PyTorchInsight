## ADDED Requirements

### Requirement: MCP 优先降级链

每个 scout SHALL 按以下优先级使用数据获取工具：

**github-scout**:
1. `mcp__pytorch-community__get_prs` / `get_issues` / `get_rfcs` / `get_commits` — 首选
2. `mcp__github__list_pull_requests` / `mcp__github__search_code` 等 — 回退
3. Bash `gh pr list --repo ... --json ...` — 末选

**web-scout**:
1. `mcp__pytorch-community__get_discussions` / `get_blog_news` / `get_events` — 首选
2. WebFetch — 回退

**slack-scout**:
1. `mcp__pytorch-community__get_slack_threads` — 首选
2. Slack Docker MCP（若启用）— 回退

#### Scenario: MCP 工具可用时优先使用

- **WHEN** github-scout 需要获取 PR 列表，pytorch-community MCP 正常可用
- **THEN** scout SHALL 使用 `mcp__pytorch-community__get_prs` 而非 `mcp__github__list_pull_requests`

#### Scenario: MCP 失败后降级

- **WHEN** `mcp__pytorch-community__get_prs` 连续 2 次调用失败
- **THEN** scout SHALL 降级到 `mcp__github__list_pull_requests`，并在返回结果中标注降级

### Requirement: 重试优先于降级

所有 scout SHALL 在触发降级之前对当前层级至少重试 1 次（间隔 5 秒）。仅在连续 2 次失败后才降级到下一层级。

#### Scenario: 首次失败后重试

- **WHEN** github-scout 调用 `mcp__pytorch-community__get_prs` 首次失败
- **THEN** scout SHALL 等待 5 秒后重试同一工具，而非立即降级

#### Scenario: 连续 2 次失败后降级

- **WHEN** github-scout 调用 `mcp__pytorch-community__get_prs` 连续 2 次失败
- **THEN** scout SHALL 降级到 `mcp__github__list_pull_requests`

### Requirement: Scout 结果写入 Staging

每个 scout SHALL 将采集结果写入 staging 目录的独立文件，而非通过对话消息返回全量数据：
- github-scout → `staging/phase1_github.md`
- web-scout → `staging/phase1_web.md`
- slack-scout → `staging/phase1_slack.md`

Scout 向 coordinator 返回的消息 SHALL 仅包含 Layer 1 统计摘要（≤50 tokens）。

#### Scenario: Scout 写入文件并返回摘要

- **WHEN** github-scout 完成采集，获取 30 条 PR
- **THEN** scout SHALL 将 30 条结构化摘要写入 `staging/phase1_github.md`，向 coordinator 返回"GitHub: 30 条 PR, MCP 正常"

## MODIFIED Requirements

### Requirement: GitHub Scout数据采集

`github-scout` SHALL通过 pytorch-community MCP 工具（首选）或 GitHub MCP 工具（回退）采集指定时间窗口内的以下类型动态：
- Pull Requests（标题、作者、标签、状态、摘要）
- Issues（标题、作者、标签、状态、摘要）
- Discussions（标题、分类、摘要）
- Releases（版本号、变更摘要）
- RFCs（通过 `get_rfcs` 获取 pytorch/rfcs 仓库内容）
- Commits（通过 `get_commits` 获取模块变更速率上下文）

采集范围由`projects/<project>.md`中的`scope`字段驱动。

显式工具映射：
```
1. mcp__pytorch-community__get_prs(since, until, module, state, max_results) — 首选
2. mcp__pytorch-community__get_issues(since, until, module, state, max_results) — 首选
3. mcp__pytorch-community__get_rfcs(since, status) — 首选（覆盖 pytorch/rfcs 仓库）
4. mcp__pytorch-community__get_commits(since, until, module, max_results) — 首选
5. mcp__github__list_pull_requests(owner, repo, state) — 回退
6. Bash gh pr list --repo ... --json ... — 末选
```

#### Scenario: 采集pytorch最近7天的PR

- **WHEN** github-scout接收到项目pytorch、时间窗口7天、scope包含pr的任务
- **THEN** scout SHALL 优先使用 `mcp__pytorch-community__get_prs` 获取 PR 列表，结果写入 staging/phase1_github.md

#### Scenario: GitHub MCP不可用时降级

- **WHEN** pytorch-community MCP 和 GitHub MCP 均不可用
- **THEN** github-scout SHALL按降级链尝试 gh CLI工具。返回结果中SHALL标注实际使用的获取方式和数据完整性影响

#### Scenario: RFC 数据获取

- **WHEN** github-scout 需要获取 RFC 信息
- **THEN** scout SHALL 使用 `mcp__pytorch-community__get_rfcs` 搜索 pytorch/rfcs 仓库

### Requirement: Token预算压缩协议

每个scout的输出SHALL遵循分层压缩协议：

**Layer 1 — 统计摘要**（必须返回给 coordinator 对话）:
- 数据源名称和状态（成功/降级/失败）
- 采集总数 vs 过滤后数量
- 实际使用的获取方式（如降级发生）
- 预算：约50 tokens

**Layer 2 — 条目列表**（写入 staging 文件）:
- 每条动态的6字段结构化摘要
- 每条约30-50 tokens，上限30条
- 写入 staging/phase1_{scout_type}.md

**Layer 3 — 补充详情**（按需获取）:
- 仅在coordinator请求特定条目的详情时返回
- 包含完整描述、评论摘要、标签详情等
- 不主动返回，避免上下文膨胀

#### Scenario: 正常压缩输出

- **WHEN** github-scout采集到100条PR，过滤后剩30条
- **THEN** scout SHALL 将 30 条结构化摘要写入 staging 文件，向 coordinator 返回 Layer 1 统计（≤50 tokens）

#### Scenario: Coordinator请求Layer 3

- **WHEN** coordinator对github-scout返回的第5条PR需要更详细信息
- **THEN** coordinator SHALL通过追加消息请求该条目的Layer 3详情，scout SHALL仅返回该条目的完整信息
