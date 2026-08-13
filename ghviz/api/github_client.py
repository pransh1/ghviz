"""
GitHub API client for ghviz.

Keeps all HTTP/API concerns isolated from rendering logic, so this module
can be ported near-verbatim to Go later (this maps to a `client` package
with a struct + methods in Go).
"""

from __future__ import annotations

import os
from typing import Any

import httpx

GITHUB_API_BASE = "https://api.github.com"


class GitHubAPIError(Exception):
    """Raised when the GitHub API returns an error response."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class RateLimitError(GitHubAPIError):
    """Raised specifically when we hit GitHub's rate limit."""


class GitHubClient:
    """Thin wrapper around the GitHub REST API."""

    def __init__(self, token: str | None = None):
        # Falls back to env var so users can `export GITHUB_TOKEN=...`
        self.token = token or os.environ.get("GITHUB_TOKEN")
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        self._client = httpx.Client(base_url=GITHUB_API_BASE, headers=headers, timeout=15.0)

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        response = self._client.get(path, params=params or {})

        if response.status_code == 403 and "rate limit" in response.text.lower():
            raise RateLimitError(
                "GitHub API rate limit exceeded. Set a GITHUB_TOKEN env var to raise your limit "
                "(unauthenticated requests are capped at 60/hour).",
                status_code=403,
            )

        if response.status_code == 404:
            raise GitHubAPIError(f"Not found: {path}", status_code=404)

        if response.status_code >= 400:
            raise GitHubAPIError(
                f"GitHub API error ({response.status_code}) for {path}: {response.text}",
                status_code=response.status_code,
            )

        return response.json()

    # ---- User-level endpoints ----

    def get_user(self, username: str) -> dict:
        return self._get(f"/users/{username}")

    def get_user_repos(self, username: str, per_page: int = 100) -> list[dict]:
        return self._get(f"/users/{username}/repos", params={"per_page": per_page, "sort": "updated"})

    # ---- Repo-level endpoints ----

    def get_repo(self, owner: str, repo: str) -> dict:
        return self._get(f"/repos/{owner}/{repo}")

    def get_repo_languages(self, owner: str, repo: str) -> dict:
        return self._get(f"/repos/{owner}/{repo}/languages")

    def get_repo_commits(self, owner: str, repo: str, per_page: int = 100) -> list[dict]:
        return self._get(f"/repos/{owner}/{repo}/commits", params={"per_page": per_page})

    def get_repo_tree(self, owner: str, repo: str, branch: str = "HEAD") -> dict:
        # recursive=1 pulls the full tree in one call (capped at GitHub's size limits)
        return self._get(f"/repos/{owner}/{repo}/git/trees/{branch}", params={"recursive": 1})

    def close(self):
        self._client.close()
