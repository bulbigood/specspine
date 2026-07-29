#!/usr/bin/env python3
"""Idempotently create a SpecSpine v3 root pair without overwriting files."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


class BootstrapError(ValueError):
    pass


INDEX_IDENTITY = re.compile(
    r"^\*\*ID:\*\*\s+`project-architecture`\s+·\s+\*\*Kind:\*\*\s+`index`\s*$",
    re.MULTILINE,
)


def read_index(path: Path) -> str:
    try:
        value = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise BootstrapError(f"cannot read rendered index {path}: {error}") from error
    if not value.strip() or INDEX_IDENTITY.search(value) is None:
        raise BootstrapError(
            "rendered index must be nonempty and identify project-architecture "
            "as an index"
        )
    return value if value.endswith("\n") else value + "\n"


def manifest(project: str) -> dict[str, Any]:
    return {
        "specspine": 3,
        "project": project,
        "implementation_freedom": "contract-equivalent",
        "areas": [],
        "assets": [],
    }


def exclusive_write(path: Path, content: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise


def bootstrap(
    root: Path,
    project: str,
    index_file: Path | None,
    *,
    require_exact: bool = False,
) -> dict[str, Any]:
    project = project.strip()
    if not project:
        raise BootstrapError("project must be nonempty")
    root = root.resolve()
    if root.exists() and not root.is_dir():
        raise BootstrapError(f"Spine root is not a directory: {root}")
    index_path = root / "README.md"
    manifest_path = root / "specspine.json"
    missing_index = not index_path.exists()
    missing_manifest = not manifest_path.exists()
    if not missing_index and not index_path.is_file():
        raise BootstrapError("README.md is not a regular file")
    if not missing_manifest and not manifest_path.is_file():
        raise BootstrapError("specspine.json is not a regular file")
    if missing_index and index_file is None:
        raise BootstrapError("--index-file is required when README.md is absent")

    rendered_index = read_index(index_file) if index_file is not None else None
    index = rendered_index if missing_index else None
    expected_manifest = manifest(project)
    if require_exact:
        if rendered_index is None:
            raise BootstrapError("--require-exact requires --index-file")
        if not missing_index and index_path.read_text(encoding="utf-8") != rendered_index:
            raise BootstrapError("existing README.md differs from rendered bootstrap")
        if not missing_manifest:
            try:
                existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as error:
                raise BootstrapError(f"cannot read existing specspine.json: {error}") from error
            if existing_manifest != expected_manifest:
                raise BootstrapError(
                    "existing specspine.json differs from rendered bootstrap"
                )
    root.mkdir(parents=True, exist_ok=True)
    manifest_bytes = (
        json.dumps(expected_manifest, ensure_ascii=False, indent=2).encode("utf-8")
        + b"\n"
    )
    created: list[str] = []
    try:
        if index is not None:
            exclusive_write(index_path, index.encode("utf-8"))
            created.append("README.md")
        if missing_manifest:
            exclusive_write(manifest_path, manifest_bytes)
            created.append("specspine.json")
    except Exception:
        for name in created:
            (root / name).unlink(missing_ok=True)
        raise
    return {
        "status": "created" if created else "already_ready",
        "spine_root": str(root),
        "created": created,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("spine_root", type=Path)
    result.add_argument("--project", required=True)
    result.add_argument("--index-file", type=Path)
    result.add_argument("--require-exact", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        result = bootstrap(
            args.spine_root,
            args.project,
            args.index_file,
            require_exact=args.require_exact,
        )
    except (BootstrapError, OSError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
