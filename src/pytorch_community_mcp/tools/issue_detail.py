"""get-issue-detail tool — retrieve detailed issue information including comments."""

from __future__ import annotations

from github import GithubException, UnknownObjectException

from pytorch_community_mcp.clients.github import GitHubClient
from pytorch_community_mcp.formatter import format_error


def _extract_linked_prs(timeline_events: list) -> list[dict]:
    """Extract linked PRs from timeline cross-reference events."""
    linked_prs = []
    seen = set()
    for event in timeline_events:
        if not hasattr(event, "event"):
            continue
        if event.event == "cross-referenced":
            source = getattr(event, "source", None)
            if source is None:
                continue
            issue = getattr(source, "issue", None)
            if issue is None:
                continue
            pr = getattr(issue, "pull_request", None)
            if pr is None:
                continue
            # It's a PR cross-reference
            number = issue.number
            if number in seen:
                continue
            seen.add(number)
            linked_prs.append({
                "number": number,
                "title": issue.title,
                "state": issue.state,
                "url": issue.html_url,
            })
    return linked_prs


def get_issue_detail(
    client: GitHubClient,
    issue_number: int,
    repo: str = "pytorch/pytorch",
    max_comments: int = 50,
    comment_length: int = 500,
) -> str:
    """Get detailed information for a single issue.

    Args:
        issue_number: Issue number. Required.
        repo: Repository (owner/name). Default "pytorch/pytorch".
        max_comments: Maximum number of comments to return. Default 50.
        comment_length: Max chars per comment body. Default 500. Use -1 for full body.
    """
    try:
        issue = client.get_issue(repo, issue_number=issue_number)
    except UnknownObjectException:
        return format_error(
            "GitHubError",
            f"Issue #{issue_number} not found in {repo}.",
            "Check that the issue number and repository are correct.",
        )
    except GithubException as e:
        return format_error(
            "GitHubError",
            str(e),
            "Check GITHUB_TOKEN is valid and has required scopes.",
        )

    if issue is None:
        return format_error(
            "GitHubError",
            f"Issue #{issue_number} not found in {repo}.",
            "Check that the issue number and repository are correct.",
        )

    # Build output
    lines: list[str] = []
    lines.append("## Summary")
    lines.append("")
    lines.append(f"**Tool:** `get-issue-detail`")
    lines.append(f"**Parameters:** issue_number={issue_number}, repo={repo!r}")
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

    # Issue metadata
    lines.append("## Issue Metadata")
    lines.append("")
    lines.append(f"**Title:** {issue.title}")
    lines.append(f"**URL:** {issue.html_url}")
    lines.append(f"**Author:** {issue.user.login if issue.user else 'unknown'}")
    lines.append(f"**State:** {issue.state}")
    lines.append(f"**Created:** {issue.created_at.strftime('%Y-%m-%d')}")
    labels = [l.name for l in issue.labels]
    if labels:
        lines.append(f"**Labels:** {', '.join(labels)}")
    assignees = [a.login for a in issue.assignees]
    if assignees:
        lines.append(f"**Assignees:** {', '.join(assignees)}")
    if issue.milestone:
        lines.append(f"**Milestone:** {issue.milestone.title}")
    lines.append("")

    # Issue body
    body = issue.body or ""
    if body:
        lines.append("### Description")
        lines.append("")
        lines.append(body)
        lines.append("")

    # Comments
    try:
        comments, total_comments = client.get_issue_comments(
            repo, issue_number=issue_number, max_comments=max_comments
        )
    except GithubException:
        comments, total_comments = [], 0

    lines.append("## Comments")
    lines.append("")
    if total_comments > len(comments):
        lines.append(f"Showing {len(comments)} of {total_comments} comments.")
        lines.append("")

    if not comments:
        lines.append("No comments.")
    else:
        for comment in comments:
            author = comment.user.login if comment.user else "unknown"
            date = comment.created_at.strftime("%Y-%m-%d")
            body_text = comment.body or ""
            if comment_length >= 0 and len(body_text) > comment_length:
                body_text = body_text[:comment_length] + "..."
            lines.append(f"### {author} ({date})")
            lines.append("")
            lines.append(body_text)
            lines.append("")

    # Linked PRs
    try:
        timeline = client.get_issue_timeline(repo, issue_number=issue_number)
        linked_prs = _extract_linked_prs(timeline)
    except GithubException:
        linked_prs = []

    lines.append("## Linked Pull Requests")
    lines.append("")
    if not linked_prs:
        lines.append("No linked pull requests.")
    else:
        for pr in linked_prs:
            lines.append(f"- [#{pr['number']} {pr['title']}]({pr['url']}) — {pr['state']}")
    lines.append("")

    return "\n".join(lines)
