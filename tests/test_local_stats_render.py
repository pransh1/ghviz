"""Tests for the local stats computation functions — kept pure (no rich, no
filesystem) so they're fast and simple to verify in isolation."""

from ghviz.models.tree import CommitNode
from ghviz.render.local_stats_render import compute_commit_activity, compute_contributor_counts


def make_commit(author: str, date: str) -> CommitNode:
    return CommitNode(
        sha="x", message="m", full_message="m", author=author, email="a@x.com",
        date=date, parents=[],
    )


def test_compute_contributor_counts_tallies_and_sorts_descending():
    nodes = [
        make_commit("Alice", "2026-01-01T00:00:00Z"),
        make_commit("Bob", "2026-01-02T00:00:00Z"),
        make_commit("Alice", "2026-01-03T00:00:00Z"),
        make_commit("Alice", "2026-01-04T00:00:00Z"),
    ]
    result = compute_contributor_counts(nodes)
    assert result == [("Alice", 3), ("Bob", 1)]


def test_compute_contributor_counts_empty_list():
    assert compute_contributor_counts([]) == []


def test_compute_commit_activity_groups_by_month_chronologically():
    nodes = [
        make_commit("A", "2026-03-05T00:00:00Z"),
        make_commit("A", "2026-01-10T00:00:00Z"),
        make_commit("A", "2026-01-20T00:00:00Z"),
        make_commit("A", "2026-02-01T00:00:00Z"),
    ]
    result = compute_commit_activity(nodes)
    # Two commits in Jan, one in Feb, one in Mar — sorted oldest month first
    assert result == [("2026-01", 2), ("2026-02", 1), ("2026-03", 1)]


def test_compute_commit_activity_ignores_commits_with_no_date():
    nodes = [make_commit("A", "")]
    assert compute_commit_activity(nodes) == []