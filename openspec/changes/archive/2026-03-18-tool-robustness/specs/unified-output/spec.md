## MODIFIED Requirements

### Requirement: Unified Markdown output format
All MCP tools SHALL return results in a consistent Markdown format. Each response SHALL include: (1) a summary header with query metadata (tool name, parameters, result count, timestamp), (2) a structured list of items with consistent field ordering, (3) source links for each item. All date fields in tool output SHALL be parsed using `datetime` and formatted as ISO date (`YYYY-MM-DD`), not via string slicing.

#### Scenario: Standard tool response
- **WHEN** any tool returns results
- **THEN** the response follows this structure: a `## Summary` section with query parameters and result count, followed by a `## Results` section with numbered items, each containing title, date, author/source, excerpt/description, and source URL

#### Scenario: Empty results
- **WHEN** any tool returns zero results
- **THEN** the response includes the `## Summary` section showing result count as 0, and a message indicating no items matched the query criteria

#### Scenario: Error response
- **WHEN** any tool encounters an API error
- **THEN** the response includes a `## Error` section with the error type, message, and a specific actionable resolution (e.g., "Check GITHUB_TOKEN is valid" not just "Try again")

## ADDED Requirements

### Requirement: Safe date parsing utility
The system SHALL provide a `safe_parse_date()` utility function that attempts to parse a date string using `datetime.fromisoformat()` and returns a `YYYY-MM-DD` string. If parsing fails, it SHALL fall back to returning the first 10 characters of the input or an empty string.

#### Scenario: Valid ISO datetime string
- **WHEN** `safe_parse_date` receives `"2024-01-15T12:30:00Z"`
- **THEN** it returns `"2024-01-15"`

#### Scenario: Already formatted date string
- **WHEN** `safe_parse_date` receives `"2024-01-15"`
- **THEN** it returns `"2024-01-15"`

#### Scenario: Invalid or empty string
- **WHEN** `safe_parse_date` receives `""` or a non-date string
- **THEN** it returns `""` without raising an exception
