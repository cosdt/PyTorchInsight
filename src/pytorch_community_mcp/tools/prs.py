"""get-prs tool — retrieve PyTorch pull requests from GitHub."""

from __future__ import annotations

from datetime import date

from github import GithubException

from pytorch_community_mcp.clients.github import GitHubClient
from pytorch_community_mcp.formatter import format_error, format_results


def get_prs(
    client: GitHubClient,
    since: str,
    until: str | None = None,
    module: str | None = None,
    state: str = "all",
    date_type: str = "created",
    max_results: int = 100,
    description_length: int = 500,
) -> str:
    """Get PyTorch pull requests within a date range.

    Args:
        since: Start date (ISO format, e.g. 2024-01-01).
        until: End date (ISO format). Defaults to today.
        module: Filter by module label (e.g. "distributed").
        state: PR state — "open", "closed", "merged", or "all". Default "all".
        date_type: Date filter type — "created" or "updated". Default "created".
        max_results: Maximum number of results. Default 100.
        description_length: Max chars of description. Default 500. Use -1 for full body.
    """
    until = until or date.today().isoformat()

    query = f"repo:pytorch/pytorch is:pr {date_type}:{since}..{until}"
    if state == "merged":
        query += " is:merged"
    elif state != "all":
        query += f" is:{state}"
    if module:
        query += f' label:"module: {module}"'

    try:
        results, total_count = client.search_issues(query, max_results=max_results)
    except GithubException as e:
        return format_error(
            "GitHubError",
            str(e),
            "Check GITHUB_TOKEN is valid and has required scopes.",
        )

    items = []
    for pr in results:
        labels = [l.name for l in pr.labels]
        body = pr.body or ""
        desc = body if description_length == -1 else body[:description_length]
        items.append(
            {
                "title": pr.title,
                "url": pr.html_url,
                "date": pr.created_at.strftime("%Y-%m-%d"),
                "author": pr.user.login if pr.user else "",
                "state": pr.state,
                "labels": ", ".join(labels) if labels else "",
                "description": desc,
            }
        )

    return format_results(
        "get-prs",
        {"since": since, "until": until, "module": module, "state": state, "date_type": date_type},
        items,
        total_count=total_count,
        rate_limit_remaining=client.rate_limit_remaining,
        rate_limit_total=client.rate_limit_total,
    )
