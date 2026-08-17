# ghviz

A terminal CLI to visualize GitHub stats, repo file trees, and commit history graphs — right in your terminal, styled like `git log --graph`.

Works two ways:
- **Remote** — look up any public GitHub repo or user from anywhere, no clone required
- **Local** (`--local`) — read straight from your current directory's `.git`, with accurate HEAD/branch info and no API rate limits

## Install

```bash
pipx install ghviz
```

Don't have `pipx`? Install it first:
```bash
python3 -m pip install --user pipx
pipx ensurepath
```

## Usage

```bash
# GitHub (remote) mode
ghviz stats <username>
ghviz tree <owner/repo>
ghviz tree <owner/repo> --commits
ghviz tree <owner/repo> --commits --limit 200

# Local mode (run from inside a git repo)
ghviz stats --local
ghviz tree --local
ghviz tree --local --commits
```

## Setup

Remote mode needs a GitHub token to avoid the 60-requests/hour unauthenticated rate limit:

```bash
export GITHUB_TOKEN=your_token_here
```

Generate one at https://github.com/settings/tokens — no scopes needed for public data.

Local mode needs no setup at all — it just needs `git` installed and to be run inside a repo.

## Development

```bash
git clone https://github.com/pransh1/ghviz.git
cd ghviz
pip install -e ".[dev]"
pytest -v
```

## License

MIT