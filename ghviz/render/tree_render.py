"""Renders a repo's file structure as a terminal tree using `rich`."""

from __future__ import annotations

from rich.tree import Tree

from ghviz.models.tree import TreeNode


def build_tree_from_github_paths(raw_tree: dict) -> TreeNode:
    """Convert GitHub's flat git-tree API response into a nested TreeNode structure.

    GitHub returns a flat list of {path, type} entries like:
        {"path": "src/api/client.py", "type": "blob"}
        {"path": "src/api", "type": "tree"}
    We rebuild the nested structure from those flat paths.
    """
    root = TreeNode(name="/", path="", is_dir=True)
    nodes: dict[str, TreeNode] = {"": root}

    entries = raw_tree.get("tree", [])
    # Sort so parent directories are created before their children
    entries = sorted(entries, key=lambda e: e["path"].count("/"))

    for entry in entries:
        path = entry["path"]
        is_dir = entry["type"] == "tree"
        parts = path.split("/")
        parent_path = "/".join(parts[:-1])
        name = parts[-1]

        node = TreeNode(name=name, path=path, is_dir=is_dir)
        nodes[path] = node

        parent = nodes.get(parent_path, root)
        parent.children.append(node)

    return root

def build_tree_from_paths(paths: list[str]) -> TreeNode:
    """Build a nested TreeNode structure from a flat list of file paths
    (e.g. from `git ls-files`), synthesizing intermediate directory nodes
    as needed — unlike GitHub's API, `git ls-files` gives us files only.
    """
    root = TreeNode(name="/", path="", is_dir=True)
    nodes: dict[str, TreeNode] = {"": root}

    for path in sorted(paths):
        parts = path.split("/")
        current_path = ""
        parent = root
        for i, part in enumerate(parts):
            current_path = f"{current_path}/{part}" if current_path else part
            is_last = i == len(parts) - 1
            if current_path not in nodes:
                node = TreeNode(name=part, path=current_path, is_dir=not is_last)
                nodes[current_path] = node
                parent.children.append(node)
            parent = nodes[current_path]

    return root


def render_tree(node: TreeNode, label: str | None = None) -> Tree:
    """Recursively build a rich.Tree for terminal rendering."""
    display_label = label or f"[bold cyan]{node.name}[/bold cyan]"
    tree = Tree(display_label)
    _add_children(tree, node)
    return tree


def _add_children(rich_tree: Tree, node: TreeNode) -> None:
    # Directories first, then files, both alphabetically — reads more naturally
    dirs = sorted([c for c in node.children if c.is_dir], key=lambda n: n.name.lower())
    files = sorted([c for c in node.children if not c.is_dir], key=lambda n: n.name.lower())

    for d in dirs:
        branch = rich_tree.add(f"[bold blue]{d.name}/[/bold blue]")
        _add_children(branch, d)

    for f in files:
        rich_tree.add(f"[white]{f.name}[/white]")
