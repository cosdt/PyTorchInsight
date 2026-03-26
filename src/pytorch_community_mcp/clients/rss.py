"""RSS feed parser for pytorch.org/feed/."""

from __future__ import annotations

from typing import Any

import feedparser
import httpx

PYTORCH_RSS_URL = "https://pytorch.org/feed/"


class RSSClient:
    """feedparser wrapper for PyTorch blog RSS."""

    def get_entries(self) -> list[dict[str, Any]]:
        """Parse the PyTorch RSS feed and return entries."""
        with httpx.Client() as client:
            resp = client.get(PYTORCH_RSS_URL, timeout=15.0)
            resp.raise_for_status()

        feed = feedparser.parse(resp.text)
        entries = []
        for entry in feed.entries:
            published = ""
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                from time import strftime
                published = strftime("%Y-%m-%d", entry.published_parsed)

            entries.append(
                {
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "date": published,
                    "author": entry.get("author", ""),
                    "summary": entry.get("summary", "")[:300],
                }
            )
        return entries
