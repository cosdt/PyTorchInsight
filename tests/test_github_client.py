"""Tests for GitHubClient — rate limiting, retries, backoff, pagination."""

from unittest.mock import MagicMock, patch

import pytest
from github import GithubException, RateLimitExceededException

from pytorch_community_mcp.clients.github import GitHubClient, RateLimitInfo


# ---------------------------------------------------------------------------
# 2.1 Construction tests
# ---------------------------------------------------------------------------


def test_construction_without_token():
    """GitHubClient(token=None) sets default rate limit values."""
    with patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=None)
    assert client.rate_limit_remaining == 30
    assert client.rate_limit_total == 30


def test_construction_with_token():
    """GitHubClient(token='ghp_xxx') initializes without error."""
    with patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token="ghp_xxx")
    assert client.rate_limit_remaining == 30
    assert client.rate_limit_total == 30


# ---------------------------------------------------------------------------
# 2.2 _update_rate_limit tests
# ---------------------------------------------------------------------------


def test_update_rate_limit_success():
    """Successful update reads search.remaining/limit/reset."""
    with patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=None)

    mock_rl = MagicMock()
    mock_rl.search.remaining = 15
    mock_rl.search.limit = 30
    mock_rl.search.reset.timestamp.return_value = 1700000000.0
    client._github.get_rate_limit.return_value = mock_rl

    client._update_rate_limit()

    assert client.rate_limit_remaining == 15
    assert client.rate_limit_total == 30
    assert client._rate_limit.reset_time == 1700000000.0


def test_update_rate_limit_github_exception_ignored():
    """GithubException during _update_rate_limit is silently ignored."""
    with patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=None)

    client._github.get_rate_limit.side_effect = GithubException(
        500, {"message": "server error"}, None
    )

    # Should not raise, values should remain at defaults
    client._update_rate_limit()
    assert client.rate_limit_remaining == 30
    assert client.rate_limit_total == 30


# ---------------------------------------------------------------------------
# 2.3 _wait_for_rate_limit tests
# ---------------------------------------------------------------------------


@patch("pytorch_community_mcp.clients.github.time")
def test_wait_no_sleep_when_quota_available(mock_time):
    """No sleep when remaining > 1."""
    with patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=None)

    # Mock _update_rate_limit to set remaining > 1
    client._rate_limit.remaining = 10
    client._github.get_rate_limit.side_effect = GithubException(
        500, {"message": "skip"}, None
    )

    client._wait_for_rate_limit()
    mock_time.sleep.assert_not_called()


@patch("pytorch_community_mcp.clients.github.time")
def test_wait_sleeps_when_rate_limited_future_reset(mock_time):
    """Sleeps correct duration when rate limited with future reset time."""
    with patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=None)

    mock_time.time.return_value = 1000.0

    # After _update_rate_limit, simulate remaining <= 1, reset 30s in future
    mock_rl = MagicMock()
    mock_rl.search.remaining = 0
    mock_rl.search.limit = 30
    mock_rl.search.reset.timestamp.return_value = 1030.0
    client._github.get_rate_limit.return_value = mock_rl

    client._wait_for_rate_limit()
    # wait_time = max(0, 1030 - 1000) + 1 = 31, min(31, 60) = 31
    mock_time.sleep.assert_called_once_with(31)


@patch("pytorch_community_mcp.clients.github.time")
def test_wait_sleeps_capped_at_60s(mock_time):
    """Sleep is capped at 60s when reset is far in the future."""
    with patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=None)

    mock_time.time.return_value = 1000.0

    mock_rl = MagicMock()
    mock_rl.search.remaining = 0
    mock_rl.search.limit = 30
    mock_rl.search.reset.timestamp.return_value = 1120.0  # 120s in future
    client._github.get_rate_limit.return_value = mock_rl

    client._wait_for_rate_limit()
    # wait_time = max(0, 120) + 1 = 121, min(121, 60) = 60
    mock_time.sleep.assert_called_once_with(60)


@patch("pytorch_community_mcp.clients.github.time")
def test_wait_sleeps_past_reset_time(mock_time):
    """Sleep is 1s when reset time is in the past."""
    with patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=None)

    mock_time.time.return_value = 1000.0

    mock_rl = MagicMock()
    mock_rl.search.remaining = 0
    mock_rl.search.limit = 30
    mock_rl.search.reset.timestamp.return_value = 990.0  # in the past
    client._github.get_rate_limit.return_value = mock_rl

    client._wait_for_rate_limit()
    # wait_time = max(0, 990 - 1000) + 1 = max(0, -10) + 1 = 1
    mock_time.sleep.assert_called_once_with(1)


# ---------------------------------------------------------------------------
# 2.4 search_issues success tests
# ---------------------------------------------------------------------------


def _make_paginated_result(items):
    """Create a mock that acts like a PaginatedList with totalCount."""
    mock = MagicMock()
    mock.__iter__ = MagicMock(return_value=iter(items))
    mock.totalCount = len(items)
    return mock


@patch("pytorch_community_mcp.clients.github.time")
def test_search_issues_returns_results(mock_time):
    """search_issues returns correct results and total_count."""
    with patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=None)

    mock_time.time.return_value = 1000.0
    # Skip rate limit waits
    client._rate_limit.remaining = 30
    client._github.get_rate_limit.side_effect = GithubException(
        500, {"message": "skip"}, None
    )

    items = [MagicMock() for _ in range(3)]
    client._github.search_issues.return_value = _make_paginated_result(items)

    result, total_count = client.search_issues("query")
    assert len(result) == 3
    assert total_count == 3


@patch("pytorch_community_mcp.clients.github.time")
def test_search_issues_truncation_at_max_results(mock_time):
    """search_issues truncates at max_results."""
    with patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=None)

    mock_time.time.return_value = 1000.0
    client._rate_limit.remaining = 30
    client._github.get_rate_limit.side_effect = GithubException(
        500, {"message": "skip"}, None
    )

    items = [MagicMock() for _ in range(5)]
    client._github.search_issues.return_value = _make_paginated_result(items)

    result, total_count = client.search_issues("query", max_results=2)
    assert len(result) == 2
    assert total_count == 5  # total_count reflects actual total, not truncated


@patch("pytorch_community_mcp.clients.github.time")
def test_search_issues_empty_results(mock_time):
    """search_issues returns empty list when no results."""
    with patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=None)

    mock_time.time.return_value = 1000.0
    client._rate_limit.remaining = 30
    client._github.get_rate_limit.side_effect = GithubException(
        500, {"message": "skip"}, None
    )

    client._github.search_issues.return_value = _make_paginated_result([])

    result, total_count = client.search_issues("query")
    assert result == []
    assert total_count == 0


# ---------------------------------------------------------------------------
# 2.5 search_issues RateLimitExceededException retry tests
# ---------------------------------------------------------------------------


@patch("pytorch_community_mcp.clients.github.time")
def test_search_issues_rate_limit_single_retry(mock_time):
    """Single rate limit failure then success."""
    with patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=None)

    mock_time.time.return_value = 1000.0
    client._rate_limit.remaining = 30
    client._github.get_rate_limit.side_effect = GithubException(
        500, {"message": "skip"}, None
    )

    items = [MagicMock()]
    client._github.search_issues.side_effect = [
        RateLimitExceededException(403, {"message": "rate limited"}, None),
        _make_paginated_result(items),
    ]

    result, total_count = client.search_issues("query")
    assert len(result) == 1
    # backoff = 2^0 * 10 = 10, min(10, 60) = 10
    mock_time.sleep.assert_any_call(10)


@patch("pytorch_community_mcp.clients.github.time")
def test_search_issues_rate_limit_exhausted(mock_time):
    """Exhausted retries on rate limit returns empty list."""
    with patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=None)

    client._rate_limit.remaining = 30
    client._github.get_rate_limit.side_effect = GithubException(
        500, {"message": "skip"}, None
    )

    client._github.search_issues.side_effect = RateLimitExceededException(
        403, {"message": "rate limited"}, None
    )

    result, total_count = client.search_issues("query", max_retries=3)
    assert result == []
    assert total_count == 0


@patch("pytorch_community_mcp.clients.github.time")
def test_search_issues_rate_limit_backoff_increases(mock_time):
    """Backoff increases: 10, 20 on successive rate limit failures."""
    with patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=None)

    mock_time.time.return_value = 1000.0
    client._rate_limit.remaining = 30
    client._github.get_rate_limit.side_effect = GithubException(
        500, {"message": "skip"}, None
    )

    items = [MagicMock()]
    client._github.search_issues.side_effect = [
        RateLimitExceededException(403, {"message": "rate limited"}, None),
        RateLimitExceededException(403, {"message": "rate limited"}, None),
        _make_paginated_result(items),
    ]

    result, total_count = client.search_issues("query")
    assert len(result) == 1
    sleep_calls = [c.args[0] for c in mock_time.sleep.call_args_list]
    assert 10 in sleep_calls
    assert 20 in sleep_calls


# ---------------------------------------------------------------------------
# 2.6 search_issues GithubException retry tests
# ---------------------------------------------------------------------------


@patch("pytorch_community_mcp.clients.github.time")
def test_search_issues_github_exception_single_retry(mock_time):
    """Single GithubException then success."""
    with patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=None)

    mock_time.time.return_value = 1000.0
    client._rate_limit.remaining = 30
    client._github.get_rate_limit.side_effect = GithubException(
        500, {"message": "skip"}, None
    )

    items = [MagicMock()]
    client._github.search_issues.side_effect = [
        GithubException(500, {"message": "server error"}, None),
        _make_paginated_result(items),
    ]

    result, total_count = client.search_issues("query")
    assert len(result) == 1
    # backoff = 2^0 = 1
    mock_time.sleep.assert_any_call(1)


@patch("pytorch_community_mcp.clients.github.time")
def test_search_issues_github_exception_exhausted(mock_time):
    """Exhausted retries on GithubException raises the exception."""
    with patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=None)

    client._rate_limit.remaining = 30
    client._github.get_rate_limit.side_effect = GithubException(
        500, {"message": "skip"}, None
    )

    client._github.search_issues.side_effect = GithubException(
        500, {"message": "server error"}, None
    )

    with pytest.raises(GithubException):
        client.search_issues("query", max_retries=3)


@patch("pytorch_community_mcp.clients.github.time")
def test_search_issues_github_exception_max_retries_1(mock_time):
    """max_retries=1 raises GithubException immediately."""
    with patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=None)

    client._rate_limit.remaining = 30
    client._github.get_rate_limit.side_effect = GithubException(
        500, {"message": "skip"}, None
    )

    client._github.search_issues.side_effect = GithubException(
        500, {"message": "server error"}, None
    )

    with pytest.raises(GithubException):
        client.search_issues("query", max_retries=1)


# ---------------------------------------------------------------------------
# 3.1 Repo cache tests
# ---------------------------------------------------------------------------


def test_get_repo_cache_hit():
    """Second call to _get_repo with same name does not call _github.get_repo."""
    with patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=None)

    mock_repo = MagicMock()
    client._github.get_repo.return_value = mock_repo

    repo1 = client._get_repo("pytorch/pytorch")
    repo2 = client._get_repo("pytorch/pytorch")

    assert repo1 is repo2
    client._github.get_repo.assert_called_once_with("pytorch/pytorch")


def test_get_repo_cache_separate_repos():
    """Different repo names get separate cache entries."""
    with patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=None)

    mock_pytorch = MagicMock(name="pytorch_repo")
    mock_vision = MagicMock(name="vision_repo")
    client._github.get_repo.side_effect = [mock_pytorch, mock_vision]

    repo1 = client._get_repo("pytorch/pytorch")
    repo2 = client._get_repo("pytorch/vision")

    assert repo1 is mock_pytorch
    assert repo2 is mock_vision
    assert client._github.get_repo.call_count == 2


def test_get_repo_cache_exception_not_cached():
    """Failed get_repo does not pollute cache — next call retries."""
    with patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=None)

    mock_repo = MagicMock()
    client._github.get_repo.side_effect = [
        GithubException(500, {"message": "server error"}, None),
        mock_repo,
    ]

    with pytest.raises(GithubException):
        client._get_repo("pytorch/pytorch")

    # Second call should retry and succeed
    repo = client._get_repo("pytorch/pytorch")
    assert repo is mock_repo
    assert client._github.get_repo.call_count == 2


def test_get_repo_used_by_get_commits():
    """get_commits uses cached repo — second call does not re-fetch repo."""
    with patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=None)

    mock_repo = MagicMock()
    mock_commits = MagicMock()
    mock_commits.totalCount = 0
    mock_commits.__iter__ = MagicMock(return_value=iter([]))
    mock_repo.get_commits.return_value = mock_commits
    client._github.get_repo.return_value = mock_repo
    # Skip rate limit
    client._github.get_rate_limit.side_effect = GithubException(
        500, {"message": "skip"}, None
    )

    from datetime import datetime, timezone

    since = datetime(2024, 1, 1, tzinfo=timezone.utc)
    client.get_commits(since=since, max_results=1)
    client.get_commits(since=since, max_results=1)

    # get_repo should only be called once (cached on first call)
    client._github.get_repo.assert_called_once()


# ---------------------------------------------------------------------------
# 3.2 Rate limit throttle tests
# ---------------------------------------------------------------------------


@patch("pytorch_community_mcp.clients.github.time")
def test_rate_limit_throttle_within_window_is_noop(mock_time):
    """Second _update_rate_limit call within 60s does not call get_rate_limit."""
    with patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=None)

    mock_time.time.return_value = 1000.0

    mock_rl = MagicMock()
    mock_rl.search.remaining = 20
    mock_rl.search.limit = 30
    mock_rl.search.reset.timestamp.return_value = 1060.0
    mock_rl.core.remaining = 4000
    mock_rl.core.limit = 5000
    mock_rl.core.reset.timestamp.return_value = 1060.0
    client._github.get_rate_limit.return_value = mock_rl

    # First call — should fetch
    client._update_rate_limit()
    assert client._github.get_rate_limit.call_count == 1

    # Second call at T+30s — should be throttled
    mock_time.time.return_value = 1030.0
    client._update_rate_limit()
    assert client._github.get_rate_limit.call_count == 1  # still 1, no new call


@patch("pytorch_community_mcp.clients.github.time")
def test_rate_limit_throttle_after_window_refreshes(mock_time):
    """_update_rate_limit call after 60s window makes a fresh API call."""
    with patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=None)

    mock_time.time.return_value = 1000.0

    mock_rl = MagicMock()
    mock_rl.search.remaining = 20
    mock_rl.search.limit = 30
    mock_rl.search.reset.timestamp.return_value = 1060.0
    mock_rl.core.remaining = 4000
    mock_rl.core.limit = 5000
    mock_rl.core.reset.timestamp.return_value = 1060.0
    client._github.get_rate_limit.return_value = mock_rl

    # First call
    client._update_rate_limit()
    assert client._github.get_rate_limit.call_count == 1

    # Call at T+61s — should refresh
    mock_time.time.return_value = 1061.0
    client._update_rate_limit()
    assert client._github.get_rate_limit.call_count == 2


@patch("pytorch_community_mcp.clients.github.time")
def test_rate_limit_throttle_failure_does_not_update_timestamp(mock_time):
    """Failed get_rate_limit does not update timestamp — next call retries."""
    with patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=None)

    mock_time.time.return_value = 1000.0

    # First call fails
    client._github.get_rate_limit.side_effect = GithubException(
        500, {"message": "server error"}, None
    )
    client._update_rate_limit()

    # Next call at T+1s should retry (not throttled) because failure didn't set timestamp
    mock_time.time.return_value = 1001.0
    mock_rl = MagicMock()
    mock_rl.search.remaining = 20
    mock_rl.search.limit = 30
    mock_rl.search.reset.timestamp.return_value = 1060.0
    mock_rl.core.remaining = 4000
    mock_rl.core.limit = 5000
    mock_rl.core.reset.timestamp.return_value = 1060.0
    client._github.get_rate_limit.side_effect = None
    client._github.get_rate_limit.return_value = mock_rl
    client._update_rate_limit()

    assert client.rate_limit_remaining == 20


@patch("pytorch_community_mcp.clients.github.time")
def test_wait_for_rate_limit_bypasses_throttle(mock_time):
    """_wait_for_rate_limit always gets fresh data, even within throttle window."""
    with patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=None)

    mock_time.time.return_value = 1000.0

    # First update — sets remaining=20, timestamp=1000
    mock_rl = MagicMock()
    mock_rl.search.remaining = 20
    mock_rl.search.limit = 30
    mock_rl.search.reset.timestamp.return_value = 1060.0
    mock_rl.core.remaining = 4000
    mock_rl.core.limit = 5000
    mock_rl.core.reset.timestamp.return_value = 1060.0
    client._github.get_rate_limit.return_value = mock_rl
    client._update_rate_limit()

    # At T+10s, _wait_for_rate_limit should force a fresh check
    mock_time.time.return_value = 1010.0
    mock_rl2 = MagicMock()
    mock_rl2.search.remaining = 5  # changed value
    mock_rl2.search.limit = 30
    mock_rl2.search.reset.timestamp.return_value = 1060.0
    mock_rl2.core.remaining = 4000
    mock_rl2.core.limit = 5000
    mock_rl2.core.reset.timestamp.return_value = 1060.0
    client._github.get_rate_limit.return_value = mock_rl2

    client._wait_for_rate_limit()

    # Should see the updated value (5), not the cached one (20)
    assert client.rate_limit_remaining == 5
    # get_rate_limit called twice total (initial + forced)
    assert client._github.get_rate_limit.call_count == 2


# ---------------------------------------------------------------------------
# 3.3 PR object cache tests
# ---------------------------------------------------------------------------


def _make_client_with_skip_rate_limit():
    """Helper: create a GitHubClient with rate limit checks disabled."""
    with patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=None)
    client._github.get_rate_limit.side_effect = GithubException(
        500, {"message": "skip"}, None
    )
    client._rate_limit.remaining = 30
    return client


@patch("pytorch_community_mcp.clients.github.time")
def test_pr_cache_hit_on_get_pr_files(mock_time):
    """get_pr_files reuses PR object cached by get_pull_request."""
    mock_time.time.return_value = 1000.0
    client = _make_client_with_skip_rate_limit()

    mock_repo = MagicMock()
    mock_pr = MagicMock()
    mock_repo.get_pull.return_value = mock_pr
    mock_pr.get_files.return_value = [MagicMock(filename="a.py")]
    client._github.get_repo.return_value = mock_repo

    # First: get_pull_request caches the PR
    client.get_pull_request(pr_number=123)

    # Second: get_pr_files should reuse cached PR, not call get_pull again
    mock_repo.get_pull.reset_mock()
    files = client.get_pr_files(pr_number=123)

    assert len(files) == 1
    mock_repo.get_pull.assert_not_called()


@patch("pytorch_community_mcp.clients.github.time")
def test_pr_cache_hit_on_get_pr_reviews(mock_time):
    """get_pr_reviews reuses PR object cached by get_pull_request."""
    mock_time.time.return_value = 1000.0
    client = _make_client_with_skip_rate_limit()

    mock_repo = MagicMock()
    mock_pr = MagicMock()
    mock_repo.get_pull.return_value = mock_pr
    mock_pr.get_reviews.return_value = [MagicMock()]
    client._github.get_repo.return_value = mock_repo

    client.get_pull_request(pr_number=42)

    mock_repo.get_pull.reset_mock()
    reviews = client.get_pr_reviews(pr_number=42)

    assert len(reviews) == 1
    mock_repo.get_pull.assert_not_called()


@patch("pytorch_community_mcp.clients.github.time")
def test_pr_cache_miss_fetches_fresh(mock_time):
    """get_pr_files without prior get_pull_request still works (cache miss)."""
    mock_time.time.return_value = 1000.0
    client = _make_client_with_skip_rate_limit()

    mock_repo = MagicMock()
    mock_pr = MagicMock()
    mock_repo.get_pull.return_value = mock_pr
    mock_pr.get_files.return_value = [MagicMock(filename="b.py")]
    client._github.get_repo.return_value = mock_repo

    files = client.get_pr_files(pr_number=99)

    assert len(files) == 1
    mock_repo.get_pull.assert_called_once_with(99)


# ---------------------------------------------------------------------------
# 3.4 Issue object cache tests
# ---------------------------------------------------------------------------


@patch("pytorch_community_mcp.clients.github.time")
def test_issue_cache_hit_on_get_issue_comments(mock_time):
    """get_issue_comments reuses Issue object cached by get_issue."""
    mock_time.time.return_value = 1000.0
    client = _make_client_with_skip_rate_limit()

    mock_repo = MagicMock()
    mock_issue = MagicMock()
    mock_repo.get_issue.return_value = mock_issue
    mock_comments = _make_paginated_result([MagicMock()])
    mock_issue.get_comments.return_value = mock_comments
    client._github.get_repo.return_value = mock_repo

    client.get_issue(issue_number=456)

    mock_repo.get_issue.reset_mock()
    comments, total = client.get_issue_comments(issue_number=456)

    assert len(comments) == 1
    mock_repo.get_issue.assert_not_called()


@patch("pytorch_community_mcp.clients.github.time")
def test_issue_cache_hit_on_get_issue_timeline(mock_time):
    """get_issue_timeline reuses Issue object cached by get_issue."""
    mock_time.time.return_value = 1000.0
    client = _make_client_with_skip_rate_limit()

    mock_repo = MagicMock()
    mock_issue = MagicMock()
    mock_repo.get_issue.return_value = mock_issue
    mock_issue.get_timeline.return_value = iter([MagicMock()])
    client._github.get_repo.return_value = mock_repo

    client.get_issue(issue_number=789)

    mock_repo.get_issue.reset_mock()
    events = client.get_issue_timeline(issue_number=789)

    assert len(events) == 1
    mock_repo.get_issue.assert_not_called()


@patch("pytorch_community_mcp.clients.github.time")
def test_pr_and_issue_cache_cross_method_repo_reuse(mock_time):
    """get_pull_request + get_pr_files + get_pr_reviews = only 1 get_repo call."""
    mock_time.time.return_value = 1000.0
    client = _make_client_with_skip_rate_limit()

    mock_repo = MagicMock()
    mock_pr = MagicMock()
    mock_repo.get_pull.return_value = mock_pr
    mock_pr.get_files.return_value = []
    mock_pr.get_reviews.return_value = []
    client._github.get_repo.return_value = mock_repo

    client.get_pull_request(pr_number=100)
    client.get_pr_files(pr_number=100)
    client.get_pr_reviews(pr_number=100)

    client._github.get_repo.assert_called_once_with("pytorch/pytorch")
