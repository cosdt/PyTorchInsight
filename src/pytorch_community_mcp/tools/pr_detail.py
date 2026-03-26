"""get-pr-detail tool — retrieve detailed PR information including files and diffs."""

from __future__ import annotations

from github import GithubException, UnknownObjectException

from pytorch_community_mcp.clients.github import GitHubClient
from pytorch_community_mcp.formatter import format_error


def _truncate_patch(patch: str | None, max_lines: int) -> tuple[str, bool]:
    """Truncate a patch to max_lines lines. Returns (truncated_patch, was_truncated)."""
    if not patch:
        return "", False
    lines = patch.split("\n")
    if max_lines >= 0 and len(lines) > max_lines:
        return "\n".join(lines[:max_lines]), True
    return patch, False


def get_pr_detail(
    client: GitHubClient,
    pr_number: int,
    repo: str = "pytorch/pytorch",
    max_diff_lines: int = 50,
    files_only: bool = False,
    include_reviews: bool = True,
) -> str:
    """Get detailed information for a single pull request.

    Args:
        pr_number: PR number. Required.
        repo: Repository (owner/name). Default "pytorch/pytorch".
        max_diff_lines: Max lines of diff per file. Default 50. Use -1 for full diff.
        files_only: If true, return only file list without diffs. Default false.
        include_reviews: If true, include review information. Default true.
    """
    try:
        pr = client.get_pull_request(repo, pr_number=pr_number)
    except UnknownObjectException:
        return format_error(
            "GitHubError",
            f"Pull request #{pr_number} not found in {repo}.",
            "Check that the PR number and repository are correct.",
        )
    except GithubException as e:
        return format_error(
            "GitHubError",
            str(e),
            "Check GITHUB_TOKEN is valid and has required scopes.",
        )

    if pr is None:
        return format_error(
            "GitHubError",
            f"Pull request #{pr_number} not found in {repo}.",
            "Check that the PR number and repository are correct.",
        )

    # Build PR metadata
    lines: list[str] = []
    lines.append("## Summary")
    lines.append("")
    lines.append(f"**Tool:** `get-pr-detail`")
    lines.append(f"**Parameters:** pr_number={pr_number}, repo={repo!r}")
    lines.append("")

    # Rate limit info
    remaining = client.core_rate_limit_remaining
    total = client.core_rate_limit_total
    if remaining < total * 0.3:
        lines.append(
            f"> **Note:** GitHub API quota low ({remaining}/{total} remaining). "
            f"Requests may be delayed."
        )
        lines.append("")

    # PR metadata
    lines.append("## PR Metadata")
    lines.append("")
    lines.append(f"**Title:** {pr.title}")
    lines.append(f"**URL:** {pr.html_url}")
    lines.append(f"**Author:** {pr.user.login if pr.user else 'unknown'}")
    lines.append(f"**State:** {pr.state}")
    lines.append(f"**Created:** {pr.created_at.strftime('%Y-%m-%d')}")
    if pr.merged:
        lines.append(f"**Merged:** {pr.merged_at.strftime('%Y-%m-%d') if pr.merged_at else 'yes'}")
        if pr.merge_commit_sha:
            lines.append(f"**Merge Commit:** {pr.merge_commit_sha[:10]}")
    labels = [l.name for l in pr.labels]
    if labels:
        lines.append(f"**Labels:** {', '.join(labels)}")
    lines.append("")

    # PR body
    body = pr.body or ""
    if body:
        lines.append("### Description")
        lines.append("")
        lines.append(body)
        lines.append("")

    # Changed files
    try:
        files = client.get_pr_files(repo, pr_number=pr_number)
    except GithubException:
        files = []

    lines.append("## Changed Files")
    lines.append("")
    lines.append(f"**Total files changed:** {len(files)}")
    total_additions = sum(f.additions for f in files)
    total_deletions = sum(f.deletions for f in files)
    lines.append(f"**Total changes:** +{total_additions} / -{total_deletions}")
    lines.append("")

    for f in files:
        status_icon = {"added": "+", "removed": "-", "modified": "~", "renamed": "→"}.get(
            f.status, "?"
        )
        lines.append(f"### [{status_icon}] {f.filename}")
        lines.append("")
        lines.append(f"**Status:** {f.status} | **+{f.additions}** / **-{f.deletions}**")

        if not files_only and f.patch:
            patch, was_truncated = _truncate_patch(f.patch, max_diff_lines)
            lines.append("")
            lines.append("```diff")
            lines.append(patch)
            lines.append("```")
            if was_truncated:
                lines.append(f"> *Diff truncated to {max_diff_lines} lines*")

        lines.append("")

    # Reviews
    if include_reviews:
        try:
            reviews = client.get_pr_reviews(repo, pr_number=pr_number)
        except GithubException:
            reviews = []

        lines.append("## Reviews")
        lines.append("")
        if not reviews:
            lines.append("No reviews yet.")
        else:
            for review in reviews:
                reviewer = review.user.login if review.user else "unknown"
                state = review.state
                submitted = review.submitted_at.strftime("%Y-%m-%d") if review.submitted_at else ""
                lines.append(f"- **{reviewer}**: {state} ({submitted})")
        lines.append("")

    return "\n".join(lines)
