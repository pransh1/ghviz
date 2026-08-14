"""Builds and renders a commit history as a terminal graph using `rich`.

v1 approach: a vertical timeline (not a full multi-lane git-log --graph layout).
Merge commits (2+ parents) are visually marked as branch points. This is a
deliberate simplification — true multi-lane graph layout (assigning branches
to columns, avoiding line crossings) is a much harder problem we can tackle
as a v2 if we want the full `git log --graph --all` look.
"""

from __future__ import annotations

from rich.console import Console, Group
from rich.text import Text

from ghviz.models.tree import CommitNode

console = Console()

DOT = "●"
MERGE_DOT = "◆"
LINE = "│"


def build_commit_graph(raw_commits: list[dict]) -> list[CommitNode]:
    """Convert GitHub's commit API response into a list of CommitNode.

    raw_commits is already in reverse-chronological order (newest first),
    which is exactly what GitHub's API gives us.
    """
    nodes = []
    for c in raw_commits:
        commit_info = c.get("commit", {})
        author_info = commit_info.get("author", {}) or {}
        full_message = commit_info.get("message", "")
        parents = [p["sha"] for p in c.get("parents", [])]

        nodes.append(
            CommitNode(
                sha=c["sha"],
                message=commit_info.get("message", "").split("\n")[0],  # first line only
                full_message=full_message,
                author=author_info.get("name", "unknown"),
                email=author_info.get("email", ""),
                date=author_info.get("date", ""),
                parents=parents,
            )
        )
    return nodes


def render_commit_graph(nodes: list[CommitNode], limit: int = 30) -> Group:
    """Render commits as a vertical timeline, marking merge commits distinctly."""
    lines = []
    shown = nodes[:limit]

    for i, node in enumerate(shown):
        is_merge = len(node.parents) > 1
        symbol = MERGE_DOT if is_merge else DOT
        symbol_style = "bold magenta" if is_merge else "bold green"

        short_sha = node.sha[:7]
        date_only = node.date.split("T")[0] if node.date else ""

        line = Text()
        line.append(f"{symbol} ", style=symbol_style)
        line.append(f"{short_sha} ", style="yellow")
        line.append(f"{node.message}  ", style="white")
        line.append(f"({node.author}, {date_only})", style="dim")
        if is_merge:
            line.append(f"  [merge, {len(node.parents)} parents]", style="bold magenta")
        lines.append(line)

        # Connector line between commits, skip after the last one
        if i < len(shown) - 1:
            lines.append(Text(LINE, style="dim"))

    if len(nodes) > limit:
        lines.append(Text(f"... {len(nodes) - limit} more commits not shown", style="dim italic"))

    return Group(*lines)