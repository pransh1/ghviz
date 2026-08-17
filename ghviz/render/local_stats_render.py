"""Computes and renders stats for a local git repo: top contributors,
language breakdown, and commit activity by month.

Computation functions are kept pure (plain data in, plain data out) and
separate from the `rich` rendering, same pattern as the rest of ghviz —
this is what makes them testable without needing a terminal at all.
"""

from __future__ import annotations

from collections import Counter

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ghviz.models.tree import CommitNode

console = Console()
BAR_CHAR = "█"


def compute_contributor_counts(nodes: list[CommitNode]) -> list[tuple[str, int]]:
    """Author -> commit count, sorted most active first."""
    counts = Counter(n.author for n in nodes)
    return counts.most_common()


def compute_commit_activity(nodes: list[CommitNode]) -> list[tuple[str, int]]:
    """'YYYY-MM' -> commit count, sorted chronologically (oldest first)."""
    months = Counter(n.date[:7] for n in nodes if n.date)
    return sorted(months.items())


def render_local_stats(repo_label: str, nodes: list[CommitNode], language_breakdown: dict[str, int]) -> None:
    total_commits = len(nodes)
    contributors = compute_contributor_counts(nodes)
    dates = sorted(n.date[:10] for n in nodes if n.date)
    first_commit = dates[0] if dates else "?"
    last_commit = dates[-1] if dates else "?"

    header = Panel(
        f"[bold]{repo_label}[/bold] (local)  •  "
        f"[cyan]{total_commits}[/cyan] commits  •  "
        f"[green]{len(contributors)}[/green] contributors  •  "
        f"[yellow]{first_commit}[/yellow] \u2192 [yellow]{last_commit}[/yellow]",
        title="Local Repo Stats",
        border_style="bright_blue",
    )
    console.print(header)

    if contributors:
        table = Table(title="Top Contributors")
        table.add_column("Author", style="cyan")
        table.add_column("Commits", justify="right", style="yellow")
        table.add_column("% of total", justify="right", style="green")
        for author, count in contributors[:10]:
            pct = (count / total_commits * 100) if total_commits else 0
            table.add_row(author, str(count), f"{pct:.1f}%")
        console.print(table)

    if language_breakdown:
        console.print(_render_bars(language_breakdown, title="Language Breakdown"))

    activity = compute_commit_activity(nodes)
    if activity:
        console.print(_render_activity_bars(activity))


def _render_bars(data: dict[str, int], title: str, max_width: int = 30, max_rows: int = 8) -> Panel:
    total = sum(data.values()) or 1
    sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)[:max_rows]

    lines = []
    for label, count in sorted_items:
        pct = count / total
        bar_len = max(1, int(pct * max_width))
        bar = Text(BAR_CHAR * bar_len, style="bold cyan")
        label_text = Text(f"{label:<12} ", style="white")
        pct_label = Text(f" {pct * 100:.1f}%", style="dim")
        lines.append(Text.assemble(label_text, bar, pct_label))

    return Panel(Group(*lines), title=title, border_style="bright_magenta")


def _render_activity_bars(activity: list[tuple[str, int]], max_rows: int = 12) -> Panel:
    recent = activity[-max_rows:]  # most recent N months, still chronological
    max_count = max((c for _, c in recent), default=1) or 1
    max_width = 30

    lines = []
    for month, count in recent:
        bar_len = max(1, int((count / max_count) * max_width))
        bar = Text(BAR_CHAR * bar_len, style="bold green")
        label_text = Text(f"{month}  ", style="white")
        count_label = Text(f" {count}", style="dim")
        lines.append(Text.assemble(label_text, bar, count_label))

    return Panel(Group(*lines), title="Commit Activity (by month)", border_style="bright_green")