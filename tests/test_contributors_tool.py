"""Tests for get_key_contributors_activity tool — cross-platform aggregation."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

from pytorch_community_mcp.clients.discourse import DiscourseClient
from pytorch_community_mcp.clients.github import GitHubClient
from pytorch_community_mcp.tools.contributors import (
    _fetch_discourse_activity,
    _fetch_github_activity,
    get_key_contributors_activity,
)


def _make_github_client():
    return MagicMock(spec=GitHubClient)


def _make_discourse_client():
    client = MagicMock(spec=DiscourseClient)
    client.search = AsyncMock(return_value=[])
    return client


def _make_mock_pr(title="Fix bug", url="https://github.com/pr/1", date_str="2024-03-01", body="desc"):
    mock = MagicMock()
    mock.title = title
    mock.html_url = url
    mock.created_at.strftime.return_value = date_str
    mock.body = body
    return mock


# ---------------------------------------------------------------------------
# 3.1 Main orchestration test — all platforms succeed
# ---------------------------------------------------------------------------


async def test_all_platforms_succeed():
    """Both platforms return data, merged and sorted by date descending."""
    github = _make_github_client()
    github.search_issues.return_value = (
        [_make_mock_pr("PR 1", "https://github.com/pr/1", "2024-03-01")],
        1,
    )

    discourse = _make_discourse_client()
    discourse.search = AsyncMock(
        return_value=[
            {
                "title": "Forum topic",
                "slug": "forum-topic",
                "id": 42,
                "created_at": "2024-01-01T00:00:00Z",
                "excerpt": "An excerpt",
            }
        ]
    )

    result = await get_key_contributors_activity(
        github, discourse, "testuser", since="2024-01-01", until="2024-06-01"
    )

    assert "## Results" in result
    assert "[PR] PR 1" in result
    assert "[Forum] Forum topic" in result
    # Should NOT have platform notes when all succeed
    assert "Platform Notes" not in result


# ---------------------------------------------------------------------------
# 3.2 Failure isolation tests
# ---------------------------------------------------------------------------


async def test_github_failure_isolation():
    """GitHub exception produces 'GitHub: unavailable' note."""
    github = _make_github_client()
    github.search_issues.side_effect = Exception("GitHub down")

    discourse = _make_discourse_client()

    result = await get_key_contributors_activity(
        github, discourse, "testuser", until="2024-06-01"
    )

    assert "GitHub: unavailable" in result


async def test_discourse_exception_unavailable():
    """Discourse exception produces 'Discourse: unavailable' note."""
    github = _make_github_client()
    github.search_issues.return_value = ([], 0)

    discourse = _make_discourse_client()
    discourse.search = AsyncMock(side_effect=RuntimeError("Discourse down"))

    result = await get_key_contributors_activity(
        github, discourse, "testuser", until="2024-06-01"
    )

    assert "Discourse: unavailable" in result


# ---------------------------------------------------------------------------
# 3.3 All platforms fail
# ---------------------------------------------------------------------------


async def test_all_platforms_fail():
    """Both platforms fail: empty items, two platform notes."""
    github = _make_github_client()
    github.search_issues.side_effect = Exception("GitHub down")

    discourse = _make_discourse_client()
    discourse.search = AsyncMock(side_effect=RuntimeError("Discourse down"))

    result = await get_key_contributors_activity(
        github, discourse, "testuser", until="2024-06-01"
    )

    assert "GitHub: unavailable" in result
    assert "Discourse: unavailable" in result
    assert "No items matched" in result


# ---------------------------------------------------------------------------
# 3.4 _fetch_github_activity unit tests
# ---------------------------------------------------------------------------


def test_github_activity_date_range_with_since():
    """Date range uses since..until when both provided."""
    client = _make_github_client()
    client.search_issues.return_value = ([], 0)

    _fetch_github_activity(client, "testuser", since="2024-01-01", until="2024-06-01")

    calls = client.search_issues.call_args_list
    assert any("created:2024-01-01..2024-06-01" in str(c) for c in calls)


def test_github_activity_date_range_without_since():
    """Date range uses *..until when since is None."""
    client = _make_github_client()
    client.search_issues.return_value = ([], 0)

    _fetch_github_activity(client, "testuser", since=None, until="2024-06-01")

    calls = client.search_issues.call_args_list
    assert any("created:*..2024-06-01" in str(c) for c in calls)


def test_github_activity_formats_prs():
    """PR items have '[PR]' prefix in title."""
    client = _make_github_client()
    pr = _make_mock_pr("Fix bug", "https://github.com/pr/1", "2024-03-01", "A fix")
    client.search_issues.side_effect = [([pr], 1), ([], 0)]

    items = _fetch_github_activity(client, "testuser", None, "2024-06-01")
    assert items[0]["title"] == "[PR] Fix bug"
    assert items[0]["platform"] == "GitHub"
    assert items[0]["description"] == "A fix"


def test_github_activity_formats_issues():
    """Issue items have '[Issue]' prefix in title."""
    client = _make_github_client()
    issue = _make_mock_pr("Bug report", "https://github.com/issue/1", "2024-02-01")
    client.search_issues.side_effect = [([], 0), ([issue], 1)]

    items = _fetch_github_activity(client, "testuser", None, "2024-06-01")
    assert items[0]["title"] == "[Issue] Bug report"


def test_github_activity_body_none():
    """body=None is handled without crash."""
    client = _make_github_client()
    pr = _make_mock_pr("No body PR", body=None)
    client.search_issues.side_effect = [([pr], 1), ([], 0)]

    items = _fetch_github_activity(client, "testuser", None, "2024-06-01")
    assert items[0]["description"] == ""


# ---------------------------------------------------------------------------
# 3.6 _fetch_discourse_activity unit tests
# ---------------------------------------------------------------------------


async def test_discourse_activity_url_with_slug_and_id():
    """URL is https://discuss.pytorch.org/t/{slug}/{id} when both present."""
    client = _make_discourse_client()
    client.search = AsyncMock(
        return_value=[
            {
                "title": "My Topic",
                "slug": "my-topic",
                "id": 123,
                "created_at": "2024-01-15T00:00:00Z",
                "excerpt": "An excerpt",
            }
        ]
    )

    items = await _fetch_discourse_activity(client, "testuser", None, "2024-06-01")
    assert items[0]["url"] == "https://discuss.pytorch.org/t/my-topic/123"


async def test_discourse_activity_url_empty_slug():
    """URL is empty when slug is missing."""
    client = _make_discourse_client()
    client.search = AsyncMock(
        return_value=[
            {
                "title": "No Slug Topic",
                "slug": "",
                "id": 123,
                "created_at": "2024-01-15T00:00:00Z",
                "excerpt": "",
            }
        ]
    )

    items = await _fetch_discourse_activity(client, "testuser", None, "2024-06-01")
    assert items[0]["url"] == ""


async def test_discourse_activity_formatting():
    """Discourse items have '[Forum]' prefix and 'Discourse' platform."""
    client = _make_discourse_client()
    client.search = AsyncMock(
        return_value=[
            {
                "title": "Test Topic",
                "slug": "test",
                "id": 1,
                "created_at": "2024-01-01T00:00:00Z",
                "excerpt": "excerpt text",
            }
        ]
    )

    items = await _fetch_discourse_activity(client, "testuser", None, "2024-06-01")
    assert items[0]["title"] == "[Forum] Test Topic"
    assert items[0]["platform"] == "Discourse"


# ---------------------------------------------------------------------------
# 3.7 Default until test
# ---------------------------------------------------------------------------


async def test_default_until_uses_today():
    """until=None defaults to date.today().isoformat()."""
    github = _make_github_client()
    github.search_issues.return_value = ([], 0)
    discourse = _make_discourse_client()

    mock_today = MagicMock()
    mock_today.isoformat.return_value = "2024-06-15"

    with patch(
        "pytorch_community_mcp.tools.contributors.date"
    ) as mock_date:
        mock_date.today.return_value = mock_today
        await get_key_contributors_activity(
            github, discourse, "testuser", until=None
        )

    # Verify that the search used today's date
    calls = github.search_issues.call_args_list
    assert any("2024-06-15" in str(c) for c in calls)


# ---------------------------------------------------------------------------
# Result sorting test (spec requirement)
# ---------------------------------------------------------------------------


async def test_results_sorted_by_date_descending():
    """Results from multiple platforms are sorted by date descending."""
    github = _make_github_client()
    github.search_issues.side_effect = [
        ([_make_mock_pr("GitHub PR", date_str="2024-03-01")], 1),
        ([], 0),
    ]

    discourse = _make_discourse_client()
    discourse.search = AsyncMock(
        return_value=[
            {
                "title": "Discourse topic",
                "slug": "topic",
                "id": 1,
                "created_at": "2024-01-01T00:00:00Z",
                "excerpt": "",
            }
        ]
    )

    result = await get_key_contributors_activity(
        github, discourse, "testuser", since="2024-01-01", until="2024-06-01"
    )

    # Verify ordering: GitHub (03-01) > Discourse (01-01)
    github_pos = result.index("[PR]")
    discourse_pos = result.index("[Forum]")
    assert github_pos < discourse_pos
