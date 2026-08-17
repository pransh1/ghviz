"""Multi-lane commit graph renderer — mirrors real `git log --graph` output.

Core idea: each active branch owns a lane (a vertical column) tracked by
"which commit sha is this column waiting to see next." As we walk commits
newest -> oldest:
  - a commit with no lane waiting for it starts a NEW lane (a branch tip)
  - a merge commit (2+ parents) OPENS an extra lane for each extra parent —
    drawn as a "\" branching off on the row right after the merge commit
  - when a lane's next expected commit turns out to already be owned by
    another lane, the lanes CONVERGE — drawn as a "/" joining in, and the
    duplicate lane is freed immediately (eager collapse), just like git does
"""

from __future__ import annotations

from datetime import datetime

from rich.console import Console, Group
from rich.text import Text

from ghviz.models.tree import CommitNode

console = Console()

LANE_COLORS = [
    "bright_cyan",
    "bright_magenta",
    "bright_yellow",
    "bright_green",
    "bright_blue",
    "bright_red",
    "orange3",
    "purple",
]

DOT = "●"
MERGE_DOT = "◆"
VLINE = "│"
BRANCH_OPEN = "\\"
BRANCH_CLOSE = "/"


class Lane:
    """A single branch column: the commit sha it's waiting for, and its color."""

    def __init__(self, sha: str, color: str):
        self.sha = sha
        self.color = color


def _next_color(used_count: int) -> str:
    return LANE_COLORS[used_count % len(LANE_COLORS)]


class CommitRow:
    """Everything the renderer needs to draw one commit's full block."""

    def __init__(self, node: CommitNode, lane_idx: int, header_snapshot: list):
        self.node = node
        self.lane_idx = lane_idx
        self.header_snapshot = header_snapshot  # columns at the "* commit ..." line
        self.open_transition: tuple[list, tuple[str, int]] | None = None  # (snapshot, (symbol, col))
        self.close_transition: tuple[list, tuple[str, int]] | None = None
        self.detail_snapshot: list = []  # columns for all plain continuation lines


def build_lane_rows(nodes: list[CommitNode]) -> list[CommitRow]:
    """Walk commits newest -> oldest, assigning lanes and recording transitions."""
    lanes: list[Lane | None] = []
    color_count = 0
    rows: list[CommitRow] = []

    for node in nodes:
        # Does an existing lane already expect this commit next?
        lane_idx = next((i for i, l in enumerate(lanes) if l is not None and l.sha == node.sha), None)

        if lane_idx is None:
            # New branch tip — allocate a fresh lane + color
            color = _next_color(color_count)
            color_count += 1
            lane_idx = next((i for i, l in enumerate(lanes) if l is None), len(lanes))
            if lane_idx == len(lanes):
                lanes.append(Lane(node.sha, color))
            else:
                lanes[lane_idx] = Lane(node.sha, color)

        # Any OTHER lane also waiting for this same sha converges into this commit right now
        for i, l in enumerate(lanes):
            if i != lane_idx and l is not None and l.sha == node.sha:
                lanes[i] = None

        header_snapshot = list(lanes)
        row = CommitRow(node, lane_idx, header_snapshot)
        color = lanes[lane_idx].color

        if not node.parents:
            lanes[lane_idx] = None  # root commit — this lane simply ends, no special symbol needed
        else:
            lanes[lane_idx] = Lane(node.parents[0], color)

            # Eager collapse: does another lane already expect this same parent sha?
            dup_idx = next(
                (i for i, l in enumerate(lanes) if i != lane_idx and l is not None and l.sha == node.parents[0]),
                None,
            )
            if dup_idx is not None:
                survivor, loser = sorted((lane_idx, dup_idx))
                row.close_transition = (list(lanes), (BRANCH_CLOSE, loser))
                lanes[loser] = None

            # Extra parents (merge sources) each open a new lane
            for parent_sha in node.parents[1:]:
                if any(l is not None and l.sha == parent_sha for l in lanes):
                    continue
                new_color = _next_color(color_count)
                color_count += 1
                slot = next((i for i, l in enumerate(lanes) if l is None), len(lanes))
                if slot == len(lanes):
                    lanes.append(Lane(parent_sha, new_color))
                else:
                    lanes[slot] = Lane(parent_sha, new_color)
                row.open_transition = (list(lanes), (BRANCH_OPEN, slot))

        row.detail_snapshot = list(lanes)
        rows.append(row)

    return rows


def _trim(snapshot: list) -> list:
    """Drop trailing empty columns so short rows don't trail dead space."""
    snap = list(snapshot)
    while snap and snap[-1] is None:
        snap.pop()
    return snap


def _prefix(snapshot: list, dot_col: int | None = None, dot_symbol: str = DOT,
            override_col: int | None = None, override_symbol: str = "") -> Text:
    """Build one colored '| | |' style column prefix."""
    snap = _trim(snapshot)
    text = Text()
    for i, lane in enumerate(snap):
        if i == dot_col:
            color = snap[i].color if snap[i] else "white"
            text.append(f"{dot_symbol} ", style=f"bold {color}")
        elif i == override_col:
            color = lane.color if lane else "white"
            text.append(f"{override_symbol} ", style=f"bold {color}")
        elif lane is not None:
            text.append(f"{VLINE} ", style=lane.color)
        else:
            text.append("  ")
    return text


# def _format_git_date(iso_date: str) -> str:
#     if not iso_date:
#         return ""
#     try:
#         dt = datetime.strptime(iso_date, "%Y-%m-%dT%H:%M:%SZ")
#         return dt.strftime("%a %b %d %H:%M:%S %Y +0000")
#     except ValueError:
#         return iso_date

def _format_git_date(iso_date: str) -> str:
    if not iso_date:
        return ""
    try:
        normalized = iso_date.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        return dt.strftime("%a %b %d %H:%M:%S %Y %z")
    except ValueError:
        return iso_date
    

def _parse_local_decoration(decoration: str) -> list[tuple[str, str]]:
    """Parse git's raw `%D` ref string (e.g. 'HEAD -> main, origin/main, tag: v1.0')
    into (label, style) pairs, matching git's own real coloring convention."""
    if not decoration:
        return []
    parts = [p.strip() for p in decoration.split(",") if p.strip()]
    result = []
    for p in parts:
        if p.startswith("HEAD -> "):
            result.append((p, "bold green"))
        elif p == "HEAD":
            result.append((p, "bold cyan"))
        elif p.startswith("tag: "):
            result.append((p, "bold yellow"))
        elif "/" in p:
            result.append((p, "bold red"))  # remote-tracking branch
        else:
            result.append((p, "bold green"))  # other local branch
    return result


def render_git_log_style(
    nodes: list[CommitNode],
    limit: int = 30,
    refs: dict[str, list[str]] | None = None,
    default_branch: str | None = None,
) -> Group:
    """Render commits as detailed multi-line blocks, matching `git log --graph` output:
    commit header (with branch decorations), Merge: line (for merges), Author, Date,
    blank, full message, blank.
    """
    refs = refs or {}
    rows = build_lane_rows(nodes[:limit])
    lines: list[Text] = []

    for row in rows:
        node = row.node
        is_merge = len(node.parents) > 1
        symbol = MERGE_DOT if is_merge else DOT

        # --- Header line: "* commit <full sha> (branch, branch, ...)" ---
        header = _prefix(row.header_snapshot, dot_col=row.lane_idx, dot_symbol=symbol)
        header.append("commit ", style="bold yellow")
        header.append(node.sha, style="bold yellow")

        branch_names = refs.get(node.sha, [])
        decorated: list[tuple[str, str]] = []
        if node.decoration:
            decorated = _parse_local_decoration(node.decoration)
        elif branch_names:
            if default_branch in branch_names:
                decorated.append(("origin/HEAD", "bold cyan"))
            for name in branch_names:
                decorated.append((f"origin/{name}", "bold red"))

        if decorated:
            header.append(" (", style="white")
            for i, (label, style) in enumerate(decorated):
                if i > 0:
                    header.append(", ", style="white")
                header.append(label, style=style)
            header.append(")", style="white")
        lines.append(header)

        # Queue of (snapshot, override) pairs for the first N continuation lines —
        # this is what draws the "\" branch-open and "/" branch-close transition rows.
        special = []
        if row.open_transition:
            special.append(row.open_transition)
        if row.close_transition:
            special.append(row.close_transition)

        def next_prefix():
            if special:
                snap, (sym, col) = special.pop(0)
                return _prefix(snap, override_col=col, override_symbol=sym)
            return _prefix(row.detail_snapshot)

        if is_merge:
            merge_line = next_prefix()
            merge_line.append("Merge: ", style="bold")
            merge_line.append(" ".join(p[:7] for p in node.parents), style="white")
            lines.append(merge_line)

        author_line = next_prefix()
        author_display = f"{node.author} <{node.email}>" if node.email else node.author
        author_line.append("Author: ", style="bold")
        author_line.append(author_display, style="white")
        lines.append(author_line)

        date_line = next_prefix()
        date_line.append("Date:   ", style="bold")
        date_line.append(_format_git_date(node.date), style="white")
        lines.append(date_line)

        lines.append(next_prefix())  # blank connector line before the message

        message_lines = (
            node.full_message.split("\n") if node.full_message else [node.message]
        )
        for msg_line in message_lines:
            body = next_prefix()
            if msg_line:
                body.append(f"    {msg_line}", style="white")
            lines.append(body)

        lines.append(next_prefix())  # blank separator between commits

    if len(nodes) > limit:
        lines.append(
            Text(f"... {len(nodes) - limit} more commits not shown", style="dim italic")
        )

    return Group(*lines)
