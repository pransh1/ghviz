"""Renders user/repo stats as terminal tables and bar-style charts using `rich`."""

from __future__ import annotations

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ghviz.models.stats import UserStats

console = Console()

# Simple block characters for terminal bar charts (no graphics needed)
BAR_CHAR = "█"


def render_user_stats(stats: UserStats) -> None:
    header = Panel(
        f"[bold]{stats.username}[/bold]  •  "
        f"[cyan]{stats.public_repos}[/cyan] repos  •  "
        f"[green]{stats.followers}[/green] followers  •  "
        f"[yellow]{stats.following}[/yellow] following",
        title="GitHub Stats",
        border_style="bright_blue",
    )
    console.print(header)

    if stats.top_repos:
        table = Table(title="Top Repos", show_lines=False)
        table.add_column("Repo", style="cyan")
        table.add_column("Stars", justify="right", style="yellow")
        table.add_column("Forks", justify="right", style="green")
        table.add_column("Language", style="magenta")
        for repo in stats.top_repos:
            table.add_row(repo.name, str(repo.stars), str(repo.forks), repo.language or "-")
        console.print(table)

    if stats.language_breakdown:
        console.print(render_language_bars(stats.language_breakdown))


def render_language_bars(language_breakdown: dict[str, int], max_width: int = 30) -> Panel:
    total = sum(language_breakdown.values()) or 1
    sorted_langs = sorted(language_breakdown.items(), key=lambda x: x[1], reverse=True)[:8]

    lines = []
    for lang, count in sorted_langs:
        pct = count / total
        bar_len = max(1, int(pct * max_width))
        bar = Text(BAR_CHAR * bar_len, style="bold cyan")
        label = Text(f"{lang:<12} ", style="white")
        pct_label = Text(f" {pct * 100:.1f}%", style="dim")
        line = Text.assemble(label, bar, pct_label)
        lines.append(line)

    return Panel(Group(*lines), title="Language Breakdown", border_style="bright_magenta")
