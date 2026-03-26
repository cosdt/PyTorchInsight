"""Tests for get_issue_detail tool — output format, comments, linked PRs, error handling."""

from unittest.mock import MagicMock

from github import GithubException, UnknownObjectException

from pytorch_community_mcp.clients.github import GitHubClient
from pytorch_community_mcp.tools.issue_detail import get_issue_detail, _extract_linked_prs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_issue(
    title="Bug report",
    url="https://github.com/pytorch/pytorch/issues/98765",
    author="user1",
    state="open",
    created="2024-01-15",
    labels=None,
    assignees=None,
    milestone=None,
    body="Issue body text",
):
    issue = MagicMock()
    issue.title = title
    issue.html_url = url
    issue.user.login = author
    issue.state = state
    issue.created_at.strftime.return_value = created
    mock_labels = []
    for l in (labels or []):
        ml = MagicMock()
        ml.name = l
        mock_labels.append(ml)
    issue.labels = mock_labels
    mock_assignees = []
    for a in (assignees or []):
        ma = MagicMock()
        ma.login = a
        mock_assignees.append(ma)
    issue.assignees = mock_assignees
    if milestone:
        issue.milestone.title = milestone
    else:
        issue.milestone = None
    issue.body = body
    return issue


def _make_mock_comment(author="commenter1", date="2024-01-16", body="Comment text"):
    c = MagicMock()
    c.user.login = author
    c.created_at.strftime.return_value = date
    c.body = body
    return c


def _make_cross_ref_event(pr_number=100, pr_title="Fix PR", pr_state="merged", pr_url="https://github.com/pytorch/pytorch/pull/100"):
    event = MagicMock()
    event.event = "cross-referenced"
    event.source.issue.number = pr_number
    event.source.issue.title = pr_title
    event.source.issue.state = pr_state
    event.source.issue.html_url = pr_url
    event.source.issue.pull_request = MagicMock()  # indicates it's a PR
    return event


def _make_client(**overrides):
    client = MagicMock(spec=GitHubClient)
    client.core_rate_limit_remaining = 4500
    client.core_rate_limit_total = 5000
    for k, v in overrides.items():
        setattr(client, k, v)
    return client


# ---------------------------------------------------------------------------
# _extract_linked_prs tests
# ---------------------------------------------------------------------------


def test_extract_linked_prs_with_cross_refs():
    events = [_make_cross_ref_event(100, "Fix PR", "merged")]
    result = _extract_linked_prs(events)
    assert len(result) == 1
    assert result[0]["number"] == 100
    assert result[0]["title"] == "Fix PR"


def test_extract_linked_prs_deduplicates():
    events = [
        _make_cross_ref_event(100, "Fix PR", "merged"),
        _make_cross_ref_event(100, "Fix PR", "merged"),  # duplicate
    ]
    result = _extract_linked_prs(events)
    assert len(result) == 1


def test_extract_linked_prs_skips_non_pr():
    event = MagicMock()
    event.event = "cross-referenced"
    event.source.issue.pull_request = None  # not a PR
    result = _extract_linked_prs([event])
    assert len(result) == 0


def test_extract_linked_prs_empty():
    result = _extract_linked_prs([])
    assert result == []


# ---------------------------------------------------------------------------
# get_issue_detail tests
# ---------------------------------------------------------------------------


def test_issue_detail_success():
    client = _make_client()
    client.get_issue.return_value = _make_mock_issue()
    client.get_issue_comments.return_value = ([_make_mock_comment()], 1)
    client.get_issue_timeline.return_value = []

    result = get_issue_detail(client, 98765)
    assert "Bug report" in result
    assert "## Issue Metadata" in result
    assert "## Comments" in result
    assert "commenter1" in result
    assert "## Linked Pull Requests" in result


def test_issue_detail_with_labels_and_assignees():
    client = _make_client()
    client.get_issue.return_value = _make_mock_issue(
        labels=["bug", "high priority"],
        assignees=["dev1", "dev2"],
        milestone="v2.5",
    )
    client.get_issue_comments.return_value = ([], 0)
    client.get_issue_timeline.return_value = []

    result = get_issue_detail(client, 98765)
    assert "bug" in result
    assert "high priority" in result
    assert "dev1" in result
    assert "v2.5" in result


def test_issue_detail_comment_truncation():
    long_body = "x" * 1000
    client = _make_client()
    client.get_issue.return_value = _make_mock_issue()
    client.get_issue_comments.return_value = ([_make_mock_comment(body=long_body)], 1)
    client.get_issue_timeline.return_value = []

    result = get_issue_detail(client, 98765, comment_length=100)
    # Should contain truncated comment (100 chars + "...")
    assert "..." in result


def test_issue_detail_no_comments():
    client = _make_client()
    client.get_issue.return_value = _make_mock_issue()
    client.get_issue_comments.return_value = ([], 0)
    client.get_issue_timeline.return_value = []

    result = get_issue_detail(client, 98765)
    assert "No comments." in result


def test_issue_detail_with_linked_prs():
    client = _make_client()
    client.get_issue.return_value = _make_mock_issue()
    client.get_issue_comments.return_value = ([], 0)
    client.get_issue_timeline.return_value = [
        _make_cross_ref_event(100, "Fix PR", "merged")
    ]

    result = get_issue_detail(client, 98765)
    assert "#100" in result
    assert "Fix PR" in result


def test_issue_detail_not_found():
    client = _make_client()
    client.get_issue.side_effect = UnknownObjectException(404, {"message": "Not Found"}, None)

    result = get_issue_detail(client, 99999)
    assert "## Error" in result
    assert "not found" in result


def test_issue_detail_auth_error():
    client = _make_client()
    client.get_issue.side_effect = GithubException(401, {"message": "Bad credentials"}, None)

    result = get_issue_detail(client, 98765)
    assert "## Error" in result
    assert "GITHUB_TOKEN" in result


def test_issue_detail_custom_repo():
    client = _make_client()
    client.get_issue.return_value = _make_mock_issue()
    client.get_issue_comments.return_value = ([], 0)
    client.get_issue_timeline.return_value = []

    get_issue_detail(client, 42, repo="pytorch/vision")
    client.get_issue.assert_called_once_with("pytorch/vision", issue_number=42)


def test_issue_detail_rate_limit_warning():
    client = _make_client()
    client.core_rate_limit_remaining = 100
    client.core_rate_limit_total = 5000
    client.get_issue.return_value = _make_mock_issue()
    client.get_issue_comments.return_value = ([], 0)
    client.get_issue_timeline.return_value = []

    result = get_issue_detail(client, 98765)
    assert "quota low" in result


def test_issue_detail_comment_count_message():
    """When more comments exist than max_comments, show total count."""
    comments = [_make_mock_comment(author=f"user{i}") for i in range(5)]
    client = _make_client()
    client.get_issue.return_value = _make_mock_issue()
    client.get_issue_comments.return_value = (comments, 20)  # 20 total, 5 returned
    client.get_issue_timeline.return_value = []

    result = get_issue_detail(client, 98765, max_comments=5)
    assert "5 of 20 comments" in result
