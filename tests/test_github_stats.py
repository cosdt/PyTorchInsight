"""Tests for GitHub API call statistics (cache hit/miss tracking).

TDD RED phase: these tests describe the stats-tracking behaviour that will be
added to GitHubClient and server.py.  They should all FAIL until the
implementation is in place.

Features under test
-------------------
- ``GitHubClient.snapshot_stats()`` — returns a ``(hits, total)`` tuple.
- ``GitHubClient.get_stats(snapshot)`` — returns delta dict with
  ``total``, ``cached``, and ``fresh`` keys.
- ``_append_api_stats(result, stats)`` in ``server.py`` — appends a
  human-readable stats line to Markdown output.
- Server tool wrappers integrate the snapshot/stats/append cycle.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests
import requests_cache
import responses

from pytorch_community_mcp.clients.github import GitHubClient


# ---------------------------------------------------------------------------
# Test-isolation fixture (autouse, function-scope)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolate_cache():
    """Uninstall requests_cache and reset class-level counters before AND after
    every test so no global state leaks between tests."""
    requests_cache.uninstall_cache()
    GitHubClient._cache_hits = 0
    GitHubClient._cache_total = 0
    yield
    requests_cache.uninstall_cache()
    GitHubClient._cache_hits = 0
    GitHubClient._cache_total = 0


# ---------------------------------------------------------------------------
# Helper: create a GitHubClient whose cache lives in tmp_path
# ---------------------------------------------------------------------------


def _make_cached_client(tmp_path, token=None):
    """Build a GitHubClient that writes its HTTP cache into *tmp_path*.

    Patches ``os.path.expanduser`` so the cache directory ends up under
    *tmp_path* instead of the real home directory, and patches ``Github``
    so no real GitHub connection is attempted.
    """
    cache_dir = str(tmp_path / "mcp_cache")
    with patch(
        "pytorch_community_mcp.clients.github.os.path.expanduser",
        return_value=cache_dir,
    ), patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=token)
    return client


# ---------------------------------------------------------------------------
# 5.1  snapshot_stats / get_stats returns correct delta
# ---------------------------------------------------------------------------


@responses.activate
def test_snapshot_and_get_stats_counts_requests(tmp_path):
    """After installing the cache, making 3 HTTP requests (2 unique URLs +
    1 repeat) should yield stats showing the correct total, cached, and
    fresh counts.

    Flow:
      1. Create client (installs cache + hooks).
      2. Take a snapshot.
      3. Make 3 requests: URL-A, URL-B, URL-A (repeat -> cache hit).
      4. Call get_stats(snapshot).
      5. Verify total=3, cached=1, fresh=2.
    """
    url_a = "https://api.github.com/repos/pytorch/pytorch/pulls/100"
    url_b = "https://api.github.com/repos/pytorch/pytorch/pulls/200"
    responses.add(responses.GET, url_a, json={"number": 100}, status=200)
    responses.add(responses.GET, url_b, json={"number": 200}, status=200)

    client = _make_cached_client(tmp_path)

    snapshot = client.snapshot_stats()

    # First request to URL-A -- fresh.
    requests.get(url_a)
    # First request to URL-B -- fresh.
    requests.get(url_b)
    # Second request to URL-A -- should be served from cache.
    requests.get(url_a)

    stats = client.get_stats(snapshot)

    assert stats["total"] == 3
    assert stats["cached"] == 1
    assert stats["fresh"] == 2


@responses.activate
def test_snapshot_stats_returns_tuple(tmp_path):
    """snapshot_stats() must return a 2-tuple of ints (hits, total)."""
    client = _make_cached_client(tmp_path)
    snapshot = client.snapshot_stats()

    assert isinstance(snapshot, tuple)
    assert len(snapshot) == 2
    assert isinstance(snapshot[0], int)
    assert isinstance(snapshot[1], int)


@responses.activate
def test_get_stats_returns_dict_with_required_keys(tmp_path):
    """get_stats() must return a dict with 'total', 'cached', 'fresh' keys."""
    client = _make_cached_client(tmp_path)
    snapshot = client.snapshot_stats()
    stats = client.get_stats(snapshot)

    assert isinstance(stats, dict)
    assert "total" in stats
    assert "cached" in stats
    assert "fresh" in stats


@responses.activate
def test_stats_delta_is_isolated_between_snapshots(tmp_path):
    """Two sequential snapshot windows should each report only their own
    requests, not cumulative totals."""
    url_a = "https://api.github.com/repos/pytorch/pytorch/pulls/300"
    url_b = "https://api.github.com/repos/pytorch/pytorch/pulls/400"
    responses.add(responses.GET, url_a, json={"number": 300}, status=200)
    responses.add(responses.GET, url_b, json={"number": 400}, status=200)

    client = _make_cached_client(tmp_path)

    # -- Window 1: one fresh request --
    snap1 = client.snapshot_stats()
    requests.get(url_a)
    stats1 = client.get_stats(snap1)

    assert stats1["total"] == 1
    assert stats1["fresh"] == 1
    assert stats1["cached"] == 0

    # -- Window 2: one fresh request to a different URL --
    snap2 = client.snapshot_stats()
    requests.get(url_b)
    stats2 = client.get_stats(snap2)

    assert stats2["total"] == 1
    assert stats2["fresh"] == 1
    assert stats2["cached"] == 0


@responses.activate
def test_stats_zero_when_no_requests_made(tmp_path):
    """If no requests are made between snapshot and get_stats, all counts
    should be zero."""
    client = _make_cached_client(tmp_path)

    snapshot = client.snapshot_stats()
    stats = client.get_stats(snapshot)

    assert stats == {"total": 0, "cached": 0, "fresh": 0}


# ---------------------------------------------------------------------------
# 5.2  get_stats without cache installed returns zeros
# ---------------------------------------------------------------------------


def test_stats_without_cache_returns_zeros():
    """When requests_cache is NOT installed, snapshot_stats / get_stats should
    still work and return all-zero stats (graceful degradation)."""
    # Ensure cache is NOT installed.
    requests_cache.uninstall_cache()

    with patch("pytorch_community_mcp.clients.github.Github"):
        # Force is_installed to return False so cache setup is skipped.
        with patch(
            "pytorch_community_mcp.clients.github.requests_cache.is_installed",
            return_value=True,
        ):
            client = GitHubClient(token=None)

    # Cache is not actually installed; stats should degrade gracefully.
    snapshot = client.snapshot_stats()
    stats = client.get_stats(snapshot)

    assert stats == {"total": 0, "cached": 0, "fresh": 0}


# ---------------------------------------------------------------------------
# 5.3  _append_api_stats correctly appends stats line
# ---------------------------------------------------------------------------


def test_append_api_stats_appends_formatted_line():
    """_append_api_stats should append the stats summary to the result string
    with the exact format: \\n\\n**API Calls:** N total (X cached, Y fresh)"""
    from pytorch_community_mcp.server import _append_api_stats

    result = "## PRs\n- PR #1"
    stats = {"total": 4, "cached": 2, "fresh": 2}

    output = _append_api_stats(result, stats)

    expected_suffix = "\n\n**API Calls:** 4 total (2 cached, 2 fresh)"
    assert output.endswith(expected_suffix)
    assert output.startswith("## PRs\n- PR #1")


def test_append_api_stats_all_fresh():
    """When all requests are fresh (no cache hits), the stats line should
    show 0 cached."""
    from pytorch_community_mcp.server import _append_api_stats

    result = "## Issues\n- Issue #5"
    stats = {"total": 3, "cached": 0, "fresh": 3}

    output = _append_api_stats(result, stats)

    assert output.endswith("\n\n**API Calls:** 3 total (0 cached, 3 fresh)")


def test_append_api_stats_all_cached():
    """When all requests are cache hits, the stats line should reflect that."""
    from pytorch_community_mcp.server import _append_api_stats

    result = "## Commits"
    stats = {"total": 5, "cached": 5, "fresh": 0}

    output = _append_api_stats(result, stats)

    assert output.endswith("\n\n**API Calls:** 5 total (5 cached, 0 fresh)")


def test_append_api_stats_zero_calls():
    """When no API calls were made, the stats line should show all zeros."""
    from pytorch_community_mcp.server import _append_api_stats

    result = "No data"
    stats = {"total": 0, "cached": 0, "fresh": 0}

    output = _append_api_stats(result, stats)

    assert output.endswith("\n\n**API Calls:** 0 total (0 cached, 0 fresh)")


def test_append_api_stats_preserves_original_content():
    """The original result content must not be modified, only appended to."""
    from pytorch_community_mcp.server import _append_api_stats

    result = "## PRs\n- PR #1\n- PR #2\n\n## Summary\nAll good."
    stats = {"total": 10, "cached": 7, "fresh": 3}

    output = _append_api_stats(result, stats)

    # The original content must appear verbatim at the start.
    assert output.startswith(result)
    # Exactly two newlines separate original from stats.
    remainder = output[len(result) :]
    assert remainder.startswith("\n\n**API Calls:**")


# ---------------------------------------------------------------------------
# 5.4  Server wrapper integrates snapshot -> tool call -> stats append
# ---------------------------------------------------------------------------


def test_server_wrapper_calls_snapshot_before_and_stats_after():
    """Each GitHub tool wrapper in server.py should:
      1. Call snapshot_stats() before the tool function.
      2. Call the tool function.
      3. Call get_stats(snapshot) after.
      4. Call _append_api_stats(result, stats) to produce the final output.
    """
    mock_client = MagicMock(spec=GitHubClient)
    mock_client.snapshot_stats.return_value = (0, 0)
    mock_client.get_stats.return_value = {"total": 3, "cached": 1, "fresh": 2}

    tool_result = "## PRs\n- PR #1"

    with patch(
        "pytorch_community_mcp.server.github_client", mock_client
    ), patch(
        "pytorch_community_mcp.server.prs_tool"
    ) as mock_prs_tool, patch(
        "pytorch_community_mcp.server._append_api_stats",
        return_value=tool_result + "\n\n**API Calls:** 3 total (1 cached, 2 fresh)",
    ) as mock_append:
        mock_prs_tool.get_prs.return_value = tool_result

        from pytorch_community_mcp.server import get_prs

        # Call the wrapper as if it were invoked by MCP.
        output = get_prs(since="2024-01-01")

    # snapshot_stats must be called before the tool.
    mock_client.snapshot_stats.assert_called_once()
    # get_stats must be called with the snapshot value.
    mock_client.get_stats.assert_called_once_with((0, 0))
    # _append_api_stats must be called to produce the final output.
    mock_append.assert_called_once_with(
        tool_result, {"total": 3, "cached": 1, "fresh": 2}
    )
    # The final output must include the stats suffix.
    assert "**API Calls:**" in output


def test_server_wrapper_integrates_for_get_issues():
    """The get_issues wrapper should also integrate the stats cycle."""
    mock_client = MagicMock(spec=GitHubClient)
    mock_client.snapshot_stats.return_value = (5, 10)
    mock_client.get_stats.return_value = {"total": 2, "cached": 0, "fresh": 2}

    tool_result = "## Issues\n- Issue #42"

    with patch(
        "pytorch_community_mcp.server.github_client", mock_client
    ), patch(
        "pytorch_community_mcp.server.issues_tool"
    ) as mock_issues_tool, patch(
        "pytorch_community_mcp.server._append_api_stats",
        return_value=tool_result + "\n\n**API Calls:** 2 total (0 cached, 2 fresh)",
    ) as mock_append:
        mock_issues_tool.get_issues.return_value = tool_result

        from pytorch_community_mcp.server import get_issues

        output = get_issues(since="2024-01-01")

    mock_client.snapshot_stats.assert_called_once()
    mock_client.get_stats.assert_called_once_with((5, 10))
    mock_append.assert_called_once_with(
        tool_result, {"total": 2, "cached": 0, "fresh": 2}
    )
    assert "**API Calls:**" in output


def test_server_wrapper_integrates_for_get_pr_detail():
    """The get_pr_detail wrapper should also integrate the stats cycle."""
    mock_client = MagicMock(spec=GitHubClient)
    mock_client.snapshot_stats.return_value = (0, 0)
    mock_client.get_stats.return_value = {"total": 5, "cached": 3, "fresh": 2}

    tool_result = "## PR #123\nTitle: Fix bug"

    with patch(
        "pytorch_community_mcp.server.github_client", mock_client
    ), patch(
        "pytorch_community_mcp.server.pr_detail_tool"
    ) as mock_pr_detail, patch(
        "pytorch_community_mcp.server._append_api_stats",
        return_value=tool_result + "\n\n**API Calls:** 5 total (3 cached, 2 fresh)",
    ) as mock_append:
        mock_pr_detail.get_pr_detail.return_value = tool_result

        from pytorch_community_mcp.server import get_pr_detail

        output = get_pr_detail(pr_number=123)

    mock_client.snapshot_stats.assert_called_once()
    mock_client.get_stats.assert_called_once_with((0, 0))
    mock_append.assert_called_once()
    assert "**API Calls:**" in output
