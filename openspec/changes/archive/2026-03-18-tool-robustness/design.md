## Context

当前 MCP server 有 7 个 tool，分布在 `tools/*.py`。错误处理现状：

| Tool | 有 try/except | 用 format_error | 备注 |
|------|:---:|:---:|------|
| get_prs | ✗ | ✗ | GithubException 直接抛出 |
| get_issues | ✗ | ✗ | 同上 |
| get_rfcs | ✗ | ✗ | 同上，且做 3 次 GitHub 搜索 |
| get_slack_threads | ✓ | ✓ | 唯一完整的 |
| get_discussions | ✗ | ✗ | httpx.HTTPStatusError 直接抛出 |
| get_events | ✓ | ✓ | 但 broad `except Exception` |
| get_blog_news | ✗ | ✗ | feedparser 无 timeout，可阻塞 |
| contributors | 部分 | ✗ | 用 `return_exceptions=True`，但 format 不统一 |

参数命名不一致：`get_events` 用 `start_date/end_date`，其余用 `since/until`。
日期处理：Discourse 和 Events 用 `[:10]` 字符串切片获取 ISO date，不安全。

### 约束
- TDD 范式：每个改动先写测试再实现
- 不引入新依赖
- 保持 `format_results()` / `format_error()` 现有签名
- 向后兼容：除 `get_events` 参数重命名外，不改变 tool 外部行为

## Goals / Non-Goals

**Goals:**
- 所有 tool 的 API 异常通过 `format_error()` 返回，不再 crash
- 统一参数命名为 `since/until`（`get_events` breaking change）
- 日期字段使用 `datetime` 解析而非字符串切片
- 为缺少 timeout 的 client（RSS、Events）增加超时保护
- 为缺少错误处理的 client（Discourse）增加异常捕获
- Tool 层达到完整测试覆盖
- TDD：测试先行

**Non-Goals:**
- 不做分页支持（单独 change）
- 不替换 PyGithub 为异步库（scope 太大）
- 不做输入参数格式校验（如验证 ISO date 格式）
- 不修改 `format_results` / `format_error` 的签名或输出结构
- 不增加日志（单独 change）

## Decisions

### D1: Tool 层统一错误处理模式

**选择**: 在每个 tool 函数中用 try/except 包裹核心逻辑，按异常类型映射到 `format_error()`

```python
# Pattern for all tools:
try:
    results = client.search_issues(query)
except GithubException as e:
    return format_error("GitHubError", str(e), "Check GITHUB_TOKEN is valid and has required scopes.")
```

**替代方案**: 装饰器统一捕获异常

**理由**: 不同 tool 需要不同的错误提示和 resolution 文案，装饰器无法区分。模式简单、显式、可读。

### D2: Events 参数从 start_date/end_date 改为 since/until

**选择**: `get_events` 的参数名和 `EventsClient.get_events` 的参数名同步重命名

**替代方案**: 只在 tool 层做参数映射（tool 接收 since/until，内部转成 start_date/end_date 传给 client）

**理由**: 参数映射会增加一层间接性。直接重命名更简洁，且 client 是内部 API，无外部消费者。`server.py` 中的 tool 定义也需同步改名。

### D3: 安全的日期解析辅助函数

**选择**: 在 `formatter.py` 中新增 `safe_parse_date(value: str) -> str` 辅助函数

```python
def safe_parse_date(value: str) -> str:
    """Try to parse a date string and return ISO date, or return as-is."""
    try:
        return datetime.fromisoformat(value).strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return value[:10] if value else ""
```

**理由**: 优先使用 `datetime.fromisoformat` 解析，解析失败时 fallback 到 `[:10]` 保证不 crash。集中在一处，所有 tool 复用。

### D4: RSS/Events/Discourse 超时和错误处理

**选择**:
- RSS: 给 `feedparser.parse()` 传入 `request_headers` + 用 `httpx` 替代默认 urllib（feedparser 原生不支持 timeout）→ 改为用 `httpx` 下载 feed XML，再 `feedparser.parse(xml_string)` 解析
- Events: 已有 `timeout=30.0`，保持不变
- Discourse: 已有 `timeout=30.0`，但 `raise_for_status()` 的异常需在 tool 层捕获

**替代方案**: 给 feedparser 包一层 signal 超时

**理由**: httpx + feedparser string parse 是最可靠的方案，无需处理 signal 在非主线程的问题。Events 和 Discourse 的 httpx 调用已有 timeout，只需在 tool 层捕获 `httpx.HTTPStatusError` 和 `httpx.TimeoutException`。

### D5: TDD 工作流程

**选择**: 每个 tool 的改造分两步：
1. 先写测试文件 `tests/test_tools.py`，覆盖正常路径和错误路径
2. 再修改 tool 代码使测试通过

**理由**: 测试先行确保错误处理逻辑有明确的预期行为，不遗漏场景。

## Risks / Trade-offs

**[Breaking change: get_events 参数]** → `start_date/end_date` → `since/until`。任何直接调用此 MCP tool 的 agent prompt 需要更新。缓解：这是 v0.1 产品，用户面窄。

**[RSS timeout 实现变更]** → 从 feedparser 原生 URL 获取改为 httpx + 字符串解析，可能遇到 feedparser 对非 URL 输入的边界行为。缓解：feedparser 官方支持字符串输入。

**[broad except 风险]** → Discourse/Events 的 tool 层会捕获 `httpx.HTTPError`（covers timeout + status），可能掩盖编程错误。缓解：只捕获 httpx 和已知 client 异常，不用 bare `except`。
