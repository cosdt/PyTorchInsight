"""Tests for API clients with mocked responses."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pytorch_community_mcp.clients.discourse import DiscourseClient
from pytorch_community_mcp.clients.events import EventsClient
from pytorch_community_mcp.clients.rss import RSSClient


def _mock_async_client(mock_response):
    """Create a mock httpx.AsyncClient that works as an async context manager."""
    mock_client_instance = AsyncMock()
    mock_client_instance.get.return_value = mock_response
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)
    return MagicMock(return_value=mock_client_instance)


# --- Discourse client tests ---


async def test_discourse_client_search():
    client = DiscourseClient(api_key="test-key", api_username="testuser")

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "topics": [
            {"id": 1, "title": "Test topic", "slug": "test-topic", "created_at": "2024-01-15"}
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient", _mock_async_client(mock_response)):
        topics = await client.search("test")

    assert len(topics) == 1
    assert topics[0]["title"] == "Test topic"


# --- Events client tests ---


async def test_events_client_get_events():
    client = EventsClient()

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "events": [
            {"title": "PyTorch Conference", "start_date": "2024-06-01", "url": "https://pytorch.org/event"}
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient", _mock_async_client(mock_response)):
        events = await client.get_events(start_date="2024-06-01")

    assert len(events) == 1
    assert events[0]["title"] == "PyTorch Conference"


# --- RSS client tests ---


def test_rss_client_get_entries():
    client = RSSClient()

    mock_entry = MagicMock()
    mock_entry.get = lambda k, d="": {
        "title": "New Blog Post",
        "link": "https://pytorch.org/blog/post",
        "author": "PyTorch Team",
        "summary": "Blog summary",
    }.get(k, d)
    mock_entry.published_parsed = (2024, 1, 15, 0, 0, 0, 0, 0, 0)

    mock_feed = MagicMock()
    mock_feed.entries = [mock_entry]

    mock_response = MagicMock()
    mock_response.text = "<rss>mock xml</rss>"
    mock_response.raise_for_status = MagicMock()

    mock_http_client = MagicMock()
    mock_http_client.get.return_value = mock_response
    mock_http_client.__enter__ = MagicMock(return_value=mock_http_client)
    mock_http_client.__exit__ = MagicMock(return_value=False)

    with patch("httpx.Client", return_value=mock_http_client), \
         patch("feedparser.parse", return_value=mock_feed) as mock_parse:
        entries = client.get_entries()

    mock_parse.assert_called_once_with("<rss>mock xml</rss>")
    assert len(entries) == 1
    assert entries[0]["title"] == "New Blog Post"
    assert entries[0]["date"] == "2024-01-15"


def test_rss_client_timeout():
    """RSSClient should propagate httpx.TimeoutException when fetch times out."""
    import httpx

    client = RSSClient()

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    mock_client_instance = MagicMock()
    mock_client_instance.get.side_effect = httpx.TimeoutException("timed out")
    mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
    mock_client_instance.__exit__ = MagicMock(return_value=False)

    with patch("httpx.Client", return_value=mock_client_instance):
        with pytest.raises(httpx.TimeoutException):
            client.get_entries()
