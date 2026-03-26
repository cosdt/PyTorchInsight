"""FastMCP server — registers all tools and configures stdio transport."""

from __future__ import annotations

from fastmcp import FastMCP

from pytorch_community_mcp.clients.discourse import DiscourseClient
from pytorch_community_mcp.clients.events import EventsClient
from pytorch_community_mcp.clients.github import GitHubClient
from pytorch_community_mcp.clients.rss import RSSClient
from pytorch_community_mcp.config import config
from pytorch_community_mcp.tools import commits as commits_tool
from pytorch_community_mcp.tools import contributors, discussions, events
from pytorch_community_mcp.tools import issue_detail as issue_detail_tool
from pytorch_community_mcp.tools import issues as issues_tool
from pytorch_community_mcp.tools import pr_detail as pr_detail_tool
from pytorch_community_mcp.tools import prs as prs_tool
from pytorch_community_mcp.tools import rfcs as rfcs_tool

mcp = FastMCP(
    "PyTorch Community MCP",
    instructions=(
        "This server provides tools to retrieve PyTorch community intelligence "
        "from GitHub, Discourse, and the official PyTorch website."
    ),
    version="0.2.0",
)

# Initialize clients
github_client = GitHubClient(token=config.github.token)
discourse_client = DiscourseClient(
    api_key=config.discourse.api_key,
    api_username=config.discourse.api_username,
)
events_client = EventsClient()
rss_client = RSSClient()


# --- Helpers ---


def _append_api_stats(result: str, stats: dict) -> str:
    """Append API call statistics to a Markdown result string."""
    return (
        f"{result}\n\n**API Calls:** {stats['total']} total "
        f"({stats['cached']} cached, {stats['fresh']} fresh)"
    )


# --- GitHub tools ---


@mcp.tool
def get_prs(
    since: str,
    until: str | None = None,
    module: str | None = None,
    state: str = "all",
    date_type: str = "created",
    max_results: int = 100,
    description_length: int = 500,
) -> str:
    """Get PyTorch pull requests within a date range.

    Args:
        since: Start date (ISO format, e.g. 2024-01-01). Required.
        until: End date (ISO format). Defaults to today.
        module: Filter by module label (e.g. "distributed", "compiler").
        state: PR state — "open", "closed", "merged", or "all". Default "all".
        date_type: Date filter type — "created" or "updated". Default "created".
        max_results: Maximum number of results to return. Default 100.
        description_length: Max chars of PR description. Default 500. Use -1 for full body.
    """
    snap = github_client.snapshot_stats()
    result = prs_tool.get_prs(
        github_client, since, until, module, state, date_type, max_results, description_length
    )
    return _append_api_stats(result, github_client.get_stats(snap))


@mcp.tool
def get_issues(
    since: str,
    until: str | None = None,
    module: str | None = None,
    state: str = "open",
    date_type: str = "created",
    max_results: int = 100,
    description_length: int = 500,
) -> str:
    """Get PyTorch issues within a date range.

    Args:
        since: Start date (ISO format). Required.
        until: End date (ISO format). Defaults to today.
        module: Filter by module label (e.g. "compiler").
        state: Issue state — "open", "closed", or "all". Default "open".
        date_type: Date filter type — "created" or "updated". Default "created".
        max_results: Maximum number of results to return. Default 100.
        description_length: Max chars of issue description. Default 500. Use -1 for full body.
    """
    snap = github_client.snapshot_stats()
    result = issues_tool.get_issues(
        github_client, since, until, module, state, date_type, max_results, description_length
    )
    return _append_api_stats(result, github_client.get_stats(snap))


@mcp.tool
def get_commits(
    since: str,
    until: str | None = None,
    author: str | None = None,
    sha: str | None = None,
    max_results: int = 100,
    message_length: int = 200,
) -> str:
    """Get PyTorch commits within a date range.

    Args:
        since: Start date (ISO format). Required.
        until: End date (ISO format). Defaults to today.
        author: Filter by author (GitHub username or email).
        sha: Branch name or commit SHA to start listing from. Default: repo default branch.
        max_results: Maximum number of commits to return. Default 100.
        message_length: Max chars of commit message to include. Default 200. Use -1 for full message.
    """
    snap = github_client.snapshot_stats()
    result = commits_tool.get_commits(
        github_client, since, until, author, sha, max_results, message_length
    )
    return _append_api_stats(result, github_client.get_stats(snap))


@mcp.tool
def get_pr_detail(
    pr_number: int,
    repo: str = "pytorch/pytorch",
    max_diff_lines: int = 50,
    files_only: bool = False,
    include_reviews: bool = True,
) -> str:
    """Get detailed information for a single pull request, including changed files, code diffs, and reviews.

    Args:
        pr_number: Pull request number. Required.
        repo: Repository in owner/name format. Default "pytorch/pytorch".
        max_diff_lines: Maximum lines of diff to show per file. Default 50. Use -1 for full diff.
        files_only: If true, return only file list with stats, no diffs. Default false.
        include_reviews: If true, include review information. Default true.
    """
    snap = github_client.snapshot_stats()
    result = pr_detail_tool.get_pr_detail(
        github_client, pr_number, repo, max_diff_lines, files_only, include_reviews
    )
    return _append_api_stats(result, github_client.get_stats(snap))


@mcp.tool
def get_issue_detail(
    issue_number: int,
    repo: str = "pytorch/pytorch",
    max_comments: int = 50,
    comment_length: int = 500,
) -> str:
    """Get detailed information for a single issue, including comments and linked PRs.

    Args:
        issue_number: Issue number. Required.
        repo: Repository in owner/name format. Default "pytorch/pytorch".
        max_comments: Maximum number of comments to return. Default 50.
        comment_length: Max chars per comment body. Default 500. Use -1 for full body.
    """
    snap = github_client.snapshot_stats()
    result = issue_detail_tool.get_issue_detail(
        github_client, issue_number, repo, max_comments, comment_length
    )
    return _append_api_stats(result, github_client.get_stats(snap))


@mcp.tool
def get_rfcs(
    since: str | None = None,
    status: str = "all",
) -> str:
    """Get PyTorch RFCs from pytorch/pytorch and pytorch/rfcs.

    Args:
        since: Start date (ISO format). Optional.
        status: RFC status — "open", "closed", or "all". Default "all".
    """
    snap = github_client.snapshot_stats()
    result = rfcs_tool.get_rfcs(github_client, since, status)
    return _append_api_stats(result, github_client.get_stats(snap))


# --- Discourse tools ---


@mcp.tool
async def get_discussions(
    query: str | None = None,
    category: str | None = None,
    since: str | None = None,
    until: str | None = None,
    limit: int = 50,
) -> str:
    """Get discussions from the PyTorch developer forum (discuss.pytorch.org).

    Args:
        query: Search string.
        category: Category name (e.g. "dev").
        since: Start date (ISO format).
        until: End date (ISO format).
        limit: Maximum number of results to return. Default 50.
    """
    return await discussions.get_discussions(
        discourse_client, query, category, since, until, limit
    )


# --- Events & Blog tools ---


@mcp.tool
async def get_events(
    since: str | None = None,
    until: str | None = None,
    search: str | None = None,
    featured: bool | None = None,
    limit: int = 50,
) -> str:
    """Get PyTorch community events from the official website.

    Args:
        since: Start date (ISO format).
        until: End date (ISO format).
        search: Keyword to filter events.
        featured: If true, return only featured events.
        limit: Maximum number of results to return. Default 50.
    """
    return await events.get_events(
        events_client, since, until, search, featured, limit
    )


@mcp.tool
def get_blog_news(
    since: str | None = None,
    limit: int = 20,
) -> str:
    """Get recent PyTorch blog posts and news from the RSS feed.

    Args:
        since: Only return posts published after this date (ISO format).
        limit: Maximum number of posts to return. Default 20.
    """
    return events.get_blog_news(rss_client, since, limit)


# --- Contributor tools ---


@mcp.tool
async def get_key_contributors_activity(
    contributor: str,
    since: str | None = None,
    until: str | None = None,
) -> str:
    """Get a contributor's activity across GitHub and Discourse.

    Args:
        contributor: GitHub username of the contributor. Required.
        since: Start date (ISO format).
        until: End date (ISO format).
    """
    snap = github_client.snapshot_stats()
    result = await contributors.get_key_contributors_activity(
        github_client, discourse_client, contributor, since, until
    )
    return _append_api_stats(result, github_client.get_stats(snap))
