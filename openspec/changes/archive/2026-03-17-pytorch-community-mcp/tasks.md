## 1. Project Scaffolding

- [x] 1.1 Create `pyproject.toml` with project metadata and dependencies (mcp[cli], PyGithub, httpx, feedparser)
- [x] 1.2 Create package directory structure: `src/pytorch_community_mcp/` with `__init__.py`, `server.py`, `config.py`
- [x] 1.3 Create `src/pytorch_community_mcp/tools/__init__.py` and `src/pytorch_community_mcp/clients/__init__.py`
- [x] 1.4 Implement `config.py` — read environment variables (GITHUB_TOKEN, SLACK_XOXC_TOKEN, SLACK_XOXD_TOKEN, SLACK_XOXP_TOKEN, DISCOURSE_API_KEY, DISCOURSE_API_USERNAME) with validation

## 2. Unified Output Formatter

- [x] 2.1 Implement `formatter.py` — `format_results()` function that takes tool name, parameters, items list and returns unified Markdown (## Summary + ## Results)
- [x] 2.2 Implement `format_error()` function for standardized error responses (## Error section with type, message, resolution)
- [x] 2.3 Implement rate limit warning injection (blockquote note when GitHub quota is low)

## 3. GitHub Client & Tools

- [x] 3.1 Implement `clients/github.py` — PyGithub wrapper with rate limit awareness, exponential backoff, and remaining quota tracking
- [x] 3.2 Implement `tools/prs.py` — `get-prs` tool (since, until, module params; search pytorch/pytorch; label-based module filtering)
- [x] 3.3 Implement `tools/issues.py` — `get-issues` tool (since, until, module, state params; search pytorch/pytorch)
- [x] 3.4 Implement `tools/rfcs.py` — `get-rfcs` tool (since, status params; search pytorch/pytorch + pytorch/rfcs; merge and deduplicate results)

## 4. Slack Client & Tools

- [x] 4.1 Implement `clients/slack.py` — httpx-based Slack API client supporting both xoxc/xoxd and xoxp authentication modes
- [x] 4.2 Implement `tools/slack.py` — `get-slack-threads` tool (channel, since, until, query params; search.messages API call; format results)
- [x] 4.3 Implement token expiry detection — catch 401/invalid_auth and return actionable error message

## 5. Discourse Client & Tools

- [x] 5.1 Implement `clients/discourse.py` — httpx-based Discourse API client with optional API key auth, targeting discuss.pytorch.org
- [x] 5.2 Implement `tools/discussions.py` — `get-discussions` tool (query, category, since, until params; use Discourse search syntax with after:/before: operators; note truncation at 50 results)

## 6. Events & RSS Client & Tools

- [x] 6.1 Implement `clients/events.py` — httpx client for pytorch.org/wp-json/tec/v1/events with start_date, end_date, search params
- [x] 6.2 Implement `clients/rss.py` — feedparser wrapper for pytorch.org/feed/
- [x] 6.3 Implement `tools/events.py` — `get-events` tool (start_date, end_date, search, featured params)
- [x] 6.4 Implement `tools/events.py` — `get-blog-news` tool (since, limit params; parse RSS feed; filter by date)

## 7. Contributor Activity Tool

- [x] 7.1 Implement `tools/contributors.py` — `get-key-contributors-activity` tool (contributor, since, until params; query GitHub + Slack + Discourse in parallel; merge into cross-platform summary)
- [x] 7.2 Handle partial platform data — return available data with notes for unavailable platforms

## 8. Server Entry Point

- [x] 8.1 Implement `server.py` — FastMCP server initialization, register all tools, configure stdio transport
- [x] 8.2 Add `__main__.py` entry point for `python -m pytorch_community_mcp`

## 9. Testing & Documentation

- [x] 9.1 Add basic tests for formatter.py (output format validation)
- [x] 9.2 Add basic tests for each client (mock API responses)
- [x] 9.3 Write setup documentation — environment variable configuration, slack-token-extractor usage, MCP client connection instructions
