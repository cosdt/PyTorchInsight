"""PyGithub wrapper with rate limit awareness and exponential backoff."""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime

import requests_cache
from github import Github, GithubException, RateLimitExceededException
from github.PaginatedList import PaginatedList


@dataclass
class RateLimitInfo:
    remaining: int = 30
    limit: int = 30
    reset_time: float = 0.0


class GitHubClient:
    """Wrapper around PyGithub with rate limit handling."""

    _cache_hits: int = 0
    _cache_total: int = 0

    def __init__(self, token: str | None = None) -> None:
        if not requests_cache.is_installed():
            cache_dir = os.path.expanduser("~/.cache/pytorch-community-mcp")
            os.makedirs(cache_dir, exist_ok=True)
            requests_cache.install_cache(
                os.path.join(cache_dir, "http_cache"),
                backend="sqlite",
                urls_expire_after={
                    "*/rate_limit": requests_cache.DO_NOT_CACHE,
                    "*/search/issues*": 120,
                    "*/pulls/*": 300,
                    "*/issues/*": 300,
                    "*/commits*": 300,
                    "*": 300,
                },
            )
            requests_cache.get_cache().delete(expired=True)
            self._hook_send()
        self._github = Github(auth=None) if token is None else Github(token)
        self._rate_limit = RateLimitInfo()
        self._core_rate_limit = RateLimitInfo(remaining=5000, limit=5000)
        self._repo_cache: dict = {}
        self._pr_cache: dict = {}
        self._issue_cache: dict = {}
        self._rate_limit_last_checked: float = 0

    @classmethod
    def _hook_send(cls) -> None:
        """Hook CachedSession.send() to count cache hits/misses."""
        original_send = requests_cache.CachedSession.send
        if getattr(original_send, "_stats_wrapped", False):
            return

        def _counting_send(self, request, **kwargs):
            response = original_send(self, request, **kwargs)
            cls._cache_total += 1
            if getattr(response, "from_cache", False):
                cls._cache_hits += 1
            return response

        _counting_send._stats_wrapped = True
        requests_cache.CachedSession.send = _counting_send

    def snapshot_stats(self) -> tuple[int, int]:
        """Return current (hits, total) for later delta computation."""
        return (GitHubClient._cache_hits, GitHubClient._cache_total)

    def get_stats(self, snapshot: tuple[int, int]) -> dict:
        """Compute delta since snapshot."""
        prev_hits, prev_total = snapshot
        total = GitHubClient._cache_total - prev_total
        cached = GitHubClient._cache_hits - prev_hits
        return {"total": total, "cached": cached, "fresh": total - cached}

    def _get_repo(self, repo_name: str):
        """Get repo object, using cache if available."""
        if repo_name not in self._repo_cache:
            self._repo_cache[repo_name] = self._github.get_repo(repo_name)
        return self._repo_cache[repo_name]

    @property
    def rate_limit_remaining(self) -> int:
        return self._rate_limit.remaining

    @property
    def rate_limit_total(self) -> int:
        return self._rate_limit.limit

    @property
    def core_rate_limit_remaining(self) -> int:
        return self._core_rate_limit.remaining

    @property
    def core_rate_limit_total(self) -> int:
        return self._core_rate_limit.limit

    _RATE_LIMIT_CHECK_INTERVAL = 60

    def _update_rate_limit(self, *, force: bool = False) -> None:
        """Fetch current rate limit from GitHub API, with time-based throttling."""
        now = time.time()
        if not force and now - self._rate_limit_last_checked < self._RATE_LIMIT_CHECK_INTERVAL:
            return
        try:
            rl = self._github.get_rate_limit()
            # PyGithub >=2.6 removed rl.search; fall back to raw_data
            if hasattr(rl, "search"):
                self._rate_limit.remaining = rl.search.remaining
                self._rate_limit.limit = rl.search.limit
                self._rate_limit.reset_time = rl.search.reset.timestamp()
            else:
                search = rl.raw_data.get("resources", {}).get("search", {})
                self._rate_limit.remaining = search.get("remaining", self._rate_limit.remaining)
                self._rate_limit.limit = search.get("limit", self._rate_limit.limit)
                self._rate_limit.reset_time = float(search.get("reset", 0))
            # Update core rate limit
            if hasattr(rl, "core"):
                self._core_rate_limit.remaining = rl.core.remaining
                self._core_rate_limit.limit = rl.core.limit
                self._core_rate_limit.reset_time = rl.core.reset.timestamp()
            else:
                core = rl.raw_data.get("resources", {}).get("core", {})
                self._core_rate_limit.remaining = core.get("remaining", self._core_rate_limit.remaining)
                self._core_rate_limit.limit = core.get("limit", self._core_rate_limit.limit)
                self._core_rate_limit.reset_time = float(core.get("reset", 0))
            self._rate_limit_last_checked = now
        except GithubException:
            pass

    def _wait_for_rate_limit(self) -> None:
        """Wait if rate limited, with exponential backoff."""
        self._update_rate_limit(force=True)
        if self._rate_limit.remaining <= 1:
            wait_time = max(0, self._rate_limit.reset_time - time.time()) + 1
            time.sleep(min(wait_time, 60))

    def search_issues(
        self,
        query: str,
        *,
        max_results: int = 100,
        max_retries: int = 3,
    ) -> tuple[list, int]:
        """Search issues/PRs with retry and rate limit handling.

        Returns a tuple of (items, total_count).
        """
        for attempt in range(max_retries):
            try:
                self._wait_for_rate_limit()
                results = self._github.search_issues(query)
                self._update_rate_limit()
                total_count = results.totalCount
                items = []
                for item in results:
                    items.append(item)
                    if len(items) >= max_results:
                        break
                return items, total_count
            except RateLimitExceededException:
                backoff = 2**attempt * 10
                time.sleep(min(backoff, 60))
                continue
            except GithubException as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2**attempt)
        return [], 0

    def get_commits(
        self,
        repo_name: str = "pytorch/pytorch",
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        author: str | None = None,
        sha: str | None = None,
        max_results: int = 100,
        max_retries: int = 3,
    ) -> tuple[list, int]:
        """Get commits from a repository with time range filtering.

        Returns a tuple of (items, total_count).
        total_count is approximate (from PyGithub pagination).
        """
        for attempt in range(max_retries):
            try:
                repo = self._get_repo(repo_name)
                kwargs: dict = {}
                if since is not None:
                    kwargs["since"] = since
                if until is not None:
                    kwargs["until"] = until
                if author is not None:
                    kwargs["author"] = author
                if sha is not None:
                    kwargs["sha"] = sha

                commits = repo.get_commits(**kwargs)
                total_count = commits.totalCount
                items = []
                for c in commits:
                    items.append(c)
                    if len(items) >= max_results:
                        break
                return items, total_count
            except RateLimitExceededException:
                backoff = 2**attempt * 10
                time.sleep(min(backoff, 60))
                continue
            except GithubException as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2**attempt)
        return [], 0

    def get_pull_request(
        self,
        repo_name: str = "pytorch/pytorch",
        *,
        pr_number: int,
        max_retries: int = 3,
    ):
        """Get a single pull request by number.

        Returns a PyGithub PullRequest object.
        """
        for attempt in range(max_retries):
            try:
                repo = self._get_repo(repo_name)
                pr = repo.get_pull(pr_number)
                self._pr_cache[(repo_name, pr_number)] = pr
                self._update_rate_limit()
                return pr
            except RateLimitExceededException:
                backoff = 2**attempt * 10
                time.sleep(min(backoff, 60))
                continue
            except GithubException:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2**attempt)
        return None

    def get_pr_files(
        self,
        repo_name: str = "pytorch/pytorch",
        *,
        pr_number: int,
        max_retries: int = 3,
    ) -> list:
        """Get the list of files changed in a pull request."""
        for attempt in range(max_retries):
            try:
                pr = self._pr_cache.get((repo_name, pr_number))
                if pr is None:
                    repo = self._get_repo(repo_name)
                    pr = repo.get_pull(pr_number)
                files = list(pr.get_files())
                self._update_rate_limit()
                return files
            except RateLimitExceededException:
                backoff = 2**attempt * 10
                time.sleep(min(backoff, 60))
                continue
            except GithubException:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2**attempt)
        return []

    def get_pr_reviews(
        self,
        repo_name: str = "pytorch/pytorch",
        *,
        pr_number: int,
        max_retries: int = 3,
    ) -> list:
        """Get reviews for a pull request."""
        for attempt in range(max_retries):
            try:
                pr = self._pr_cache.get((repo_name, pr_number))
                if pr is None:
                    repo = self._get_repo(repo_name)
                    pr = repo.get_pull(pr_number)
                reviews = list(pr.get_reviews())
                self._update_rate_limit()
                return reviews
            except RateLimitExceededException:
                backoff = 2**attempt * 10
                time.sleep(min(backoff, 60))
                continue
            except GithubException:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2**attempt)
        return []

    def get_issue(
        self,
        repo_name: str = "pytorch/pytorch",
        *,
        issue_number: int,
        max_retries: int = 3,
    ):
        """Get a single issue by number.

        Returns a PyGithub Issue object.
        """
        for attempt in range(max_retries):
            try:
                repo = self._get_repo(repo_name)
                issue = repo.get_issue(issue_number)
                self._issue_cache[(repo_name, issue_number)] = issue
                self._update_rate_limit()
                return issue
            except RateLimitExceededException:
                backoff = 2**attempt * 10
                time.sleep(min(backoff, 60))
                continue
            except GithubException:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2**attempt)
        return None

    def get_issue_comments(
        self,
        repo_name: str = "pytorch/pytorch",
        *,
        issue_number: int,
        max_comments: int = 50,
        max_retries: int = 3,
    ) -> tuple[list, int]:
        """Get comments for an issue.

        Returns a tuple of (comments, total_count).
        """
        for attempt in range(max_retries):
            try:
                issue = self._issue_cache.get((repo_name, issue_number))
                if issue is None:
                    repo = self._get_repo(repo_name)
                    issue = repo.get_issue(issue_number)
                all_comments = issue.get_comments()
                total_count = all_comments.totalCount
                comments = []
                for c in all_comments:
                    comments.append(c)
                    if len(comments) >= max_comments:
                        break
                self._update_rate_limit()
                return comments, total_count
            except RateLimitExceededException:
                backoff = 2**attempt * 10
                time.sleep(min(backoff, 60))
                continue
            except GithubException:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2**attempt)
        return [], 0

    def get_issue_timeline(
        self,
        repo_name: str = "pytorch/pytorch",
        *,
        issue_number: int,
        max_retries: int = 3,
    ) -> list:
        """Get timeline events for an issue to extract linked PRs."""
        for attempt in range(max_retries):
            try:
                issue = self._issue_cache.get((repo_name, issue_number))
                if issue is None:
                    repo = self._get_repo(repo_name)
                    issue = repo.get_issue(issue_number)
                events = []
                for event in issue.get_timeline():
                    events.append(event)
                self._update_rate_limit()
                return events
            except RateLimitExceededException:
                backoff = 2**attempt * 10
                time.sleep(min(backoff, 60))
                continue
            except GithubException:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2**attempt)
        return []
