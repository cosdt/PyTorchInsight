## 1. Dependencies

- [x] 1.1 Add `requests-cache >= 1.0` to `pyproject.toml` runtime dependencies; add `responses >= 0.25` to `[dev]` dependencies
- [x] 1.2 Run `uv lock` to update lock file

## 2. Cache Installation

- [x] 2.1 Add cache installation in `GitHubClient.__init__` **before** `Github()` constructor, with `requests_cache.is_installed()` idempotency guard. SQLite backend at `~/.cache/pytorch-community-mcp/http_cache.sqlite`, auto-creating directory via `os.makedirs(exist_ok=True)`
- [x] 2.2 Configure per-URL TTL: `rate_limit` → `requests_cache.DO_NOT_CACHE`, `search/issues` → 120s, `pulls/issues/commits` → 300s, default → 300s
- [x] 2.3 Do NOT enable `stale_if_error` (requests-cache applies it to ALL errors including 4xx, which would mask auth failures). Errors propagate normally to existing retry/backoff.
- [x] 2.4 Add startup cache cleanup inside idempotency guard: `requests_cache.get_cache().delete(expired=True)` after `install_cache()`

## 3. API Call Statistics

- [x] 3.1 Hook `CachedSession.send()` after `install_cache()` to count cache hits/misses via `response.from_cache` attribute. Maintain `_cache_hits` and `_cache_total` counters on `GitHubClient` instance. Note: requests-cache has NO built-in counters — must self-implement.
- [x] 3.2 Add `snapshot_stats() -> tuple[int, int]` and `get_stats(snapshot) -> dict` methods to `GitHubClient`. Per-call snapshot model prevents race conditions in FastMCP's thread pool. Returns `{total: int, cached: int, fresh: int}`.
- [x] 3.3 Add `_append_api_stats(result: str, stats: dict) -> str` helper in `server.py` that appends `**API Calls:** N total (X cached, Y fresh)` to Markdown output
- [x] 3.4 Update each `@mcp.tool` wrapper in `server.py` (7 GitHub tools) to call `snapshot_stats()` before and `get_stats()` after, passing result through `_append_api_stats()`. Tool implementation files (`tools/*.py`) and `formatter.py` require NO changes.

## 4. Tests — Cache

- [x] 4.0 Verify all existing tests pass with cache installed (smoke test — run first to confirm no regressions)
- [x] 4.1 Test: cache persists across `GitHubClient` re-instantiation (use `responses` library to mock HTTP, verify second request hits cache)
- [x] 4.2 Test: idempotent installation — multiple `GitHubClient()` calls result in only one `install_cache()` invocation
- [x] 4.3 Test: rate_limit endpoint is NOT cached (request always passes through — verify via `responses` call count or `session.cache.urls()`)
- [x] 4.4 Test: per-URL TTL configured correctly (verify `CachedResponse.expires` delta matches configured TTL — no sleep needed)
- [x] 4.5 Test: ETag conditional request behavior (use `responses` callback to return 304 when If-None-Match present → verify cached body returned; 200 with new data → verify cache updated)
- [x] 4.6 Test: errors propagate normally — 5xx response raises exception (no stale fallback)
- [x] 4.7 Test: errors propagate normally — network timeout/connection error raises exception
- [x] 4.8 Test: 4xx errors (401/403) propagate normally — NOT masked by any cache behavior
- [x] 4.9 Test: cache directory is auto-created when it does not exist (use `tmp_path` fixture)
- [x] 4.10 Test: startup cleanup — populate cache with expired entries, instantiate `GitHubClient`, verify expired entries removed
- [x] 4.11 Test: httpx-based clients (Slack, Discourse, Events, RSS) are not affected by the cache monkey-patch
- [x] 4.12 Add function-scope autouse fixture in `conftest.py` that calls `requests_cache.uninstall_cache()` before AND after each test, ensuring test isolation

## 5. Tests — API Call Statistics

- [x] 5.1 Test: `snapshot_stats()` / `get_stats(snapshot)` returns correct delta (use `responses` to mock 3 requests, 1 cached → stats show total=3, cached=1, fresh=2)
- [x] 5.2 Test: `get_stats()` without cache installed returns `{total: 0, cached: 0, fresh: 0}`
- [x] 5.3 Test: `_append_api_stats()` correctly appends stats line to Markdown string
- [x] 5.4 Test: server.py wrapper integrates snapshot → tool call → stats append (end-to-end with mock client)

## 6. Validation

- [x] 6.1 Run e2e test against real GitHub API: cold run (all cache miss) → warm run (cache hits visible in API Calls stats)
- [x] 6.2 Verify cache file is created at expected path after first run
