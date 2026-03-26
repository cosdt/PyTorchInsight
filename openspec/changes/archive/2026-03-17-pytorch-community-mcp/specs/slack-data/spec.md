## ADDED Requirements

### Requirement: get-slack-threads tool
The system SHALL provide a `get-slack-threads` MCP tool that retrieves messages from PyTorch Slack channels. The tool SHALL accept `channel` (required, channel name or ID), `since` (optional, ISO date), `until` (optional, ISO date), and `query` (optional, search string) parameters. The tool SHALL authenticate using xoxc/xoxd browser session tokens or xoxp user tokens.

#### Scenario: Search messages in a channel
- **WHEN** user calls `get-slack-threads` with `channel="#general"` and `query="distributed training"` and `since="2024-01-01"`
- **THEN** system returns matching Slack messages with thread context, formatted in unified Markdown output

#### Scenario: Fetch recent messages from channel
- **WHEN** user calls `get-slack-threads` with `channel="#dev"` and `since="2024-03-01"`
- **THEN** system returns messages posted since 2024-03-01 in the #dev channel

#### Scenario: Authentication failure
- **WHEN** Slack API returns 401 or `invalid_auth` error
- **THEN** system returns an error message indicating the token has expired and instructions to refresh via slack-token-extractor

### Requirement: Slack token flexibility
The system SHALL support two authentication modes for Slack: (1) xoxc + xoxd browser session tokens, and (2) xoxp OAuth user tokens. The authentication mode SHALL be determined by which environment variables are configured.

#### Scenario: xoxc/xoxd authentication
- **WHEN** `SLACK_XOXC_TOKEN` and `SLACK_XOXD_TOKEN` environment variables are set
- **THEN** system uses these tokens with `Authorization: Bearer xoxc-...` header and `Cookie: d=xoxd-...` header for all Slack API calls

#### Scenario: xoxp authentication
- **WHEN** `SLACK_XOXP_TOKEN` environment variable is set (and xoxc/xoxd are not set)
- **THEN** system uses the xoxp token with standard `Authorization: Bearer xoxp-...` header

#### Scenario: No Slack token configured
- **WHEN** no Slack token environment variables are set
- **THEN** Slack-related tools SHALL still be registered but return an error message indicating Slack is not configured
