## ADDED Requirements

### Requirement: All tools are registered
The test suite SHALL verify that all 8 expected tools are registered with the FastMCP server instance.

#### Scenario: Tool count and names
- **WHEN** the `mcp` server instance is inspected
- **THEN** exactly 8 tools SHALL be registered with names: `get_prs`, `get_issues`, `get_rfcs`, `get_slack_threads`, `get_discussions`, `get_events`, `get_blog_news`, `get_key_contributors_activity`

### Requirement: Tool descriptions are non-empty
The test suite SHALL verify that every registered tool has a non-empty description string.

#### Scenario: Each tool has a description
- **WHEN** each registered tool's metadata is inspected
- **THEN** the description SHALL be a non-empty string

### Requirement: Tool parameter schemas are valid
The test suite SHALL verify that each tool's input schema includes the required parameters as defined in `server.py`.

#### Scenario: get_prs has required 'since' parameter
- **WHEN** the `get_prs` tool schema is inspected
- **THEN** `since` SHALL be listed as a required parameter of type string

#### Scenario: get_key_contributors_activity has required 'contributor' parameter
- **WHEN** the `get_key_contributors_activity` tool schema is inspected
- **THEN** `contributor` SHALL be listed as a required parameter of type string

#### Scenario: get_slack_threads has required 'channel' parameter
- **WHEN** the `get_slack_threads` tool schema is inspected
- **THEN** `channel` SHALL be listed as a required parameter of type string

### Requirement: Server metadata is correct
The test suite SHALL verify that the MCP server has the correct name and version.

#### Scenario: Server name and version
- **WHEN** the `mcp` FastMCP instance is inspected
- **THEN** the name SHALL be "PyTorch Community MCP" and version SHALL be "0.1.0"

### Requirement: Sync tool invocation through server
The test suite SHALL verify that a synchronous tool can be called through the FastMCP instance with mocked clients and return a valid formatted result.

#### Scenario: get_prs via server with mocked GitHubClient
- **WHEN** `get_prs` is invoked through the MCP server with `since="2024-01-01"` and the underlying `github_client.search_issues` is mocked to return one result
- **THEN** the response SHALL contain "## Results" and the mocked PR title

### Requirement: Async tool invocation through server
The test suite SHALL verify that an async tool can be called through the FastMCP instance with mocked clients and return a valid formatted result.

#### Scenario: get_discussions via server with mocked DiscourseClient
- **WHEN** `get_discussions` is invoked through the MCP server with `query="test"` and the underlying `discourse_client.search` is mocked
- **THEN** the response SHALL contain "## Results" and the mocked topic title

### Requirement: Import isolation from real credentials
The test suite SHALL ensure that importing the server module for testing does not trigger real credential resolution or network calls.

#### Scenario: Config is mocked during import
- **WHEN** integration tests import `server.py`
- **THEN** `Config.from_env()` SHALL be mocked to return dummy config with no tokens, and no network calls SHALL be made
