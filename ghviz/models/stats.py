"""Data models for user/repo stats. Kept plain and simple on purpose —
these fields map 1:1 to future Go structs."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RepoSummary:
    name: str
    stars: int
    forks: int
    language: str | None
    updated_at: str


@dataclass
class UserStats:
    username: str
    public_repos: int
    followers: int
    following: int
    top_repos: list[RepoSummary] = field(default_factory=list)
    language_breakdown: dict[str, int] = field(default_factory=dict)  # language -> byte count
