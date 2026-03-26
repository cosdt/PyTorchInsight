## ADDED Requirements

### Requirement: All platforms succeed
The test suite SHALL verify that `get_key_contributors_activity()` correctly merges and sorts results from all three platforms when all succeed.

#### Scenario: Three platforms return data
- **WHEN** GitHub returns 2 items, Slack returns 1 item, Discourse returns 1 item
- **THEN** the result SHALL contain all 4 items sorted by date descending with no platform notes

### Requirement: GitHub failure isolation
The test suite SHALL verify that a GitHub exception does not prevent Slack and Discourse results from appearing.

#### Scenario: GitHub raises exception
- **WHEN** `_fetch_github_activity` raises an exception
- **THEN** the result SHALL include Slack and Discourse items and platform notes SHALL contain "GitHub: unavailable"

### Requirement: Slack not configured
The test suite SHALL verify the "not configured" path when Slack client is unavailable.

#### Scenario: Slack client not available
- **WHEN** `slack_client.available` is `False`
- **THEN** `_fetch_slack_activity` SHALL return `None` and platform notes SHALL contain "Slack: not configured"

### Requirement: Slack failure isolation
The test suite SHALL verify that a Slack exception is isolated from other platform results.

#### Scenario: Slack raises exception
- **WHEN** `_fetch_slack_activity` raises an exception
- **THEN** platform notes SHALL contain "Slack: unavailable" and other platform results SHALL be present

### Requirement: Slack auth error returns None
The test suite SHALL verify that `SlackAuthError` in `_fetch_slack_activity` results in `None` (not an exception).

#### Scenario: SlackAuthError during search
- **WHEN** `client.search_messages` raises `SlackAuthError`
- **THEN** `_fetch_slack_activity` SHALL return `None`

### Requirement: Discourse failure isolation
The test suite SHALL verify that a Discourse exception is isolated from other platform results.

#### Scenario: Discourse raises exception
- **WHEN** `_fetch_discourse_activity` raises an exception
- **THEN** platform notes SHALL contain "Discourse: unavailable" and other platform results SHALL be present

### Requirement: All platforms fail
The test suite SHALL verify behavior when all three platforms fail simultaneously.

#### Scenario: All three platforms fail
- **WHEN** GitHub raises an exception, Slack returns `None`, and Discourse raises an exception
- **THEN** items SHALL be empty and platform notes SHALL contain entries for all three platforms

### Requirement: Default until date
The test suite SHALL verify that `until` defaults to today's date when not provided.

#### Scenario: until parameter is None
- **WHEN** `get_key_contributors_activity(until=None)` is called
- **THEN** the date queries SHALL use today's date as the until value

### Requirement: GitHub activity date range construction
The test suite SHALL verify that `_fetch_github_activity` constructs correct search queries.

#### Scenario: Both since and until provided
- **WHEN** `since="2024-01-01"` and `until="2024-06-01"`
- **THEN** the GitHub search query SHALL contain `created:2024-01-01..2024-06-01`

#### Scenario: Only until provided (since is None)
- **WHEN** `since=None` and `until="2024-06-01"`
- **THEN** the GitHub search query SHALL contain `created:*..2024-06-01`

### Requirement: GitHub activity item formatting
The test suite SHALL verify that GitHub PR and issue items are formatted correctly.

#### Scenario: PR with body
- **WHEN** GitHub returns a PR with `title="Fix bug"` and `body="Long description..."`
- **THEN** the item SHALL have `title="[PR] Fix bug"`, `platform="GitHub"`, and `description` truncated to 150 chars

#### Scenario: Issue with None body
- **WHEN** GitHub returns an issue with `body=None`
- **THEN** the item SHALL have `description=""` (no crash)

### Requirement: Discourse activity URL construction
The test suite SHALL verify URL construction for Discourse topics.

#### Scenario: Topic with slug and id
- **WHEN** Discourse returns a topic with `slug="my-topic"` and `id=123`
- **THEN** the item URL SHALL be `https://discuss.pytorch.org/t/my-topic/123`

#### Scenario: Topic with missing slug or id
- **WHEN** Discourse returns a topic with `slug=""` or `id=""`
- **THEN** the item URL SHALL be `""`

### Requirement: Result sorting
The test suite SHALL verify that results from multiple platforms are sorted by date descending.

#### Scenario: Mixed platform results with different dates
- **WHEN** GitHub returns an item dated "2024-03-01", Slack returns "2024-05-01", Discourse returns "2024-01-01"
- **THEN** the final items SHALL be ordered: Slack (05-01), GitHub (03-01), Discourse (01-01)
