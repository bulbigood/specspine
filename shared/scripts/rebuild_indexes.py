#!/usr/bin/env python3
"""Deterministically rebuild the physical navigation indexes of a SpecSpine."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


INDEX_NAME = "_INDEX.md"
MANIFEST_NAME = "specspine.json"


class IndexError(ValueError):
    pass


def load_manifest(root: Path) -> dict[str, Any]:
    path = root / MANIFEST_NAME
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise IndexError(f"cannot read {path}: {error}") from error
    if not isinstance(value, dict) or value.get("specspine") != 3:
        raise IndexError(f"{path} is not a SpecSpine v3 manifest")
    return value


def index_id(root: Path, directory: Path) -> str:
    if directory == root:
        return "project-architecture"
    relative = directory.relative_to(root).as_posix()
    slug = re.sub(r"[^a-z0-9]+", "-", relative.casefold()).strip("-") or "directory"
    digest = hashlib.sha256(relative.encode("utf-8")).hexdigest()[:8]
    return f"index-{slug[:48].rstrip('-')}-{digest}"


def is_spine_root(path: Path) -> bool:
    return (path / INDEX_NAME).is_file() and (path / MANIFEST_NAME).is_file()


def nested_roots(root: Path) -> list[Path]:
    result: list[Path] = []
    for current, directories, _ in os.walk(root):
        directory = Path(current)
        if directory != root and is_spine_root(directory):
            result.append(directory)
            directories[:] = []
    return sorted(result)


def owned_directories(root: Path) -> list[Path]:
    result: list[Path] = []
    for current, directories, _ in os.walk(root):
        directory = Path(current)
        if directory != root and is_spine_root(directory):
            directories[:] = []
            continue
        result.append(directory)
    return sorted(result)


def title_for(directory: Path, root: Path, project: str) -> str:
    if directory == root:
        return f"{project} architecture"
    return directory.name.replace("-", " ").replace("_", " ").strip().title() or "Directory"


def render_index(root: Path, directory: Path, project: str, children: list[Path]) -> str:
    lines = [
        f"# {title_for(directory, root, project)}",
        "",
        f"**ID:** `{index_id(root, directory)}` · **Kind:** `index`",
        "",
    ]
    if directory == root:
        lines.extend(
            [
                "SpecSpine is the project's long-lived, linked specification and "
                "architectural memory used to reconstruct contract-equivalent implementations.",
                "",
                "This directory contains the project's long-lived architectural intent and "
                "architecture-relevant repository observations.",
                "",
            ]
        )
    lines.extend(["## Contents", ""])
    entries: list[tuple[str, str]] = []
    for path in sorted(directory.iterdir(), key=lambda item: item.name.casefold()):
        if path.name == INDEX_NAME or path.is_symlink():
            continue
        if path.is_file():
            entries.append((path.name, path.name))
        elif path.is_dir():
            child_index = path / INDEX_NAME
            if child_index.is_file() or path in children:
                entries.append((path.name + "/", f"{path.name}/{INDEX_NAME}"))
    if entries:
        lines.extend(f"- [{label}]({target})" for label, target in entries)
    else:
        lines.append("- No indexed entries.")
    lines.append("")
    if directory == root and children:
        lines.extend(["## Nested SpecSpines", ""])
        for child in children:
            target = child.relative_to(root).as_posix() + f"/{INDEX_NAME}"
            lines.append(f"- [{child.relative_to(root).as_posix()}]({target})")
        lines.append("")
    return "\n".join(lines)


def rebuild(root: Path) -> dict[str, Any]:
    root = root.resolve()
    manifest = load_manifest(root)
    project = str(manifest.get("project", "")).strip()
    if not project:
        raise IndexError("manifest project must be nonempty")
    children = nested_roots(root)
    changed: list[str] = []
    for directory in reversed(owned_directories(root)):
        path = directory / INDEX_NAME
        content = render_index(root, directory, project, children)
        if not path.is_file() or path.read_text(encoding="utf-8") != content:
            path.write_text(content, encoding="utf-8")
            changed.append(path.relative_to(root).as_posix())
    return {"root": str(root), "changed": sorted(changed), "nested_roots": [
        path.relative_to(root).as_posix() for path in children
    ]}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("spine_root", type=Path)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        result = rebuild(args.spine_root)
    except (IndexError, OSError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
