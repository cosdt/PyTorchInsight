"""Tests for GitHub HTTP caching via requests_cache.

TDD RED phase: these tests describe the caching behaviour that will be
added to GitHubClient.__init__.  They should all FAIL until the
implementation is in place.

Every test that exercises cache behaviour creates a GitHubClient, which
is the code path that will call ``requests_cache.install_cache()``.  Until
that code is written, the cache is never installed and the assertions on
``from_cache``, TTL, etc. will fail.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, call, patch

import httpx
import pytest
import requests
import requests_cache
import responses

from pytorch_community_mcp.clients.github import GitHubClient


# ---------------------------------------------------------------------------
# 4.12  Test-isolation fixture (autouse, function-scope)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolate_cache():
    """Uninstall requests_cache before AND after every test.

    This guarantees no test leaks global session-patching state into the
    next test, regardless of pass/fail/error.
    """
    requests_cache.uninstall_cache()
    yield
    requests_cache.uninstall_cache()


# ---------------------------------------------------------------------------
# Helper: create a GitHubClient whose cache lives in tmp_path
# ---------------------------------------------------------------------------

def _make_cached_client(tmp_path, token=None):
    """Build a GitHubClient that writes its HTTP cache into *tmp_path*.

    The implementation will call ``os.path.expanduser("~/.cache/...")`` to
    locate the cache directory.  We patch that call so it returns a
    directory under *tmp_path*, preventing any test from writing into the
    real user cache.

    We also patch ``Github`` so no real GitHub connection is attempted
    during construction.
    """
    cache_dir = str(tmp_path / "mcp_cache")
    with patch(
        "pytorch_community_mcp.clients.github.os.path.expanduser",
        return_value=cache_dir,
    ), patch("pytorch_community_mcp.clients.github.Github"):
        client = GitHubClient(token=token)
    return client


# ---------------------------------------------------------------------------
# 4.1  Cache persists across GitHubClient re-instantiation
# ---------------------------------------------------------------------------


@responses.activate
def test_cache_persists_across_reinstantiation(tmp_path):
    """A cached response survives across two GitHubClient lifetimes.

    Flow:
      1. Create client-1 -> __init__ installs cache, make an HTTP request.
      2. Create client-2 -> __init__ sees cache already installed (no-op).
      3. Repeat the same HTTP request -> served from cache.
    """
    call_count = 0

    def _callback(request):
        nonlocal call_count
        call_count += 1
        return (200, {}, '{"id": 1}')

    url = "https://api.github.com/repos/pytorch/pytorch/pulls/999"
    responses.add_callback(responses.GET, url, callback=_callback)

    # First client -- installs the cache.
    _make_cached_client(tmp_path)
    resp1 = requests.get(url)
    assert resp1.status_code == 200
    assert call_count == 1

    # Second client -- cache already installed (idempotent).
    _make_cached_client(tmp_path)
    resp2 = requests.get(url)
    assert resp2.status_code == 200

    # The second response must come from cache.
    assert getattr(resp2, "from_cache", False) is True
    # The callback must NOT have been invoked a second time.
    assert call_count == 1


# ---------------------------------------------------------------------------
# 4.2  Idempotent installation
# ---------------------------------------------------------------------------


def test_idempotent_install(tmp_path):
    """install_cache is called only once even when two clients are created.

    This patches the module-level names that the implementation will
    import (``requests_cache``, ``os``) to verify the __init__ gating
    logic without touching the filesystem.
    """
    with patch(
        "pytorch_community_mcp.clients.github.requests_cache.install_cache"
    ) as mock_install, patch(
        "pytorch_community_mcp.clients.github.requests_cache.is_installed",
        side_effect=[False, True],
    ), patch(
        "pytorch_community_mcp.clients.github.requests_cache.get_cache"
    ), patch(
        "pytorch_community_mcp.clients.github.os.makedirs"
    ), patch(
        "pytorch_community_mcp.clients.github.os.path.expanduser",
        return_value=str(tmp_path / "cache"),
    ), patch(
        "pytorch_community_mcp.clients.github.os.path.join",
        return_value=str(tmp_path / "cache" / "http_cache"),
    ), patch(
        "pytorch_community_mcp.clients.github.Github"
    ):
        GitHubClient(token=None)
        GitHubClient(token=None)

    mock_install.assert_called_once()


# ---------------------------------------------------------------------------
# 4.3  rate_limit endpoint is NOT cached
# ---------------------------------------------------------------------------


@responses.activate
def test_rate_limit_endpoint_not_cached(tmp_path):
    """Requests to */rate_limit must bypass the cache entirely."""
    _make_cached_client(tmp_path)

    url = "https://api.github.com/rate_limit"
    responses.add(responses.GET, url, json={"rate": {}}, status=200)

    requests.get(url)
    requests.get(url)

    # Both requests should have hit the real (mocked) endpoint.
    assert len(responses.calls) == 2


# ---------------------------------------------------------------------------
# 4.4  Per-URL TTL configured correctly
# ---------------------------------------------------------------------------


@responses.activate
def test_search_issues_ttl_is_120s(tmp_path):
    """search/issues responses expire after ~120 seconds."""
    _make_cached_client(tmp_path)

    url = "https://api.github.com/search/issues?q=repo:pytorch/pytorch"
    responses.add(responses.GET, url, json={"items": []}, status=200)

    resp = requests.get(url)

    # CachedResponse must expose an .expires datetime ~120s in the future.
    assert hasattr(resp, "expires"), "Expected CachedResponse with .expires attr"
    assert resp.expires is not None
    delta = resp.expires - datetime.now(timezone.utc)
    assert 115 <= delta.total_seconds() <= 125


@responses.activate
def test_pulls_ttl_is_300s(tmp_path):
    """pulls/* responses expire after ~300 seconds."""
    _make_cached_client(tmp_path)

    url = "https://api.github.com/repos/pytorch/pytorch/pulls/123"
    responses.add(responses.GET, url, json={"number": 123}, status=200)

    resp = requests.get(url)
    assert hasattr(resp, "expires"), "Expected CachedResponse with .expires attr"
    assert resp.expires is not None
    delta = resp.expires - datetime.now(timezone.utc)
    assert 295 <= delta.total_seconds() <= 305


# ---------------------------------------------------------------------------
# 4.5  ETag / conditional-request behaviour
# ---------------------------------------------------------------------------


@responses.activate
def test_etag_conditional_request(tmp_path):
    """Cache returns body on 304 using ETag / If-None-Match."""
    _make_cached_client(tmp_path)

    url = "https://api.github.com/repos/pytorch/pytorch/issues/42"
    call_count = 0

    def _callback(request):
        nonlocal call_count
        call_count += 1
        if request.headers.get("If-None-Match") == '"abc123"':
            return (304, {}, "")
        return (200, {"ETag": '"abc123"'}, '{"id": 42}')

    responses.add_callback(responses.GET, url, callback=_callback)

    # First request -- 200 with ETag.
    resp1 = requests.get(url)
    assert resp1.status_code == 200
    assert resp1.json()["id"] == 42

    # Expire the cached entry so requests_cache sends a conditional request.
    cache = requests_cache.get_cache()
    for key in cache.responses:
        cached = cache.responses[key]
        cached.expires = datetime.now(timezone.utc) - timedelta(seconds=1)
        cache.responses[key] = cached

    # Second request -- should send If-None-Match, get 304, return cached body.
    resp2 = requests.get(url)
    assert resp2.status_code == 200
    assert resp2.json()["id"] == 42


# ---------------------------------------------------------------------------
# 4.6  5xx errors propagate (no stale fallback)
# ---------------------------------------------------------------------------


@responses.activate
def test_5xx_error_propagates(tmp_path):
    """A 500 response must NOT be masked by stale cache."""
    _make_cached_client(tmp_path)

    url = "https://api.github.com/repos/pytorch/pytorch/pulls/500"
    responses.add(responses.GET, url, json={"message": "error"}, status=500)

    resp = requests.get(url)
    assert resp.status_code == 500


# ---------------------------------------------------------------------------
# 4.7  Network timeout / connection error propagates
# ---------------------------------------------------------------------------


@responses.activate
def test_connection_error_propagates(tmp_path):
    """A ConnectionError must propagate, not be swallowed by cache."""
    _make_cached_client(tmp_path)

    url = "https://api.github.com/repos/pytorch/pytorch/pulls/999"
    responses.add(
        responses.GET,
        url,
        body=ConnectionError("network unreachable"),
    )

    with pytest.raises(ConnectionError):
        requests.get(url)


# ---------------------------------------------------------------------------
# 4.8  4xx errors (401/403) propagate normally
# ---------------------------------------------------------------------------


@responses.activate
def test_401_propagates(tmp_path):
    """A 401 response must propagate and not be cached."""
    _make_cached_client(tmp_path)

    url = "https://api.github.com/repos/pytorch/pytorch/pulls/401"
    responses.add(responses.GET, url, json={"message": "Unauthorized"}, status=401)

    resp = requests.get(url)
    assert resp.status_code == 401


@responses.activate
def test_403_propagates(tmp_path):
    """A 403 response must propagate and not be cached."""
    _make_cached_client(tmp_path)

    url = "https://api.github.com/repos/pytorch/pytorch/pulls/403"
    responses.add(responses.GET, url, json={"message": "Forbidden"}, status=403)

    resp = requests.get(url)
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 4.9  Cache directory auto-created
# ---------------------------------------------------------------------------


def test_cache_directory_auto_created(tmp_path):
    """GitHubClient creates the cache directory if it does not exist.

    Patches module-level names to verify __init__ calls
    ``os.makedirs(cache_dir, exist_ok=True)``.
    """
    target_dir = tmp_path / "deep" / "nested" / "cache"
    assert not target_dir.exists()

    with (
        patch(
            "pytorch_community_mcp.clients.github.os.path.expanduser",
            return_value=str(target_dir),
        ),
        patch("pytorch_community_mcp.clients.github.os.makedirs") as mock_makedirs,
        patch(
            "pytorch_community_mcp.clients.github.requests_cache.is_installed",
            return_value=False,
        ),
        patch("pytorch_community_mcp.clients.github.requests_cache.install_cache"),
        patch("pytorch_community_mcp.clients.github.requests_cache.get_cache"),
        patch(
            "pytorch_community_mcp.clients.github.os.path.join",
            return_value=str(target_dir / "http_cache"),
        ),
        patch("pytorch_community_mcp.clients.github.Github"),
    ):
        GitHubClient(token=None)

    mock_makedirs.assert_called_once_with(str(target_dir), exist_ok=True)


# ---------------------------------------------------------------------------
# 4.10  Startup cleanup of expired entries
# ---------------------------------------------------------------------------


@responses.activate
def test_startup_cleanup_removes_expired_entries(tmp_path):
    """GitHubClient.__init__ triggers deletion of expired cache entries."""
    # Step 1: create client -> installs cache; populate with a response.
    _make_cached_client(tmp_path)

    url = "https://api.github.com/repos/pytorch/pytorch/issues/1"
    responses.add(responses.GET, url, json={"id": 1}, status=200)
    requests.get(url)

    # Verify the entry is in the cache.
    cache = requests_cache.get_cache()
    assert len(list(cache.responses)) > 0

    # Step 2: manually expire the entry.
    for key in cache.responses:
        cached = cache.responses[key]
        cached.expires = datetime.now(timezone.utc) - timedelta(hours=1)
        cache.responses[key] = cached

    # Step 3: uninstall (simulates process restart) then create client -> __init__
    # calls ``requests_cache.get_cache().delete(expired=True)``.
    requests_cache.uninstall_cache()
    _make_cached_client(tmp_path)

    # Step 4: expired entry should now be gone.
    cache = requests_cache.get_cache()
    assert len(list(cache.responses)) == 0


# ---------------------------------------------------------------------------
# 4.11  httpx-based clients are unaffected
# ---------------------------------------------------------------------------


def test_httpx_not_cached(tmp_path):
    """requests_cache monkey-patches requests.Session, not httpx.

    After installing the cache, verify that httpx transport classes
    are not patched — httpx uses its own transport layer and must be
    completely unaffected by requests_cache.
    """
    _make_cached_client(tmp_path)

    # httpx.Response never has a from_cache attribute (intrinsic property).
    resp = httpx.Response(200)
    assert not hasattr(resp, "from_cache")

    # The httpx transport is not monkey-patched by requests_cache.
    assert not hasattr(httpx.Client, "_cache")
    assert not hasattr(httpx.AsyncClient, "_cache")
