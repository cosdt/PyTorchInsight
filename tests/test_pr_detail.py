"""Tests for get_pr_detail tool — output format, truncation, error handling."""

from unittest.mock import MagicMock

from github import GithubException, UnknownObjectException

from pytorch_community_mcp.clients.github import GitHubClient
from pytorch_community_mcp.tools.pr_detail import get_pr_detail, _truncate_patch


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_mock_pr(
    title="Fix distributed",
    url="https://github.com/pytorch/pytorch/pull/12345",
    author="user1",
    state="open",
    created="2024-01-15",
    merged=False,
    merge_commit_sha=None,
    merged_at=None,
    labels=None,
    body="PR body text",
):
    pr = MagicMock()
    pr.title = title
    pr.html_url = url
    pr.user.login = author
    pr.state = state
    pr.created_at.strftime.return_value = created
    pr.merged = merged
    pr.merge_commit_sha = merge_commit_sha
    if merged_at:
        pr.merged_at.strftime.return_value = merged_at
    else:
        pr.merged_at = None
    pr.labels = [MagicMock(name=l) for l in (labels or [])]
    pr.body = body
    return pr


def _make_mock_file(filename="src/main.py", status="modified", additions=10, deletions=5, patch="@@ -1,5 +1,10 @@\n+added line\n-removed line"):
    f = MagicMock()
    f.filename = filename
    f.status = status
    f.additions = additions
    f.deletions = deletions
    f.patch = patch
    return f


def _make_mock_review(reviewer="reviewer1", state="APPROVED", date="2024-01-16"):
    r = MagicMock()
    r.user.login = reviewer
    r.state = state
    r.submitted_at.strftime.return_value = date
    return r


def _make_client(**overrides):
    client = MagicMock(spec=GitHubClient)
    client.core_rate_limit_remaining = 4500
    client.core_rate_limit_total = 5000
    for k, v in overrides.items():
        setattr(client, k, v)
    return client


# ---------------------------------------------------------------------------
# _truncate_patch tests
# ---------------------------------------------------------------------------


def test_truncate_patch_short():
    patch, truncated = _truncate_patch("line1\nline2\nline3", 5)
    assert patch == "line1\nline2\nline3"
    assert truncated is False


def test_truncate_patch_long():
    patch, truncated = _truncate_patch("line1\nline2\nline3\nline4", 2)
    assert patch == "line1\nline2"
    assert truncated is True


def test_truncate_patch_none():
    patch, truncated = _truncate_patch(None, 50)
    assert patch == ""
    assert truncated is False


def test_truncate_patch_unlimited():
    patch, truncated = _truncate_patch("line1\nline2\nline3", -1)
    assert patch == "line1\nline2\nline3"
    assert truncated is False


# ---------------------------------------------------------------------------
# get_pr_detail tests
# ---------------------------------------------------------------------------


def test_pr_detail_success():
    client = _make_client()
    client.get_pull_request.return_value = _make_mock_pr()
    client.get_pr_files.return_value = [_make_mock_file()]
    client.get_pr_reviews.return_value = [_make_mock_review()]

    result = get_pr_detail(client, 12345)
    assert "Fix distributed" in result
    assert "## PR Metadata" in result
    assert "## Changed Files" in result
    assert "## Reviews" in result
    assert "src/main.py" in result
    assert "reviewer1" in result
    assert "APPROVED" in result


def test_pr_detail_files_only():
    client = _make_client()
    client.get_pull_request.return_value = _make_mock_pr()
    client.get_pr_files.return_value = [_make_mock_file()]
    client.get_pr_reviews.return_value = []

    result = get_pr_detail(client, 12345, files_only=True)
    assert "src/main.py" in result
    assert "```diff" not in result


def test_pr_detail_with_diffs():
    client = _make_client()
    client.get_pull_request.return_value = _make_mock_pr()
    client.get_pr_files.return_value = [_make_mock_file()]
    client.get_pr_reviews.return_value = []

    result = get_pr_detail(client, 12345, files_only=False)
    assert "```diff" in result
    assert "+added line" in result


def test_pr_detail_diff_truncation():
    long_patch = "\n".join(f"line {i}" for i in range(100))
    client = _make_client()
    client.get_pull_request.return_value = _make_mock_pr()
    client.get_pr_files.return_value = [_make_mock_file(patch=long_patch)]
    client.get_pr_reviews.return_value = []

    result = get_pr_detail(client, 12345, max_diff_lines=5)
    assert "Diff truncated to 5 lines" in result


def test_pr_detail_no_reviews():
    client = _make_client()
    client.get_pull_request.return_value = _make_mock_pr()
    client.get_pr_files.return_value = []
    client.get_pr_reviews.return_value = []

    result = get_pr_detail(client, 12345, include_reviews=True)
    assert "No reviews yet." in result


def test_pr_detail_exclude_reviews():
    client = _make_client()
    client.get_pull_request.return_value = _make_mock_pr()
    client.get_pr_files.return_value = []

    result = get_pr_detail(client, 12345, include_reviews=False)
    assert "## Reviews" not in result


def test_pr_detail_not_found():
    client = _make_client()
    client.get_pull_request.side_effect = UnknownObjectException(404, {"message": "Not Found"}, None)

    result = get_pr_detail(client, 99999)
    assert "## Error" in result
    assert "not found" in result


def test_pr_detail_auth_error():
    client = _make_client()
    client.get_pull_request.side_effect = GithubException(401, {"message": "Bad credentials"}, None)

    result = get_pr_detail(client, 12345)
    assert "## Error" in result
    assert "GITHUB_TOKEN" in result


def test_pr_detail_merged_pr():
    client = _make_client()
    client.get_pull_request.return_value = _make_mock_pr(
        merged=True, merge_commit_sha="abc123def456", merged_at="2024-01-20"
    )
    client.get_pr_files.return_value = []
    client.get_pr_reviews.return_value = []

    result = get_pr_detail(client, 12345)
    assert "Merged:" in result
    assert "Merge Commit:" in result


def test_pr_detail_rate_limit_warning():
    client = _make_client()
    client.core_rate_limit_remaining = 100
    client.core_rate_limit_total = 5000
    client.get_pull_request.return_value = _make_mock_pr()
    client.get_pr_files.return_value = []
    client.get_pr_reviews.return_value = []

    result = get_pr_detail(client, 12345)
    assert "quota low" in result


def test_pr_detail_custom_repo():
    client = _make_client()
    client.get_pull_request.return_value = _make_mock_pr()
    client.get_pr_files.return_value = []
    client.get_pr_reviews.return_value = []

    get_pr_detail(client, 42, repo="pytorch/vision")
    client.get_pull_request.assert_called_once_with("pytorch/vision", pr_number=42)
