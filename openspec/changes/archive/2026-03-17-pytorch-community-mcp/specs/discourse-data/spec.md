## ADDED Requirements

### Requirement: get-discussions tool
The system SHALL provide a `get-discussions` MCP tool that retrieves posts and topics from discuss.pytorch.org via the Discourse REST API. The tool SHALL accept `query` (optional, search string), `category` (optional, category name), `since` (optional, ISO date), and `until` (optional, ISO date) parameters. Date filtering SHALL use Discourse search syntax (`after:` / `before:` operators).

#### Scenario: Search discussions by keyword and date range
- **WHEN** user calls `get-discussions` with `query="distributed training"` and `since="2024-01-01"` and `until="2024-03-01"`
- **THEN** system returns matching Discourse topics with title, author, date, reply count, and excerpt, formatted in unified Markdown output

#### Scenario: Browse category
- **WHEN** user calls `get-discussions` with `category="dev"` and `since="2024-01-01"`
- **THEN** system returns recent topics in the "dev" category since 2024-01-01

#### Scenario: Result count exceeds Discourse limit
- **WHEN** Discourse search returns 50 results (the maximum per query)
- **THEN** system includes a note in the response indicating results may be truncated

### Requirement: Discourse authentication
The system SHALL authenticate with Discourse using API key and username provided via environment variables. The system SHALL also support unauthenticated access for public endpoints (with lower rate limits).

#### Scenario: Authenticated access
- **WHEN** `DISCOURSE_API_KEY` and `DISCOURSE_API_USERNAME` environment variables are set
- **THEN** system includes `Api-Key` and `Api-Username` headers in all Discourse API requests

#### Scenario: Unauthenticated access
- **WHEN** no Discourse API credentials are configured
- **THEN** system makes unauthenticated requests (public data only, subject to stricter rate limits)
