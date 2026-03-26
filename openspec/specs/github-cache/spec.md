### Requirement: HTTP persistent cache
The system SHALL persist GitHub API HTTP responses to a SQLite-backed cache on disk, so that responses survive MCP process restarts and can be reused across sessions. The cache file SHALL be stored at `~/.cache/pytorch-community-mcp/http_cache.sqlite`. The cache installation SHALL be idempotent — multiple `GitHubClient` instantiations SHALL NOT cause redundant cache installations (use `requests_cache.is_installed()` guard).

#### Scenario: Cache persists across process restarts
- **WHEN** a tool call fetches data from GitHub, the MCP process terminates, and a new MCP process starts and makes the same request within the TTL window
- **THEN** the response is served from the on-disk cache (verifiable via `response.from_cache == True`)

#### Scenario: Cache directory auto-creation
- **WHEN** the cache directory `~/.cache/pytorch-community-mcp/` does not exist
- **THEN** the system SHALL create it automatically on first use

#### Scenario: Idempotent cache installation
- **WHEN** `GitHubClient` is instantiated multiple times (e.g., in tests)
- **THEN** `install_cache()` SHALL only execute once (guarded by `requests_cache.is_installed()`)

### Requirement: ETag conditional requests
The system SHALL use HTTP conditional requests (`If-None-Match` with `ETag`) when a cached response has expired. A 304 Not Modified response from GitHub SHALL be treated as a cache hit, reusing the stored response body. 304 responses do not count against GitHub's rate limit.

#### Scenario: Conditional request returns 304
- **WHEN** a cached response has expired and the system sends a request with `If-None-Match` header
- **AND** GitHub returns 304 Not Modified
- **THEN** the system SHALL return the previously cached response body

#### Scenario: Conditional request returns 200
- **WHEN** a cached response has expired and the system sends a request with `If-None-Match` header
- **AND** GitHub returns 200 OK with new data
- **THEN** the system SHALL update the cache with the new response and return the new data

### Requirement: Per-URL TTL configuration
The system SHALL apply different cache TTLs based on the GitHub API endpoint pattern. The `rate_limit` endpoint SHALL NOT be cached, to preserve the real-time accuracy of rate limit awareness.

| URL Pattern | TTL |
|---|---|
| `*/rate_limit` | **Not cached** (requests pass through) |
| `*/search/issues*` | 120 seconds |
| `*/pulls/*` | 300 seconds |
| `*/issues/*` | 300 seconds |
| `*/commits*` | 300 seconds |
| All other endpoints | 300 seconds |

#### Scenario: Rate limit endpoint is never cached
- **WHEN** the system calls the `GET /rate_limit` endpoint
- **THEN** the request SHALL always be sent to GitHub (no cache lookup, no cache storage)

#### Scenario: Search results use shorter TTL
- **WHEN** a `search/issues` response is cached
- **AND** 120 seconds have not elapsed since caching
- **THEN** the cached response SHALL be returned without contacting GitHub

#### Scenario: Search results expire after TTL
- **WHEN** a `search/issues` response was cached more than 120 seconds ago
- **THEN** the system SHALL send a conditional request to GitHub to validate the cache

#### Scenario: Detail endpoints use longer TTL
- **WHEN** a `pulls/{number}` or `issues/{number}` response is cached
- **AND** 300 seconds have not elapsed since caching
- **THEN** the cached response SHALL be returned without contacting GitHub

#### Scenario: Commits endpoint uses longer TTL
- **WHEN** a `commits` response is cached
- **AND** 300 seconds have not elapsed since caching
- **THEN** the cached response SHALL be returned without contacting GitHub

### Requirement: Errors propagate normally (no stale fallback)
The system SHALL NOT use `stale_if_error`. All HTTP errors (4xx, 5xx) and network errors SHALL propagate normally to the existing retry/backoff logic in `GitHubClient`. There is no stale cache fallback.

#### Scenario: 5xx error propagates to retry logic
- **WHEN** a request to GitHub returns a 5xx server error
- **THEN** the error SHALL propagate to `GitHubClient`'s existing retry/backoff mechanism

#### Scenario: 4xx error propagates normally
- **WHEN** a request to GitHub returns a 4xx client error (e.g., 401 Unauthorized, 403 Forbidden)
- **THEN** the error SHALL propagate normally (not masked by stale cache)

#### Scenario: Network error propagates to retry logic
- **WHEN** a request to GitHub fails with a network error
- **THEN** the error SHALL propagate to `GitHubClient`'s existing retry/backoff mechanism

### Requirement: Startup cache cleanup
The system SHALL delete expired cache entries from the SQLite database on first `GitHubClient` initialization (inside the idempotent guard), to prevent long-term database file growth.

#### Scenario: Expired entries cleaned on startup
- **WHEN** `GitHubClient` is initialized for the first time and the cache contains expired entries
- **THEN** the expired entries SHALL be removed from the SQLite database

### Requirement: API call statistics
The `GitHubClient` SHALL provide per-operation call statistics via `snapshot_stats()` and `get_stats(snapshot)`. Stats SHALL report: total HTTP requests, cache hits, and fresh API calls. The stats injection SHALL be done in `server.py` tool wrappers (not in tool implementation code).

#### Scenario: Tool response includes API call stats
- **WHEN** a tool call completes (e.g., `get_pr_detail`)
- **THEN** the response SHALL include a line: `**API Calls:** N total (X cached, Y fresh)`

#### Scenario: Stats are per-call via snapshot (thread-safe)
- **WHEN** two tools execute concurrently in the FastMCP thread pool
- **THEN** each tool's stats SHALL reflect only its own HTTP requests (via independent snapshot tokens)

#### Scenario: Stats work without cache installed
- **WHEN** the cache is not installed (e.g., in test environment)
- **AND** `get_stats()` is called
- **THEN** it SHALL return `{total: 0, cached: 0, fresh: 0}`

### Requirement: Transparent to tool layer
The HTTP cache SHALL operate at the transport layer. Tool code (`tools/*.py`) and `formatter.py` SHALL NOT require any changes. The only changes SHALL be in `GitHubClient` (cache + stats) and `server.py` (stats wrapper injection).

#### Scenario: Existing tools work unchanged
- **WHEN** the cache is installed
- **THEN** all existing MCP tools (`get_prs`, `get_issues`, `get_rfcs`, `get_commits`, `get_pr_detail`, `get_issue_detail`, `get_key_contributors_activity`) SHALL produce identical outputs for the same inputs (within TTL freshness window), plus an appended API stats line

#### Scenario: Non-GitHub clients unaffected
- **WHEN** the cache is installed via `requests.Session` monkey-patch
- **THEN** httpx-based clients (SlackClient, DiscourseClient, EventsClient, RSSClient) SHALL NOT be affected by the cache
