"""get-key-contributors-activity tool — cross-platform contributor summary."""

from __future__ import annotations

import asyncio
from datetime import date

from pytorch_community_mcp.clients.discourse import DiscourseClient
from pytorch_community_mcp.clients.github import GitHubClient
from pytorch_community_mcp.formatter import format_results, safe_parse_date


async def get_key_contributors_activity(
    github_client: GitHubClient,
    discourse_client: DiscourseClient,
    contributor: str,
    since: str | None = None,
    until: str | None = None,
) -> str:
    """Get a contributor's activity across GitHub and Discourse.

    Args:
        contributor: GitHub username of the contributor.
        since: Start date (ISO format).
        until: End date (ISO format).
    """
    until = until or date.today().isoformat()
    items: list[dict] = []
    platform_notes: list[str] = []

    # Run platform queries in parallel
    github_task = asyncio.to_thread(
        _fetch_github_activity, github_client, contributor, since, until
    )
    discourse_task = _fetch_discourse_activity(
        discourse_client, contributor, since, until
    )

    github_result, discourse_result = await asyncio.gather(
        github_task, discourse_task, return_exceptions=True
    )

    # Process GitHub results
    if isinstance(github_result, Exception):
        platform_notes.append(f"GitHub: unavailable ({github_result})")
    else:
        items.extend(github_result)

    # Process Discourse results
    if isinstance(discourse_result, Exception):
        platform_notes.append(f"Discourse: unavailable ({discourse_result})")
    else:
        items.extend(discourse_result)

    # Sort by date descending
    items.sort(key=lambda x: x.get("date", ""), reverse=True)

    result = format_results(
        "get-key-contributors-activity",
        {"contributor": contributor, "since": since, "until": until},
        items,
    )

    if platform_notes:
        notes = "\n".join(f"- {n}" for n in platform_notes)
        result += f"\n\n> **Platform Notes:**\n{notes}\n"

    return result


def _fetch_github_activity(
    client: GitHubClient,
    contributor: str,
    since: str | None,
    until: str,
) -> list[dict]:
    """Fetch contributor activity from GitHub."""
    items = []
    date_range = f"{since}..{until}" if since else f"*..{until}"

    # PRs authored
    query = f"repo:pytorch/pytorch is:pr author:{contributor} created:{date_range}"
    results, _ = client.search_issues(query, max_results=50)
    for pr in results:
        items.append(
            {
                "title": f"[PR] {pr.title}",
                "url": pr.html_url,
                "date": pr.created_at.strftime("%Y-%m-%d"),
                "author": contributor,
                "platform": "GitHub",
                "description": (pr.body or "")[:150],
            }
        )

    # Issues authored
    query = f"repo:pytorch/pytorch is:issue author:{contributor} created:{date_range}"
    results, _ = client.search_issues(query, max_results=50)
    for issue in results:
        items.append(
            {
                "title": f"[Issue] {issue.title}",
                "url": issue.html_url,
                "date": issue.created_at.strftime("%Y-%m-%d"),
                "author": contributor,
                "platform": "GitHub",
                "description": (issue.body or "")[:150],
            }
        )

    return items


async def _fetch_discourse_activity(
    client: DiscourseClient,
    contributor: str,
    since: str | None,
    until: str,
) -> list[dict]:
    """Fetch contributor activity from Discourse."""
    search_parts = [f"@{contributor}"]
    if since:
        search_parts.append(f"after:{since}")
    search_parts.append(f"before:{until}")

    topics = await client.search(" ".join(search_parts))

    items = []
    for topic in topics:
        slug = topic.get("slug", "")
        topic_id = topic.get("id", "")
        url = (
            f"https://discuss.pytorch.org/t/{slug}/{topic_id}"
            if slug and topic_id
            else ""
        )
        items.append(
            {
                "title": f"[Forum] {topic.get('title', '')}",
                "url": url,
                "date": safe_parse_date(topic.get("created_at", "")),
                "author": contributor,
                "platform": "Discourse",
                "description": topic.get("excerpt", topic.get("blurb", ""))[:150],
            }
        )
    return items
