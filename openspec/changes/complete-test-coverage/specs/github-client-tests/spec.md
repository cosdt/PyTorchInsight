## ADDED Requirements

### Requirement: GitHubClient construction tests
The test suite SHALL verify that `GitHubClient` initializes correctly with and without a token, and that default rate limit values are set.

#### Scenario: Construction without token
- **WHEN** `GitHubClient(token=None)` is created
- **THEN** the client SHALL have `rate_limit_remaining == 30` and `rate_limit_total == 30`

#### Scenario: Construction with token
- **WHEN** `GitHubClient(token="ghp_xxx")` is created
- **THEN** the client SHALL initialize without error and have default rate limit values

### Requirement: Rate limit update tests
The test suite SHALL verify that `_update_rate_limit()` correctly reads rate limit info from the GitHub API and handles errors gracefully.

#### Scenario: Successful rate limit update
- **WHEN** `_update_rate_limit()` is called and the GitHub API returns `search.remaining=15, search.limit=30, search.reset=<timestamp>`
- **THEN** `rate_limit_remaining` SHALL be `15` and `rate_limit_total` SHALL be `30`

#### Scenario: Rate limit update with GithubException
- **WHEN** `_update_rate_limit()` is called and the GitHub API raises `GithubException`
- **THEN** the rate limit values SHALL remain unchanged (silent failure)

### Requirement: Wait for rate limit tests
The test suite SHALL verify that `_wait_for_rate_limit()` sleeps the correct duration when rate limited and skips sleeping when quota is available.

#### Scenario: Sufficient quota remaining
- **WHEN** `_wait_for_rate_limit()` is called and `remaining > 1`
- **THEN** `time.sleep` SHALL NOT be called

#### Scenario: Rate limited with future reset time
- **WHEN** `_wait_for_rate_limit()` is called, `remaining <= 1`, and `reset_time` is 30 seconds in the future
- **THEN** `time.sleep` SHALL be called with `31` (wait_time + 1)

#### Scenario: Rate limited with max cap
- **WHEN** `_wait_for_rate_limit()` is called, `remaining <= 1`, and `reset_time` is 120 seconds in the future
- **THEN** `time.sleep` SHALL be called with `60` (capped at 60s)

#### Scenario: Rate limited with past reset time
- **WHEN** `_wait_for_rate_limit()` is called, `remaining <= 1`, and `reset_time` is in the past
- **THEN** `time.sleep` SHALL be called with `1` (max(0, negative) + 1)

### Requirement: Search issues success tests
The test suite SHALL verify that `search_issues()` returns correct results and respects `max_results` truncation.

#### Scenario: Successful search returning results
- **WHEN** `search_issues("query")` is called and the GitHub API returns 3 issues
- **THEN** the method SHALL return a list of 3 issue objects

#### Scenario: Truncation at max_results
- **WHEN** `search_issues("query", max_results=2)` is called and the API returns 5 issues
- **THEN** the method SHALL return exactly 2 issue objects

#### Scenario: Empty results
- **WHEN** `search_issues("query")` is called and the API returns 0 issues
- **THEN** the method SHALL return an empty list

### Requirement: Search issues retry on RateLimitExceededException
The test suite SHALL verify exponential backoff behavior when rate limited.

#### Scenario: Single rate limit then success
- **WHEN** `search_issues()` raises `RateLimitExceededException` on attempt 1 and succeeds on attempt 2
- **THEN** `time.sleep` SHALL be called with `10` (2^0 * 10) and the method SHALL return results

#### Scenario: Exhausted retries on rate limit
- **WHEN** `search_issues(max_retries=3)` raises `RateLimitExceededException` on all 3 attempts
- **THEN** the method SHALL return an empty list `[]`

#### Scenario: Backoff duration increases
- **WHEN** `search_issues()` raises `RateLimitExceededException` on attempts 1 and 2, then succeeds on attempt 3
- **THEN** `time.sleep` SHALL be called with `10` then `20` (2^0*10, 2^1*10)

### Requirement: Search issues retry on GithubException
The test suite SHALL verify retry and error propagation for general GitHub errors.

#### Scenario: Single GithubException then success
- **WHEN** `search_issues()` raises `GithubException` on attempt 1 and succeeds on attempt 2
- **THEN** `time.sleep` SHALL be called with `1` (2^0) and the method SHALL return results

#### Scenario: Exhausted retries on GithubException
- **WHEN** `search_issues(max_retries=3)` raises `GithubException` on all 3 attempts
- **THEN** the method SHALL raise the `GithubException` from the final attempt

#### Scenario: Single retry with max_retries=1
- **WHEN** `search_issues(max_retries=1)` raises `GithubException` on the only attempt
- **THEN** the method SHALL raise `GithubException` immediately
