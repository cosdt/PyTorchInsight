"""Tests for MCP tool functions — error handling, parameter mapping, output format."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from github import GithubException

from pytorch_community_mcp.clients.discourse import DiscourseClient
from pytorch_community_mcp.clients.events import EventsClient
from pytorch_community_mcp.clients.rss import RSSClient


# ---------------------------------------------------------------------------
# 2.1 get_events tests
# ---------------------------------------------------------------------------


async def test_get_events_success():
    """get_events returns formatted results with since/until params."""
    from pytorch_community_mcp.tools.events import get_events

    client = EventsClient()
    client.get_events = AsyncMock(
        return_value=[
            {
                "title": "PyTorch Conference",
                "url": "https://pytorch.org/event",
                "start_date": "2024-06-01T00:00:00",
                "end_date": "2024-06-02T00:00:00",
                "venue": {"venue": "San Francisco"},
                "description": "<p>A great event</p>",
            }
        ]
    )

    result = await get_events(client, since="2024-06-01", until="2024-06-30")
    assert "PyTorch Conference" in result
    assert "## Summary" in result
    assert "## Results" in result
    assert "San Francisco" in result


async def test_get_events_api_error():
    """get_events returns format_error on httpx.HTTPError."""
    from pytorch_community_mcp.tools.events import get_events

    client = EventsClient()
    client.get_events = AsyncMock(
        side_effect=httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=MagicMock(status_code=500)
        )
    )

    result = await get_events(client, since="2024-06-01")
    assert "## Error" in result
    assert "EventsError" in result


async def test_get_events_timeout():
    """get_events returns format_error on timeout."""
    from pytorch_community_mcp.tools.events import get_events

    client = EventsClient()
    client.get_events = AsyncMock(side_effect=httpx.TimeoutException("timed out"))

    result = await get_events(client, since="2024-06-01")
    assert "## Error" in result
    assert "EventsError" in result


# ---------------------------------------------------------------------------
# 2.4 get_blog_news tests
# ---------------------------------------------------------------------------


def test_get_blog_news_success():
    """get_blog_news returns formatted results."""
    from pytorch_community_mcp.tools.events import get_blog_news

    client = RSSClient()
    client.get_entries = MagicMock(
        return_value=[
            {
                "title": "New Post",
                "url": "https://pytorch.org/blog/new",
                "date": "2024-06-15",
                "author": "PyTorch Team",
                "summary": "Summary text",
            }
        ]
    )

    result = get_blog_news(client)
    assert "New Post" in result
    assert "## Results" in result


def test_get_blog_news_rss_error():
    """get_blog_news returns format_error on RSS fetch failure."""
    from pytorch_community_mcp.tools.events import get_blog_news

    client = RSSClient()
    client.get_entries = MagicMock(side_effect=httpx.HTTPError("connection failed"))

    result = get_blog_news(client)
    assert "## Error" in result
    assert "RSSError" in result


# ---------------------------------------------------------------------------
# 3.1 get_prs tests
# ---------------------------------------------------------------------------


def _make_mock_issue(title="Test PR", url="https://github.com/pr/1",
                     date="2024-01-15", author="user1", state="open",
                     labels=None, body="Description"):
    """Helper to create a mock GitHub Issue/PR object."""
    mock = MagicMock()
    mock.title = title
    mock.html_url = url
    mock.created_at.strftime.return_value = date
    mock.user.login = author
    mock.state = state
    mock.labels = [MagicMock(name=l) for l in (labels or [])]
    mock.body = body
    return mock


def test_get_prs_success():
    """get_prs returns formatted results on success."""
    from pytorch_community_mcp.clients.github import GitHubClient
    from pytorch_community_mcp.tools.prs import get_prs

    client = MagicMock(spec=GitHubClient)
    client.search_issues.return_value = ([_make_mock_issue(title="Fix distributed")], 1)
    client.rate_limit_remaining = 25
    client.rate_limit_total = 30

    result = get_prs(client, since="2024-01-01")
    assert "Fix distributed" in result
    assert "## Results" in result


def test_get_prs_github_exception():
    """get_prs returns format_error on GithubException."""
    from pytorch_community_mcp.clients.github import GitHubClient
    from pytorch_community_mcp.tools.prs import get_prs

    client = MagicMock(spec=GitHubClient)
    client.search_issues.side_effect = GithubException(401, {"message": "Bad credentials"}, None)

    result = get_prs(client, since="2024-01-01")
    assert "## Error" in result
    assert "GitHubError" in result


def test_get_prs_empty_results():
    """get_prs returns empty results message."""
    from pytorch_community_mcp.clients.github import GitHubClient
    from pytorch_community_mcp.tools.prs import get_prs

    client = MagicMock(spec=GitHubClient)
    client.search_issues.return_value = ([], 0)
    client.rate_limit_remaining = 25
    client.rate_limit_total = 30

    result = get_prs(client, since="2024-01-01")
    assert "No items matched" in result


def test_get_prs_merged_state():
    """get_prs with state='merged' adds 'is:merged' to query."""
    from pytorch_community_mcp.clients.github import GitHubClient
    from pytorch_community_mcp.tools.prs import get_prs

    client = MagicMock(spec=GitHubClient)
    client.search_issues.return_value = ([], 0)
    client.rate_limit_remaining = 25
    client.rate_limit_total = 30

    get_prs(client, since="2024-01-01", state="merged")
    query = client.search_issues.call_args[0][0]
    assert "is:merged" in query


def test_get_prs_date_type_updated():
    """get_prs with date_type='updated' uses 'updated:' in query."""
    from pytorch_community_mcp.clients.github import GitHubClient
    from pytorch_community_mcp.tools.prs import get_prs

    client = MagicMock(spec=GitHubClient)
    client.search_issues.return_value = ([], 0)
    client.rate_limit_remaining = 25
    client.rate_limit_total = 30

    get_prs(client, since="2024-01-01", date_type="updated")
    query = client.search_issues.call_args[0][0]
    assert "updated:" in query
    assert "created:" not in query


# ---------------------------------------------------------------------------
# 3.3 get_issues tests
# ---------------------------------------------------------------------------


def test_get_issues_success():
    """get_issues returns formatted results on success."""
    from pytorch_community_mcp.clients.github import GitHubClient
    from pytorch_community_mcp.tools.issues import get_issues

    client = MagicMock(spec=GitHubClient)
    client.search_issues.return_value = ([_make_mock_issue(title="Bug report")], 1)
    client.rate_limit_remaining = 25
    client.rate_limit_total = 30

    result = get_issues(client, since="2024-01-01")
    assert "Bug report" in result
    assert "## Results" in result


def test_get_issues_github_exception():
    """get_issues returns format_error on GithubException."""
    from pytorch_community_mcp.clients.github import GitHubClient
    from pytorch_community_mcp.tools.issues import get_issues

    client = MagicMock(spec=GitHubClient)
    client.search_issues.side_effect = GithubException(403, {"message": "rate limit"}, None)

    result = get_issues(client, since="2024-01-01")
    assert "## Error" in result
    assert "GitHubError" in result


def test_get_issues_empty_results():
    """get_issues returns empty results message."""
    from pytorch_community_mcp.clients.github import GitHubClient
    from pytorch_community_mcp.tools.issues import get_issues

    client = MagicMock(spec=GitHubClient)
    client.search_issues.return_value = ([], 0)
    client.rate_limit_remaining = 25
    client.rate_limit_total = 30

    result = get_issues(client, since="2024-01-01")
    assert "No items matched" in result


def test_get_issues_date_type_updated():
    """get_issues with date_type='updated' uses 'updated:' in query."""
    from pytorch_community_mcp.clients.github import GitHubClient
    from pytorch_community_mcp.tools.issues import get_issues

    client = MagicMock(spec=GitHubClient)
    client.search_issues.return_value = ([], 0)
    client.rate_limit_remaining = 25
    client.rate_limit_total = 30

    get_issues(client, since="2024-01-01", date_type="updated")
    query = client.search_issues.call_args[0][0]
    assert "updated:" in query


# ---------------------------------------------------------------------------
# 3.5 get_rfcs tests
# ---------------------------------------------------------------------------


def test_get_rfcs_success():
    """get_rfcs returns formatted results on success."""
    from pytorch_community_mcp.clients.github import GitHubClient
    from pytorch_community_mcp.tools.rfcs import get_rfcs

    client = MagicMock(spec=GitHubClient)
    client.search_issues.return_value = (
        [_make_mock_issue(title="RFC: New feature", url="https://github.com/rfc/1")],
        1,
    )
    client.rate_limit_remaining = 25
    client.rate_limit_total = 30

    result = get_rfcs(client, since="2024-01-01")
    assert "RFC: New feature" in result
    assert "## Results" in result


def test_get_rfcs_github_exception():
    """get_rfcs returns format_error on GithubException."""
    from pytorch_community_mcp.clients.github import GitHubClient
    from pytorch_community_mcp.tools.rfcs import get_rfcs

    client = MagicMock(spec=GitHubClient)
    client.search_issues.side_effect = GithubException(401, {"message": "Bad credentials"}, None)

    result = get_rfcs(client, since="2024-01-01")
    assert "## Error" in result
    assert "GitHubError" in result


# ---------------------------------------------------------------------------
# 3.7 get_commits tests
# ---------------------------------------------------------------------------


def test_get_commits_success():
    """get_commits returns formatted results on success."""
    from pytorch_community_mcp.clients.github import GitHubClient
    from pytorch_community_mcp.tools.commits import get_commits

    client = MagicMock(spec=GitHubClient)

    mock_commit = MagicMock()
    mock_commit.sha = "abc123def456"
    mock_commit.html_url = "https://github.com/pytorch/pytorch/commit/abc123"
    mock_commit.commit.message = "Fix bug in distributed (#12345)\n\nDetailed description"
    mock_commit.commit.author.date.strftime.return_value = "2024-03-01"
    mock_commit.commit.author.name = "Test User"
    mock_commit.author.login = "testuser"

    client.get_commits.return_value = ([mock_commit], 1)
    client.rate_limit_remaining = 25
    client.rate_limit_total = 30

    result = get_commits(client, since="2024-03-01")
    assert "Fix bug in distributed" in result
    assert "## Results" in result
    assert "abc123def4" in result  # sha[:10]


def test_get_commits_github_exception():
    """get_commits returns format_error on GithubException."""
    from pytorch_community_mcp.clients.github import GitHubClient
    from pytorch_community_mcp.tools.commits import get_commits

    client = MagicMock(spec=GitHubClient)
    client.get_commits.side_effect = GithubException(401, {"message": "Bad credentials"}, None)

    result = get_commits(client, since="2024-03-01")
    assert "## Error" in result
    assert "GitHubError" in result


def test_get_commits_pr_number_extraction():
    """get_commits extracts PR number from commit message."""
    from pytorch_community_mcp.tools.commits import _extract_pr_number

    assert _extract_pr_number("Fix bug (#123)") == "123"
    assert _extract_pr_number("Pull Request resolved: https://github.com/pytorch/pytorch/pull/456") == "456"
    assert _extract_pr_number("No PR reference here") == ""


# ---------------------------------------------------------------------------
# 4.1 get_discussions tests
# ---------------------------------------------------------------------------


async def test_get_discussions_success():
    """get_discussions returns formatted results on success."""
    from pytorch_community_mcp.tools.discussions import get_discussions

    client = DiscourseClient()
    client.search = AsyncMock(
        return_value=[
            {
                "id": 123,
                "title": "How to use torch.compile",
                "slug": "how-to-use-torch-compile",
                "created_at": "2024-01-15T12:00:00Z",
                "last_poster_username": "user1",
                "posts_count": 5,
                "views": 100,
                "excerpt": "A discussion about torch.compile",
            }
        ]
    )

    result = await get_discussions(client, query="torch.compile")
    assert "torch.compile" in result
    assert "## Results" in result


async def test_get_discussions_http_error():
    """get_discussions returns format_error on HTTP error."""
    from pytorch_community_mcp.tools.discussions import get_discussions

    client = DiscourseClient()
    client.search = AsyncMock(
        side_effect=httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=MagicMock(status_code=500)
        )
    )

    result = await get_discussions(client, query="test")
    assert "## Error" in result
    assert "DiscourseError" in result


async def test_get_discussions_timeout():
    """get_discussions returns format_error on timeout."""
    from pytorch_community_mcp.tools.discussions import get_discussions

    client = DiscourseClient()
    client.search = AsyncMock(side_effect=httpx.TimeoutException("timed out"))

    result = await get_discussions(client, query="test")
    assert "## Error" in result
    assert "DiscourseError" in result
