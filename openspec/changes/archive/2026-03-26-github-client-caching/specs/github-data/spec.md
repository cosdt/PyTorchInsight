## MODIFIED Requirements

### Requirement: Rate limit handling
The system SHALL implement rate limit awareness for GitHub Search API (30 requests/minute) and Core API (5000 requests/hour). When approaching the limit, the system SHALL apply exponential backoff. The system SHALL expose remaining quota information in tool responses when quota is below 30%. The HTTP persistent cache SHALL reduce actual API call volume by serving cached responses and using ETag conditional requests (304 responses do not count against rate limit), thereby lowering the probability of hitting rate limits. The `rate_limit` endpoint itself SHALL NOT be cached, to ensure rate limit checks always reflect real-time quota status.

#### Scenario: Rate limit approaching
- **WHEN** GitHub API response shows `x-ratelimit-remaining` below 30% of the limit
- **THEN** system includes a warning note in the response indicating remaining API quota

#### Scenario: Cached response avoids rate limit consumption
- **WHEN** a tool call is made and the HTTP cache contains a valid (non-expired) response
- **THEN** no GitHub API request is made and no rate limit units are consumed

#### Scenario: Conditional request avoids rate limit consumption
- **WHEN** a tool call is made and the HTTP cache contains an expired response with an ETag
- **AND** GitHub returns 304 Not Modified
- **THEN** no rate limit units are consumed for this request

#### Scenario: Rate limit check always uses fresh data
- **WHEN** `_wait_for_rate_limit(force=True)` or `_update_rate_limit()` queries the `/rate_limit` endpoint
- **THEN** the request SHALL bypass the HTTP cache and always hit the GitHub API
