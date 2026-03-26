## 1. Test Infrastructure Setup

- [x] 1.1 Add `pytest-cov>=5.0` to `[project.optional-dependencies] dev` in `pyproject.toml`
- [x] 1.2 Add `[tool.pytest.ini_options]` with `asyncio_mode = "auto"` to `pyproject.toml`
- [x] 1.3 Add `[tool.coverage.run]` with `source = ["src/pytorch_community_mcp"]` and `omit = ["**/token_extractor.py"]` to `pyproject.toml`
- [x] 1.4 Add `[tool.coverage.report]` with `fail_under = 80` and `show_missing = true` to `pyproject.toml`
- [x] 1.5 Create `tests/conftest.py` with shared `make_mock_issue` fixture (extract from existing `_make_mock_issue` helper in `test_tools.py`) and a `mock_async_client` fixture (extract from existing `_mock_async_client` helper in `test_clients.py`)
- [x] 1.6 Update existing tests: remove `@pytest.mark.asyncio` decorators (now handled by `asyncio_mode = "auto"`) and use shared fixtures from conftest where applicable
- [x] 1.7 Run `uv run pytest --co` to verify all existing tests still collect correctly

## 2. GitHubClient Unit Tests

- [x] 2.1 Create `tests/test_github_client.py` with construction tests: `token=None` and `token="ghp_xxx"` verify default rate limit values
- [x] 2.2 Add `_update_rate_limit` tests: successful update reads `search.remaining/limit/reset`, GithubException is silently ignored
- [x] 2.3 Add `_wait_for_rate_limit` tests: no sleep when `remaining > 1`, correct sleep duration calculation, 60s cap, past reset time handling (all with mocked `time.sleep` and `time.time`)
- [x] 2.4 Add `search_issues` success tests: returns correct results, truncation at `max_results`, empty results
- [x] 2.5 Add `search_issues` RateLimitExceededException retry tests: single failure then success, exhausted retries returns `[]`, backoff duration increases (10, 20, 40...)
- [x] 2.6 Add `search_issues` GithubException retry tests: single failure then success, exhausted retries raises, `max_retries=1` raises immediately
- [x] 2.7 Run `uv run pytest tests/test_github_client.py -v` to verify all pass

## 3. Contributors Tool Unit Tests

- [x] 3.1 Create `tests/test_contributors_tool.py` with the main orchestration test: all three platforms succeed, items merged and sorted by date descending, no platform notes
- [x] 3.2 Add failure isolation tests: GitHub exception → "GitHub: unavailable" note, Slack returns None → "Slack: not configured" note, Slack exception → "Slack: unavailable" note, Discourse exception → "Discourse: unavailable" note
- [x] 3.3 Add all-platforms-fail test: empty items, three platform notes
- [x] 3.4 Add `_fetch_github_activity` unit tests: date range construction with/without `since`, item formatting for PRs and Issues, `body=None` handling
- [x] 3.5 Add `_fetch_slack_activity` unit tests: `client.available=False` returns None, `SlackAuthError` returns None, successful search returns formatted items
- [x] 3.6 Add `_fetch_discourse_activity` unit tests: URL construction with/without slug+id, item formatting
- [x] 3.7 Add default `until` test: verify `until=None` defaults to `date.today().isoformat()`
- [x] 3.8 Run `uv run pytest tests/test_contributors_tool.py -v` to verify all pass

## 4. Integration Tests

- [x] 4.1 Create `tests/test_integration.py` with `Config.from_env()` mocked before server import (use `unittest.mock.patch` on `pytorch_community_mcp.config.Config.from_env` returning dummy config)
- [x] 4.2 Add tool registration test: verify 8 tools registered, correct names, non-empty descriptions
- [x] 4.3 Add parameter schema tests: `get_prs` requires `since`, `get_key_contributors_activity` requires `contributor`, `get_slack_threads` requires `channel`
- [x] 4.4 Add server metadata test: name is "PyTorch Community MCP", version is "0.1.0"
- [x] 4.5 Add sync tool invocation test: call `get_prs` through server with mocked `github_client`, verify formatted response
- [x] 4.6 Add async tool invocation test: call `get_discussions` through server with mocked `discourse_client`, verify formatted response
- [x] 4.7 Run `uv run pytest tests/test_integration.py -v` to verify all pass

## 5. Final Verification

- [x] 5.1 Run full test suite with coverage: `uv run pytest --cov --cov-report=term-missing` and verify coverage >= 80%
- [x] 5.2 If coverage is below 80%, identify remaining gaps and add targeted tests to close them
- [x] 5.3 Run `uv run pytest --cov --cov-fail-under=80` to verify the coverage gate works
