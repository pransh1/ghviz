"""Tests for the multi-lane commit graph algorithm — the trickiest piece of ghviz.

These tests check the LOGIC (which lane each commit lands in, when lanes open
and close) rather than the rendered text, since that's what's actually easy to
break silently while refactoring.
"""

from ghviz.models.tree import CommitNode
from ghviz.render.graph_render import (
    _format_git_date,
    _parse_local_decoration,
    build_lane_rows,
    render_git_log_style,
)


def make_commit(sha: str, parents: list[str], message: str = "msg") -> CommitNode:
    return CommitNode(
        sha=sha, message=message, full_message=message,
        author="Test", email="test@example.com", date="2026-08-14T10:00:00Z",
        parents=parents,
    )


def test_linear_history_stays_in_single_lane():
    # A -> B -> C, no merges: every commit should land in lane 0
    nodes = [
        make_commit("c3", ["c2"]),
        make_commit("c2", ["c1"]),
        make_commit("c1", []),
    ]
    rows = build_lane_rows(nodes)
    assert [row.lane_idx for row in rows] == [0, 0, 0]


def test_root_commit_has_no_parents_and_ends_its_lane():
    nodes = [make_commit("c1", [])]
    rows = build_lane_rows(nodes)
    assert rows[0].detail_snapshot[rows[0].lane_idx] is None


def test_merge_commit_opens_a_second_lane():
    # merge has two parents -> should record an open_transition
    nodes = [
        make_commit("merge", ["p1", "p2"]),  # merge commit, parents not in our node list (fine)
    ]
    rows = build_lane_rows(nodes)
    assert rows[0].open_transition is not None
    _, (symbol, _col) = rows[0].open_transition
    assert symbol == "\\"


def test_diverging_and_reconverging_branches_close_correctly():
    # merge -> (p1 continues mainline, p2 is a second parent branch)
    # p2's own commit then points back to the same sha p1 is waiting for -> should collapse
    nodes = [
        make_commit("merge", ["base", "feature_tip"]),
        make_commit("feature_tip", ["base"]),
        make_commit("base", []),
    ]
    rows = build_lane_rows(nodes)

    merge_row, feature_row, base_row = rows

    # merge commit opens a second lane
    assert merge_row.open_transition is not None

    # feature_tip's own advance collides with the lane already waiting for "base" -> closes
    assert feature_row.close_transition is not None

    # by the time we reach "base", only one lane should still be active
    active_lanes = [l for l in base_row.header_snapshot if l is not None]
    assert len(active_lanes) == 1


def test_render_git_log_style_includes_merge_marker():
    nodes = [
        make_commit("merge", ["p1", "p2"], message="Merge things"),
        make_commit("p1", [], message="first parent"),
        make_commit("p2", [], message="second parent"),
    ]
    group = render_git_log_style(nodes)
    rendered_text = "\n".join(t.plain for t in group.renderables)
    assert "Merge:" in rendered_text
    assert "Merge things" in rendered_text


class TestParseLocalDecoration:
    def test_head_pointing_at_branch(self):
        result = _parse_local_decoration("HEAD -> main, origin/main")
        labels = [label for label, _style in result]
        assert "HEAD -> main" in labels
        assert "origin/main" in labels

    def test_detached_head(self):
        result = _parse_local_decoration("HEAD")
        assert result == [("HEAD", "bold cyan")]

    def test_tag(self):
        result = _parse_local_decoration("tag: v1.0")
        assert result == [("tag: v1.0", "bold yellow")]

    def test_empty_string_returns_empty_list(self):
        assert _parse_local_decoration("") == []


class TestFormatGitDate:
    def test_github_style_z_suffix(self):
        result = _format_git_date("2026-08-14T10:00:00Z")
        assert "2026" in result
        assert "Aug" in result

    def test_local_git_style_offset(self):
        result = _format_git_date("2026-08-14T10:00:00+05:30")
        assert "2026" in result

    def test_empty_string(self):
        assert _format_git_date("") == ""

    def test_garbage_input_falls_back_to_raw_string(self):
        assert _format_git_date("not-a-date") == "not-a-date"