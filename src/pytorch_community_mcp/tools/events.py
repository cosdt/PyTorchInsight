"""get-events and get-blog-news tools."""

from __future__ import annotations

import re

import httpx

from pytorch_community_mcp.clients.events import EventsClient
from pytorch_community_mcp.clients.rss import RSSClient
from pytorch_community_mcp.formatter import format_error, format_results, safe_parse_date


async def get_events(
    client: EventsClient,
    since: str | None = None,
    until: str | None = None,
    search: str | None = None,
    featured: bool | None = None,
    limit: int = 50,
) -> str:
    """Get PyTorch community events.

    Args:
        since: Start date (ISO format).
        until: End date (ISO format).
        search: Keyword to filter events.
        featured: If true, return only featured events.
        limit: Maximum number of results to return. Default 50.
    """
    try:
        events = await client.get_events(
            start_date=since,
            end_date=until,
            search=search,
            featured=featured,
        )
    except httpx.HTTPError as e:
        return format_error(
            "EventsError",
            f"Events API request failed: {e}",
            "The pytorch.org Events API may be down. Try again later.",
        )

    events = events[:limit]

    items = []
    for event in events:
        # Strip HTML tags from description
        description = event.get("description", "")
        description = re.sub(r"<[^>]+>", "", description)[:200]

        items.append(
            {
                "title": event.get("title", ""),
                "url": event.get("url", ""),
                "date": safe_parse_date(event.get("start_date", "")),
                "end_date": safe_parse_date(event.get("end_date", "")),
                "venue": (
                    event["venue"].get("venue", "Virtual")
                    if isinstance(event.get("venue"), dict)
                    else "Virtual"
                ),
                "description": description,
            }
        )

    return format_results(
        "get-events",
        {
            "since": since,
            "until": until,
            "search": search,
            "featured": featured,
            "limit": limit,
        },
        items,
    )


def get_blog_news(
    client: RSSClient,
    since: str | None = None,
    limit: int = 20,
) -> str:
    """Get recent PyTorch blog posts and news.

    Args:
        since: Only return posts published after this date (ISO format).
        limit: Maximum number of posts to return. Default 20.
    """
    try:
        entries = client.get_entries()
    except httpx.HTTPError as e:
        return format_error(
            "RSSError",
            f"RSS feed fetch failed: {e}",
            "The pytorch.org RSS feed may be down. Try again later.",
        )

    if since:
        entries = [e for e in entries if e["date"] >= since]

    entries = entries[:limit]

    items = []
    for entry in entries:
        items.append(
            {
                "title": entry["title"],
                "url": entry["url"],
                "date": entry["date"],
                "author": entry["author"],
                "description": entry["summary"],
            }
        )

    return format_results(
        "get-blog-news",
        {"since": since, "limit": limit},
        items,
    )
