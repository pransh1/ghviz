# ghviz

A terminal CLI to visualize GitHub stats and repo file trees — right in your terminal.

## Install

```bash
pipx install ghviz   # coming soon (not yet published)
```

For now, install from source:

```bash
git clone https://github.com/<your-username>/ghviz.git
cd ghviz
pip install -e .
```

## Usage

```bash
ghviz stats <username>        # user stats: repos, followers, top repos, languages
ghviz tree <owner/repo>       # visualize a repo's file tree
ghviz tree <owner/repo> --branch main
```

## Setup

GitHub's unauthenticated API is capped at 60 requests/hour. Set a personal access token
to raise that limit:

```bash
export GITHUB_TOKEN=your_token_here
```

## Roadmap

- [ ] Commit/branch tree visual (`ghviz tree --commits`)
- [ ] Contribution heatmap
- [ ] Publish to PyPI + pipx
- [ ] Homebrew tap
- [ ] Port to Go for single-binary distribution

## License

MIT
