#!/usr/bin/env python3
"""Maintain the run-scoped exhaustive SpecSpine Map coverage frontier."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import os
import re
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA_VERSION = 2
STATES = {"queued", "active", "locally_saturated", "blocked", "complete"}
BRANCH_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TERMINAL_REFUSAL = re.compile(r"^no useful node:\s+\S")


class LedgerError(ValueError):
    pass


def load(path: Path) -> dict[str, Any]:
    try:
        ledger = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise LedgerError(f"cannot read ledger {path}: {error}") from error
    if not isinstance(ledger, dict):
        raise LedgerError("ledger root must be an object")
    return ledger


def atomic_write(path: Path, ledger: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(ledger, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def branch(
    branch_id: str,
    parent: str | None,
    question: str,
    state: str = "queued",
    **extra: Any,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": branch_id,
        "parent": parent,
        "question": question,
        "state": state,
        "owner": None,
        "terminal_reason": None,
        "resolution": None,
        "published": [],
        "reservations": [],
        "replacements": [],
    }
    result.update(extra)
    return result


def validate_id(value: str) -> str:
    if not BRANCH_ID.fullmatch(value):
        raise LedgerError(
            f"invalid branch id {value!r}; use lowercase kebab-case"
        )
    return value


def validate_relative_path(value: str) -> str:
    candidate = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or candidate.is_absolute()
        or any(part in {"", ".", ".."} for part in candidate.parts)
    ):
        raise LedgerError(f"invalid relative path: {value!r}")
    return candidate.as_posix()


def branches(ledger: dict[str, Any]) -> dict[str, dict[str, Any]]:
    value = ledger.get("branches")
    if not isinstance(value, dict):
        raise LedgerError("ledger branches must be an object")
    return value


def require_branch(
    ledger: dict[str, Any], branch_id: str
) -> dict[str, Any]:
    try:
        return branches(ledger)[branch_id]
    except KeyError as error:
        raise LedgerError(f"unknown branch: {branch_id}") from error


def children_of(ledger: dict[str, Any], parent: str) -> list[dict[str, Any]]:
    return sorted(
        (item for item in branches(ledger).values() if item.get("parent") == parent),
        key=lambda item: item["id"],
    )


def save(path: Path, ledger: dict[str, Any]) -> None:
    ledger["revision"] = ledger.get("revision", 0) + 1
    atomic_write(path, ledger)


def command_init(args: argparse.Namespace) -> dict[str, Any]:
    if args.ledger.exists() and not args.force:
        raise LedgerError(f"ledger already exists: {args.ledger}")
    ledger = {
        "schema_version": SCHEMA_VERSION,
        "revision": 0,
        "scope": args.scope,
        "root": "root",
        "branches": {
            "root": branch(
                "root", None, args.root_question, state="active", origin="operator"
            )
        },
    }
    save(args.ledger, ledger)
    return ledger


def command_add(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    validate_id(args.id)
    parent = require_branch(ledger, args.parent)
    if args.prerequisite:
        require_branch(ledger, args.prerequisite)
    if parent["state"] not in {"queued", "active"}:
        raise LedgerError(
            f"add requires queued or active parent: {args.parent}"
        )
    candidate = branch(
        args.id,
        args.parent,
        args.question,
        origin=args.origin,
        prerequisite=args.prerequisite,
        namespace=args.namespace,
    )
    existing = branches(ledger).get(args.id)
    if existing is not None:
        if existing == candidate:
            return ledger
        raise LedgerError(f"conflicting branch id: {args.id}")
    branches(ledger)[args.id] = candidate
    save(args.ledger, ledger)
    return ledger


def command_documented(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    validate_id(args.id)
    parent = require_branch(ledger, args.parent)
    if parent["state"] not in {"queued", "active"}:
        raise LedgerError(
            f"documented requires queued or active parent: {args.parent}"
        )
    candidate = branch(
        args.id,
        args.parent,
        args.question,
        state="complete",
        origin=args.origin,
        namespace=args.namespace,
        resolution="already_documented",
        document=args.document,
    )
    existing = branches(ledger).get(args.id)
    if existing is not None:
        if existing == candidate:
            return ledger
        raise LedgerError(f"conflicting branch id: {args.id}")
    branches(ledger)[args.id] = candidate
    save(args.ledger, ledger)
    return ledger


def command_assign(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    item = require_branch(ledger, args.id)
    if item["state"] != "queued":
        raise LedgerError(f"assign requires queued state: {args.id}")
    if not args.owner.strip():
        raise LedgerError("owner must not be empty")
    item["state"] = "active"
    item["owner"] = args.owner
    save(args.ledger, ledger)
    return ledger


def command_release(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    item = require_branch(ledger, args.id)
    if item["state"] not in {"active", "blocked", "locally_saturated"}:
        raise LedgerError(
            f"release requires active, blocked, or locally_saturated state: {args.id}"
        )
    item["state"] = "queued"
    item["owner"] = None
    item["terminal_reason"] = None
    item["resolution"] = None
    save(args.ledger, ledger)
    return ledger


def command_reserve(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    item = require_branch(ledger, args.id)
    if item["state"] not in {"queued", "active"}:
        raise LedgerError(f"reserve requires queued or active state: {args.id}")
    requested = sorted({validate_relative_path(value) for value in args.path})
    replacements = sorted(
        {validate_relative_path(value) for value in args.replace_existing}
    )
    unknown = sorted(set(replacements) - set(requested))
    if unknown:
        raise LedgerError(
            "replacement paths are not reserved paths: "
            + ", ".join(unknown)
        )
    conflicts: list[str] = []
    for other_id, other in branches(ledger).items():
        if other_id == args.id:
            continue
        occupied = set(other.get("reservations", [])) | set(
            other.get("published", [])
        )
        conflicts.extend(sorted(set(requested) & occupied))
    if conflicts:
        raise LedgerError(
            "destination reserved by another branch: "
            + ", ".join(sorted(set(conflicts)))
        )
    item["reservations"] = sorted(
        set(item.get("reservations", [])) | set(requested)
    )
    item["replacements"] = sorted(
        set(item.get("replacements", [])) | set(replacements)
    )
    save(args.ledger, ledger)
    return ledger


def command_unreserve(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    item = require_branch(ledger, args.id)
    if item["state"] not in {"queued", "active", "blocked"}:
        raise LedgerError(f"unreserve requires queued, active, or blocked state: {args.id}")
    requested = {validate_relative_path(value) for value in args.path}
    published = set(item.get("published", []))
    if requested & published:
        raise LedgerError("cannot unreserve a published path")
    item["reservations"] = sorted(set(item.get("reservations", [])) - requested)
    item["replacements"] = sorted(set(item.get("replacements", [])) - requested)
    save(args.ledger, ledger)
    return ledger


def command_publish(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    item = require_branch(ledger, args.id)
    if item["state"] != "active":
        raise LedgerError(f"publish requires active state: {args.id}")
    published = sorted({validate_relative_path(value) for value in args.path})
    unknown = sorted(set(published) - set(item.get("reservations", [])))
    if unknown:
        raise LedgerError(
            "published paths were not reserved by this branch: "
            + ", ".join(unknown)
        )
    item["published"] = sorted(set(item.get("published", [])) | set(published))
    save(args.ledger, ledger)
    return ledger


def command_state(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    item = require_branch(ledger, args.id)
    current = item["state"]
    target = args.state
    if target == "locally_saturated":
        if current != "active":
            raise LedgerError("locally_saturated requires active state")
        if not args.terminal_reason or not TERMINAL_REFUSAL.match(
            args.terminal_reason.strip()
        ):
            raise LedgerError(
                "locally_saturated requires an exact "
                "'no useful node: <evidence-based reason>' refusal"
            )
        item["state"] = target
        item["owner"] = None
        item["terminal_reason"] = args.terminal_reason
        item["resolution"] = "independently_refused"
    elif target == "blocked":
        if current not in {"queued", "active"}:
            raise LedgerError("blocked requires queued or active state")
        if not args.terminal_reason:
            raise LedgerError("blocked requires --terminal-reason")
        item["state"] = target
        item["owner"] = None
        item["terminal_reason"] = args.terminal_reason
    elif target == "complete":
        if current != "locally_saturated":
            raise LedgerError("complete requires locally_saturated state")
        incomplete = [
            child["id"]
            for child in children_of(ledger, args.id)
            if child["state"] != "complete"
        ]
        if incomplete:
            raise LedgerError(
                "cannot complete branch with incomplete children: "
                + ", ".join(incomplete)
            )
        item["state"] = target
    else:
        raise LedgerError("use assign/release to enter queued or active state")
    save(args.ledger, ledger)
    return ledger


def audit_findings(ledger: dict[str, Any], final: bool) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if ledger.get("schema_version") != SCHEMA_VERSION:
        findings.append({"code": "schema", "message": "unsupported schema version"})
    if ledger.get("root") != "root":
        findings.append({"code": "root", "message": "root id must be 'root'"})
    try:
        items = branches(ledger)
    except LedgerError as error:
        return [{"code": "branches", "message": str(error)}]
    for key, item in sorted(items.items()):
        if not isinstance(item, dict) or item.get("id") != key:
            findings.append({"code": "identity", "branch": key, "message": "id mismatch"})
            continue
        if not BRANCH_ID.fullmatch(key):
            findings.append({"code": "id", "branch": key, "message": "invalid id"})
        if item.get("state") not in STATES:
            findings.append({"code": "state", "branch": key, "message": "invalid state"})
        for field in ("published", "reservations", "replacements"):
            values = item.get(field)
            if not isinstance(values, list):
                findings.append(
                    {"code": field, "branch": key, "message": f"{field} must be a list"}
                )
                continue
            try:
                normalized = [validate_relative_path(value) for value in values]
            except (LedgerError, TypeError) as error:
                findings.append(
                    {"code": field, "branch": key, "message": str(error)}
                )
                continue
            if normalized != sorted(set(normalized)):
                findings.append(
                    {"code": field, "branch": key, "message": f"{field} must be sorted and unique"}
                )
        reservations = item.get("reservations", [])
        replacements = item.get("replacements", [])
        published = item.get("published", [])
        if (
            isinstance(reservations, list)
            and isinstance(published, list)
            and all(isinstance(value, str) for value in reservations + published)
            and set(published) - set(reservations)
        ):
            findings.append(
                {
                    "code": "published",
                    "branch": key,
                    "message": "published path is not reserved by its branch",
                }
            )
        if (
            isinstance(reservations, list)
            and isinstance(replacements, list)
            and all(isinstance(value, str) for value in reservations + replacements)
            and set(replacements) - set(reservations)
        ):
            findings.append(
                {
                    "code": "replacements",
                    "branch": key,
                    "message": "replacement path is not reserved by its branch",
                }
            )
    reservation_owners: dict[str, str] = {}
    for key, item in sorted(items.items()):
        if not isinstance(item, dict):
            continue
        reserved_paths = item.get("reservations", [])
        if not isinstance(reserved_paths, list):
            reserved_paths = []
        for path in reserved_paths:
            if not isinstance(path, str):
                continue
            owner = reservation_owners.setdefault(path, key)
            if owner != key:
                findings.append(
                    {
                        "code": "reservation_conflict",
                        "branch": key,
                        "message": f"{path} is also reserved by {owner}",
                    }
                )
        parent = item.get("parent")
        if key == "root":
            if parent is not None:
                findings.append({"code": "parent", "branch": key, "message": "root has parent"})
        elif parent not in items:
            findings.append({"code": "parent", "branch": key, "message": "missing parent"})
        seen = {key}
        cursor = parent
        while cursor in items:
            if cursor in seen:
                findings.append(
                    {"code": "cycle", "branch": key, "message": "parent cycle"}
                )
                break
            seen.add(cursor)
            cursor = items[cursor].get("parent")
        prerequisite = item.get("prerequisite")
        if prerequisite and prerequisite not in items:
            findings.append(
                {
                    "code": "prerequisite",
                    "branch": key,
                    "message": "missing prerequisite",
                }
            )
        if item.get("state") == "active" and not item.get("owner") and key != "root":
            findings.append({"code": "owner", "branch": key, "message": "active without owner"})
        if item.get("state") == "locally_saturated" and (
            not isinstance(item.get("terminal_reason"), str)
            or not TERMINAL_REFUSAL.match(item["terminal_reason"].strip())
        ):
            findings.append(
                {
                    "code": "reason",
                    "branch": key,
                    "message": "missing exact refusal reason",
                }
            )
        if item.get("state") == "complete":
            incomplete = [
                child["id"]
                for child in children_of(ledger, key)
                if child.get("state") != "complete"
            ]
            if incomplete:
                findings.append(
                    {
                        "code": "children",
                        "branch": key,
                        "message": "incomplete children: " + ", ".join(incomplete),
                    }
                )
        if final and item.get("state") != "complete":
            findings.append(
                {
                    "code": "unfinished",
                    "branch": key,
                    "message": f"state is {item.get('state')}",
                }
            )
    return findings


def command_audit(args: argparse.Namespace) -> tuple[list[dict[str, str]], int]:
    findings = audit_findings(load(args.ledger), args.final)
    return findings, 1 if findings else 0


def command_ready(args: argparse.Namespace) -> list[dict[str, Any]]:
    ledger = load(args.ledger)
    return [
        item
        for item in sorted(branches(ledger).values(), key=lambda value: value["id"])
        if item["state"] == "queued"
        and (
            not item.get("prerequisite")
            or require_branch(ledger, item["prerequisite"])["state"] == "complete"
        )
    ]


def command_summary(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    items = branches(ledger)
    counts = Counter(item["state"] for item in items.values())
    ready = command_ready(args)
    non_root_active = sorted(
        item["id"]
        for item in items.values()
        if item["id"] != "root" and item["state"] == "active"
    )
    blocked = sorted(
        item["id"] for item in items.values() if item["state"] == "blocked"
    )
    final_clean = not audit_findings(ledger, final=True)
    blocked_stop = (
        bool(blocked)
        and not ready
        and not non_root_active
        and counts["queued"] == 0
    )
    return {
        "revision": ledger.get("revision"),
        "state_counts": {
            state: counts[state] for state in sorted(STATES) if counts[state]
        },
        "ready": [item["id"] for item in ready],
        "active": non_root_active,
        "blocked": blocked,
        "terminal": "saturated" if final_clean else "blocked" if blocked_stop else None,
    }


def compact_result(args: argparse.Namespace, result: Any) -> Any:
    if not getattr(args, "compact", False) or not isinstance(result, dict):
        return result
    receipt: dict[str, Any] = {
        "status": "ok",
        "command": args.command,
        "revision": result.get("revision"),
    }
    if hasattr(args, "id"):
        receipt["branch"] = args.id
    return receipt


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="command", required=True)

    def mutation(name: str) -> argparse.ArgumentParser:
        command = subparsers.add_parser(name)
        command.add_argument(
            "--compact",
            action="store_true",
            help="emit a compact mutation receipt instead of the full ledger",
        )
        return command

    init = mutation("init")
    init.add_argument("ledger", type=Path)
    init.add_argument("--scope", required=True)
    init.add_argument("--root-question", required=True)
    init.add_argument("--force", action="store_true")
    init.set_defaults(handler=command_init)

    add = mutation("add")
    add.add_argument("ledger", type=Path)
    add.add_argument("id")
    add.add_argument("--parent", required=True)
    add.add_argument("--question", required=True)
    add.add_argument("--origin", required=True)
    add.add_argument("--prerequisite")
    add.add_argument("--namespace")
    add.set_defaults(handler=command_add)

    documented = mutation("documented")
    documented.add_argument("ledger", type=Path)
    documented.add_argument("id")
    documented.add_argument("--parent", required=True)
    documented.add_argument("--question", required=True)
    documented.add_argument("--document", required=True)
    documented.add_argument("--origin", required=True)
    documented.add_argument("--namespace")
    documented.set_defaults(handler=command_documented)

    assign = mutation("assign")
    assign.add_argument("ledger", type=Path)
    assign.add_argument("id")
    assign.add_argument("--owner", required=True)
    assign.set_defaults(handler=command_assign)

    release = mutation("release")
    release.add_argument("ledger", type=Path)
    release.add_argument("id")
    release.set_defaults(handler=command_release)

    reserve = mutation("reserve")
    reserve.add_argument("ledger", type=Path)
    reserve.add_argument("id")
    reserve.add_argument("--path", action="append", required=True)
    reserve.add_argument("--replace-existing", action="append", default=[])
    reserve.set_defaults(handler=command_reserve)

    unreserve = mutation("unreserve")
    unreserve.add_argument("ledger", type=Path)
    unreserve.add_argument("id")
    unreserve.add_argument("--path", action="append", required=True)
    unreserve.set_defaults(handler=command_unreserve)

    publish = mutation("publish")
    publish.add_argument("ledger", type=Path)
    publish.add_argument("id")
    publish.add_argument("--path", action="append", required=True)
    publish.set_defaults(handler=command_publish)

    state = mutation("state")
    state.add_argument("ledger", type=Path)
    state.add_argument("id")
    state.add_argument("state", choices=sorted(STATES))
    state.add_argument("--terminal-reason")
    state.set_defaults(handler=command_state)

    ready = subparsers.add_parser("ready")
    ready.add_argument("ledger", type=Path)
    ready.set_defaults(handler=command_ready)

    summary = subparsers.add_parser("summary")
    summary.add_argument("ledger", type=Path)
    summary.set_defaults(handler=command_summary)

    audit = subparsers.add_parser("audit")
    audit.add_argument("ledger", type=Path)
    audit.add_argument("--final", action="store_true")
    audit.set_defaults(handler=command_audit)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        result = args.handler(args)
    except (LedgerError, OSError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    exit_code = 0
    if isinstance(result, tuple):
        result, exit_code = result
    result = compact_result(args, result)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
