## 1. Safe Date Parsing & RSS Timeout (Foundation)

- [x] 1.1 TDD: Write tests for `safe_parse_date()` in `tests/test_formatter.py` — valid ISO datetime, date-only, empty string, non-date string
- [x] 1.2 Implement `safe_parse_date()` in `formatter.py`
- [x] 1.3 TDD: Write test for `RSSClient` timeout — mock httpx to raise `httpx.TimeoutException`, assert it propagates
- [x] 1.4 Refactor `RSSClient.get_entries()` to use `httpx` for fetching + `feedparser.parse(xml_string)` for parsing, with `timeout=15.0`

## 2. Events Tool — Parameter Rename & Error Handling

- [x] 2.1 TDD: Write tests for `get_events` tool in `tests/test_tools.py` — success path with `since/until` params, API error path, timeout path
- [x] 2.2 Rename `get_events` parameters from `start_date/end_date` to `since/until` in `tools/events.py`, `clients/events.py`, and `server.py`
- [x] 2.3 Replace `except Exception` with specific `httpx.HTTPError` catch in `tools/events.py`
- [x] 2.4 TDD: Write tests for `get_blog_news` tool — success path, RSS fetch error path
- [x] 2.5 Add error handling in `tools/events.py:get_blog_news()` — catch `httpx.HTTPError` and return `format_error`

## 3. GitHub Tools — Error Handling

- [x] 3.1 TDD: Write tests for `get_prs` tool in `tests/test_tools.py` — success path, GithubException on search, empty results
- [x] 3.2 Add try/except to `tools/prs.py` — catch `GithubException`, return `format_error("GitHubError", ...)`
- [x] 3.3 TDD: Write tests for `get_issues` tool — success path, GithubException, empty results
- [x] 3.4 Add try/except to `tools/issues.py` — catch `GithubException`, return `format_error("GitHubError", ...)`
- [x] 3.5 TDD: Write tests for `get_rfcs` tool — success path, GithubException
- [x] 3.6 Add try/except to `tools/rfcs.py` — catch `GithubException`, return `format_error("GitHubError", ...)`

## 4. Discourse Tool — Error Handling

- [x] 4.1 TDD: Write tests for `get_discussions` tool in `tests/test_tools.py` — success path, HTTP error, timeout
- [x] 4.2 Add try/except to `tools/discussions.py` — catch `httpx.HTTPError`, return `format_error("DiscourseError", ...)`

## 5. Date Parsing Migration

- [x] 5.1 Replace `topic.get("created_at", "")[:10]` with `safe_parse_date()` in `tools/discussions.py`
- [x] 5.2 Replace `event.get("start_date", "")[:10]` and `event.get("end_date", "")[:10]` with `safe_parse_date()` in `tools/events.py`
- [x] 5.3 Replace `topic.get("created_at", "")[:10]` with `safe_parse_date()` in `tools/contributors.py` (Discourse section)
- [x] 5.4 Replace `msg.get("ts", "")[:10]` with `safe_parse_date()` in `tools/contributors.py` (Slack section)

## 6. Verify All Tests Pass

- [x] 6.1 Run full test suite (`pytest tests/ -v`), confirm all existing + new tests pass
