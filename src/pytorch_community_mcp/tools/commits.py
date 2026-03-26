"""get-commits tool — retrieve PyTorch commits from GitHub."""

from __future__ import annotations

import re
from datetime import date, datetime, timezone

from github import GithubException

from pytorch_community_mcp.clients.github import GitHubClient
from pytorch_community_mcp.formatter import format_error, format_results


_PR_NUMBER_RE = re.compile(r"Pull Request resolved:.*?(?:#|/pull/)(\d+)|\(#(\d+)\)")


def _extract_pr_number(message: str) -> str:
    """Extract PR number from commit message if present."""
    match = _PR_NUMBER_RE.search(message)
    if match:
        return match.group(1) or match.group(2) or ""
    return ""


def get_commits(
    client: GitHubClient,
    since: str,
    until: str | None = None,
    author: str | None = None,
    sha: str | None = None,
    max_results: int = 100,
    message_length: int = 200,
) -> str:
    """Get PyTorch commits within a date range.

    Args:
        client: GitHub API client.
        since: Start date (ISO format).
        until: End date (ISO format). Defaults to today.
        author: Filter by author (GitHub username or email).
        sha: Branch name or commit SHA to start from. Defaults to main.
        max_results: Maximum number of commits to return. Default 100.
        message_length: Max chars of commit message to include. Default 200. Use -1 for full message.
    """
    until = until or date.today().isoformat()

    since_dt = datetime.fromisoformat(since).replace(tzinfo=timezone.utc)
    until_dt = datetime.fromisoformat(until).replace(tzinfo=timezone.utc)
    # Include the full end date
    if until_dt.hour == 0 and until_dt.minute == 0:
        until_dt = until_dt.replace(hour=23, minute=59, second=59)

    try:
        results, total_count = client.get_commits(
            since=since_dt,
            until=until_dt,
            author=author,
            sha=sha,
            max_results=max_results,
        )
    except GithubException as e:
        return format_error(
            "GitHubError",
            str(e),
            "Check GITHUB_TOKEN is valid and has required scopes.",
        )

    items = []
    for commit in results:
        message = commit.commit.message or ""
        first_line = message.split("\n", 1)[0]
        pr_number = _extract_pr_number(message)

        if message_length == -1:
            desc = message
        else:
            desc = message[:message_length]

        item: dict = {
            "title": first_line[:120],
            "url": commit.html_url,
            "date": commit.commit.author.date.strftime("%Y-%m-%d") if commit.commit.author.date else "",
            "author": commit.author.login if commit.author else (commit.commit.author.name or ""),
            "sha": commit.sha[:10],
            "description": desc,
        }
        if pr_number:
            item["pr"] = f"#{pr_number}"

        items.append(item)

    return format_results(
        "get-commits",
        {"since": since, "until": until, "author": author, "sha": sha},
        items,
        total_count=total_count,
        rate_limit_remaining=client.rate_limit_remaining,
        rate_limit_total=client.rate_limit_total,
    )
