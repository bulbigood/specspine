#!/usr/bin/env python3
"""Validate and publish one exhaustive Map producer checkpoint transactionally."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import frontier


class PublishError(ValueError):
    def __init__(self, message: str, findings: Any | None = None):
        super().__init__(message)
        self.findings = findings


def candidate_files(root: Path) -> set[str]:
    if not root.is_dir():
        raise PublishError(f"staging root is not a directory: {root}")
    result: set[str] = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise PublishError(f"staging contains a symbolic link: {path}")
        if path.is_file():
            result.add(path.relative_to(root).as_posix())
    return result


def run_checker(
    checker: Path,
    spine_root: Path,
    staging_root: Path | None = None,
    replacements: list[str] | None = None,
) -> None:
    command = [sys.executable, str(checker), str(spine_root)]
    if staging_root is not None:
        command.extend(["--candidates", str(staging_root)])
    for path in replacements or []:
        command.extend(["--replace-existing", path])
    command.append("--json")
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    try:
        findings = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        detail = result.stderr.strip() or result.stdout.strip() or "no output"
        raise PublishError(f"checker returned invalid JSON: {detail}") from error
    if result.returncode != 0 or findings != []:
        raise PublishError("checker blocked publication", findings)


def rollback_moves(
    changes: list[dict[str, Any]],
    staging_root: Path,
    spine_root: Path,
    backup_root: Path,
) -> None:
    for change in reversed(changes):
        relative = change["relative"]
        source = staging_root / relative
        destination = spine_root / relative
        backup = backup_root / relative
        if change["candidate_moved"] and destination.exists():
            source.parent.mkdir(parents=True, exist_ok=True)
            os.replace(destination, source)
        if change["backup_created"] and backup.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(backup, destination)


def publish(args: argparse.Namespace) -> dict[str, Any]:
    staging_resolved = args.staging_root.resolve()
    spine_resolved = args.spine_root.resolve()
    if (
        staging_resolved == spine_resolved
        or staging_resolved.is_relative_to(spine_resolved)
        or spine_resolved.is_relative_to(staging_resolved)
    ):
        raise PublishError("staging root and live Spine must be disjoint")

    requested = sorted({frontier.validate_relative_path(path) for path in args.path})
    replacements = sorted(
        {frontier.validate_relative_path(path) for path in args.replace_existing}
    )
    if "README.md" in requested:
        raise PublishError("producer checkpoints must not publish README.md")
    if set(replacements) - set(requested):
        raise PublishError("replacement paths must also be requested paths")

    ledger = frontier.load(args.ledger)
    item = frontier.require_branch(ledger, args.branch)
    if item["state"] != "active":
        raise PublishError(f"publication requires active branch: {args.branch}")

    actual = candidate_files(args.staging_root)
    if actual != set(requested):
        raise PublishError(
            "staging paths differ from declared final destinations",
            {
                "declared": requested,
                "staging": sorted(actual),
            },
        )
    for relative in requested:
        destination = args.spine_root / relative
        if destination.exists() and relative not in replacements:
            raise PublishError(
                f"existing destination requires --replace-existing: {relative}"
            )
        if not destination.exists() and relative in replacements:
            raise PublishError(f"replacement destination does not exist: {relative}")

    frontier.command_reserve(
        SimpleNamespace(
            ledger=args.ledger,
            id=args.branch,
            path=requested,
            replace_existing=replacements,
        )
    )
    run_checker(
        args.checker,
        args.spine_root,
        args.staging_root,
        replacements,
    )

    backup_root = Path(
        tempfile.mkdtemp(prefix=".specspine-publish-", dir=args.ledger.parent)
    )
    changes: list[dict[str, Any]] = []
    cleanup_backup = True
    try:
        for relative in requested:
            source = args.staging_root / relative
            destination = args.spine_root / relative
            backup = backup_root / relative
            change = {
                "relative": relative,
                "backup_created": False,
                "candidate_moved": False,
            }
            changes.append(change)
            if destination.exists():
                backup.parent.mkdir(parents=True, exist_ok=True)
                os.replace(destination, backup)
                change["backup_created"] = True
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(source, destination)
            change["candidate_moved"] = True

        run_checker(args.checker, args.spine_root)
        updated = frontier.command_publish(
            SimpleNamespace(
                ledger=args.ledger,
                id=args.branch,
                path=requested,
            )
        )
    except BaseException as error:
        try:
            rollback_moves(changes, args.staging_root, args.spine_root, backup_root)
        except BaseException as rollback_error:
            cleanup_backup = False
            raise PublishError(
                "publication and rollback failed; recovery backup preserved at "
                f"{backup_root}: {rollback_error}"
            ) from error
        raise
    finally:
        if cleanup_backup:
            shutil.rmtree(backup_root, ignore_errors=True)

    return {
        "status": "published",
        "branch": args.branch,
        "paths": requested,
        "revision": updated["revision"],
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("ledger", type=Path)
    result.add_argument("branch")
    result.add_argument("spine_root", type=Path)
    result.add_argument("staging_root", type=Path)
    result.add_argument("--path", action="append", required=True)
    result.add_argument("--replace-existing", action="append", default=[])
    result.add_argument(
        "--checker",
        type=Path,
        default=Path(__file__).with_name("check_spine.py"),
    )
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        result = publish(args)
    except (frontier.LedgerError, PublishError, OSError) as error:
        payload: dict[str, Any] = {"error": str(error)}
        if isinstance(error, PublishError) and error.findings is not None:
            payload["findings"] = error.findings
        print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
