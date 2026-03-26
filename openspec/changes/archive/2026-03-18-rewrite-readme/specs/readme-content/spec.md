## ADDED Requirements

### Requirement: Project introduction section
The README SHALL contain an introduction section that explains this is a FastMCP server providing PyTorch community intelligence tools. It SHALL mention the 8 curated tools and the data sources (GitHub, Slack, Discourse, pytorch.org Events, RSS feed). It SHALL explain the value proposition: unified, PyTorch-specific tools with standardized Markdown output instead of 120+ generic tools.

#### Scenario: User reads introduction
- **WHEN** a user opens the README for the first time
- **THEN** they understand this is an MCP server for PyTorch community data aggregation within the first paragraph

### Requirement: Tools overview table
The README SHALL include a table listing all 8 tools with their name, brief description, and primary data source. Tools: `get_prs`, `get_issues`, `get_rfcs`, `get_slack_threads`, `get_discussions`, `get_events`, `get_blog_news`, `get_key_contributors_activity`.

#### Scenario: User checks available tools
- **WHEN** a user looks at the tools table
- **THEN** they can see all tool names, what each does, and which data source it queries

### Requirement: Deployment instructions
The README SHALL include step-by-step deployment instructions covering: (1) installing dependencies via pip or uv, (2) setting required environment variables (GITHUB_TOKEN, SLACK tokens, DISCOURSE keys), (3) running the server with `python -m pytorch_community_mcp`.

#### Scenario: User deploys from scratch
- **WHEN** a user follows the deployment section
- **THEN** they can install dependencies, set credentials, and start the MCP server

### Requirement: Environment variables reference
The README SHALL include a table of all environment variables with columns: variable name, purpose, required/optional status, and notes.

#### Scenario: User configures credentials
- **WHEN** a user checks the environment variables table
- **THEN** they know which tokens are required, which are optional, and what each is for

### Requirement: Client configuration examples
The README SHALL include JSON configuration snippets for at least Claude Code and OpenCode. Each snippet SHALL show the `mcpServers` block with command, args, and env fields.

#### Scenario: User configures Claude Code
- **WHEN** a user copies the Claude Code config snippet into their settings
- **THEN** the MCP server is properly registered and can be used via Claude Code

#### Scenario: User configures OpenCode
- **WHEN** a user copies the OpenCode config snippet into their config
- **THEN** the MCP server is properly registered and can be used via OpenCode

### Requirement: Remove outdated content
The README SHALL NOT contain any references to the old multi-agent delivery runtime, opencode agents, daily reports, SMTP, or other legacy concepts.

#### Scenario: No legacy references
- **WHEN** a user reads the entire README
- **THEN** they find no mention of orchestrator agents, delivery runtime, daily_report, or .opencode/ paths
