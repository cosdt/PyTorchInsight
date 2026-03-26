"""Discourse API client for discuss.pytorch.org."""

from __future__ import annotations

from typing import Any

import httpx

DISCOURSE_BASE = "https://discuss.pytorch.org"


class DiscourseClient:
    """httpx-based Discourse API client."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        api_username: str | None = None,
    ) -> None:
        self._api_key = api_key
        self._api_username = api_username

    def _get_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/json"}
        if self._api_key and self._api_username:
            headers["Api-Key"] = self._api_key
            headers["Api-Username"] = self._api_username
        return headers

    async def search(
        self,
        query: str,
    ) -> list[dict[str, Any]]:
        """Search Discourse topics. Returns up to 50 results."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{DISCOURSE_BASE}/search.json",
                headers=self._get_headers(),
                params={"q": query},
                timeout=30.0,
            )
            resp.raise_for_status()

        data = resp.json()
        return data.get("topics", [])

    async def get_latest(
        self,
        category_slug: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get latest topics, optionally filtered by category."""
        url = f"{DISCOURSE_BASE}/latest.json"
        if category_slug:
            url = f"{DISCOURSE_BASE}/c/{category_slug}.json"

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url,
                headers=self._get_headers(),
                timeout=30.0,
            )
            resp.raise_for_status()

        data = resp.json()
        return data.get("topic_list", {}).get("topics", [])
