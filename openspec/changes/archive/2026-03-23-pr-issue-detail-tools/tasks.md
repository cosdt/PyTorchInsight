## 1. GitHubClient Extensions

- [x] 1.1 Add core rate limit tracking to `GitHubClient` (track `core` rate limit alongside existing `search` rate limit)
- [x] 1.2 Add `get_pull_request(repo, pr_number)` method that returns a PyGithub `PullRequest` object with retry and rate limit handling
- [x] 1.3 Add `get_pr_files(repo, pr_number)` method that returns the list of changed files via `PullRequest.get_files()`
- [x] 1.4 Add `get_pr_reviews(repo, pr_number)` method that returns reviews via `PullRequest.get_reviews()`
- [x] 1.5 Add `get_issue(repo, issue_number)` method that returns a PyGithub `Issue` object with retry and rate limit handling
- [x] 1.6 Add `get_issue_comments(repo, issue_number, max_comments)` method that returns comments via `Issue.get_comments()`
- [x] 1.7 Add `get_issue_timeline(repo, issue_number)` method that returns timeline events for extracting linked PRs

## 2. PR Detail Tool

- [x] 2.1 Create `tools/pr_detail.py` with `get_pr_detail()` function implementing the spec: PR metadata, changed files with stats, truncated diffs, and reviews
- [x] 2.2 Register `get_pr_detail` tool in `server.py` with all parameters (`pr_number`, `repo`, `max_diff_lines`, `files_only`, `include_reviews`)
- [x] 2.3 Handle diff truncation: truncate each file's patch to `max_diff_lines` lines with a truncation indicator
- [x] 2.4 Handle error cases: PR not found, repo not found, authentication error

## 3. Issue Detail Tool

- [x] 3.1 Create `tools/issue_detail.py` with `get_issue_detail()` function implementing the spec: issue metadata, comments, and linked PRs
- [x] 3.2 Register `get_issue_detail` tool in `server.py` with all parameters (`issue_number`, `repo`, `max_comments`, `comment_length`)
- [x] 3.3 Extract linked PRs from timeline events (cross-reference events)
- [x] 3.4 Handle error cases: issue not found, repo not found, authentication error

## 4. Tests

- [x] 4.1 Write unit tests for `GitHubClient` new methods (mock PyGithub objects)
- [x] 4.2 Write unit tests for `get_pr_detail` tool (mock client, verify output format and truncation)
- [x] 4.3 Write unit tests for `get_issue_detail` tool (mock client, verify output format and comment handling)
- [x] 4.4 Write integration smoke test that calls real GitHub API for a known pytorch/pytorch PR and issue (skip if no token)
