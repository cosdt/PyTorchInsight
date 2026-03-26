## ADDED Requirements

### Requirement: Discourse tool error handling
The `get-discussions` tool SHALL catch Discourse API exceptions (HTTP errors, timeouts) and return structured error responses via the unified error format instead of raising unhandled exceptions.

#### Scenario: Discourse API returns HTTP error
- **WHEN** the Discourse API returns a non-2xx status code (e.g., 429 rate limit, 500 server error)
- **THEN** system returns an error response with type "DiscourseError", the HTTP status, and resolution guidance

#### Scenario: Discourse API times out
- **WHEN** the Discourse API request exceeds the timeout limit
- **THEN** system returns an error response with type "DiscourseError" and resolution guidance to retry later
