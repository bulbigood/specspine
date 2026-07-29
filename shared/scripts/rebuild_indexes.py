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

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from spec_contract import (
    FORMAT_MAJOR,
    INDEX_NAME,
    MANIFEST_NAME,
    PresentationError,
    presentation,
)


class IndexError(ValueError):
    pass


SUMMARY_RE = re.compile(r"^\*\*Summary:\*\*\s+(.+?)\s*$")
IDENTITY_RE = re.compile(
    r"^\*\*ID:\*\*\s+`[^`]+`\s+·\s+\*\*Kind:\*\*\s+`[^`]+`\s*$"
)


def document_summary(path: Path) -> str:
    """Read the required explicit summary of a specification document."""
    if path.suffix.casefold() != ".md":
        return ""
    lines = path.read_text(encoding="utf-8").splitlines()
    identity = next(
        (position for position, line in enumerate(lines) if IDENTITY_RE.fullmatch(line.strip())),
        None,
    )
    if identity is None:
        return ""
    cursor = identity + 1
    while cursor < len(lines) and (
        not lines[cursor].strip()
        or lines[cursor].startswith("**Aliases:**")
        or lines[cursor].strip().startswith("<!--")
    ):
        cursor += 1
    explicit = SUMMARY_RE.fullmatch(lines[cursor].strip()) if cursor < len(lines) else None
    if explicit:
        return explicit.group(1).strip()
    raise IndexError(f"{path}: missing single-line **Summary:** field after identity and aliases")


def load_manifest(root: Path) -> dict[str, Any]:
    path = root / MANIFEST_NAME
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise IndexError(f"cannot read {path}: {error}") from error
    if not isinstance(value, dict) or value.get("specspine") != FORMAT_MAJOR:
        raise IndexError(f"{path} is not a SpecSpine v3 manifest")
    try:
        presentation(value)
    except PresentationError as error:
        raise IndexError(f"invalid presentation profile: {error}") from error
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


def title_for(
    directory: Path,
    root: Path,
    project: str,
    index_text: dict[str, str],
) -> str:
    if directory == root:
        return index_text["root-title"].format(project=project)
    return directory.name.replace("-", " ").replace("_", " ").strip().title() or "Directory"


def render_index(
    root: Path,
    directory: Path,
    project: str,
    children: list[Path],
    index_text: dict[str, str],
) -> str:
    lines = [
        f"# {title_for(directory, root, project, index_text)}",
        "",
        f"**ID:** `{index_id(root, directory)}` · **Kind:** `index`",
        "",
    ]
    if directory == root:
        lines.extend(
            [
                index_text["purpose"],
                "",
                index_text["scope"],
                "",
                f"## {index_text['guide-heading']}",
                "",
                index_text["guide"],
                "",
                f"## {index_text['glossary-heading']}",
                "",
                index_text["glossary"],
                "",
            ]
        )
    lines.extend([f"## {index_text['contents-heading']}", ""])
    entries: list[tuple[str, str, str]] = []
    for path in sorted(directory.iterdir(), key=lambda item: item.name.casefold()):
        if path.name == INDEX_NAME or path.is_symlink():
            continue
        if path.is_file():
            entries.append((path.name, path.name, document_summary(path)))
        elif path.is_dir():
            child_index = path / INDEX_NAME
            if child_index.is_file() or path in children:
                entries.append((path.name + "/", f"{path.name}/{INDEX_NAME}", ""))
    if entries:
        lines.extend(
            f"- [{label}]({target})" + (f" — {summary}" if summary else "")
            for label, target, summary in entries
        )
    else:
        lines.append(f"- {index_text['empty']}")
    lines.append("")
    if directory == root and children:
        lines.extend([f"## {index_text['nested-heading']}", ""])
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
    index_text = presentation(manifest)["index"]
    changed: list[str] = []
    for directory in reversed(owned_directories(root)):
        path = directory / INDEX_NAME
        content = render_index(root, directory, project, children, index_text)
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
