## ADDED Requirements

### Requirement: get-pr-detail tool
The system SHALL provide a `get_pr_detail` MCP tool that retrieves detailed information for a single PyTorch pull request, including changed files and code diffs. The tool SHALL accept `pr_number` (required, int), `repo` (optional, string, default "pytorch/pytorch"), `max_diff_lines` (optional, int, default 50), `files_only` (optional, bool, default false), and `include_reviews` (optional, bool, default true) parameters.

#### Scenario: Fetch PR detail with changed files and diffs
- **WHEN** user calls `get_pr_detail` with `pr_number=12345`
- **THEN** system returns the PR metadata (title, body, state, author, created date, merged status, merge commit SHA), a list of changed files with per-file stats (filename, status, additions, deletions), and the unified diff patch for each file truncated to `max_diff_lines` lines

#### Scenario: Fetch PR detail with files only (no diffs)
- **WHEN** user calls `get_pr_detail` with `pr_number=12345` and `files_only=true`
- **THEN** system returns the PR metadata and a list of changed files with per-file stats (filename, status, additions, deletions) but does NOT include any diff/patch content

#### Scenario: Fetch PR detail with custom diff truncation
- **WHEN** user calls `get_pr_detail` with `pr_number=12345` and `max_diff_lines=200`
- **THEN** system returns diffs for each file truncated to at most 200 lines, with a truncation indicator if the original diff was longer

#### Scenario: Fetch PR detail for a non-default repo
- **WHEN** user calls `get_pr_detail` with `pr_number=42` and `repo="pytorch/vision"`
- **THEN** system retrieves the PR from the `pytorch/vision` repository instead of the default `pytorch/pytorch`

### Requirement: PR review information
When `include_reviews` is true (default), the `get_pr_detail` tool SHALL include review information: list of reviews with reviewer username, state (APPROVED, CHANGES_REQUESTED, COMMENTED, DISMISSED), and submitted date.

#### Scenario: PR with reviews
- **WHEN** user calls `get_pr_detail` with `pr_number=12345` and `include_reviews=true`
- **THEN** system returns the list of reviews with each review's author, state, and date

#### Scenario: PR with no reviews
- **WHEN** user calls `get_pr_detail` for a PR that has no reviews
- **THEN** system returns an empty reviews list

### Requirement: PR detail error handling
The `get_pr_detail` tool SHALL handle errors gracefully and return structured error responses via the unified error format.

#### Scenario: PR not found
- **WHEN** user calls `get_pr_detail` with a `pr_number` that does not exist
- **THEN** system returns an error response with type "GitHubError" and a message indicating the PR was not found

#### Scenario: Repository not found
- **WHEN** user calls `get_pr_detail` with a `repo` that does not exist
- **THEN** system returns an error response with type "GitHubError" and a message indicating the repository was not found

#### Scenario: Authentication error
- **WHEN** the GitHub token is invalid or missing
- **THEN** system returns an error response with type "GitHubError" and resolution guidance to check the GITHUB_TOKEN

### Requirement: PR detail rate limit reporting
The `get_pr_detail` tool SHALL report the GitHub core API rate limit status in the response, using the same pattern as existing tools.

#### Scenario: Rate limit information in response
- **WHEN** user calls `get_pr_detail` successfully
- **THEN** the response includes current core rate limit remaining and total in the summary section
