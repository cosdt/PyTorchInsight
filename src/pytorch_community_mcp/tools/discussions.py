"""get-discussions tool — retrieve posts from discuss.pytorch.org."""

from __future__ import annotations

import httpx

from pytorch_community_mcp.clients.discourse import DiscourseClient
from pytorch_community_mcp.formatter import format_error, format_results, safe_parse_date

DISCOURSE_BASE = "https://discuss.pytorch.org"
MAX_DISCOURSE_RESULTS = 50


async def get_discussions(
    client: DiscourseClient,
    query: str | None = None,
    category: str | None = None,
    since: str | None = None,
    until: str | None = None,
    limit: int = 50,
) -> str:
    """Get discussions from the PyTorch developer forum.

    Args:
        query: Search string.
        category: Category name (e.g. "dev").
        since: Start date (ISO format).
        until: End date (ISO format).
        limit: Maximum number of results to return. Default 50.
    """
    try:
        # Build Discourse search query with date operators
        search_parts: list[str] = []
        if query:
            search_parts.append(query)
        if category:
            search_parts.append(f"category:{category}")
        if since:
            search_parts.append(f"after:{since}")
        if until:
            search_parts.append(f"before:{until}")

        if search_parts:
            search_query = " ".join(search_parts)
            topics = await client.search(search_query)
        else:
            topics = await client.get_latest(category)
    except httpx.HTTPError as e:
        return format_error(
            "DiscourseError",
            f"Discourse API request failed: {e}",
            "The discuss.pytorch.org API may be down. Try again later.",
        )

    topics = topics[:limit]
    truncated = len(topics) >= limit

    items = []
    for topic in topics:
        slug = topic.get("slug", "")
        topic_id = topic.get("id", "")
        url = f"{DISCOURSE_BASE}/t/{slug}/{topic_id}" if slug and topic_id else ""

        items.append(
            {
                "title": topic.get("title", ""),
                "url": url,
                "date": safe_parse_date(topic.get("created_at", "")),
                "author": topic.get("last_poster_username", ""),
                "replies": topic.get("posts_count", 0) - 1,
                "views": topic.get("views", 0),
                "description": topic.get("excerpt", topic.get("blurb", ""))[:200],
            }
        )

    return format_results(
        "get-discussions",
        {"query": query, "category": category, "since": since, "until": until, "limit": limit},
        items,
        truncated=truncated,
    )
