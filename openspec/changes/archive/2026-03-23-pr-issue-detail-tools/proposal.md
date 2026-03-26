## Why

Currently `get_prs` and `get_issues` only return high-level metadata (title, URL, date, author, state, labels, description). When analyzing PyTorch community activity, users frequently need to understand **what code actually changed** — which files were modified, what the diff looks like, and how many lines were added/removed. This granular information is critical for briefings, code review triage, and impact analysis, but currently requires leaving the MCP workflow to manually inspect each PR/issue on GitHub.

## What Changes

- Add a new **`get_pr_detail`** tool that retrieves detailed information for a single PR, including:
  - Full PR metadata (title, body, state, review status, merge status)
  - List of changed files with stats (additions, deletions, filename, status)
  - Code diffs (patch content) for each file, with configurable truncation
  - Review comments and review decisions
- Add a new **`get_issue_detail`** tool that retrieves detailed information for a single issue, including:
  - Full issue metadata (title, body, state, labels, assignees, milestone)
  - Timeline of comments with authors
  - Linked PRs (cross-references)
- Add new methods to `GitHubClient` to support fetching PR files, diffs, and issue details via PyGithub's Repository/PullRequest API (not the Search API)
- The existing `get_prs` and `get_issues` list tools remain unchanged — the new detail tools complement them for drill-down workflows

## Capabilities

### New Capabilities
- `pr-detail`: Retrieve detailed PR information including changed files, code diffs, and review status for a single PR
- `issue-detail`: Retrieve detailed issue information including comments and linked PRs for a single issue

### Modified Capabilities
<!-- No existing spec requirements are changing — the list tools remain as-is -->

## Impact

- **Code**: New tool modules `tools/pr_detail.py` and `tools/issue_detail.py`; new methods in `clients/github.py`; new tool registrations in `server.py`
- **APIs**: Uses PyGithub's `PullRequest.get_files()`, `PullRequest.get_reviews()`, `PullRequest.get_review_comments()`, `Issue.get_comments()`, and `Issue.get_timeline()` — these hit GitHub's REST API (core rate limit, not search rate limit)
- **Dependencies**: No new dependencies — PyGithub already supports all needed endpoints
- **Rate limits**: Detail tools use GitHub's core rate limit (5000/hr for authenticated) rather than search rate limit (30/min), so they won't compete with existing list tools
