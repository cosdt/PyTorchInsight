## 1. Token Extractor Module

- [x] 1.1 Create `src/pytorch_community_mcp/token_extractor.py` with core functions ported from `playwright_extract.py`: `load_tokens_from_file()`, `validate_tokens()`, `try_extract_from_local_chrome()`, `save_tokens()`, plus `PLAYWRIGHT_AVAILABLE` runtime flag
- [x] 1.2 Add `playwright` as optional dependency in `pyproject.toml` under `[project.optional-dependencies]` as `slack-auto = ["playwright"]`

## 2. Config Layer Changes

- [x] 2.1 Change `SlackConfig` from `frozen=True` to mutable dataclass, add `resolve()` classmethod implementing three-phase token resolution (env vars → saved file → Chrome extraction)
- [x] 2.2 Add `refresh()` method to `SlackConfig` that re-runs Phase 2 and Phase 3 (skip env vars) and updates token fields in place
- [x] 2.3 Update `Config.from_env()` to call `SlackConfig.resolve()` instead of directly reading env vars

## 3. Slack Client Changes

- [x] 3.1 Add `update_tokens(xoxc, xoxd)` method to `SlackClient` for runtime token replacement
- [x] 3.2 Add `refresh_callback` parameter to `SlackClient.__init__()` — an optional callable that attempts token refresh and returns `(xoxc, xoxd)` or `None`
- [x] 3.3 Update `search_messages()` to catch `SlackAuthError`, invoke `refresh_callback`, call `update_tokens()`, and retry once on success

## 4. Server Startup Integration

- [x] 4.1 Update `server.py` to wire `SlackConfig.refresh()` as the `SlackClient` refresh callback
- [x] 4.2 Update the Slack tool error message to include auto-extraction guidance when `playwright` is not installed

## 5. Tests

- [x] 5.1 Unit tests for `token_extractor.py`: `load_tokens_from_file()` with valid/invalid/missing files, `validate_tokens()` mock, `PLAYWRIGHT_AVAILABLE` flag when playwright not installed
- [x] 5.2 Unit tests for `SlackConfig.resolve()`: env var priority, saved file fallback, all-fail case
- [x] 5.3 Unit tests for `SlackClient` retry: auth error triggers refresh callback, successful retry, failed retry raises original error
