"""Shared test fixtures."""

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def make_mock_issue():
    """Factory fixture for creating mock GitHub Issue/PR objects."""

    def _make(
        title="Test PR",
        url="https://github.com/pr/1",
        date="2024-01-15",
        author="user1",
        state="open",
        labels=None,
        body="Description",
    ):
        mock = MagicMock()
        mock.title = title
        mock.html_url = url
        mock.created_at.strftime.return_value = date
        mock.user.login = author
        mock.state = state
        mock.labels = [MagicMock(name=l) for l in (labels or [])]
        mock.body = body
        return mock

    return _make


@pytest.fixture
def mock_async_client():
    """Factory fixture for creating a mock httpx.AsyncClient context manager."""

    def _make(mock_response):
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=False)
        return MagicMock(return_value=mock_client_instance)

    return _make
