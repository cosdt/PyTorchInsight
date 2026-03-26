## Why

当前 MCP server 的 7 个 tool 中，只有 Slack tool 有完整的错误处理链。其余 6 个 tool 在 API 出错时直接抛出原始异常（`GithubException`、`httpx.HTTPStatusError`），agent 看到的是 Python stack trace 而非可操作的错误信息。此外，tool 间参数命名不一致（`since/until` vs `start_date/end_date`）、日期处理用字符串切片而非解析、错误消息格式不统一，降低了 agent 的调用可靠性。

## What Changes

- 所有 tool 函数增加 try/except 错误处理，API 异常一律通过 `format_error()` 返回结构化错误信息
- **BREAKING** `get-events` 参数 `start_date` → `since`、`end_date` → `until`，统一全局命名
- 所有日期字段使用 `datetime` 解析而非 `[:10]` 字符串切片
- 为 RSS client 和 Events client 增加请求超时
- 为 Discourse client 增加 HTTP 错误处理
- 采用 TDD 范式：先写 tool 层测试，再实现错误处理

## Capabilities

### New Capabilities

_None — this change hardens existing capabilities._

### Modified Capabilities

- `github-data`: 增加 tool 层异常处理场景（API 错误、token 无效返回 format_error 而非 crash）
- `discourse-data`: 增加 API 错误处理场景（HTTP 错误、超时返回 format_error）
- `events-data`: **BREAKING** 参数重命名 `start_date→since`、`end_date→until`；增加超时处理；RSS 增加超时
- `unified-output`: 增加错误消息必须包含可操作的 resolution 指引的要求

## Impact

- **代码**: `tools/*.py`（所有 7 个 tool 文件）、`clients/discourse.py`（错误处理）、`clients/events.py`（超时）、`clients/rss.py`（超时）、`server.py`（参数重命名）
- **测试**: 新增 `tests/test_tools.py`（tool 层完整测试覆盖，TDD 先写）
- **API**: `get-events` 参数名变更（**BREAKING**）
- **依赖**: 无新增依赖
