## ADDED Requirements

### Requirement: Unified Markdown output format
All MCP tools SHALL return results in a consistent Markdown format. Each response SHALL include: (1) a summary header with query metadata (tool name, parameters, result count, timestamp), (2) a structured list of items with consistent field ordering, (3) source links for each item.

#### Scenario: Standard tool response
- **WHEN** any tool returns results
- **THEN** the response follows this structure: a `## Summary` section with query parameters and result count, followed by a `## Results` section with numbered items, each containing title, date, author/source, excerpt/description, and source URL

#### Scenario: Empty results
- **WHEN** any tool returns zero results
- **THEN** the response includes the `## Summary` section showing result count as 0, and a message indicating no items matched the query criteria

#### Scenario: Error response
- **WHEN** any tool encounters an API error
- **THEN** the response includes a `## Error` section with the error type, message, and suggested resolution (e.g., "Token expired, re-run slack-token-extractor")

### Requirement: Rate limit transparency
When any underlying API is approaching its rate limit, the tool response SHALL include a `> Note:` block indicating remaining API quota. This SHALL apply to GitHub Search API (30 req/min threshold).

#### Scenario: Low rate limit warning
- **WHEN** a GitHub tool response is generated while `x-ratelimit-remaining` is below 10
- **THEN** the response includes a Markdown blockquote note: `> Note: GitHub API quota low (N/30 remaining). Queries may be delayed.`
