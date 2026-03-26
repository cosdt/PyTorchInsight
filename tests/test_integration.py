"""Integration tests — tool registration, parameter schemas, and server metadata."""

import importlib
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pytorch_community_mcp.clients.github import GitHubClient
from pytorch_community_mcp.config import (
    Config,
    DiscourseConfig,
    GitHubConfig,
)

DUMMY_CONFIG = Config(
    github=GitHubConfig(token=None),
    discourse=DiscourseConfig(),
)

EXPECTED_TOOLS = {
    "get_prs",
    "get_issues",
    "get_commits",
    "get_rfcs",
    "get_pr_detail",
    "get_issue_detail",
    "get_discussions",
    "get_events",
    "get_blog_news",
    "get_key_contributors_activity",
}


@pytest.fixture(scope="module")
def server():
    """Import server module with mocked config to avoid credential resolution."""
    sys.modules.pop("pytorch_community_mcp.server", None)

    with patch("pytorch_community_mcp.config.config", DUMMY_CONFIG):
        import pytorch_community_mcp.server as srv

        yield srv

    sys.modules.pop("pytorch_community_mcp.server", None)


# ---------------------------------------------------------------------------
# 4.2 Tool registration tests
# ---------------------------------------------------------------------------


async def test_tool_count_and_names(server):
    """Exactly 10 tools registered with expected names."""
    tools = await server.mcp.list_tools()
    names = {t.name for t in tools}
    assert len(tools) == 10
    assert names == EXPECTED_TOOLS


async def test_tool_descriptions_non_empty(server):
    """Every tool has a non-empty description."""
    tools = await server.mcp.list_tools()
    for t in tools:
        assert t.description, f"Tool {t.name} has empty description"
        assert len(t.description.strip()) > 0


# ---------------------------------------------------------------------------
# 4.3 Parameter schema tests
# ---------------------------------------------------------------------------


async def test_get_prs_requires_since(server):
    """get_prs schema has 'since' as a required string parameter."""
    tools = await server.mcp.list_tools()
    get_prs = next(t for t in tools if t.name == "get_prs")
    schema = get_prs.parameters
    assert "since" in schema["required"]
    assert schema["properties"]["since"]["type"] == "string"


async def test_get_key_contributors_requires_contributor(server):
    """get_key_contributors_activity schema has 'contributor' as required string."""
    tools = await server.mcp.list_tools()
    tool = next(t for t in tools if t.name == "get_key_contributors_activity")
    schema = tool.parameters
    assert "contributor" in schema["required"]
    assert schema["properties"]["contributor"]["type"] == "string"


# ---------------------------------------------------------------------------
# 4.4 Server metadata tests
# ---------------------------------------------------------------------------


def test_server_name(server):
    """Server name is 'PyTorch Community MCP'."""
    assert server.mcp.name == "PyTorch Community MCP"


def test_server_version(server):
    """Server version is '0.1.0'."""
    assert server.mcp.version == "0.2.0"


# ---------------------------------------------------------------------------
# 4.5 Sync tool invocation test
# ---------------------------------------------------------------------------


async def test_get_prs_invocation(server):
    """get_prs returns formatted response through the server."""
    mock_issue = MagicMock()
    mock_issue.title = "Test PR"
    mock_issue.html_url = "https://github.com/test/1"
    mock_issue.created_at.strftime.return_value = "2024-01-15"
    mock_issue.user.login = "user1"
    mock_issue.state = "open"
    mock_issue.labels = []
    mock_issue.body = "Test body"

    mock_gh = MagicMock(spec=GitHubClient)
    mock_gh.search_issues.return_value = ([mock_issue], 1)
    mock_gh.rate_limit_remaining = 25
    mock_gh.rate_limit_total = 30

    original = server.github_client
    server.github_client = mock_gh
    try:
        result = await server.mcp.call_tool("get_prs", {"since": "2024-01-01"})
        text = result.content[0].text
        assert "## Results" in text
        assert "Test PR" in text
    finally:
        server.github_client = original


# ---------------------------------------------------------------------------
# 4.6 Async tool invocation test
# ---------------------------------------------------------------------------


async def test_get_discussions_invocation(server):
    """get_discussions returns formatted response through the server."""
    mock_disc = MagicMock()
    mock_disc.search = AsyncMock(
        return_value=[
            {
                "id": 42,
                "title": "Test Topic",
                "slug": "test-topic",
                "created_at": "2024-01-15T12:00:00Z",
                "last_poster_username": "user1",
                "posts_count": 5,
                "views": 100,
                "excerpt": "An excerpt",
            }
        ]
    )

    original = server.discourse_client
    server.discourse_client = mock_disc
    try:
        result = await server.mcp.call_tool("get_discussions", {"query": "test"})
        text = result.content[0].text
        assert "## Results" in text
        assert "Test Topic" in text
    finally:
        server.discourse_client = original
