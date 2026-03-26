"""Tests for the unified output formatter."""

from pytorch_community_mcp.formatter import format_error, format_results


def test_format_results_basic():
    result = format_results(
        "test-tool",
        {"since": "2024-01-01"},
        [
            {
                "title": "Test Item",
                "url": "https://example.com",
                "date": "2024-01-15",
                "author": "user1",
                "description": "A test item.",
            }
        ],
    )
    assert "## Summary" in result
    assert "test-tool" in result
    assert "## Results" in result
    assert "Test Item" in result
    assert "https://example.com" in result
    assert "2024-01-15" in result
    assert "user1" in result


def test_format_results_empty():
    result = format_results("test-tool", {"query": "nothing"}, [])
    assert "## Summary" in result
    assert "Results:** 0" in result
    assert "No items matched" in result


def test_format_results_rate_limit_warning():
    result = format_results(
        "test-tool",
        {},
        [{"title": "Item"}],
        rate_limit_remaining=5,
        rate_limit_total=30,
    )
    assert "quota low" in result
    assert "5/30" in result


def test_format_results_no_rate_limit_warning_when_ok():
    result = format_results(
        "test-tool",
        {},
        [{"title": "Item"}],
        rate_limit_remaining=25,
        rate_limit_total=30,
    )
    assert "quota low" not in result


def test_format_results_truncated():
    result = format_results(
        "test-tool",
        {},
        [{"title": "Item"}],
        truncated=True,
    )
    assert "truncated" in result


def test_format_results_total_count_shown_when_truncated():
    """When total_count > len(items), show 'X / Y total' and truncation note."""
    result = format_results(
        "test-tool",
        {},
        [{"title": "Item 1"}, {"title": "Item 2"}],
        total_count=50,
    )
    assert "2 / 50 total" in result
    assert "truncated" in result.lower()


def test_format_results_total_count_hidden_when_all_returned():
    """When total_count == len(items), show plain count without truncation."""
    result = format_results(
        "test-tool",
        {},
        [{"title": "Item 1"}, {"title": "Item 2"}],
        total_count=2,
    )
    assert "Results:** 2" in result
    assert "truncated" not in result.lower()


def test_format_error():
    result = format_error(
        "AuthenticationError",
        "Token expired",
        "Check your API credentials",
    )
    assert "## Error" in result
    assert "AuthenticationError" in result
    assert "Token expired" in result
    assert "API credentials" in result


def test_format_error_no_resolution():
    result = format_error("APIError", "Service unavailable")
    assert "## Error" in result
    assert "Resolution" not in result


# --- safe_parse_date tests ---

from pytorch_community_mcp.formatter import safe_parse_date


def test_safe_parse_date_iso_datetime():
    assert safe_parse_date("2024-01-15T12:30:00Z") == "2024-01-15"


def test_safe_parse_date_iso_datetime_with_offset():
    assert safe_parse_date("2024-01-15T12:30:00+00:00") == "2024-01-15"


def test_safe_parse_date_date_only():
    assert safe_parse_date("2024-01-15") == "2024-01-15"


def test_safe_parse_date_empty_string():
    assert safe_parse_date("") == ""


def test_safe_parse_date_non_date_string():
    assert safe_parse_date("not-a-date") == "not-a-date"
