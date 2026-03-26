## ADDED Requirements

### Requirement: pytest-cov is a dev dependency
The project SHALL include `pytest-cov>=5.0` in the `[project.optional-dependencies] dev` section of `pyproject.toml`.

#### Scenario: Dev dependency includes pytest-cov
- **WHEN** `pyproject.toml` dev dependencies are inspected
- **THEN** `pytest-cov>=5.0` SHALL be listed

### Requirement: Coverage source is configured
The coverage configuration SHALL target the `src/pytorch_community_mcp` package.

#### Scenario: Coverage source path
- **WHEN** `[tool.coverage.run]` in `pyproject.toml` is inspected
- **THEN** `source` SHALL include `src/pytorch_community_mcp`

### Requirement: Token extractor is omitted from coverage
The coverage configuration SHALL omit `token_extractor.py` from measurement since its Chrome extraction helpers cannot be meaningfully unit tested.

#### Scenario: Omit pattern
- **WHEN** `[tool.coverage.run]` in `pyproject.toml` is inspected
- **THEN** `omit` SHALL include a pattern matching `**/token_extractor.py`

### Requirement: Coverage threshold is enforced
The coverage report SHALL fail the test run if line coverage falls below 80%.

#### Scenario: Fail under threshold
- **WHEN** `[tool.coverage.report]` in `pyproject.toml` is inspected
- **THEN** `fail_under` SHALL be set to `80`

### Requirement: Missing lines are shown
The coverage report SHALL show which lines are not covered to aid debugging.

#### Scenario: Show missing enabled
- **WHEN** `[tool.coverage.report]` in `pyproject.toml` is inspected
- **THEN** `show_missing` SHALL be `true`

### Requirement: asyncio_mode is auto
The pytest configuration SHALL set `asyncio_mode = "auto"` to eliminate boilerplate markers on async tests.

#### Scenario: pytest asyncio_mode
- **WHEN** `[tool.pytest.ini_options]` in `pyproject.toml` is inspected
- **THEN** `asyncio_mode` SHALL be `"auto"`

### Requirement: Shared test fixtures exist
A `tests/conftest.py` SHALL provide shared fixtures to reduce mock duplication across test files.

#### Scenario: conftest.py exists with fixtures
- **WHEN** `tests/conftest.py` is inspected
- **THEN** it SHALL contain at least a fixture for creating mock GitHub issue objects (reusable `_make_mock_issue` pattern)
