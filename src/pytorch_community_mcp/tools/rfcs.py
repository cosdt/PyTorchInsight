"""get-rfcs tool — retrieve PyTorch RFCs from GitHub."""

from __future__ import annotations

from github import GithubException

from pytorch_community_mcp.clients.github import GitHubClient
from pytorch_community_mcp.formatter import format_error, format_results


def get_rfcs(
    client: GitHubClient,
    since: str | None = None,
    status: str = "all",
) -> str:
    """Get PyTorch RFCs from pytorch/pytorch and pytorch/rfcs.

    Args:
        since: Start date (ISO format). Optional.
        status: RFC status — "open", "closed", or "all". Default "all".
    """
    all_items: dict[str, dict] = {}  # url -> item, for dedup
    combined_total = 0

    try:
        # Search pytorch/pytorch for RFC-labeled issues/PRs
        query_main = 'repo:pytorch/pytorch "RFC" in:title'
        if since:
            query_main += f" created:>={since}"
        if status != "all":
            query_main += f" is:{status}"

        results, total = client.search_issues(query_main)
        combined_total += total
        for item in results:
            all_items[item.html_url] = {
                "title": item.title,
                "url": item.html_url,
                "date": item.created_at.strftime("%Y-%m-%d"),
                "author": item.user.login if item.user else "",
                "state": item.state,
                "repo": "pytorch/pytorch",
                "description": (item.body or "")[:500],
            }

        # Search pytorch/rfcs
        query_rfcs = "repo:pytorch/rfcs is:issue"
        if since:
            query_rfcs += f" created:>={since}"
        if status != "all":
            query_rfcs += f" is:{status}"

        results, total = client.search_issues(query_rfcs)
        combined_total += total
        for item in results:
            if item.html_url not in all_items:
                all_items[item.html_url] = {
                    "title": item.title,
                    "url": item.html_url,
                    "date": item.created_at.strftime("%Y-%m-%d"),
                    "author": item.user.login if item.user else "",
                    "state": item.state,
                    "repo": "pytorch/rfcs",
                    "description": (item.body or "")[:500],
                }

        # Also search PRs in pytorch/rfcs
        query_rfcs_pr = "repo:pytorch/rfcs is:pr"
        if since:
            query_rfcs_pr += f" created:>={since}"
        if status != "all":
            query_rfcs_pr += f" is:{status}"

        results, total = client.search_issues(query_rfcs_pr)
        combined_total += total
        for item in results:
            if item.html_url not in all_items:
                all_items[item.html_url] = {
                    "title": item.title,
                    "url": item.html_url,
                    "date": item.created_at.strftime("%Y-%m-%d"),
                    "author": item.user.login if item.user else "",
                    "state": item.state,
                    "repo": "pytorch/rfcs",
                    "description": (item.body or "")[:500],
                }
    except GithubException as e:
        return format_error(
            "GitHubError",
            str(e),
            "Check GITHUB_TOKEN is valid and has required scopes.",
        )

    # Sort by date descending
    items = sorted(all_items.values(), key=lambda x: x["date"], reverse=True)

    return format_results(
        "get-rfcs",
        {"since": since, "status": status},
        items,
        total_count=combined_total,
        rate_limit_remaining=client.rate_limit_remaining,
        rate_limit_total=client.rate_limit_total,
    )
