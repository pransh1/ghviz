"""Reads commit history and file tree directly from a local `.git` repo,
by shelling out to the real `git` binary — no GitHub API involved.

This gives us data the API can never provide: the real local HEAD, real
local branch names, and no rate limits. Trade-off: only works when you're
standing inside an actual clone, unlike the GitHub-API mode which works
on any public repo from anywhere.
"""

from __future__ import annotations

import subprocess

from ghviz.models.tree import CommitNode

# Non-printable separators that will never appear in real commit data —
# safer than splitting on "|" or "," which commit messages can legitimately contain.
RECORD_SEP = "\x1e"
FIELD_SEP = "\x1f"


class LocalGitError(Exception):
    """Raised when a local git command fails (not a repo, git not installed, etc.)."""


def is_git_repo(path: str = ".") -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", path, "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, timeout=5,
        )
        return result.returncode == 0 and result.stdout.strip() == "true"
    except FileNotFoundError:
        return False  # git itself isn't installed


def get_local_commits(path: str = ".", limit: int = 100) -> list[CommitNode]:
    """Run `git log` with a custom format and parse it into CommitNode objects."""
    fmt = f"%H{FIELD_SEP}%P{FIELD_SEP}%an{FIELD_SEP}%ae{FIELD_SEP}%aI{FIELD_SEP}%D{FIELD_SEP}%B{RECORD_SEP}"
    result = subprocess.run(
        ["git", "-C", path, "log", f"-n{limit}", f"--pretty=format:{fmt}"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise LocalGitError(result.stderr.strip() or "git log failed")

    nodes: list[CommitNode] = []
    for record in result.stdout.split(RECORD_SEP):
        record = record.strip("\n")
        if not record.strip():
            continue
        fields = record.split(FIELD_SEP)
        if len(fields) < 7:
            continue
        sha, parents_raw, author, email, date_iso, decoration, body = fields[:7]
        full_message = body.strip("\n")

        nodes.append(
            CommitNode(
                sha=sha,
                message=full_message.split("\n")[0] if full_message else "",
                full_message=full_message,
                author=author,
                email=email,
                date=date_iso,
                parents=parents_raw.split() if parents_raw.strip() else [],
                decoration=decoration.strip(),
            )
        )
    return nodes


def get_local_tracked_files(path: str = ".") -> list[str]:
    """List every git-tracked file (respects .gitignore automatically)."""
    result = subprocess.run(
        ["git", "-C", path, "ls-files"], capture_output=True, text=True, timeout=15
    )
    if result.returncode != 0:
        raise LocalGitError(result.stderr.strip() or "git ls-files failed")
    return [line for line in result.stdout.splitlines() if line.strip()]