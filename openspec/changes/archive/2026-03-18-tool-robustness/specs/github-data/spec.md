## ADDED Requirements

### Requirement: GitHub tool error handling
All GitHub-based tools (`get-prs`, `get-issues`, `get-rfcs`) SHALL catch GitHub API exceptions and return structured error responses via the unified error format instead of raising unhandled exceptions.

#### Scenario: GitHub API returns authentication error
- **WHEN** a GitHub tool call fails with a 401 authentication error
- **THEN** system returns an error response with type "GitHubError", the error message, and resolution guidance to check the GITHUB_TOKEN

#### Scenario: GitHub API returns rate limit error
- **WHEN** a GitHub tool call fails with a 403 rate limit error
- **THEN** system returns an error response with type "GitHubError" and resolution guidance indicating the rate limit has been exceeded

#### Scenario: GitHub API returns network error
- **WHEN** a GitHub tool call fails due to a network timeout or connection error
- **THEN** system returns an error response with type "GitHubError" and resolution guidance to retry later
