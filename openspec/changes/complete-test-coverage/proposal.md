## Why

The MCP server has significant test gaps — GitHubClient (rate limiting, retries, backoff) has zero tests, the `get_key_contributors_activity` tool (193 lines of cross-platform aggregation) is completely untested, and there are no integration tests verifying tool registration or MCP protocol compliance. There is also no coverage tooling or threshold, so regressions go unnoticed. This needs to be fixed before any further feature work to establish a reliable safety net.

## What Changes

- Add comprehensive unit tests for `GitHubClient` covering rate limit handling, exponential backoff, retry logic, pagination truncation, and error propagation
- Add comprehensive unit tests for `get_key_contributors_activity` tool and its three platform-specific fetch functions (`_fetch_github_activity`, `_fetch_slack_activity`, `_fetch_discourse_activity`)
- Add integration tests verifying all 8 tools are registered correctly with proper names, parameter schemas, and descriptions via FastMCP
- Add `pytest-cov` to dev dependencies with a coverage threshold (80%) and coverage configuration
- Add `conftest.py` with shared test fixtures to reduce mock duplication across test files
- Configure `pytest.ini_options` with `asyncio_mode = "auto"` to eliminate boilerplate `@pytest.mark.asyncio` decorators

## Capabilities

### New Capabilities
- `github-client-tests`: Unit tests for GitHubClient covering rate limits, retries, backoff, and pagination
- `contributors-tool-tests`: Unit tests for the contributors tool covering cross-platform aggregation, error isolation, and result formatting
- `integration-tests`: Integration tests verifying server tool registration, parameter schemas, and end-to-end tool invocation via FastMCP
- `coverage-gate`: pytest-cov configuration with fail_under threshold to prevent coverage regressions

### Modified Capabilities

_(none — no existing spec-level requirements are changing)_

## Impact

- **Files added**: `tests/conftest.py`, `tests/test_github_client.py`, `tests/test_contributors_tool.py`, `tests/test_integration.py`
- **Files modified**: `pyproject.toml` (dev deps, pytest config, coverage config)
- **Dependencies added**: `pytest-cov>=5.0`
- **CI impact**: Test suite will fail if coverage drops below 80%
- **No runtime code changes** — this is purely test infrastructure
