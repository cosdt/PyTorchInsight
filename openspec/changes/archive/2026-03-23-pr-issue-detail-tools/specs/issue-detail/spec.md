## ADDED Requirements

### Requirement: get-issue-detail tool
The system SHALL provide a `get_issue_detail` MCP tool that retrieves detailed information for a single PyTorch issue, including comments and linked PRs. The tool SHALL accept `issue_number` (required, int), `repo` (optional, string, default "pytorch/pytorch"), `max_comments` (optional, int, default 50), and `comment_length` (optional, int, default 500) parameters.

#### Scenario: Fetch issue detail with comments
- **WHEN** user calls `get_issue_detail` with `issue_number=98765`
- **THEN** system returns the issue metadata (title, body, state, author, created date, labels, assignees, milestone) and a chronological list of comments with each comment's author, date, and body text

#### Scenario: Fetch issue detail with comment truncation
- **WHEN** user calls `get_issue_detail` with `issue_number=98765` and `comment_length=200`
- **THEN** system returns comments with each comment body truncated to at most 200 characters

#### Scenario: Fetch issue detail with limited comments
- **WHEN** user calls `get_issue_detail` with `issue_number=98765` and `max_comments=10`
- **THEN** system returns at most 10 comments (the most recent), with a note indicating total comment count if more exist

#### Scenario: Fetch issue detail for a non-default repo
- **WHEN** user calls `get_issue_detail` with `issue_number=42` and `repo="pytorch/vision"`
- **THEN** system retrieves the issue from the `pytorch/vision` repository

### Requirement: Linked PRs in issue detail
The `get_issue_detail` tool SHALL identify and include cross-referenced pull requests linked to the issue when available via the timeline API.

#### Scenario: Issue with linked PRs
- **WHEN** user calls `get_issue_detail` for an issue that has cross-referenced PRs
- **THEN** system returns a list of linked PRs with each PR's number, title, state, and URL

#### Scenario: Issue with no linked PRs
- **WHEN** user calls `get_issue_detail` for an issue with no cross-referenced PRs
- **THEN** system returns an empty linked PRs list

### Requirement: Issue detail error handling
The `get_issue_detail` tool SHALL handle errors gracefully and return structured error responses via the unified error format.

#### Scenario: Issue not found
- **WHEN** user calls `get_issue_detail` with an `issue_number` that does not exist
- **THEN** system returns an error response with type "GitHubError" and a message indicating the issue was not found

#### Scenario: Repository not found
- **WHEN** user calls `get_issue_detail` with a `repo` that does not exist
- **THEN** system returns an error response with type "GitHubError" and a message indicating the repository was not found

### Requirement: Issue detail rate limit reporting
The `get_issue_detail` tool SHALL report the GitHub core API rate limit status in the response.

#### Scenario: Rate limit information in response
- **WHEN** user calls `get_issue_detail` successfully
- **THEN** the response includes current core rate limit remaining and total in the summary section
