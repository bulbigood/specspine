#!/usr/bin/env python3
"""Discover, rebuild, and mechanically check all SpecSpines in a workspace."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any


INDEX_NAME = "_INDEX.md"
MANIFEST_NAME = "specspine.json"
README_NAME = "README.md"
STATE_PATH = Path(".specspine/workspace-index.json")
PRUNED_NAMES = {".git", ".hg", ".svn", "node_modules", "__pycache__"}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SCRIPT_ROOT = Path(__file__).resolve().parent
CHECKER = load_module("specspine_workspace_checker", SCRIPT_ROOT / "check_spine.py")
INDEXER = load_module("specspine_workspace_indexer", SCRIPT_ROOT / "rebuild_indexes.py")


def discover(workspace: Path) -> list[Path]:
    workspace = workspace.resolve()
    roots: list[Path] = []
    state_root = (workspace / ".specspine").resolve()
    for current, directories, files in os.walk(workspace):
        directory = Path(current)
        directories[:] = [
            name
            for name in directories
            if name not in PRUNED_NAMES
            and (directory / name).resolve() != state_root
        ]
        if INDEX_NAME in files and MANIFEST_NAME in files and README_NAME in files:
            roots.append(directory.resolve())
    return sorted(set(roots))


def graph(workspace: Path, roots: list[Path]) -> dict[str, Any]:
    workspace = workspace.resolve()
    root_set = set(roots)
    rows: list[dict[str, str | None]] = []
    for root in roots:
        parent = next(
            (
                candidate
                for candidate in sorted(root.parents, key=lambda path: len(path.parts), reverse=True)
                if candidate in root_set
            ),
            None,
        )
        rows.append(
            {
                "root": root.relative_to(workspace).as_posix() or ".",
                "index": (root / INDEX_NAME).relative_to(workspace).as_posix(),
                "parent": (
                    parent.relative_to(workspace).as_posix() or "."
                    if parent is not None
                    else None
                ),
            }
        )
    return {"specspine": 4, "workspace": str(workspace), "roots": rows}


def write_graph(workspace: Path, value: dict[str, Any]) -> bool:
    path = workspace / STATE_PATH
    content = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if path.is_file() and path.read_text(encoding="utf-8") == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    roots = discover(workspace)
    rebuilt: list[str] = []
    if args.rebuild:
        for root in reversed(roots):
            result = INDEXER.rebuild(root)
            rebuilt.extend(f"{root.relative_to(workspace)}/{path}" for path in result["changed"])
        roots = discover(workspace)
    expected = graph(workspace, roots)
    graph_path = workspace / STATE_PATH
    graph_current = None
    if graph_path.is_file():
        try:
            graph_current = json.loads(graph_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            pass
    graph_changed = write_graph(workspace, expected) if args.rebuild else graph_current != expected
    findings = {
        str(root.relative_to(workspace)): [
            item.__dict__ for item in CHECKER.check(root)
        ]
        for root in roots
    }
    result = {
        "roots": [str(root.relative_to(workspace)) for root in roots],
        "graph": str(STATE_PATH),
        "graph_changed": graph_changed,
        "rebuilt": sorted(rebuilt),
        "findings": findings,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False))
    has_errors = any(
        item["severity"] == "error"
        for rows in findings.values()
        for item in rows
    )
    return 1 if has_errors or (graph_changed and not args.rebuild) else 0


if __name__ == "__main__":
    raise SystemExit(main())
