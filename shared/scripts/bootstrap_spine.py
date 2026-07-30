#!/usr/bin/env python3
"""Idempotently initialize a workspace and its SpecSpine v3 root files."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from spec_contract import (
    DEFAULT_INDEX_TEXT,
    FORMAT_MAJOR,
    INDEX_NAME,
    MANIFEST_NAME,
    README_NAME,
    render_root_readme,
)


class BootstrapError(ValueError):
    pass


INDEX_IDENTITY = re.compile(
    r"^\*\*ID:\*\*\s+`project-architecture`\s+·\s+\*\*Kind:\*\*\s+`index`\s*$",
    re.MULTILINE,
)


def read_index(path: Path, project: str) -> str:
    try:
        value = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise BootstrapError(f"cannot read rendered index {path}: {error}") from error
    value = value.replace("{project}", project)
    if not value.strip() or INDEX_IDENTITY.search(value) is None:
        raise BootstrapError(
            "rendered index must be nonempty and identify project-architecture "
            "as an index"
        )
    return value if value.endswith("\n") else value + "\n"


def read_readme(path: Path, project: str) -> str:
    try:
        value = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise BootstrapError(f"cannot read rendered README {path}: {error}") from error
    value = value.replace("{project}", project)
    if not value.strip():
        raise BootstrapError("rendered README must be nonempty")
    return value if value.endswith("\n") else value + "\n"


def manifest(project: str) -> dict[str, Any]:
    return {
        "specspine": FORMAT_MAJOR,
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


def ensure_workspace_ignore(workspace: Path) -> str:
    workspace = workspace.resolve()
    if not workspace.is_dir():
        raise BootstrapError(f"workspace is not a directory: {workspace}")
    try:
        completed = subprocess.run(
            ["git", "-C", str(workspace), "rev-parse", "--show-toplevel"],
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return "not_git_repository"
    if completed.returncode != 0:
        return "not_git_repository"
    try:
        repository_root = Path(completed.stdout.strip()).resolve()
    except (OSError, RuntimeError):
        return "not_git_repository"
    if repository_root != workspace:
        return "not_git_repository"
    ignore_path = workspace / ".gitignore"
    rule = ".specspine"
    if ignore_path.exists() and not ignore_path.is_file():
        raise BootstrapError(f".gitignore is not a regular file: {ignore_path}")
    try:
        existing = ignore_path.read_text(encoding="utf-8") if ignore_path.exists() else ""
    except (OSError, UnicodeError) as error:
        raise BootstrapError(f"cannot read {ignore_path}: {error}") from error
    if rule in existing.splitlines():
        return "already_present"
    separator = "" if not existing or existing.endswith("\n") else "\n"
    with ignore_path.open("a", encoding="utf-8") as stream:
        stream.write(f"{separator}{rule}\n")
        stream.flush()
        os.fsync(stream.fileno())
    return "created" if not existing else "updated"


def bootstrap(
    root: Path,
    project: str,
    index_file: Path | None,
    *,
    readme_file: Path | None = None,
    require_exact: bool = False,
    workspace: Path | None = None,
) -> dict[str, Any]:
    project = project.strip()
    if not project:
        raise BootstrapError("project must be nonempty")
    root = root.resolve()
    if root.exists() and not root.is_dir():
        raise BootstrapError(f"Spine root is not a directory: {root}")
    index_path = root / INDEX_NAME
    manifest_path = root / MANIFEST_NAME
    readme_path = root / README_NAME
    missing_index = not index_path.exists()
    missing_manifest = not manifest_path.exists()
    missing_readme = not readme_path.exists()
    if not missing_index and not index_path.is_file():
        raise BootstrapError("_INDEX.md is not a regular file")
    if not missing_manifest and not manifest_path.is_file():
        raise BootstrapError("specspine.json is not a regular file")
    if not missing_readme and not readme_path.is_file():
        raise BootstrapError("README.md is not a regular file")
    if missing_index and index_file is None:
        raise BootstrapError("--index-file is required when _INDEX.md is absent")

    rendered_index = read_index(index_file, project) if index_file is not None else None
    rendered_readme = (
        read_readme(readme_file, project) if readme_file is not None else None
    )
    index = rendered_index if missing_index else None
    expected_manifest = manifest(project)
    if require_exact:
        if rendered_index is None:
            raise BootstrapError("--require-exact requires --index-file")
        if not missing_index and index_path.read_text(encoding="utf-8") != rendered_index:
            raise BootstrapError("existing _INDEX.md differs from rendered bootstrap")
        if not missing_manifest:
            try:
                existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as error:
                raise BootstrapError(f"cannot read existing specspine.json: {error}") from error
            if existing_manifest != expected_manifest:
                raise BootstrapError(
                    "existing specspine.json differs from rendered bootstrap"
                )
    ignore_status = ensure_workspace_ignore(workspace) if workspace is not None else None
    root.mkdir(parents=True, exist_ok=True)
    manifest_bytes = (
        json.dumps(expected_manifest, ensure_ascii=False, indent=2).encode("utf-8")
        + b"\n"
    )
    readme_bytes = (
        rendered_readme or render_root_readme(project, DEFAULT_INDEX_TEXT)
    ).encode("utf-8")
    created: list[str] = []
    try:
        if index is not None:
            exclusive_write(index_path, index.encode("utf-8"))
            created.append("_INDEX.md")
        if missing_manifest:
            exclusive_write(manifest_path, manifest_bytes)
            created.append("specspine.json")
        if missing_readme:
            exclusive_write(readme_path, readme_bytes)
            created.append("README.md")
    except Exception:
        for name in created:
            (root / name).unlink(missing_ok=True)
        raise
    result = {
        "status": "created" if created else "already_ready",
        "spine_root": str(root),
        "created": created,
    }
    if ignore_status is not None:
        result["workspace_gitignore"] = ignore_status
    return result


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("spine_root", type=Path)
    result.add_argument("--project", required=True)
    result.add_argument("--index-file", type=Path)
    result.add_argument("--readme-file", type=Path)
    result.add_argument("--require-exact", action="store_true")
    result.add_argument(
        "--workspace",
        type=Path,
        help="ensure the workspace .gitignore contains the .specspine rule",
    )
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        result = bootstrap(
            args.spine_root,
            args.project,
            args.index_file,
            readme_file=args.readme_file,
            require_exact=args.require_exact,
            workspace=args.workspace,
        )
    except (BootstrapError, OSError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
