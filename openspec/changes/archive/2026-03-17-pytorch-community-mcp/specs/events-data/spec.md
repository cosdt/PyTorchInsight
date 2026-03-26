## ADDED Requirements

### Requirement: get-events tool
The system SHALL provide a `get-events` MCP tool that retrieves PyTorch community events from the official Events API (`pytorch.org/wp-json/tec/v1/events`). The tool SHALL accept `start_date` (optional, ISO date), `end_date` (optional, ISO date), `search` (optional, keyword), and `featured` (optional, boolean) parameters. No authentication SHALL be required for this tool.

#### Scenario: Fetch upcoming events
- **WHEN** user calls `get-events` with `start_date="2024-06-01"`
- **THEN** system returns events starting from 2024-06-01 with title, dates, location/virtual, description, and registration link, formatted in unified Markdown output

#### Scenario: Search for specific event type
- **WHEN** user calls `get-events` with `search="conference"` and `start_date="2024-01-01"`
- **THEN** system returns events matching "conference" keyword since 2024-01-01

#### Scenario: Events API unavailable
- **WHEN** the Events API at pytorch.org returns a non-200 status code
- **THEN** system returns an error message indicating the Events API is temporarily unavailable

### Requirement: get-blog-news tool
The system SHALL provide a `get-blog-news` MCP tool that retrieves recent PyTorch blog posts and news from the RSS feed at `pytorch.org/feed/`. The tool SHALL accept `since` (optional, ISO date) and `limit` (optional, integer, default 20) parameters.

#### Scenario: Fetch recent blog posts
- **WHEN** user calls `get-blog-news` with `limit=10`
- **THEN** system returns the 10 most recent blog posts with title, date, author, summary, and link

#### Scenario: Filter by date
- **WHEN** user calls `get-blog-news` with `since="2024-01-01"`
- **THEN** system returns only blog posts published since 2024-01-01
