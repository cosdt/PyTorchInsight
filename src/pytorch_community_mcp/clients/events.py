"""Events API client for pytorch.org/wp-json/tec/v1/events."""

from __future__ import annotations

from typing import Any

import httpx

EVENTS_API_BASE = "https://pytorch.org/wp-json/tribe/events/v1/events"


class EventsClient:
    """httpx client for PyTorch Events API (WordPress TEC REST)."""

    async def get_events(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        search: str | None = None,
        featured: bool | None = None,
        per_page: int = 50,
    ) -> list[dict[str, Any]]:
        """Fetch events from the PyTorch Events API."""
        params: dict[str, Any] = {"per_page": per_page}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if search:
            params["search"] = search
        if featured is not None:
            params["featured"] = str(featured).lower()

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                EVENTS_API_BASE,
                params=params,
                timeout=30.0,
            )
            resp.raise_for_status()

        data = resp.json()
        return data.get("events", [])
