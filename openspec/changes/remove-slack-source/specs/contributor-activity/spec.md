## MODIFIED Requirements

### Requirement: get-key-contributors-activity tool
The system SHALL provide a `get-key-contributors-activity` MCP tool that aggregates a contributor's activity across GitHub and Discourse. The tool SHALL accept `contributor` (required, GitHub username), `since` (optional, ISO date), and `until` (optional, ISO date) parameters. The tool SHALL query each platform and merge results into a single cross-platform activity summary.

#### Scenario: Fetch contributor activity across platforms
- **WHEN** user calls `get-key-contributors-activity` with `contributor="ezyang"` and `since="2024-01-01"`
- **THEN** system returns a unified summary including: GitHub PRs/issues/comments by ezyang, and Discourse posts by ezyang, all within the specified time range

#### Scenario: Partial platform data
- **WHEN** one platform (e.g., Discourse) is not configured or returns an error
- **THEN** system returns available data from the remaining platform(s) with a note indicating which platform was unavailable

#### Scenario: Contributor not found on a platform
- **WHEN** the specified contributor username does not exist on one or more platforms
- **THEN** system returns data from platforms where the contributor was found, with a note for platforms where they were not found

### Requirement: Cross-platform username mapping
The system SHALL attempt to correlate usernames across platforms. By default, the system SHALL use the GitHub username as the search key for all platforms. The system MAY support a configurable username mapping file for cases where usernames differ across platforms.

#### Scenario: Same username across platforms
- **WHEN** contributor's GitHub username matches their Discourse username
- **THEN** system automatically correlates their activity across all platforms

#### Scenario: Different usernames across platforms
- **WHEN** a username mapping is configured for a contributor
- **THEN** system uses the mapped usernames to query each platform

## REMOVED Requirements

### Requirement: Slack platform in contributor activity
**Reason**: Slack 信源已从系统中完全移除，不再作为贡献者活动的数据来源。
**Migration**: `get-key-contributors-activity` 现在仅聚合 GitHub 和 Discourse 数据。无需额外操作，Slack 数据之前已处于可选状态（不可用时会自动跳过）。
