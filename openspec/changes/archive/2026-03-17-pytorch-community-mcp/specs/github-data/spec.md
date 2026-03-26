## ADDED Requirements

### Requirement: get-prs tool
The system SHALL provide a `get-prs` MCP tool that retrieves PyTorch pull requests from GitHub within a specified time range. The tool SHALL accept `since` (required, ISO date), `until` (optional, ISO date, defaults to today), and `module` (optional, string) parameters. The tool SHALL search across `pytorch/pytorch` repository. When `module` is specified, the tool SHALL filter PRs by label matching the module name (e.g., "module: distributed").

#### Scenario: Fetch PRs within date range
- **WHEN** user calls `get-prs` with `since="2024-01-01"` and `until="2024-01-31"`
- **THEN** system returns all PRs in pytorch/pytorch created between 2024-01-01 and 2024-01-31, formatted in unified Markdown output

#### Scenario: Fetch PRs filtered by module
- **WHEN** user calls `get-prs` with `since="2024-01-01"` and `module="distributed"`
- **THEN** system returns only PRs with label "module: distributed" created since 2024-01-01

#### Scenario: GitHub rate limit reached
- **WHEN** GitHub Search API returns 403 with rate limit error
- **THEN** system waits per the `retry-after` header and retries, returning results after the backoff period

### Requirement: get-issues tool
The system SHALL provide a `get-issues` MCP tool that retrieves PyTorch issues from GitHub within a specified time range. The tool SHALL accept `since` (required), `until` (optional), `module` (optional), and `state` (optional, "open"/"closed"/"all", default "open") parameters. The tool SHALL search across `pytorch/pytorch` repository.

#### Scenario: Fetch open issues by module
- **WHEN** user calls `get-issues` with `since="2024-01-01"` and `module="compiler"` and `state="open"`
- **THEN** system returns open issues with label "module: compiler" created since 2024-01-01

#### Scenario: No results found
- **WHEN** query returns zero matching issues
- **THEN** system returns a Markdown message stating no issues were found matching the criteria

### Requirement: get-rfcs tool
The system SHALL provide a `get-rfcs` MCP tool that retrieves PyTorch RFCs. The tool SHALL search across both `pytorch/pytorch` (issues/PRs with "RFC" in title or label) and `pytorch/rfcs` repository. The tool SHALL accept `since` (optional) and `status` (optional, "open"/"closed"/"all") parameters.

#### Scenario: Fetch RFCs from both repos
- **WHEN** user calls `get-rfcs` with `since="2024-01-01"`
- **THEN** system returns RFCs from both pytorch/pytorch and pytorch/rfcs, merged and deduplicated, sorted by creation date descending

#### Scenario: Fetch all open RFCs
- **WHEN** user calls `get-rfcs` with `status="open"`
- **THEN** system returns all currently open RFCs across both repositories

### Requirement: Rate limit handling
The system SHALL implement rate limit awareness for GitHub Search API (30 requests/minute). When approaching the limit, the system SHALL apply exponential backoff. The system SHALL expose remaining quota information in tool responses when quota is below 30%.

#### Scenario: Rate limit approaching
- **WHEN** GitHub API response shows `x-ratelimit-remaining` below 30% of the limit
- **THEN** system includes a warning note in the response indicating remaining API quota
