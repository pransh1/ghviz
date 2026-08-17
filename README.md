# ghviz

A terminal CLI to visualize GitHub stats, repo file trees, and commit history graphs — right in your terminal, styled like `git log --graph`.

## Features
 
- **`ghviz stats`** — repo count, followers, top repos, language breakdown for any GitHub user
- **`ghviz tree`** — a repo's file structure as a colored, nested terminal tree
- **`ghviz tree --commits`** — a full multi-lane commit graph, matching `git log --graph`'s output: branch colors, merge/split lines, author, date, and full commit messages
- **Two data sources, one interface:**
  - **Remote (default)** — look up *any* public GitHub repo or user from anywhere, no clone required
  - **Local (`--local`)** — read straight from your current directory's `.git`, giving you accurate `HEAD`/branch info and zero API rate limits


## Install

Works identically on macOS, Linux, and Windows:
 
```bash
pipx install ghviz
```

**Don't have `pipx`?**
 
macOS / Linux:
```bash
python3 -m pip install --user pipx
pipx ensurepath
```
 
Windows (PowerShell or Command Prompt):
```powershell
py -m pip install --user pipx
py -m pipx ensurepath
```
Close and reopen your terminal afterward — PATH changes only take effect in a fresh window on Windows.

## Usage

### GitHub (remote) mode — works from anywhere
 
```bash
ghviz stats <username>
ghviz tree <owner/repo>
ghviz tree <owner/repo> --branch develop
ghviz tree <owner/repo> --commits
ghviz tree <owner/repo> --commits --limit 200
```
 
### Local mode — run from inside a git repo
 
```bash
ghviz stats --local
ghviz tree --local
ghviz tree --local --commits
```

### All options
 
| Command | Option | Description |
|---|---|---|
| `stats` | `<username>` | GitHub username (omit when using `--local`) |
| `stats` | `--local` | Show stats for the local repo in the current directory |
| `tree` | `<owner/repo>` | Repo to look up (omit when using `--local`) |
| `tree` | `--branch` | Branch to visualize (remote mode only, default `HEAD`) |
| `tree` | `--commits` | Show the commit history graph instead of the file tree |
| `tree` | `--limit` | Max commits to show with `--commits` (default `100`) |
| `tree` | `--local` | Read the local `.git` repo instead of GitHub |


## Setup

Remote mode needs a GitHub token to avoid the 60-requests/hour unauthenticated rate limit:

```bash
export GITHUB_TOKEN=your_token_here
```

Generate one at [github.com/settings/tokens](https://github.com/settings/tokens) — no scopes needed for public data. Add the `export` line to your shell profile (`~/.bashrc`, `~/.zshrc`) to make it permanent.
 
Local mode needs no setup at all beyond having `git` itself installed and being run from inside a repo. Linux usually has this already; on Windows, install [Git for Windows](https://git-scm.com/download/win) if you don't.

## Development

```bash
git clone https://github.com/pransh1/ghviz.git
cd ghviz
pip install -e ".[dev]"
pytest -v
```

## Contributing
 
Issues and PRs welcome. If you're adding a feature, a test alongside it goes a long way — see `tests/` for the existing patterns.
 
## License
 
MIT — see [LICENSE](LICENSE).