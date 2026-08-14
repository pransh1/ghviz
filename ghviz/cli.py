"""ghviz CLI entrypoint."""

from __future__ import annotations

import typer
from rich.console import Console

from ghviz.api.github_client import GitHubAPIError, GitHubClient, RateLimitError
from ghviz.models.stats import RepoSummary, UserStats
from ghviz.render.stats_render import render_user_stats
from ghviz.render.term_utils import real_terminal_width
from ghviz.render.tree_render import build_tree_from_github_paths, render_tree
from ghviz.render.commit_render import build_commit_graph, render_commit_graph
# from ghviz.render.commit_render import build_commit_graph
from ghviz.render.graph_render import render_git_log_style

app = typer.Typer(
    name="ghviz",
    help="Visualize GitHub stats and repo trees, right in your terminal.",
    add_completion=False,
)
console = Console(width=real_terminal_width())


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
    commits: bool = typer.Option(False, "--commits", help="Show commit history graph instead of file tree"),
    limit: int = typer.Option(100, help="Max commits to show (only with --commits)"),
):
    """Show a repo's file tree, or its commit history graph with --commits."""
    if "/" not in repo:
        console.print("[bold red]Error:[/bold red] repo must be in 'owner/name' format")
        raise typer.Exit(code=1)

    owner, repo_name = repo.split("/", 1)
    client = GitHubClient()
    try:
        if commits:
            with console.status(f"[bold cyan]Fetching commit history for {repo}..."):
                raw_commits = client.get_repo_commits(owner, repo_name, max_total=limit)
                raw_branches = client.get_repo_branches(owner, repo_name)
                repo_info = client.get_repo(owner, repo_name)

            commit_nodes = build_commit_graph(raw_commits)

            refs: dict[str, list[str]] = {}
            for b in raw_branches:
                sha = b.get("commit", {}).get("sha")
                if sha:
                    refs.setdefault(sha, []).append(b["name"])

            default_branch = repo_info.get("default_branch")

            # console.print(render_git_log_style(commit_nodes, limit=limit, refs=refs, default_branch=default_branch))
            output = render_git_log_style(commit_nodes, limit=limit, refs=refs, default_branch=default_branch)
            console.print(output, soft_wrap=True)
            return

        with console.status(f"[bold cyan]Fetching tree for {repo}..."):
            raw_tree = client.get_repo_tree(owner, repo_name, branch=branch)

        root_node = build_tree_from_github_paths(raw_tree)
        rich_tree = render_tree(root_node, label=f"[bold cyan]{repo}[/bold cyan]")
        console.print(rich_tree, soft_wrap=True)
        # if console.is_terminal:
        #     with console.pager(styles=True):
        #         console.print(rich_tree)
        # else:
        #     console.print(rich_tree)

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
