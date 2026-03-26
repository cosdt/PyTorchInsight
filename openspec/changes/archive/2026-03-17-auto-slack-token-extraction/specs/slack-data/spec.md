## MODIFIED Requirements

### Requirement: No Slack token configured
The system SHALL support two authentication modes for Slack: (1) xoxc + xoxd browser session tokens, and (2) xoxp OAuth user tokens. When no tokens are provided via environment variables, the system SHALL attempt automatic token extraction before declaring Slack unavailable. Slack-related tools SHALL still be registered regardless of token availability.

#### Scenario: No Slack token configured, auto-extraction succeeds
- **WHEN** no Slack token environment variables are set AND auto-extraction from local Chrome succeeds
- **THEN** system uses the auto-extracted tokens and Slack tools function normally

#### Scenario: No Slack token configured, auto-extraction fails
- **WHEN** no Slack token environment variables are set AND auto-extraction fails
- **THEN** Slack-related tools SHALL still be registered but return an error message indicating Slack is not configured, with instructions on how to set up tokens manually or install playwright for auto-extraction

### Requirement: Authentication failure
The system SHALL handle Slack authentication failures by attempting automatic token refresh before returning errors to the user.

#### Scenario: Authentication failure with auto-refresh
- **WHEN** Slack API returns 401 or `invalid_auth` error AND auto token refresh succeeds
- **THEN** system retries the request with refreshed tokens and returns results normally

#### Scenario: Authentication failure without auto-refresh
- **WHEN** Slack API returns 401 or `invalid_auth` error AND auto token refresh fails
- **THEN** system returns an error message indicating the token has expired and instructions to refresh via slack-token-extractor or by logging into Slack in Chrome
