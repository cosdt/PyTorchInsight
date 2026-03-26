## Context

The PyTorch Community MCP server currently provides list-level tools (`get_prs`, `get_issues`) that use GitHub's Search API to retrieve collections of PRs/issues with basic metadata. Users need to drill down into individual items to understand code changes, but the current tools don't expose file-level or diff-level detail.

PyGithub already provides full access to the GitHub REST API endpoints needed: `PullRequest.get_files()` returns changed files with patches, and `Issue.get_comments()` returns comment threads. These use the core rate limit (5000/hr authenticated) rather than the search rate limit (30/min).

## Goals / Non-Goals

**Goals:**
- Enable drill-down from PR list to individual PR with full changed-files and diff information
- Enable drill-down from issue list to individual issue with comments and linked PRs
- Keep responses within reasonable token budgets via configurable truncation
- Reuse existing `GitHubClient` patterns (rate limiting, retry, error handling)

**Non-Goals:**
- Modifying existing `get_prs` or `get_issues` tools
- Supporting batch detail fetches (multiple PRs in one call)
- Providing write operations (commenting, approving, merging)
- Supporting non-pytorch repos (though the implementation will be generic enough)

## Decisions

### 1. Separate detail tools vs. adding parameters to existing tools

**Decision**: Create new `get_pr_detail` and `get_issue_detail` tools rather than adding `include_files`/`include_diff` parameters to existing list tools.

**Rationale**: List tools return many items via the Search API; fetching files for each would be N additional API calls and produce enormous responses. Separate detail tools make the drill-down workflow explicit and keep each tool focused.

**Alternative considered**: Adding an `include_files: bool` flag to `get_prs`. Rejected because it would make list queries extremely slow and token-heavy.

### 2. PR identification by number vs. URL

**Decision**: Accept `pr_number` (int) as the primary identifier, with an optional `repo` parameter defaulting to `pytorch/pytorch`.

**Rationale**: PR numbers are concise, unambiguous within a repo, and what users naturally reference. The `get_prs` list tool output includes URLs from which numbers are easily extractable.

### 3. Diff content handling

**Decision**: Include file patches (unified diff) in the response with a configurable `max_diff_lines` parameter (default 50 per file). Provide a `files_only` flag to skip diffs entirely and return just the file list with stats.

**Rationale**: Full diffs for large PRs (100+ files, thousands of lines) would blow up response tokens. Truncation with an explicit parameter gives users control. The `files_only` mode is useful for quick impact assessment.

### 4. Core rate limit tracking

**Decision**: Add core rate limit tracking to `GitHubClient` alongside existing search rate limit tracking. Detail tools will report core rate limit status in responses.

**Rationale**: Detail tools use the core rate limit (5000/hr), not the search limit (30/min). Users need visibility into both. The same pattern already exists for search limits.

## Risks / Trade-offs

- **[Large PR responses]** → Mitigated by `max_diff_lines` truncation and `files_only` mode. Default 50 lines per file keeps most responses reasonable.
- **[Rate limit consumption]** → Each `get_pr_detail` call makes 1-3 API calls (PR + files + reviews). At 5000/hr core limit, this supports ~1600-2500 detail queries/hr, which is adequate.
- **[PyGithub version compatibility]** → `PullRequest.get_files()` and `Issue.get_comments()` are stable PyGithub APIs available since early versions. No compatibility risk.
