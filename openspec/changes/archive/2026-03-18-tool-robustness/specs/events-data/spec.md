## MODIFIED Requirements

### Requirement: get-events tool
The system SHALL provide a `get-events` MCP tool that retrieves PyTorch community events from the official Events API (`pytorch.org/wp-json/tec/v1/events`). The tool SHALL accept `since` (optional, ISO date), `until` (optional, ISO date), `search` (optional, keyword), and `featured` (optional, boolean) parameters. No authentication SHALL be required for this tool.

#### Scenario: Fetch upcoming events
- **WHEN** user calls `get-events` with `since="2024-06-01"`
- **THEN** system returns events starting from 2024-06-01 with title, dates, location/virtual, description, and registration link, formatted in unified Markdown output

#### Scenario: Search for specific event type
- **WHEN** user calls `get-events` with `search="conference"` and `since="2024-01-01"`
- **THEN** system returns events matching "conference" keyword since 2024-01-01

#### Scenario: Events API unavailable
- **WHEN** the Events API at pytorch.org returns a non-200 status code or times out
- **THEN** system returns a structured error response with type "EventsError" and resolution guidance

## ADDED Requirements

### Requirement: Blog news error handling
The `get-blog-news` tool SHALL handle RSS feed fetch failures (network errors, timeouts) and return structured error responses instead of raising unhandled exceptions or blocking indefinitely. The RSS feed fetch SHALL have an explicit timeout.

#### Scenario: RSS feed unavailable
- **WHEN** the RSS feed at pytorch.org/feed/ is unreachable or times out
- **THEN** system returns an error response with type "RSSError" and resolution guidance to retry later

#### Scenario: RSS feed returns malformed data
- **WHEN** the RSS feed returns data that cannot be parsed
- **THEN** system returns an error response with type "RSSError" indicating the feed data is malformed
