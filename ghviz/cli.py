"""ghviz CLI entrypoint."""

from __future__ import annotations

import typer
from rich.console import Console

from ghviz.api.github_client import GitHubAPIError, GitHubClient, RateLimitError
from ghviz.models.stats import RepoSummary, UserStats
from ghviz.render.stats_render import render_user_stats
from ghviz.render.tree_render import build_tree_from_github_paths, render_tree

app = typer.Typer(
    name="ghviz",
    help="Visualize GitHub stats and repo trees, right in your terminal.",
    add_completion=False,
)
console = Console()


@app.command()
def stats(username: str = typer.Argument(..., help="GitHub username to fetch stats for")):
    """Show GitHub stats for a user: repo count, followers, top repos, language breakdown."""
    client = GitHubClient()
    try:
        with console.status(f"[bold cyan]Fetching stats for {username}..."):
            user_data = client.get_user(username)
            repos_data = client.get_user_repos(username)

        top_repos_sorted = sorted(repos_data, key=lambda r: r.get("stargazers_count", 0), reverse=True)[:5]
        top_repos = [
            RepoSummary(
                name=r["name"],
                stars=r.get("stargazers_count", 0),
                forks=r.get("forks_count", 0),
                language=r.get("language"),
                updated_at=r.get("updated_at", ""),
            )
            for r in top_repos_sorted
        ]

        language_breakdown: dict[str, int] = {}
        for r in repos_data:
            lang = r.get("language")
            if lang:
                language_breakdown[lang] = language_breakdown.get(lang, 0) + 1

        user_stats = UserStats(
            username=user_data.get("login", username),
            public_repos=user_data.get("public_repos", 0),
            followers=user_data.get("followers", 0),
            following=user_data.get("following", 0),
            top_repos=top_repos,
            language_breakdown=language_breakdown,
        )

        render_user_stats(user_stats)

    except RateLimitError as e:
        console.print(f"[bold red]Rate limit hit:[/bold red] {e}")
        raise typer.Exit(code=1)
    except GitHubAPIError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)
    finally:
        client.close()


@app.command()
def tree(
    repo: str = typer.Argument(..., help="Repo in owner/name format, e.g. torvalds/linux"),
    branch: str = typer.Option("HEAD", help="Branch to visualize"),
):
    """Show a repo's file tree as an interactive-style terminal tree."""
    if "/" not in repo:
        console.print("[bold red]Error:[/bold red] repo must be in 'owner/name' format")
        raise typer.Exit(code=1)

    owner, repo_name = repo.split("/", 1)
    client = GitHubClient()
    try:
        with console.status(f"[bold cyan]Fetching tree for {repo}..."):
            raw_tree = client.get_repo_tree(owner, repo_name, branch=branch)

        root_node = build_tree_from_github_paths(raw_tree)
        rich_tree = render_tree(root_node, label=f"[bold cyan]{repo}[/bold cyan]")
        console.print(rich_tree)

    except RateLimitError as e:
        console.print(f"[bold red]Rate limit hit:[/bold red] {e}")
        raise typer.Exit(code=1)
    except GitHubAPIError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)
    finally:
        client.close()


if __name__ == "__main__":
    app()
