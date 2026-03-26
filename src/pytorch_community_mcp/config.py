"""Configuration management — reads credentials from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class GitHubConfig:
    token: str | None = None

    @property
    def available(self) -> bool:
        return self.token is not None


@dataclass(frozen=True)
class DiscourseConfig:
    api_key: str | None = None
    api_username: str | None = None

    @property
    def available(self) -> bool:
        return self.api_key is not None and self.api_username is not None


@dataclass(frozen=True)
class Config:
    github: GitHubConfig
    discourse: DiscourseConfig

    @classmethod
    def from_env(cls) -> Config:
        return cls(
            github=GitHubConfig(
                token=os.environ.get("GITHUB_TOKEN"),
            ),
            discourse=DiscourseConfig(
                api_key=os.environ.get("DISCOURSE_API_KEY"),
                api_username=os.environ.get("DISCOURSE_API_USERNAME"),
            ),
        )


config = Config.from_env()
