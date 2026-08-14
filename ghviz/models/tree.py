"""Data models for file tree and commit tree visuals."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TreeNode:
    """A single file/folder node in a repo's file tree."""

    name: str
    path: str
    is_dir: bool
    children: list["TreeNode"] = field(default_factory=list)


@dataclass
class CommitNode:
    """A single commit for the commit/branch graph visual."""

    sha: str
    message: str
    full_message: str
    author: str
    email: str
    date: str
    parents: list[str] = field(default_factory=list)
