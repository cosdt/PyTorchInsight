## Context

当前 MCP 服务集成了三个数据源：GitHub、Slack、Discourse。Slack 信源包含完整的客户端（`clients/slack.py`）、token 自动提取模块（`token_extractor.py`、398行）、配置层（`SlackConfig`）、MCP tool（`get-slack-threads`）、以及在 `get-key-contributors-activity` 中的跨平台聚合。Slack 信源已确认完全不再需要。

## Goals / Non-Goals

**Goals:**
- 完全移除 Slack 信源相关的所有代码、配置、测试和文档
- 保持其他功能（GitHub、Discourse）完全不受影响
- 确保移除后所有测试通过
- 简化 `get-key-contributors-activity` 为两平台（GitHub + Discourse）

**Non-Goals:**
- 不引入新的数据源替代 Slack
- 不重构其他不相关的代码
- 不修改归档（archive）中的历史变更记录

## Decisions

### Decision 1: 直接删除而非软禁用

直接删除所有 Slack 相关代码，而非通过 feature flag 或条件判断禁用。

**理由**: Slack 信源已明确不再需要，软禁用只会留下死代码。符合 simplicity first 原则。

**替代方案**: 保留代码但默认禁用 → 增加维护负担，无实际价值。

### Decision 2: 移除 playwright 可选依赖

`playwright` 在项目中仅用于 Slack token 自动提取。移除 Slack 后，`playwright` 不再有任何用途，应同步移除。

**理由**: 减少依赖树，`pyproject.toml` 中的 `slack-auto` extra 和 `playwright` 依赖都只服务于 Slack。

### Decision 3: contributor-activity tool 签名变更

从 `get_key_contributors_activity` 函数签名中移除 `slack_client` 参数，移除 `_fetch_slack_activity` 函数，以及 Slack 相关的 platform notes 处理。

**理由**: 保留无用参数会造成困惑。server.py 中的调用点也需同步修改。

### Decision 4: 归档 Slack 相关 specs

将 `openspec/specs/slack-data/` 和 `openspec/specs/auto-token-extraction/` 目录删除（它们的历史已保留在 archive 中的旧变更里）。

**理由**: 这些 specs 描述的能力已不存在，保留会误导。

### Decision 5: 逐步移除，由外向内

移除顺序：先改引用方（server、contributors、config、__init__）→ 再删被引用的纯 Slack 文件（client、tool、token_extractor）→ 修改测试 → 更新文档和配置。

**理由**: 由外向内遵循依赖方向，确保每步中间状态都可正常 import 和运行测试。如果先删被引用文件，消费方会立即出现 import 断裂。

## Risks / Trade-offs

- **[风险] 遗漏引用** → 移除后运行全量测试 + grep 搜索 "slack"/"Slack" 确保无残留引用
- **[风险] uv.lock 不同步** → 修改 pyproject.toml 后执行 `uv lock` 重新生成
- **[风险] contributor tool 行为变化对下游的影响** → 这是 BREAKING change，但 Slack 数据已不可用，实际无影响
