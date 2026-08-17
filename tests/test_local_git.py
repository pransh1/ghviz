"""Integration tests for local_git.py — these create a REAL temp git repo and
run actual `git` commands against it, rather than mocking subprocess. This is
worth the slower test because the whole point of this module is correctly
parsing real git output.
"""

import subprocess

import pytest

from ghviz.api.local_git import LocalGitError, get_local_commits, get_local_tracked_files, is_git_repo


def run(args: list[str], cwd: str) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    """A small real git repo: one commit on main, a feature branch, then a merge."""
    path = str(tmp_path)
    run(["git", "init", "-q", "-b", "main"], cwd=path)
    run(["git", "config", "user.email", "test@example.com"], cwd=path)
    run(["git", "config", "user.name", "Test User"], cwd=path)

    (tmp_path / "README.md").write_text("hello\n")
    run(["git", "add", "-A"], cwd=path)
    run(["git", "commit", "-q", "-m", "initial commit"], cwd=path)

    run(["git", "checkout", "-q", "-b", "feat/thing"], cwd=path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "client.py").write_text("print(1)\n")
    run(["git", "add", "-A"], cwd=path)
    run(["git", "commit", "-q", "-m", "feat: add client"], cwd=path)

    run(["git", "checkout", "-q", "main"], cwd=path)
    run(["git", "merge", "--no-ff", "-q", "feat/thing", "-m", "Merge branch 'feat/thing'"], cwd=path)

    return path


def test_is_git_repo_true_for_real_repo(repo):
    assert is_git_repo(repo) is True


def test_is_git_repo_false_for_non_repo(tmp_path):
    assert is_git_repo(str(tmp_path)) is False


def test_get_local_commits_returns_all_three_commits(repo):
    nodes = get_local_commits(repo)
    assert len(nodes) == 3
    messages = {n.message for n in nodes}
    assert messages == {"initial commit", "feat: add client", "Merge branch 'feat/thing'"}


def test_get_local_commits_merge_has_two_parents(repo):
    nodes = get_local_commits(repo)
    merge_node = next(n for n in nodes if n.message.startswith("Merge"))
    assert len(merge_node.parents) == 2


def test_get_local_commits_head_decoration_present(repo):
    nodes = get_local_commits(repo)
    merge_node = next(n for n in nodes if n.message.startswith("Merge"))
    assert "HEAD -> main" in merge_node.decoration


def test_get_local_commits_respects_limit(repo):
    nodes = get_local_commits(repo, limit=1)
    assert len(nodes) == 1


def test_get_local_tracked_files_lists_all_files(repo):
    files = get_local_tracked_files(repo)
    assert set(files) == {"README.md", "src/client.py"}


def test_get_local_commits_raises_on_non_repo(tmp_path):
    with pytest.raises(LocalGitError):
        get_local_commits(str(tmp_path))