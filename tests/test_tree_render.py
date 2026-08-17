"""Tests for the two file-tree builders: one for GitHub's flat tree API response,
one for a flat list of local `git ls-files` paths.
"""

from ghviz.render.tree_render import build_tree_from_github_paths, build_tree_from_paths


def test_build_tree_from_github_paths_nests_correctly():
    raw_tree = {
        "tree": [
            {"path": "src", "type": "tree"},
            {"path": "src/api", "type": "tree"},
            {"path": "src/api/client.py", "type": "blob"},
            {"path": "README.md", "type": "blob"},
        ]
    }

    root = build_tree_from_github_paths(raw_tree)

    # Root should have two children: the "src" dir and the "README.md" file
    child_names = {c.name for c in root.children}
    assert child_names == {"src", "README.md"}

    src_node = next(c for c in root.children if c.name == "src")
    assert src_node.is_dir is True

    api_node = next(c for c in src_node.children if c.name == "api")
    assert api_node.is_dir is True

    client_node = next(c for c in api_node.children if c.name == "client.py")
    assert client_node.is_dir is False


def test_build_tree_from_github_paths_empty_tree():
    root = build_tree_from_github_paths({"tree": []})
    assert root.children == []


def test_build_tree_from_paths_synthesizes_missing_directories():
    # Unlike GitHub's API, `git ls-files` gives us files only — no explicit
    # directory entries. The builder must create the intermediate dirs itself.
    paths = ["src/api/client.py", "src/api/server.py", "README.md"]

    root = build_tree_from_paths(paths)

    child_names = {c.name for c in root.children}
    assert child_names == {"src", "README.md"}

    src_node = next(c for c in root.children if c.name == "src")
    api_node = next(c for c in src_node.children if c.name == "api")
    file_names = {c.name for c in api_node.children}
    assert file_names == {"client.py", "server.py"}

    # api dir itself should be marked as a directory, not a file
    assert api_node.is_dir is True


def test_build_tree_from_paths_handles_flat_files_only():
    root = build_tree_from_paths(["a.py", "b.py"])
    assert {c.name for c in root.children} == {"a.py", "b.py"}
    assert all(not c.is_dir for c in root.children)