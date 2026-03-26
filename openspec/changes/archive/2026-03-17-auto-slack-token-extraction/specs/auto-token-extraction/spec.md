## ADDED Requirements

### Requirement: Three-phase token resolution at startup
The system SHALL attempt to resolve Slack xoxc/xoxd tokens at MCP server startup using a three-phase strategy executed in order: (1) environment variables, (2) saved token file, (3) local Chrome auto-extraction. The system SHALL use the first phase that yields valid tokens and skip remaining phases.

#### Scenario: Environment variables are set
- **WHEN** `SLACK_XOXC_TOKEN` and `SLACK_XOXD_TOKEN` environment variables are both set
- **THEN** system uses these tokens directly without checking saved file or Chrome

#### Scenario: Saved token file has valid tokens
- **WHEN** environment variables are not set AND `~/.slack_tokens.env` contains xoxc/xoxd tokens AND those tokens pass `auth.test` validation
- **THEN** system uses the saved tokens

#### Scenario: Saved token file has expired tokens
- **WHEN** environment variables are not set AND `~/.slack_tokens.env` contains tokens that fail `auth.test` validation
- **THEN** system proceeds to Phase 3 (Chrome auto-extraction)

#### Scenario: Chrome auto-extraction succeeds
- **WHEN** Phases 1 and 2 fail AND Google Chrome is installed AND a Chrome profile contains valid Slack session cookies
- **THEN** system extracts tokens from Chrome headlessly, saves them to `~/.slack_tokens.env` with 0o600 permissions, and uses them

#### Scenario: All phases fail
- **WHEN** all three phases fail to produce valid tokens
- **THEN** Slack tools SHALL remain registered but `SlackConfig.available` SHALL be `False`

### Requirement: Playwright optional dependency
The system SHALL treat `playwright` as an optional dependency. Phase 3 (Chrome auto-extraction) SHALL only be attempted when `playwright` is importable at runtime.

#### Scenario: Playwright not installed
- **WHEN** `playwright` package is not installed
- **THEN** system skips Phase 3 and falls back to Phases 1 and 2 only, without raising an error

#### Scenario: Playwright installed but Chrome not available
- **WHEN** `playwright` is installed but Google Chrome is not found on the system
- **THEN** system skips Phase 3 without raising an error

### Requirement: Runtime token refresh on auth failure
The system SHALL automatically attempt to re-resolve tokens when a Slack API call fails with an authentication error (`invalid_auth`, `token_expired`, `not_authed`). The refresh SHALL re-execute Phase 2 and Phase 3 (skipping Phase 1 since env vars are static). The original API call SHALL be retried at most once after a successful refresh.

#### Scenario: Token expired mid-session, refresh succeeds
- **WHEN** a `search_messages` call returns `invalid_auth` AND token refresh via Chrome auto-extraction succeeds
- **THEN** system retries the API call with the new tokens and returns results normally

#### Scenario: Token expired mid-session, refresh fails
- **WHEN** a `search_messages` call returns `token_expired` AND token refresh fails
- **THEN** system raises `SlackAuthError` with a message indicating the token has expired and instructions for manual refresh

#### Scenario: Retry limit
- **WHEN** a refreshed token also fails authentication
- **THEN** system SHALL NOT attempt further refreshes and SHALL raise `SlackAuthError`

### Requirement: Token file format compatibility
The system SHALL read and write token files in the same format as `slack-token-extractor`, using the variable names `SLACK_MCP_XOXC_TOKEN` and `SLACK_MCP_XOXD_TOKEN` in the `.env` file. The system SHALL map these to the internal `SLACK_XOXC_TOKEN` / `SLACK_XOXD_TOKEN` naming when loading.

#### Scenario: Read tokens saved by slack-token-extractor
- **WHEN** `~/.slack_tokens.env` was previously created by `slack-token-extractor` CLI
- **THEN** system reads `SLACK_MCP_XOXC_TOKEN` and `SLACK_MCP_XOXD_TOKEN` values and uses them as xoxc/xoxd tokens
