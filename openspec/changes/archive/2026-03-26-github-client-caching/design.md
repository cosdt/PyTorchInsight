# Design: GitHub Client HTTP 持久化缓存

## Context

openinsight 是此 MCP 的唯一消费者。其工作模式：

- 每次运行启动新的 MCP 进程（stdio transport），进程结束后 in-memory 缓存全部丢失
- 多 agent 并发调用 MCP tool（建议 concurrency ≤ 2）
- 典型调用链：list 查询（get_prs, get_issues, get_rfcs × 3 search）→ 筛选 → detail 查询（get_pr_detail, get_issue_detail × ≤30 items）
- 运行频率：每日或每周
- 单次运行发起 150-200+ GitHub HTTP 请求

当前 in-memory 缓存（`_repo_cache`, `_pr_cache`, `_issue_cache`, rate limit throttle）仅解决 session 内 object 级别的重复获取，不解决跨 session 复用。

### GitHub API 缓存特性

GitHub REST API 对缓存有良好支持：
- 响应头包含 `ETag` 和 `Last-Modified`
- 客户端可发送 `If-None-Match` / `If-Modified-Since` 条件请求
- **304 Not Modified 响应不计入 rate limit**（核心节省机制）
- 大多数 endpoint 返回 `Cache-Control: private, max-age=60`

## Goals / Non-Goals

**Goals:**
- 跨 session 的 GitHub API rate limit 消耗减少 50%+（通过 ETag 条件请求产生的 304）
- 对现有 tool 代码完全透明，不改变任何 API 签名或调用方式
- 缓存持久化到磁盘，跨 MCP 进程生命周期复用

**Non-Goals:**
- 不实现 application 级 delta 查询
- 不替换 PyGithub 库
- 不缓存 Slack/Discourse/Events/RSS 等非 GitHub 数据源
- 不做 GraphQL 迁移

## Decisions

### Decision 1: 使用 `requests-cache` 全局安装

**选择**：通过 `requests_cache.install_cache()` 全局 monkey-patch `requests.Session`。

**理由**：
- PyGithub 内部创建 `requests.Session`，不暴露自定义 Session 的接口（PyGithub issue #2865 仍 open）
- `requests_cache.install_cache()` 是该库推荐的 application-level 集成方式，且 requests-cache 官方仓库中有专门的 PyGithub 集成示例（`examples/pygithub.py`）
- 全局 patch 只影响 `requests.Session`，其他 client（Slack/Discourse/Events/RSS）使用 `httpx`，不受影响
- 替代方案调研结论：CacheControl（PSF 维护，无 SQLite 后端、无 per-URL TTL）、hishel（无全局 patch 机制，无法透明集成 PyGithub）、PyGithub 内置 ETag（issue #536 自 2017 年 open 至今未实现）均不可行。requests-cache 是此场景的唯一可行方案

### Decision 2: SQLite 后端 + 文件位置

**选择**：SQLite 后端，存储在 `~/.cache/pytorch-community-mcp/http_cache.sqlite`。

**理由**：
- SQLite 是 requests-cache 最成熟的后端，支持 WAL 模式并发读
- `~/.cache/` 是 XDG 规范的缓存目录，用户清理缓存时自然会清除
- 单文件便于管理和调试
- 替代方案（文件系统后端）在大量缓存条目时性能较差

### Decision 3: Per-URL TTL 策略

**选择**：按 endpoint 类型配置不同的 TTL。`rate_limit` endpoint 不缓存。

| URL Pattern | TTL | 理由 |
|---|---|---|
| `*/rate_limit` | **不缓存** | `_wait_for_rate_limit(force=True)` 依赖实时数据做限额门控。缓存此 endpoint 会导致 force=True 拿到旧的 remaining 值，完全破坏 rate limit 感知的实时性。此 endpoint 响应极小（几百字节），调用频率也低（每分钟最多 1 次），缓存收益微乎其微 |
| `*/search/issues*` | 120s | search 结果变化频繁，但 2 分钟内重复查询大概率相同 |
| `*/pulls/*`, `*/issues/*` | 300s | detail 数据短期内稳定 |
| `*/commits*` | 300s | commit 历史不可变 |
| 其他 | 300s | 保守默认值 |

TTL 过期后，requests-cache 自动发送带 `If-None-Match` 的条件请求。304 = 缓存命中（免费），200 = 更新缓存。

### Decision 4: 缓存安装时机与幂等性

**选择**：在 `GitHubClient.__init__` 中、`Github()` 构造之前安装缓存，并使用 `requests_cache.is_installed()` 幂等守卫。

```python
def __init__(self, token: str | None = None) -> None:
    if not requests_cache.is_installed():
        requests_cache.install_cache(...)
        requests_cache.get_cache().delete(expired=True)  # 启动清理
    self._github = Github(...)  # Session 创建在 install_cache 之后
```

**理由**：
- `install_cache()` 必须在 `Github()` 之前调用。虽然 PyGithub 当前懒加载 Session（`Requester.__connection = None`），但将安装放在前面更稳健，不依赖 PyGithub 内部实现细节
- 幂等守卫防止测试中多次实例化 `GitHubClient` 导致重复安装（每次 `install_cache()` 会创建新的后端实例，泄漏旧 SQLite 连接）
- 启动清理放在幂等守卫内部，仅首次安装时执行
- 避免 import 副作用（模块级 monkey-patch 会影响测试）

### Decision 5: 不使用 stale_if_error

**选择**：**不启用** `stale_if_error`。错误处理完全依赖现有的 retry/backoff 机制。

**理由**：
- requests-cache 的 `stale_if_error=True` **会对 4xx 错误也触发 stale fallback**（经源码验证：4xx → `raise_for_status()` → 异常被 `_handle_error` 捕获 → 返回过期缓存）。这意味着 token 失效（401）或权限撤销（403）时，系统会静默返回旧数据，掩盖认证问题。这是安全隐患。
- requests-cache 不提供 "仅对 5xx stale，4xx 正常传播" 的原生配置——`stale_if_error` 是 all-or-nothing 的
- 现有 `GitHubClient` 的 retry/backoff 机制（3 次重试 + 指数退避）已能处理瞬态错误
- 移除此功能简化了行为模型，消除了 "什么类型的错误会返回旧数据" 的歧义

**被否决的替代方案**：
- `stale_if_error=True` + 自定义 hook 拦截 4xx：增加复杂度，hook 与 requests-cache 内部实现耦合
- `allowable_codes=(200, 400, 401, 403, 404)`：会导致 4xx 响应被缓存写入，不可接受

### Decision 6: API 调用统计（可观测性）

**选择**：`GitHubClient` 提供 per-call 统计能力。统计注入在 `server.py` 的 tool wrapper 层完成，tool 实现代码零侵入。

**实现方式**：

1. **统计计数器**：在 `install_cache()` 后，hook `CachedSession.send()` 方法。每次 HTTP 响应后，检查 `response.from_cache` 属性累加计数器。requests-cache 无内置 hit/miss 计数器，需自行实现。

2. **Per-call snapshot（防并发竞争）**：
   ```python
   def snapshot_stats(self) -> tuple[int, int]:
       """Return current (hits, total) for later delta computation."""
       return (self._cache_hits, self._cache_total)

   def get_stats(self, snapshot: tuple[int, int]) -> dict:
       """Compute delta since snapshot."""
       prev_hits, prev_total = snapshot
       total = self._cache_total - prev_total
       cached = self._cache_hits - prev_hits
       return {"total": total, "cached": cached, "fresh": total - cached}
   ```
   FastMCP 线程池可能并发执行 tool。per-call snapshot 避免共享可变状态竞争——每个 wrapper 持有自己的 snapshot token（局部变量）。

3. **server.py wrapper 层注入**（零侵入 tool 代码）：
   ```python
   @mcp.tool
   def get_prs(...) -> str:
       snap = github_client.snapshot_stats()
       result = prs_tool.get_prs(github_client, ...)
       return _append_api_stats(result, github_client.get_stats(snap))
   ```
   - `_append_api_stats()` 将统计行追加到 Markdown 字符串末尾
   - `formatter.py` 不需要改动（无新参数）
   - 7 个 tool 文件不需要改动（零侵入）
   - `pr_detail.py` / `issue_detail.py`（不使用 `format_results`）也自然覆盖

4. **输出格式**：`**API Calls:** 4 total (2 cached, 2 fresh)`
   - `cached` 包含 TTL 内直接命中 + 304 条件复用（对 agent 而言都是"免费"的）
   - `fresh` = 实际消耗 rate limit 配额的 200 响应

**理由**：
- openinsight 的 agent 可以量化对比：同一查询通过此 MCP 的实际 API 消耗 vs 直接使用 GitHub MCP 的调用次数
- server.py wrapper 层注入消除了散弹式修改（7 个 tool 文件 → 仅 server.py）
- per-call snapshot 在并发环境下线程安全

### Decision 7: 启动时清理过期缓存

**选择**：在 `install_cache()` 后立即调用 `cache.delete(expired=True)` 清理过期条目。放在 Decision 4 的幂等守卫内部，仅首次安装时执行。

**理由**：
- 防止 SQLite 文件长期膨胀（过期条目不会自动从文件中删除，只是不再被使用）
- 每次 MCP 进程启动时清理一次，开销极低（单次 SQL DELETE）
- 比定时清理更简单，且与进程生命周期自然对齐

## Risks / Trade-offs

- **[全局 monkey-patch]** → 仅影响 `requests.Session`。httpx-based clients（Slack/Discourse/Events/RSS）不受影响。如果未来有其他 `requests`-based 代码被引入，也会被缓存——但这个 MCP 中只有 PyGithub 用 requests。
- **[SQLite 并发写入]** → FastMCP 线程池可能并发调用 tool。requests-cache 的 SQLite 后端使用 `threading.RLock` + `check_same_thread=False`，支持并发读 + 序列化写。最坏情况：并发写时有短暂 lock wait，不会导致数据损坏。
- **[缓存数据膨胀]** → 启动时 `cache.delete(expired=True)` 自动清理。pytorch/pytorch 的 detail 数据单条约 10-50KB，30 条 × 300s = 缓存稳态 ~1.5MB，不构成存储问题。
- **[PyGithub 内部 Session 变化]** → PyGithub 通过 `requests.Session` 发起 HTTP 调用是其核心设计的一部分，极不可能改变。requests-cache 的 install_cache 也是 requests 生态中的标准做法。风险极低。
- **[缓存一致性]** → TTL + ETag 双重机制保障。TTL 内使用缓存避免不必要调用；TTL 过期后通过 ETag 验证。唯一的一致性窗口是 TTL 期间数据可能是旧的——对于 openinsight 的报告生成场景（非实时），这是可接受的。
- **[无 stale fallback]** → 移除 `stale_if_error` 意味着 GitHub 5xx/网络错误时不会返回旧数据。但现有 retry/backoff（3 次 × 指数退避）已覆盖瞬态错误。对于持续性故障，"无数据"比"旧数据"更安全——agent 能感知到问题而非得到过时信息。
- **[与现有 in-memory 缓存共存]** → HTTP 缓存（跨 session 复用 JSON 响应）与现有 application 缓存（`_repo_cache`/`_pr_cache`/`_issue_cache`，session 内复用已反序列化的对象）职责不重叠。前者减少 HTTP 调用，后者减少重复反序列化和 API 编排。两层保留，无冲突。
