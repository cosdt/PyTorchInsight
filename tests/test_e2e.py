"""End-to-end tests — call real APIs, no mocks.

Run with:
    uv run pytest tests/test_e2e.py -v -s --timeout=180

Time window: past 7 days from today.
"""

from __future__ import annotations

import os
import re
from datetime import date, timedelta

import pytest

from pytorch_community_mcp.clients.discourse import DiscourseClient
from pytorch_community_mcp.clients.events import EventsClient
from pytorch_community_mcp.clients.github import GitHubClient
from pytorch_community_mcp.clients.rss import RSSClient
from pytorch_community_mcp.tools import contributors, discussions, events
from pytorch_community_mcp.tools import issues as issues_tool
from pytorch_community_mcp.tools import prs as prs_tool
from pytorch_community_mcp.tools import rfcs as rfcs_tool

# Time window: past 7 days
TODAY = date.today()
SINCE = (TODAY - timedelta(days=7)).isoformat()
UNTIL = TODAY.isoformat()


# --------------- fixtures ---------------

@pytest.fixture(scope="module")
def github_client():
    token = os.environ.get("GITHUB_TOKEN")
    return GitHubClient(token=token)


@pytest.fixture(scope="module")
def discourse_client():
    return DiscourseClient(
        api_key=os.environ.get("DISCOURSE_API_KEY"),
        api_username=os.environ.get("DISCOURSE_API_USERNAME"),
    )


@pytest.fixture(scope="module")
def events_client():
    return EventsClient()


@pytest.fixture(scope="module")
def rss_client():
    return RSSClient()


# --------------- helper ---------------

def extract_result_count(result: str) -> int | None:
    """Parse ``**Results:** N`` from Markdown output. Returns *None* if not found."""
    m = re.search(r"\*\*Results:\*\*\s*(\d+)", result)
    return int(m.group(1)) if m else None


def result_has_error(result: str) -> bool:
    """Check for a tool-level error section (``## Error``)."""
    return "\n## Error\n" in result or result.startswith("## Error\n")


def assert_valid_markdown(result: str, tool_name: str, *, min_results: int = 0):
    """Structural checks on the Markdown output.

    Parameters
    ----------
    min_results:
        When > 0, parse the ``**Results:** N`` line and assert N >= min_results.
    """
    assert isinstance(result, str), f"{tool_name}: result is not a string"
    assert len(result) > 0, f"{tool_name}: result is empty"
    assert tool_name in result, f"{tool_name}: tool name not found in output"
    assert not result_has_error(result), f"{tool_name}: unexpected error in output"
    if min_results > 0:
        count = extract_result_count(result)
        assert count is not None, f"{tool_name}: could not parse result count"
        assert count >= min_results, (
            f"{tool_name}: expected >= {min_results} results, got {count}"
        )
    return result


# --------------- GitHub tools ---------------


class TestGetPRs:
    def test_basic(self, github_client):
        result = prs_tool.get_prs(github_client, SINCE, UNTIL)
        print(f"\n{'='*60}\nget_prs({SINCE} -> {UNTIL})\n{'='*60}")
        print(result[:2000])
        assert_valid_markdown(result, "get-prs", min_results=1)

    def test_with_module_filter(self, github_client):
        result = prs_tool.get_prs(github_client, SINCE, UNTIL, module="distributed")
        print(f"\n{'='*60}\nget_prs(module=distributed)\n{'='*60}")
        print(result[:1500])
        assert_valid_markdown(result, "get-prs")


class TestGetIssues:
    def test_basic(self, github_client):
        result = issues_tool.get_issues(github_client, SINCE, UNTIL)
        print(f"\n{'='*60}\nget_issues({SINCE} -> {UNTIL})\n{'='*60}")
        print(result[:2000])
        assert_valid_markdown(result, "get-issues", min_results=1)

    def test_closed_state(self, github_client):
        result = issues_tool.get_issues(github_client, SINCE, UNTIL, state="closed")
        print(f"\n{'='*60}\nget_issues(state=closed)\n{'='*60}")
        print(result[:1500])
        assert_valid_markdown(result, "get-issues", min_results=1)


class TestGetRFCs:
    def test_basic(self, github_client):
        result = rfcs_tool.get_rfcs(github_client, since=SINCE)
        print(f"\n{'='*60}\nget_rfcs(since={SINCE})\n{'='*60}")
        print(result[:2000])
        assert_valid_markdown(result, "get-rfcs")


# --------------- Discourse tools ---------------


class TestGetDiscussions:
    @pytest.mark.asyncio
    async def test_basic(self, discourse_client):
        result = await discussions.get_discussions(
            discourse_client, query="pytorch", since=SINCE, until=UNTIL
        )
        print(f"\n{'='*60}\nget_discussions(pytorch, {SINCE} -> {UNTIL})\n{'='*60}")
        print(result[:2000])
        assert_valid_markdown(result, "get-discussions", min_results=1)

    @pytest.mark.asyncio
    async def test_latest_no_query(self, discourse_client):
        result = await discussions.get_discussions(discourse_client)
        print(f"\n{'='*60}\nget_discussions(latest)\n{'='*60}")
        print(result[:1500])
        assert_valid_markdown(result, "get-discussions")


# --------------- Events & Blog tools ---------------


class TestGetEvents:
    @pytest.mark.asyncio
    async def test_basic(self, events_client):
        result = await events.get_events(events_client, since=SINCE, until=UNTIL)
        print(f"\n{'='*60}\nget_events({SINCE} -> {UNTIL})\n{'='*60}")
        print(result[:2000])
        assert_valid_markdown(result, "get-events")

    @pytest.mark.asyncio
    async def test_with_search(self, events_client):
        result = await events.get_events(events_client, search="pytorch")
        print(f"\n{'='*60}\nget_events(search=pytorch)\n{'='*60}")
        print(result[:1500])
        assert_valid_markdown(result, "get-events")


class TestGetBlogNews:
    def test_basic(self, rss_client):
        result = events.get_blog_news(rss_client, since=SINCE, limit=5)
        print(f"\n{'='*60}\nget_blog_news(since={SINCE}, limit=5)\n{'='*60}")
        print(result[:2000])
        assert_valid_markdown(result, "get-blog-news")

    def test_no_filter(self, rss_client):
        result = events.get_blog_news(rss_client, limit=3)
        print(f"\n{'='*60}\nget_blog_news(limit=3)\n{'='*60}")
        print(result[:1500])
        assert_valid_markdown(result, "get-blog-news")


# --------------- Contributors tool ---------------


class TestGetKeyContributorsActivity:
    @pytest.mark.asyncio
    async def test_basic(self, github_client, discourse_client):
        result = await contributors.get_key_contributors_activity(
            github_client, discourse_client,
            contributor="ezyang",
            since=SINCE,
            until=UNTIL,
        )
        print(f"\n{'='*60}\nget_key_contributors_activity(ezyang, {SINCE} -> {UNTIL})\n{'='*60}")
        print(result[:3000])
        assert_valid_markdown(result, "get-key-contributors-activity")
