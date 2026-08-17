"""Tests for converting GitHub's raw commit API response into CommitNode objects."""

from ghviz.render.commit_render import build_commit_graph


def test_build_commit_graph_parses_basic_fields():
    raw_commits = [
        {
            "sha": "abc123",
            "commit": {
                "message": "Fix the bug\n\nLonger explanation here.",
                "author": {"name": "Jane Doe", "email": "jane@example.com", "date": "2026-08-14T10:00:00Z"},
            },
            "parents": [{"sha": "parent1"}],
        }
    ]

    nodes = build_commit_graph(raw_commits)

    assert len(nodes) == 1
    node = nodes[0]
    assert node.sha == "abc123"
    assert node.message == "Fix the bug"  # first line only
    assert node.full_message == "Fix the bug\n\nLonger explanation here."
    assert node.author == "Jane Doe"
    assert node.email == "jane@example.com"
    assert node.parents == ["parent1"]


def test_build_commit_graph_handles_merge_commit_multiple_parents():
    raw_commits = [
        {
            "sha": "merge_sha",
            "commit": {"message": "Merge branch", "author": {"name": "A", "email": "a@x.com", "date": "2026-01-01T00:00:00Z"}},
            "parents": [{"sha": "p1"}, {"sha": "p2"}],
        }
    ]
    nodes = build_commit_graph(raw_commits)
    assert nodes[0].parents == ["p1", "p2"]


def test_build_commit_graph_handles_missing_author_gracefully():
    raw_commits = [
        {
            "sha": "sha1",
            "commit": {"message": "no author info"},
            "parents": [],
        }
    ]
    nodes = build_commit_graph(raw_commits)
    assert nodes[0].author == "unknown"
    assert nodes[0].email == ""
    assert nodes[0].parents == []


def test_build_commit_graph_empty_list():
    assert build_commit_graph([]) == []