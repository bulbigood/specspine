#!/usr/bin/env python3
"""Run a reliable exhaustive SpecSpine Map campaign.

The campaign deliberately separates four authorities:

* deterministic repository inventory defines the lower bound of discovery;
* one-shot producers draft one bounded task into private staging;
* the root orchestrator publishes and integrates accepted drafts;
* the ledger derives completion from inventory, ToDo, and integration state.

Producer prose is never treated as proof of coverage or saturation.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, Iterator


SCHEMA_VERSION = 2
TASK_STATES = {"todo", "assigned", "published", "complete", "blocked"}
CHECKPOINT_STATUSES = {
    "draft_ready",
    "no_architectural_value",
    "needs_more_evidence",
    "blocked",
}
SOURCE_CLASSIFICATIONS = {
    "mapped",
    "queued",
    "neighbor-owned",
    "generated",
    "vendored",
    "test-only",
    "no-architecture-value",
}
OWNER_CLASSIFICATIONS = {"mapped", "neighbor-owned"}
TERMINAL_CLASSIFICATIONS = {
    "generated",
    "vendored",
    "test-only",
    "no-architecture-value",
}
REVIEW_DISPOSITIONS = {
    "integrated",
    "already_canonical",
    "not_architectural",
}
SUGGESTION_DISPOSITIONS = {"queued", "covered", "rejected"}
DEFERRED_CHECKER_CODES = {"UNREACHABLE_SPEC"}
COLLAPSED_DIRECTORIES = {
    ".git",
    ".next",
    ".venv",
    ".yarn",
    "build",
    "dist",
    "node_modules",
    "target",
    "vendor",
    "venv",
}


class CampaignError(ValueError):
    pass


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def digest_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CampaignError(f"cannot read JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise CampaignError(f"JSON root must be an object: {path}")
    return value


def validate_id(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not value
        or any(
            not (
                character.isascii()
                and (character.islower() or character.isdigit() or character == "-")
            )
            for character in value
        )
        or value.startswith("-")
        or value.endswith("-")
        or "--" in value
    ):
        raise CampaignError(f"invalid stable ID: {value!r}")
    return value


def validate_relative_path(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CampaignError(f"invalid relative path: {value!r}")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or value.startswith("./"):
        raise CampaignError(f"path must be repository-relative: {value!r}")
    return path.as_posix()


def string_list(
    value: Any,
    field: str,
    *,
    nonempty: bool = False,
) -> list[str]:
    if (
        not isinstance(value, list)
        or (nonempty and not value)
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        qualifier = "nonempty " if nonempty else ""
        raise CampaignError(f"{field} must be a {qualifier}list of strings")
    return list(value)


def document_hashes(spine_root: Path) -> dict[str, str]:
    return {
        path.relative_to(spine_root).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(spine_root.rglob("*.md"))
        if path.is_file()
    }


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(canonical_json(value) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def load(path: Path) -> dict[str, Any]:
    ledger = read_json(path)
    if ledger.get("schema_version") != SCHEMA_VERSION:
        raise CampaignError(
            f"unsupported campaign schema: {ledger.get('schema_version')!r}; "
            f"expected {SCHEMA_VERSION}"
        )
    if not isinstance(ledger.get("tasks"), dict):
        raise CampaignError("campaign tasks are missing")
    return ledger


@contextlib.contextmanager
def locked_ledger(path: Path) -> Iterator[dict[str, Any]]:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + ".lock")
    with lock_path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        ledger = load(path)
        yield ledger


def save_locked(path: Path, ledger: dict[str, Any]) -> None:
    ledger["revision"] += 1
    atomic_write(path, ledger)


def new_task(raw: dict[str, Any], *, source: str) -> dict[str, Any]:
    task_id = validate_id(raw.get("id"))
    question = raw.get("question")
    reason = raw.get("reason")
    if not isinstance(question, str) or not question.strip():
        raise CampaignError(f"ToDo {task_id} needs a question")
    if not isinstance(reason, str) or not reason.strip():
        raise CampaignError(f"ToDo {task_id} needs a reason")
    evidence = string_list(raw.get("evidence", []), f"ToDo {task_id} evidence")
    documents = [
        validate_relative_path(value)
        for value in string_list(
            raw.get("documents", []),
            f"ToDo {task_id} documents",
        )
    ]
    excludes = string_list(raw.get("excludes", []), f"ToDo {task_id} excludes")
    anchor = raw.get("anchor")
    if anchor is not None:
        if not isinstance(anchor, dict):
            raise CampaignError(f"ToDo {task_id} anchor must be an object")
        document = validate_relative_path(anchor.get("document"))
        location = anchor.get("location")
        known = anchor.get("known")
        if (
            not isinstance(location, str)
            or not location.strip()
            or not isinstance(known, str)
            or not known.strip()
        ):
            raise CampaignError(
                f"ToDo {task_id} anchor needs nonempty location and known"
            )
        anchor = {
            "document": document,
            "location": location,
            "known": known,
        }
    return {
        "id": task_id,
        "question": question.strip(),
        "reason": reason.strip(),
        "origin": source,
        "evidence": evidence,
        "documents": documents,
        "excludes": excludes,
        "anchor": anchor,
        "state": "todo",
        "owner": None,
        "attempts": 0,
        "published": [],
        "checkpoint_digest": None,
        "producer_suggestions": [],
        "suggestion_reviews": {},
        "terminal_reason": None,
    }


def task_definition(task: dict[str, Any]) -> dict[str, Any]:
    return {
        key: task.get(key)
        for key in (
            "id",
            "question",
            "reason",
            "origin",
            "evidence",
            "documents",
            "excludes",
            "anchor",
        )
    }


def task_semantics(task: dict[str, Any]) -> dict[str, Any]:
    definition = task_definition(task)
    definition.pop("origin", None)
    return definition


def add_tasks(
    ledger: dict[str, Any],
    raw_tasks: list[Any],
    *,
    source: str,
) -> list[str]:
    added: list[str] = []
    for raw in raw_tasks:
        if not isinstance(raw, dict):
            raise CampaignError("each ToDo entry must be an object")
        task = new_task(raw, source=source)
        existing = ledger["tasks"].get(task["id"])
        if existing is not None:
            if task_semantics(existing) != task_semantics(task):
                raise CampaignError(f"conflicting ToDo ID: {task['id']}")
            continue
        ledger["tasks"][task["id"]] = task
        added.append(task["id"])
    return added


def require_task(ledger: dict[str, Any], task_id: str) -> dict[str, Any]:
    task_id = validate_id(task_id)
    try:
        task = ledger["tasks"][task_id]
    except KeyError as error:
        raise CampaignError(f"unknown ToDo: {task_id}") from error
    if task.get("state") not in TASK_STATES:
        raise CampaignError(f"invalid ToDo state: {task_id}")
    return task


def repository_unit(relative_path: Path) -> str:
    parts = relative_path.parts
    if len(parts) == 1:
        return parts[0]
    first = parts[0]
    if first in COLLAPSED_DIRECTORIES:
        return first
    if len(parts) >= 4 and parts[:3] == ("public", "app", "features"):
        return Path(*parts[:4]).as_posix()
    if (
        len(parts) >= 3
        and first == "pkg"
        and parts[1]
        in {
            "api",
            "cmd",
            "infra",
            "plugins",
            "registry",
            "services",
            "storage",
            "tsdb",
        }
    ):
        return Path(*parts[:3]).as_posix()
    if first in {
        "apps",
        "cmd",
        "internal",
        "kinds",
        "lib",
        "modules",
        "packages",
        "plugins",
        "services",
        "src",
    }:
        return Path(*parts[:2]).as_posix()
    return first


def repository_inventory(
    repository_root: Path,
    *,
    spine_root: Path | None = None,
) -> dict[str, Any]:
    root = repository_root.resolve()
    if not root.is_dir():
        raise CampaignError(f"repository root is not a directory: {root}")
    excluded_spine: Path | None = None
    if spine_root is not None:
        resolved_spine = spine_root.resolve()
        try:
            resolved_spine.relative_to(root)
        except ValueError:
            pass
        else:
            excluded_spine = resolved_spine

    units: dict[str, dict[str, Any]] = {}
    snapshot = hashlib.sha256()
    for directory, names, files in os.walk(root):
        current = Path(directory)
        names.sort()
        files.sort()
        if excluded_spine is not None and (
            current == excluded_spine or excluded_spine in current.parents
        ):
            names[:] = []
            continue
        relative_directory = current.relative_to(root)
        if relative_directory.parts and relative_directory.parts[0] == ".git":
            names[:] = []
            continue
        collapsed = [
            name for name in names if name in COLLAPSED_DIRECTORIES and name != ".git"
        ]
        for name in collapsed:
            area_path = (relative_directory / name).as_posix()
            stat = (current / name).stat()
            snapshot.update(
                f"D\0{area_path}\0{stat.st_size}\0{stat.st_mtime_ns}\n".encode()
            )
            area = repository_unit(Path(area_path))
            record = units.setdefault(area, {"area": area, "files": 0, "samples": []})
            record["samples"].append(area_path + "/")
            names.remove(name)
        for filename in files:
            path = relative_directory / filename
            source = current / filename
            snapshot.update(f"F\0{path.as_posix()}\0".encode())
            with source.open("rb") as stream:
                while chunk := stream.read(1024 * 1024):
                    snapshot.update(chunk)
            snapshot.update(b"\n")
            area = repository_unit(path)
            record = units.setdefault(area, {"area": area, "files": 0, "samples": []})
            record["files"] += 1
            if len(record["samples"]) < 5:
                record["samples"].append(path.as_posix())
    inventory = sorted(units.values(), key=lambda value: value["area"])
    return {
        "repository_root": str(root),
        "areas": inventory,
        "digest": snapshot.hexdigest(),
        "shape_digest": digest_json(inventory),
    }


def validate_document_inventory(
    spine_root: Path,
    inspected: Any,
    *,
    field: str,
) -> dict[str, str]:
    documents = document_hashes(spine_root)
    paths = {
        validate_relative_path(value)
        for value in string_list(inspected, field, nonempty=True)
    }
    if paths != set(documents):
        raise CampaignError(
            f"{field} must equal every live Markdown document; "
            f"missing={sorted(set(documents) - paths)}, "
            f"unknown={sorted(paths - set(documents))}"
        )
    return documents


def validate_empty_reason(
    todo: list[Any],
    terminal_reason: Any,
    *,
    prefix: str,
) -> None:
    if todo:
        if terminal_reason is not None:
            raise CampaignError("terminal_reason must be null when ToDo is nonempty")
    elif (
        not isinstance(terminal_reason, str)
        or not terminal_reason.startswith(prefix)
    ):
        raise CampaignError(f"empty ToDo requires '{prefix}<reason>'")


def command_init(args: argparse.Namespace) -> dict[str, Any]:
    if args.ledger.exists():
        raise CampaignError(f"campaign already exists: {args.ledger}")
    ledger = {
        "schema_version": SCHEMA_VERSION,
        "campaign_id": str(uuid.uuid4()),
        "revision": 0,
        "scope": args.scope,
        "root_question": args.root_question,
        "spine_state": args.spine_state,
        "tasks": {},
        "used_producers": {},
        "publication_epoch": 0,
        "publication_history": [],
        "documentation_seed": None,
        "source_pass": None,
        "integration_pass": None,
    }
    atomic_write(args.ledger, ledger)
    return ledger


def command_seed_from_spine(args: argparse.Namespace) -> dict[str, Any]:
    plan = read_json(args.plan)
    documents = validate_document_inventory(
        args.spine_root.resolve(),
        plan.get("evidence_inspected"),
        field="documentation seed evidence_inspected",
    )
    raw_todo = plan.get("todo")
    if not isinstance(raw_todo, list):
        raise CampaignError("documentation seed todo must be a list")
    validate_empty_reason(
        raw_todo,
        plan.get("terminal_reason"),
        prefix="no documentation-derived ToDo: ",
    )
    with locked_ledger(args.ledger) as ledger:
        if ledger["spine_state"] != "existing":
            raise CampaignError("seed-from-spine requires --spine-state existing")
        if ledger["documentation_seed"] is not None:
            raise CampaignError("documentation seed already exists")
        added = add_tasks(
            ledger,
            raw_todo,
            source="documentation-seed",
        )
        ledger["documentation_seed"] = {
            "documents": documents,
            "todo": added,
            "terminal_reason": plan.get("terminal_reason"),
        }
        save_locked(args.ledger, ledger)
        return {
            "status": "seeded",
            "campaign_id": ledger["campaign_id"],
            "documents": len(documents),
            "added_todo": added,
            "revision": ledger["revision"],
        }


def command_inventory(args: argparse.Namespace) -> dict[str, Any]:
    return repository_inventory(
        args.repository_root,
        spine_root=args.spine_root,
    )


def command_source_pass(args: argparse.Namespace) -> dict[str, Any]:
    report = read_json(args.report)
    inventory = repository_inventory(
        args.repository_root,
        spine_root=args.spine_root,
    )
    rows = report.get("inventory")
    if not isinstance(rows, list):
        raise CampaignError("source pass inventory must be a list")
    normalized: dict[str, dict[str, Any]] = {}
    raw_todo = report.get("todo")
    if not isinstance(raw_todo, list):
        raise CampaignError("source pass todo must be a list")
    todo_ids = {
        validate_id(value.get("id"))
        for value in raw_todo
        if isinstance(value, dict)
    }
    if len(todo_ids) != len(raw_todo):
        raise CampaignError("source pass todo contains invalid or duplicate IDs")
    live_documents = document_hashes(args.spine_root.resolve())
    for row in rows:
        if not isinstance(row, dict):
            raise CampaignError("source inventory classification must be an object")
        area = row.get("area")
        classification = row.get("classification")
        reason = row.get("reason")
        if not isinstance(area, str) or not area:
            raise CampaignError("source inventory classification needs area")
        if area in normalized:
            raise CampaignError(f"duplicate source inventory area: {area}")
        if classification not in SOURCE_CLASSIFICATIONS:
            raise CampaignError(
                f"invalid source classification for {area}: {classification!r}"
            )
        if not isinstance(reason, str) or not reason.strip():
            raise CampaignError(f"source inventory area needs reason: {area}")
        owner = row.get("owner_document")
        task = row.get("task")
        if classification in OWNER_CLASSIFICATIONS:
            owner = validate_relative_path(owner)
            if owner not in live_documents:
                raise CampaignError(f"unknown owner document for {area}: {owner}")
            if task is not None:
                raise CampaignError(f"owned source area must not name a task: {area}")
        elif classification == "queued":
            task = validate_id(task)
            if task not in todo_ids:
                raise CampaignError(f"queued source area has no matching ToDo: {area}")
            if owner is not None:
                raise CampaignError(f"queued source area must not claim an owner: {area}")
        else:
            if owner is not None or task is not None:
                raise CampaignError(
                    f"terminal source classification cannot name owner/task: {area}"
                )
        normalized[area] = {
            "classification": classification,
            "reason": reason.strip(),
            "owner_document": owner,
            "task": task,
        }
    expected_areas = {value["area"] for value in inventory["areas"]}
    if set(normalized) != expected_areas:
        raise CampaignError(
            "source pass must classify every deterministic inventory area; "
            f"missing={sorted(expected_areas - set(normalized))}, "
            f"unknown={sorted(set(normalized) - expected_areas)}"
        )
    validate_empty_reason(
        raw_todo,
        report.get("terminal_reason"),
        prefix="no source-derived ToDo: ",
    )
    with locked_ledger(args.ledger) as ledger:
        if ledger["spine_state"] == "existing" and ledger["documentation_seed"] is None:
            raise CampaignError("seed-from-spine is required before source-pass")
        added = add_tasks(ledger, raw_todo, source="source-pass")
        ledger["source_pass"] = {
            "repository_root": str(args.repository_root.resolve()),
            "spine_root": str(args.spine_root.resolve()),
            "inventory_digest": inventory["digest"],
            "inventory": normalized,
            "todo": added,
            "terminal_reason": report.get("terminal_reason"),
            "publication_epoch": ledger["publication_epoch"],
        }
        save_locked(args.ledger, ledger)
        return {
            "status": "recorded",
            "areas": len(normalized),
            "added_todo": added,
            "revision": ledger["revision"],
        }


def command_todo_add(args: argparse.Namespace) -> dict[str, Any]:
    raw = {
        "id": args.id,
        "question": args.question,
        "reason": args.reason,
        "evidence": args.evidence,
        "documents": args.document,
        "excludes": args.exclude,
    }
    with locked_ledger(args.ledger) as ledger:
        added = add_tasks(ledger, [raw], source=args.origin)
        if added:
            ledger["integration_pass"] = None
        save_locked(args.ledger, ledger)
        return {
            "status": "added" if added else "already-present",
            "added_todo": added,
            "revision": ledger["revision"],
        }


def command_todo(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    tasks = [
        task_definition(task)
        | {
            "state": task["state"],
            "attempts": task["attempts"],
            "terminal_reason": task["terminal_reason"],
        }
        for task in sorted(ledger["tasks"].values(), key=lambda value: value["id"])
        if args.all or task["state"] in {"todo", "assigned", "published", "blocked"}
    ]
    return {"campaign_id": ledger["campaign_id"], "todo": tasks}


def command_ready(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    return {
        "campaign_id": ledger["campaign_id"],
        "ready": [
            task["id"]
            for task in sorted(ledger["tasks"].values(), key=lambda value: value["id"])
            if task["state"] == "todo"
        ],
    }


def command_assign(args: argparse.Namespace) -> dict[str, Any]:
    with locked_ledger(args.ledger) as ledger:
        task = require_task(ledger, args.id)
        if task["state"] != "todo":
            raise CampaignError(f"assign requires todo state: {args.id}")
        if args.owner in ledger["used_producers"]:
            previous = ledger["used_producers"][args.owner]
            raise CampaignError(
                f"one producer may run only one task: {args.owner} already ran {previous}"
            )
        task["state"] = "assigned"
        task["owner"] = args.owner
        task["attempts"] += 1
        ledger["used_producers"][args.owner] = task["id"]
        save_locked(args.ledger, ledger)
        return {
            "status": "assigned",
            "task": task_definition(task),
            "owner": args.owner,
            "revision": ledger["revision"],
        }


def command_release(args: argparse.Namespace) -> dict[str, Any]:
    with locked_ledger(args.ledger) as ledger:
        task = require_task(ledger, args.id)
        if task["state"] != "assigned":
            raise CampaignError(f"release requires assigned state: {args.id}")
        task["state"] = "todo"
        task["owner"] = None
        save_locked(args.ledger, ledger)
        return {
            "status": "released",
            "task": args.id,
            "revision": ledger["revision"],
        }


def candidate_files(root: Path) -> dict[str, Path]:
    if not root.is_dir():
        raise CampaignError(f"staging root is not a directory: {root}")
    result: dict[str, Path] = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise CampaignError(f"staging contains symbolic link: {path}")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = path
    return result


def validate_suggestions(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        raise CampaignError("discovered_directions must be a list")
    suggestions: list[dict[str, Any]] = []
    seen: set[str] = set()
    for value in raw:
        if not isinstance(value, dict):
            raise CampaignError("discovered direction must be an object")
        suggestion = new_task(value, source="producer-suggestion")
        if suggestion["id"] in seen:
            raise CampaignError(f"duplicate discovered direction: {suggestion['id']}")
        seen.add(suggestion["id"])
        suggestions.append(task_definition(suggestion))
    return suggestions


def validate_checkpoint(
    raw: dict[str, Any],
    staging: dict[str, Path],
) -> tuple[str, list[dict[str, str]], list[dict[str, Any]]]:
    status = raw.get("status")
    if status not in CHECKPOINT_STATUSES:
        raise CampaignError(f"invalid checkpoint status: {status!r}")
    string_list(
        raw.get("evidence_inspected"),
        "checkpoint evidence_inspected",
        nonempty=True,
    )
    findings = string_list(raw.get("findings"), "checkpoint findings", nonempty=True)
    if not findings:
        raise CampaignError("checkpoint findings must be nonempty")
    raw_candidates = raw.get("candidates")
    if not isinstance(raw_candidates, list):
        raise CampaignError("checkpoint candidates must be a list")
    candidates: list[dict[str, str]] = []
    for value in raw_candidates:
        if not isinstance(value, dict) or set(value) != {"path", "operation"}:
            raise CampaignError("candidate requires only path and operation")
        path = validate_relative_path(value["path"])
        operation = value["operation"]
        if operation not in {"create", "replace"}:
            raise CampaignError(f"invalid candidate operation: {operation!r}")
        if path == "README.md":
            raise CampaignError("producer must not publish README.md")
        candidates.append({"path": path, "operation": operation})
    paths = [value["path"] for value in candidates]
    if len(paths) != len(set(paths)) or set(paths) != set(staging):
        raise CampaignError(
            f"checkpoint/staging paths differ: checkpoint={sorted(paths)}, "
            f"staging={sorted(staging)}"
        )
    if status == "draft_ready" and not candidates:
        raise CampaignError("draft_ready requires at least one candidate")
    if status != "draft_ready" and candidates:
        raise CampaignError(f"{status} must not publish candidates")
    suggestions = validate_suggestions(raw.get("discovered_directions", []))
    if status != "draft_ready" and suggestions:
        raise CampaignError(
            f"{status} cannot emit discovered_directions without a draft to integrate"
        )
    terminal_reason = raw.get("terminal_reason")
    required_evidence = raw.get("required_evidence", [])
    if status == "no_architectural_value":
        if (
            not isinstance(terminal_reason, str)
            or not terminal_reason.startswith("no architectural value: ")
        ):
            raise CampaignError(
                "no_architectural_value requires "
                "'no architectural value: <reason>'"
            )
    elif status == "needs_more_evidence":
        string_list(
            required_evidence,
            "required_evidence",
            nonempty=True,
        )
        if terminal_reason is not None:
            raise CampaignError("needs_more_evidence terminal_reason must be null")
    elif status == "blocked":
        if not isinstance(terminal_reason, str) or not terminal_reason.strip():
            raise CampaignError("blocked checkpoint needs terminal_reason")
    elif terminal_reason is not None:
        raise CampaignError("draft_ready terminal_reason must be null")
    return status, candidates, suggestions


def run_checker(checker: Path, root: Path, *, candidates: bool) -> None:
    command = [sys.executable, str(checker), str(root), "--json"]
    if candidates:
        command.append("--candidates")
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    try:
        findings = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        detail = result.stderr.strip() or result.stdout.strip() or "no output"
        raise CampaignError(f"checker returned invalid JSON: {detail}") from error
    if not isinstance(findings, list):
        raise CampaignError("checker output must be a JSON list")
    material = [
        value
        for value in findings
        if not (
            not candidates
            and isinstance(value, dict)
            and value.get("code") in DEFERRED_CHECKER_CODES
        )
    ]
    if result.returncode != 0 and not findings:
        raise CampaignError(result.stderr.strip() or "checker failed")
    if material:
        raise CampaignError(
            "SpecSpine checker rejected publication: "
            + json.dumps(material, ensure_ascii=False)
        )


def rollback_publication(
    destinations: list[Path],
    backups: dict[Path, Path],
    sources: dict[Path, Path],
) -> None:
    for destination in reversed(destinations):
        source = sources[destination]
        source.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            os.replace(destination, source)
        backup = backups.get(destination)
        if backup is not None and backup.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(backup, destination)


def command_accept(args: argparse.Namespace) -> dict[str, Any]:
    raw = read_json(args.checkpoint)
    staging = candidate_files(args.staging_root)
    status, candidates, suggestions = validate_checkpoint(raw, staging)
    checkpoint_digest = digest_json(raw)
    if candidates:
        run_checker(args.checker, args.staging_root, candidates=True)

    backups_root = Path(tempfile.mkdtemp(prefix="specspine-map-backup."))
    destinations: list[Path] = []
    backups: dict[Path, Path] = {}
    sources: dict[Path, Path] = {}
    published: list[str] = []
    try:
        with locked_ledger(args.ledger) as ledger:
            task = require_task(ledger, args.id)
            if task["state"] != "assigned":
                raise CampaignError(f"accept requires assigned task: {args.id}")
            if task["owner"] != args.owner:
                raise CampaignError(
                    f"checkpoint owner mismatch: expected {task['owner']}, got {args.owner}"
                )
            if status == "draft_ready":
                spine_root = args.spine_root.resolve()
                plans: list[tuple[dict[str, str], Path, Path, bool]] = []
                for candidate in candidates:
                    source = staging[candidate["path"]]
                    destination = spine_root / candidate["path"]
                    exists = destination.exists()
                    if candidate["operation"] == "create" and exists:
                        raise CampaignError(f"create destination exists: {candidate['path']}")
                    if candidate["operation"] == "replace" and not exists:
                        raise CampaignError(
                            f"replace destination is missing: {candidate['path']}"
                        )
                    plans.append((candidate, source, destination, exists))
                try:
                    for candidate, source, destination, exists in plans:
                        sources[destination] = source
                        if exists:
                            backup = backups_root / candidate["path"]
                            backup.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(destination, backup)
                            backups[destination] = backup
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        os.replace(source, destination)
                        destinations.append(destination)
                        published.append(candidate["path"])
                    run_checker(args.checker, spine_root, candidates=False)
                except Exception:
                    rollback_publication(destinations, backups, sources)
                    raise
                task["state"] = "published"
                task["published"] = published
                task["producer_suggestions"] = suggestions
                ledger["publication_epoch"] += 1
                ledger["integration_pass"] = None
                for candidate in candidates:
                    ledger["publication_history"].append(
                        {
                            "task": task["id"],
                            "path": candidate["path"],
                            "operation": candidate["operation"],
                            "publication_epoch": ledger["publication_epoch"],
                        }
                    )
            elif status == "no_architectural_value":
                task["state"] = "complete"
                task["terminal_reason"] = raw["terminal_reason"]
                task["producer_suggestions"] = suggestions
            elif status == "needs_more_evidence":
                task["state"] = "todo"
                task["evidence"] = sorted(
                    set(task["evidence"])
                    | set(
                        string_list(
                            raw["required_evidence"],
                            "required_evidence",
                            nonempty=True,
                        )
                    )
                )
            else:
                task["state"] = "blocked"
                task["terminal_reason"] = raw["terminal_reason"]
                task["producer_suggestions"] = suggestions
            task["owner"] = None
            task["checkpoint_digest"] = checkpoint_digest
            save_locked(args.ledger, ledger)
            return {
                "status": "accepted",
                "task": task["id"],
                "task_state": task["state"],
                "published": published,
                "suggestions_pending_review": [
                    value["id"] for value in suggestions
                ],
                "revision": ledger["revision"],
            }
    finally:
        shutil.rmtree(backups_root, ignore_errors=True)


def command_block(args: argparse.Namespace) -> dict[str, Any]:
    with locked_ledger(args.ledger) as ledger:
        task = require_task(ledger, args.id)
        if task["state"] not in {"todo", "assigned"}:
            raise CampaignError(f"block requires todo or assigned state: {args.id}")
        task["state"] = "blocked"
        task["owner"] = None
        task["terminal_reason"] = args.reason
        save_locked(args.ledger, ledger)
        return {
            "status": "blocked",
            "task": args.id,
            "revision": ledger["revision"],
        }


def command_integration_pass(args: argparse.Namespace) -> dict[str, Any]:
    report = read_json(args.report)
    spine_root = args.spine_root.resolve()
    documents = validate_document_inventory(
        spine_root,
        report.get("evidence_inspected"),
        field="integration evidence_inspected",
    )
    reviews = report.get("task_reviews")
    if not isinstance(reviews, list):
        raise CampaignError("integration task_reviews must be a list")
    suggestion_reviews = report.get("suggestion_reviews")
    if not isinstance(suggestion_reviews, list):
        raise CampaignError("integration suggestion_reviews must be a list")
    raw_todo = report.get("todo")
    if not isinstance(raw_todo, list):
        raise CampaignError("integration todo must be a list")
    validate_empty_reason(
        raw_todo,
        report.get("terminal_reason"),
        prefix="no integration-derived ToDo: ",
    )
    organization = report.get("organization")
    if (
        not isinstance(organization, dict)
        or organization.get("status")
        not in {"flat_sufficient", "directories_sufficient", "reorganized"}
        or not isinstance(organization.get("reason"), str)
        or not organization["reason"].strip()
    ):
        raise CampaignError("integration needs a reasoned organization assessment")
    run_checker(args.checker, spine_root, candidates=False)

    normalized_reviews: dict[str, dict[str, str]] = {}
    for value in reviews:
        if not isinstance(value, dict):
            raise CampaignError("task review must be an object")
        task_id = validate_id(value.get("task"))
        disposition = value.get("disposition")
        reason = value.get("reason")
        if disposition not in REVIEW_DISPOSITIONS:
            raise CampaignError(
                f"invalid integration disposition for {task_id}: {disposition!r}"
            )
        if not isinstance(reason, str) or not reason.strip():
            raise CampaignError(f"task review needs a reason: {task_id}")
        if task_id in normalized_reviews:
            raise CampaignError(f"duplicate task review: {task_id}")
        normalized_reviews[task_id] = {
            "disposition": disposition,
            "reason": reason.strip(),
        }

    normalized_suggestions: dict[tuple[str, str], dict[str, str]] = {}
    for value in suggestion_reviews:
        if not isinstance(value, dict):
            raise CampaignError("suggestion review must be an object")
        task_id = validate_id(value.get("task"))
        suggestion_id = validate_id(value.get("suggestion"))
        disposition = value.get("disposition")
        reason = value.get("reason")
        queued_task = value.get("todo")
        if disposition not in SUGGESTION_DISPOSITIONS:
            raise CampaignError(
                f"invalid suggestion disposition for {suggestion_id}: {disposition!r}"
            )
        if not isinstance(reason, str) or not reason.strip():
            raise CampaignError(
                f"suggestion review needs a reason: {suggestion_id}"
            )
        if disposition == "queued":
            queued_task = validate_id(queued_task)
        elif queued_task is not None:
            raise CampaignError(
                f"non-queued suggestion must not name ToDo: {suggestion_id}"
            )
        key = (task_id, suggestion_id)
        if key in normalized_suggestions:
            raise CampaignError(f"duplicate suggestion review: {key}")
        normalized_suggestions[key] = {
            "disposition": disposition,
            "reason": reason.strip(),
            "todo": queued_task,
        }

    with locked_ledger(args.ledger) as ledger:
        published = {
            task["id"]: task
            for task in ledger["tasks"].values()
            if task["state"] == "published"
        }
        if set(normalized_reviews) != set(published):
            raise CampaignError(
                "integration must review every published task; "
                f"missing={sorted(set(published) - set(normalized_reviews))}, "
                f"unknown={sorted(set(normalized_reviews) - set(published))}"
            )
        expected_suggestions = {
            (task_id, suggestion["id"])
            for task_id, task in published.items()
            for suggestion in task["producer_suggestions"]
        }
        if set(normalized_suggestions) != expected_suggestions:
            raise CampaignError(
                "integration must disposition every producer suggestion; "
                f"missing={sorted(expected_suggestions - set(normalized_suggestions))}, "
                f"unknown={sorted(set(normalized_suggestions) - expected_suggestions)}"
            )
        added = add_tasks(
            ledger,
            raw_todo,
            source=f"integration-{ledger['publication_epoch']}",
        )
        added_set = set(added) | {
            validate_id(value.get("id"))
            for value in raw_todo
            if isinstance(value, dict)
        }
        for key, review in normalized_suggestions.items():
            if review["disposition"] == "queued" and review["todo"] not in added_set:
                raise CampaignError(
                    f"queued suggestion {key} has no matching integration ToDo"
                )
        for task_id, task in published.items():
            task["state"] = "complete"
            task["terminal_reason"] = normalized_reviews[task_id]["reason"]
            task["suggestion_reviews"] = {
                suggestion_id: normalized_suggestions[(task_id, suggestion_id)]
                for candidate_task, suggestion_id in expected_suggestions
                if candidate_task == task_id
            }
        ledger["integration_pass"] = {
            "publication_epoch": ledger["publication_epoch"],
            "documents": documents,
            "task_reviews": normalized_reviews,
            "suggestion_reviews": {
                f"{task}:{suggestion}": value
                for (task, suggestion), value in normalized_suggestions.items()
            },
            "todo": sorted(added_set),
            "terminal_reason": report.get("terminal_reason"),
            "organization": organization,
        }
        save_locked(args.ledger, ledger)
        return {
            "status": "integrated",
            "reviewed_tasks": sorted(published),
            "added_todo": added,
            "revision": ledger["revision"],
        }


def current_inventory(ledger: dict[str, Any]) -> bool:
    source = ledger.get("source_pass")
    if not isinstance(source, dict):
        return False
    try:
        current = repository_inventory(
            Path(source["repository_root"]),
            spine_root=Path(source["spine_root"]),
        )
    except (CampaignError, KeyError, OSError):
        return False
    return current["digest"] == source.get("inventory_digest")


def current_integration(ledger: dict[str, Any]) -> bool:
    integration = ledger.get("integration_pass")
    source = ledger.get("source_pass")
    if (
        not isinstance(integration, dict)
        or not isinstance(source, dict)
        or integration.get("publication_epoch") != ledger["publication_epoch"]
        or integration.get("todo")
    ):
        return False
    try:
        current_documents = document_hashes(Path(source["spine_root"]))
    except (KeyError, OSError):
        return False
    return current_documents == integration.get("documents")


def terminal_gates(ledger: dict[str, Any]) -> dict[str, bool]:
    tasks = list(ledger["tasks"].values())
    return {
        "todo_empty": not any(task["state"] == "todo" for task in tasks),
        "producers_finished": not any(
            task["state"] == "assigned" for task in tasks
        ),
        "publications_integrated": not any(
            task["state"] == "published" for task in tasks
        ),
        "no_blocked_tasks": not any(
            task["state"] == "blocked" for task in tasks
        ),
        "source_inventory_current": current_inventory(ledger),
        "integration_current": current_integration(ledger),
    }


def command_summary(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    gates = terminal_gates(ledger)
    states = {
        state: sorted(
            task["id"]
            for task in ledger["tasks"].values()
            if task["state"] == state
        )
        for state in sorted(TASK_STATES)
    }
    terminal: str | None = None
    if all(gates.values()):
        terminal = "inventory_closed"
    elif (
        gates["todo_empty"]
        and gates["producers_finished"]
        and gates["publications_integrated"]
        and not gates["no_blocked_tasks"]
    ):
        terminal = "blocked"
    return {
        "campaign_id": ledger["campaign_id"],
        "revision": ledger["revision"],
        "states": states,
        "ready": states["todo"],
        "terminal_gates": gates,
        "terminal": terminal,
    }


def command_coverage_report(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    summary = command_summary(args)
    inventory = ledger.get("source_pass", {}).get("inventory", {})
    counts = {
        classification: sum(
            1
            for value in inventory.values()
            if value.get("classification") == classification
        )
        for classification in sorted(SOURCE_CLASSIFICATIONS)
    }
    return {
        "campaign_id": ledger["campaign_id"],
        "scope": ledger["scope"],
        "terminal": summary["terminal"],
        "terminal_gates": summary["terminal_gates"],
        "task_states": {
            state: len(values) for state, values in summary["states"].items()
        },
        "inventory_classifications": counts,
        "coverage_claim": (
            "inventory_closed"
            if summary["terminal"] == "inventory_closed"
            else "blocked"
            if summary["terminal"] == "blocked"
            else "partial"
        ),
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("ledger", type=Path)
    init.add_argument("--scope", required=True)
    init.add_argument("--root-question", required=True)
    init.add_argument(
        "--spine-state",
        choices=("empty", "existing"),
        default="empty",
    )

    seed = sub.add_parser("seed-from-spine")
    seed.add_argument("ledger", type=Path)
    seed.add_argument("spine_root", type=Path)
    seed.add_argument("plan", type=Path)

    inventory = sub.add_parser("inventory")
    inventory.add_argument("repository_root", type=Path)
    inventory.add_argument("--spine-root", type=Path)

    source = sub.add_parser("source-pass")
    source.add_argument("ledger", type=Path)
    source.add_argument("repository_root", type=Path)
    source.add_argument("spine_root", type=Path)
    source.add_argument("report", type=Path)

    add = sub.add_parser("todo-add")
    add.add_argument("ledger", type=Path)
    add.add_argument("id")
    add.add_argument("--question", required=True)
    add.add_argument("--reason", required=True)
    add.add_argument("--origin", required=True)
    add.add_argument("--evidence", action="append", default=[])
    add.add_argument("--document", action="append", default=[])
    add.add_argument("--exclude", action="append", default=[])

    todo = sub.add_parser("todo")
    todo.add_argument("ledger", type=Path)
    todo.add_argument("--all", action="store_true")

    ready = sub.add_parser("ready")
    ready.add_argument("ledger", type=Path)

    assign = sub.add_parser("assign")
    assign.add_argument("ledger", type=Path)
    assign.add_argument("id")
    assign.add_argument("--owner", required=True)

    release = sub.add_parser("release")
    release.add_argument("ledger", type=Path)
    release.add_argument("id")

    accept = sub.add_parser("accept")
    accept.add_argument("ledger", type=Path)
    accept.add_argument("id")
    accept.add_argument("checkpoint", type=Path)
    accept.add_argument("staging_root", type=Path)
    accept.add_argument("spine_root", type=Path)
    accept.add_argument("--owner", required=True)
    accept.add_argument(
        "--checker",
        type=Path,
        default=Path(__file__).with_name("check_spine.py"),
    )

    block = sub.add_parser("block")
    block.add_argument("ledger", type=Path)
    block.add_argument("id")
    block.add_argument("--reason", required=True)

    integration = sub.add_parser("integration-pass")
    integration.add_argument("ledger", type=Path)
    integration.add_argument("spine_root", type=Path)
    integration.add_argument("report", type=Path)
    integration.add_argument(
        "--checker",
        type=Path,
        default=Path(__file__).with_name("check_spine.py"),
    )

    summary = sub.add_parser("summary")
    summary.add_argument("ledger", type=Path)

    coverage = sub.add_parser("coverage-report")
    coverage.add_argument("ledger", type=Path)

    return result


def main() -> int:
    args = parser().parse_args()
    commands = {
        "init": command_init,
        "seed-from-spine": command_seed_from_spine,
        "inventory": command_inventory,
        "source-pass": command_source_pass,
        "todo-add": command_todo_add,
        "todo": command_todo,
        "ready": command_ready,
        "assign": command_assign,
        "release": command_release,
        "accept": command_accept,
        "block": command_block,
        "integration-pass": command_integration_pass,
        "summary": command_summary,
        "coverage-report": command_coverage_report,
    }
    try:
        value = commands[args.command](args)
    except (CampaignError, OSError, UnicodeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(value, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
