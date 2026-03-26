## Context

The PyTorch Community MCP server has 20 source modules and 6 test files. Current estimated line coverage is ~40%. Two critical modules — `GitHubClient` (rate limit/retry logic) and `contributors.py` (cross-platform `asyncio.gather` aggregation) — have zero tests. There are no integration tests verifying tool registration. No coverage tooling exists.

Existing tests follow a consistent pattern: mock external HTTP clients, test the tool/client function directly, assert on output format. The project uses `pytest` + `pytest-asyncio` with `unittest.mock`.

Key constraint: `server.py` executes `config = Config.from_env()` at import time, which triggers Slack token resolution (file reads, network validation, Chrome extraction). Integration tests must isolate this.

## Goals / Non-Goals

**Goals:**
- Achieve >=80% line coverage across `src/pytorch_community_mcp` (excluding `token_extractor.py` Chrome extraction helpers)
- Test all GitHubClient behaviors: rate limiting, backoff, retry, pagination truncation, error propagation
- Test all contributors tool paths: three-platform parallel execution, error isolation, result merging/sorting, platform notes
- Verify all 8 tools are correctly registered with FastMCP (names, parameter schemas, descriptions)
- Establish coverage gate that fails CI on regression
- Reduce test boilerplate via shared fixtures in `conftest.py`

**Non-Goals:**
- Testing Chrome/Playwright token extraction (requires real browser, low ROI for mock cost)
- Testing `Config.from_env()` or `SlackConfig.resolve()` beyond what already exists
- End-to-end tests against real GitHub/Slack/Discourse APIs
- Refactoring production code to improve testability

## Decisions

### 1. Mock PyGithub at the instance level, not at import

**Decision:** Mock `self._github` (the `Github` instance) on `GitHubClient`, not the `github` module import.

**Why:** `GitHubClient.__init__` creates a `Github(token)` instance and stores it as `self._github`. Mocking at the instance level lets us test retry/backoff logic without touching the import system. This is also how the existing tool tests already mock the client (`MagicMock(spec=GitHubClient)`).

**Alternative considered:** Patching `github.Github` at import — more fragile, breaks if import path changes.

### 2. Mock `time.sleep` and `time.time` for backoff tests

**Decision:** Patch `time.sleep` and `time.time` in the `pytorch_community_mcp.clients.github` module to test wait/backoff behavior without real delays.

**Why:** `_wait_for_rate_limit()` and `search_issues()` both call `time.sleep`. Tests must verify the sleep duration calculations (backoff = 2^attempt * 10, capped at 60s) without actually waiting.

### 3. Test contributors tool by mocking the three client objects

**Decision:** Pass mock `GitHubClient`, `SlackClient`, and `DiscourseClient` instances directly to `get_key_contributors_activity()`.

**Why:** The function accepts clients as arguments — no patching needed. Mock each client's methods to return controlled data or raise exceptions. This naturally tests the `asyncio.gather(return_exceptions=True)` error isolation.

### 4. Integration tests: import `mcp` object, don't start stdio transport

**Decision:** Import the `mcp` FastMCP instance from `server.py` and use its internal registry to inspect registered tools. Mock `Config.from_env()` at import time to prevent real credential resolution.

**Why:** FastMCP stores tools in an accessible registry. We can verify tool names, parameter schemas, and descriptions without running the MCP protocol. This avoids the complexity of stdio transport testing while catching registration bugs (typos, missing params, wrong types).

**Alternative considered:** Using FastMCP's test client (`mcp.call_tool()`) for full E2E — included as a second-level integration test for key tools.

### 5. Coverage: omit token_extractor Chrome helpers, set threshold at 80%

**Decision:** Configure `coverage.run` to omit `token_extractor.py` entirely (its file I/O functions are already tested in `test_token_extractor.py`). Set `fail_under = 80`.

**Why:** Chrome extraction helpers depend on Playwright, real browser profiles, and filesystem state. Mocking all of that is high effort, low value. The 80% threshold is achievable with the planned new tests and leaves room for the remaining untested slack tool without blocking.

### 6. Add `asyncio_mode = "auto"` to pytest config

**Decision:** Set `asyncio_mode = "auto"` in `[tool.pytest.ini_options]` to auto-detect async test functions.

**Why:** Eliminates the need for `@pytest.mark.asyncio` on every async test. All existing and new async tests benefit. This is the recommended pytest-asyncio configuration.

## Risks / Trade-offs

- **Import-time side effects in server.py** → Mitigation: Patch `Config.from_env` before importing `server` in integration tests, or use `importlib.reload` with mocked config.
- **`asyncio_mode = "auto"` may affect existing tests** → Mitigation: Run existing test suite after config change to verify no regressions. Low risk since all existing async tests already use `@pytest.mark.asyncio`.
- **80% threshold may be too aggressive initially** → Mitigation: Start at 80%, adjust down if needed. The planned tests should comfortably exceed this for the non-omitted source files.
- **Mock fidelity for PyGithub objects** → Mitigation: Use `MagicMock` with careful attribute setup matching real PyGithub `Issue` objects (`.title`, `.html_url`, `.created_at`, `.body`, `.user.login`). The existing `_make_mock_issue` helper in `test_tools.py` is a good pattern to reuse.
