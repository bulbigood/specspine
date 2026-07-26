#!/usr/bin/env python3
"""Run a durable exhaustive Map campaign with transactional checkpoint acceptance."""

from __future__ import annotations

import argparse
import contextlib
import copy
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path, PurePosixPath
from typing import Any, Iterator


SCHEMA_VERSION = 1
STATES = {"queued", "active", "locally_saturated", "blocked", "complete"}
BRANCH_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TERMINAL_REASON = re.compile(r"^no useful node:\s+\S")
DEFERRED_CODES = {"ID_SECTION_UNVERIFIED", "UNREACHABLE_SPEC"}
QUALITY_GATES = {
    "ownership_coverage",
    "orientation",
    "information_gain",
    "change_utility",
    "non_duplication",
}
QUALITY_STATUSES = {"pass", "gap", "not_applicable"}
SOURCE_CLASSIFICATIONS = {
    "summarized",
    "queued",
    "neighbor_owned",
    "generated",
    "vendored",
    "test_only",
    "no_durable_architecture_value",
}
SPINE_STATES = {"empty", "existing"}
DOCUMENTATION_SIGNALS = {
    "coverage_gap",
    "open_question",
    "broad_owner",
    "weak_relationship",
    "missing_depth",
    "stale_evidence",
    "navigation_gap",
    "semantic_inconsistency",
}


class CampaignError(ValueError):
    pass


def emit(value: Any, *, error: bool = False) -> None:
    print(
        json.dumps(value, ensure_ascii=False, sort_keys=True),
        file=sys.stderr if error else sys.stdout,
    )


def validate_id(value: str) -> str:
    if not BRANCH_ID.fullmatch(value):
        raise CampaignError(f"invalid branch id: {value!r}")
    return value


def validate_path(value: str) -> str:
    path = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise CampaignError(f"invalid relative path: {value!r}")
    return path.as_posix()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CampaignError(f"cannot read JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise CampaignError(f"JSON root must be an object: {path}")
    return value


def load(path: Path) -> dict[str, Any]:
    ledger = read_json(path)
    if ledger.get("schema_version") != SCHEMA_VERSION:
        raise CampaignError("unsupported campaign schema")
    if not isinstance(ledger.get("branches"), dict):
        raise CampaignError("campaign branches must be an object")
    return ledger


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False)
            stream.write("\n")
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


@contextlib.contextmanager
def locked(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(path.name + ".lock")
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def save(path: Path, ledger: dict[str, Any]) -> None:
    ledger["revision"] = int(ledger.get("revision", 0)) + 1
    atomic_write(path, ledger)


def new_branch(
    branch_id: str,
    parent: str | None,
    question: str,
    *,
    state: str = "queued",
    **extra: Any,
) -> dict[str, Any]:
    return {
        "id": branch_id,
        "parent": parent,
        "question": question,
        "state": state,
        "owner": None,
        "terminal_reason": None,
        "published": [],
        **extra,
    }


def require_branch(ledger: dict[str, Any], branch_id: str) -> dict[str, Any]:
    try:
        return ledger["branches"][branch_id]
    except KeyError as error:
        raise CampaignError(f"unknown branch: {branch_id}") from error


def affinity_domain(ledger: dict[str, Any], branch_id: str) -> str:
    root = ledger["root"]
    current = require_branch(ledger, branch_id)
    while current.get("parent") not in {None, root}:
        current = require_branch(ledger, current["parent"])
    return current["id"]


def mutate(path: Path, action) -> dict[str, Any]:
    with locked(path):
        ledger = load(path)
        changed = action(ledger)
        if changed:
            save(path, ledger)
        return ledger


def command_init(args: argparse.Namespace) -> dict[str, Any]:
    with locked(args.ledger):
        if args.ledger.exists():
            raise CampaignError(f"campaign already exists: {args.ledger}")
        ledger = {
            "schema_version": SCHEMA_VERSION,
            "campaign_id": str(uuid.uuid4()),
            "revision": 1,
            "frontier_epoch": 0,
            "discovery_pass": None,
            "documentation_pass": None,
            "integration_pass": None,
            "spine_state": args.spine_state,
            "documentation_plan": None,
            "scope": args.scope,
            "root": "root",
            "branches": {
                "root": new_branch(
                    "root",
                    None,
                    args.root_question,
                    state="active",
                    origin="operator",
                )
            },
        }
        atomic_write(args.ledger, ledger)
        return ledger


def validate_documentation_plan(
    spine_root_value: Path, plan_value: Path
) -> tuple[
    dict[str, Any], dict[str, Path], list[dict[str, Any]], str | None
]:
    plan = read_json(plan_value)
    spine_root = spine_root_value.resolve()
    if not spine_root.is_dir():
        raise CampaignError(f"Spine root is not a directory: {spine_root_value}")
    markdown = {
        path.relative_to(spine_root).as_posix(): path
        for path in spine_root.rglob("*.md")
        if path.is_file()
    }
    inspected = plan.get("evidence_inspected")
    if (
        not isinstance(inspected, list)
        or not inspected
        or any(not isinstance(value, str) for value in inspected)
    ):
        raise CampaignError("documentation plan needs nonempty evidence_inspected")
    inspected_paths = {validate_path(value) for value in inspected}
    if inspected_paths != set(markdown):
        missing = sorted(set(markdown) - inspected_paths)
        unknown = sorted(inspected_paths - set(markdown))
        raise CampaignError(
            "documentation plan does not cover the live Spine; "
            f"missing={missing}, unknown={unknown}"
        )
    directions = plan.get("directions")
    if not isinstance(directions, list):
        raise CampaignError("documentation plan directions must be a list")
    terminal_reason = plan.get("terminal_reason")
    if not directions and (
        not isinstance(terminal_reason, str)
        or not terminal_reason.startswith("no documentation-derived direction: ")
    ):
        raise CampaignError(
            "an empty documentation plan needs "
            "'no documentation-derived direction: <reason>'"
        )

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in directions:
        if not isinstance(raw, dict):
            raise CampaignError("documentation direction must be an object")
        branch_id = validate_id(raw.get("id", ""))
        if branch_id in seen:
            raise CampaignError(f"duplicate documentation direction: {branch_id}")
        seen.add(branch_id)
        question = raw.get("question")
        documents = raw.get("documents")
        signals = raw.get("signals")
        if not isinstance(question, str) or not question.strip():
            raise CampaignError(f"direction {branch_id} needs a question")
        if (
            not isinstance(documents, list)
            or not documents
            or any(not isinstance(value, str) for value in documents)
        ):
            raise CampaignError(f"direction {branch_id} needs owner documents")
        owner_documents = [validate_path(value) for value in documents]
        unknown_documents = sorted(set(owner_documents) - set(markdown))
        if unknown_documents:
            raise CampaignError(
                f"direction {branch_id} has unknown documents: {unknown_documents}"
            )
        if not isinstance(signals, list) or not signals:
            raise CampaignError(f"direction {branch_id} needs gap signals")
        normalized_signals: list[dict[str, str]] = []
        for signal in signals:
            if not isinstance(signal, dict):
                raise CampaignError(f"direction {branch_id} signal must be an object")
            kind = signal.get("type")
            detail = signal.get("detail")
            if kind not in DOCUMENTATION_SIGNALS:
                raise CampaignError(
                    f"direction {branch_id} has invalid signal type: {kind!r}"
                )
            if not isinstance(detail, str) or not detail.strip():
                raise CampaignError(
                    f"direction {branch_id} signal needs nonempty detail"
                )
            normalized_signals.append({"type": kind, "detail": detail})
        normalized.append(
            {
                "id": branch_id,
                "question": question,
                "documents": owner_documents,
                "signals": normalized_signals,
            }
        )
    return plan, markdown, normalized, terminal_reason


def documentation_snapshot(
    plan: dict[str, Any],
    markdown: dict[str, Path],
    directions: list[dict[str, Any]],
    terminal_reason: str | None,
) -> dict[str, Any]:
    return {
        "digest": hashlib.sha256(
            json.dumps(plan, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest(),
        "documents": {
            relative: hashlib.sha256(path.read_bytes()).hexdigest()
            for relative, path in sorted(markdown.items())
        },
        "directions": directions,
        "terminal_reason": terminal_reason,
    }


def command_seed_from_spine(args: argparse.Namespace) -> dict[str, Any]:
    plan, markdown, normalized, terminal_reason = validate_documentation_plan(
        args.spine_root, args.plan
    )

    def action(ledger: dict[str, Any]) -> bool:
        if ledger.get("spine_state") != "existing":
            raise CampaignError("seed-from-spine requires --spine-state existing")
        if ledger.get("documentation_plan") is not None:
            raise CampaignError("documentation plan is already recorded")
        if set(ledger["branches"]) != {ledger["root"]}:
            raise CampaignError(
                "documentation plan must be recorded before other branches"
            )
        root = require_branch(ledger, ledger["root"])
        if root["state"] != "active":
            raise CampaignError("root branch is not active")
        for direction in normalized:
            ledger["branches"][direction["id"]] = new_branch(
                direction["id"],
                ledger["root"],
                direction["question"],
                origin="existing Spine: " + ", ".join(direction["documents"]),
                namespace=None,
                prerequisite=None,
                resolution=None,
                document=None,
                plan_origin="existing_spine",
                plan_documents=direction["documents"],
                plan_signals=direction["signals"],
            )
        ledger["documentation_plan"] = documentation_snapshot(
            plan, markdown, normalized, terminal_reason
        )
        ledger["frontier_epoch"] = int(ledger.get("frontier_epoch", 0)) + len(
            normalized
        )
        return True

    ledger = mutate(args.ledger, action)
    return {
        "status": "seeded",
        "campaign_id": ledger.get("campaign_id"),
        "documents": len(markdown),
        "directions": [value["id"] for value in normalized],
        "revision": ledger["revision"],
    }


def command_documentation_pass(args: argparse.Namespace) -> dict[str, Any]:
    plan, markdown, normalized, terminal_reason = validate_documentation_plan(
        args.spine_root, args.plan
    )

    def action(ledger: dict[str, Any]) -> bool:
        unfinished = sorted(
            item["id"]
            for item in ledger["branches"].values()
            if item["id"] != ledger["root"] and item["state"] != "complete"
        )
        if unfinished:
            raise CampaignError(
                "documentation pass requires all producer branches complete: "
                + ", ".join(unfinished)
            )
        if (
            ledger.get("spine_state") == "existing"
            and ledger.get("documentation_plan") is None
        ):
            raise CampaignError("initial seed-from-spine plan is missing")
        snapshot = documentation_snapshot(
            plan, markdown, normalized, terminal_reason
        )
        ledger.setdefault("documentation_review_history", []).append(
            {
                "frontier_epoch": ledger["frontier_epoch"],
                **snapshot,
            }
        )
        if normalized:
            for direction in normalized:
                if direction["id"] in ledger["branches"]:
                    raise CampaignError(
                        "documentation review direction must use a new branch id: "
                        + direction["id"]
                    )
                ledger["branches"][direction["id"]] = new_branch(
                    direction["id"],
                    ledger["root"],
                    direction["question"],
                    origin="final Spine review: "
                    + ", ".join(direction["documents"]),
                    namespace=None,
                    prerequisite=None,
                    resolution=None,
                    document=None,
                    plan_origin="documentation_review",
                    plan_documents=direction["documents"],
                    plan_signals=direction["signals"],
                )
            ledger["frontier_epoch"] += len(normalized)
            ledger["discovery_pass"] = None
            ledger["documentation_pass"] = None
            ledger["integration_pass"] = None
        else:
            ledger["documentation_pass"] = {
                "frontier_epoch": ledger["frontier_epoch"],
                **snapshot,
            }
        return True

    ledger = mutate(args.ledger, action)
    return {
        "status": "gaps_found" if normalized else "no_gaps",
        "campaign_id": ledger.get("campaign_id"),
        "documents": len(markdown),
        "directions": [value["id"] for value in normalized],
        "revision": ledger["revision"],
    }


def command_add(args: argparse.Namespace, *, documented: bool = False) -> dict[str, Any]:
    def action(ledger: dict[str, Any]) -> bool:
        if (
            ledger.get("spine_state") == "existing"
            and ledger.get("documentation_plan") is None
        ):
            raise CampaignError(
                "record the documentation-first frontier with seed-from-spine "
                "before adding source-derived branches"
            )
        if documented and any(
            branch.get("published")
            or (
                branch["id"] != ledger["root"]
                and branch.get("state") in {"active", "locally_saturated", "blocked"}
            )
            for branch in ledger["branches"].values()
        ):
            raise CampaignError(
                "documented seeding is allowed only before assignment or publication"
            )
        branch_id = validate_id(args.id)
        parent = require_branch(ledger, args.parent)
        if parent["state"] not in {"queued", "active"}:
            raise CampaignError(f"parent is not open: {args.parent}")
        if args.prerequisite:
            require_branch(ledger, args.prerequisite)
        candidate = new_branch(
            branch_id,
            args.parent,
            args.question,
            state="complete" if documented else "queued",
            origin=args.origin,
            namespace=args.namespace,
            prerequisite=args.prerequisite,
            resolution="already_documented" if documented else None,
            document=args.document if documented else None,
        )
        existing = ledger["branches"].get(branch_id)
        if existing is not None:
            if existing != candidate:
                raise CampaignError(f"conflicting branch id: {branch_id}")
            return False
        ledger["branches"][branch_id] = candidate
        validate_dependency_graph(ledger)
        ledger["frontier_epoch"] += 1
        ledger["discovery_pass"] = None
        ledger["documentation_pass"] = None
        ledger["integration_pass"] = None
        return True

    return mutate(args.ledger, action)


def command_assign(args: argparse.Namespace) -> dict[str, Any]:
    def action(ledger: dict[str, Any]) -> bool:
        if (
            ledger.get("spine_state") == "existing"
            and ledger.get("documentation_plan") is None
            and args.id != ledger["root"]
        ):
            raise CampaignError(
                "record the documentation-first frontier with seed-from-spine "
                "before assigning producers"
            )
        item = require_branch(ledger, args.id)
        if item["state"] != "queued":
            raise CampaignError(f"assign requires queued state: {args.id}")
        if not args.owner.strip():
            raise CampaignError("owner must not be empty")
        active_for_owner = sorted(
            branch["id"]
            for branch in ledger["branches"].values()
            if branch.get("owner") == args.owner
            and branch["state"] == "active"
            and branch["id"] != args.id
        )
        if active_for_owner:
            raise CampaignError(
                f"producer is still active on {active_for_owner}; "
                "wait for its terminal checkpoint"
            )
        assignments = ledger.setdefault("producer_assignments", {})
        previous_assignments = assignments.get(args.owner, [])
        producer_seen = bool(previous_assignments) or args.owner in ledger.get(
            "producer_affinity", {}
        )
        if (
            producer_seen
            and args.id not in previous_assignments
            and item.get("discovered_by_owner") != args.owner
        ):
            raise CampaignError(
                f"fresh producer required for {args.id}: {args.owner} did not "
                "discover this branch in its own checkpoint"
            )
        domain = affinity_domain(ledger, args.id)
        affinity = ledger.setdefault("producer_affinity", {})
        previous = affinity.get(args.owner)
        if previous is not None and previous != domain:
            raise CampaignError(
                f"producer affinity violation: {args.owner} owns {previous}, "
                f"cannot assign {domain}"
            )
        affinity[args.owner] = domain
        if args.id not in previous_assignments:
            assignments[args.owner] = [*previous_assignments, args.id]
        item["state"] = "active"
        item["owner"] = args.owner
        return True

    return mutate(args.ledger, action)


def command_release(args: argparse.Namespace) -> dict[str, Any]:
    def action(ledger: dict[str, Any]) -> bool:
        item = require_branch(ledger, args.id)
        if item["state"] not in {"active", "blocked"}:
            raise CampaignError(f"release requires active or blocked state: {args.id}")
        item["state"] = "queued"
        item["owner"] = None
        item["terminal_reason"] = None
        return True

    return mutate(args.ledger, action)


def command_block(args: argparse.Namespace) -> dict[str, Any]:
    def action(ledger: dict[str, Any]) -> bool:
        item = require_branch(ledger, args.id)
        if item["state"] not in {"queued", "active"}:
            raise CampaignError(f"block requires queued or active state: {args.id}")
        item["state"] = "blocked"
        item["owner"] = None
        item["terminal_reason"] = args.reason
        return True

    return mutate(args.ledger, action)


def candidate_files(root: Path) -> dict[str, Path]:
    if not root.is_dir():
        raise CampaignError(f"staging root is not a directory: {root}")
    result: dict[str, Path] = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise CampaignError(f"staging contains a symbolic link: {path}")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = path
    return result


def validate_quality_gate(raw: dict[str, Any], *, terminal: bool) -> None:
    quality = raw.get("quality_gate")
    if not isinstance(quality, dict) or set(quality) != QUALITY_GATES:
        raise CampaignError(
            "checkpoint quality_gate requires exactly: "
            + ", ".join(sorted(QUALITY_GATES))
        )
    gaps: list[str] = []
    for name in sorted(QUALITY_GATES):
        value = quality[name]
        if not isinstance(value, dict) or set(value) != {"status", "reason"}:
            raise CampaignError(
                f"quality gate {name} requires only status and reason"
            )
        if value["status"] not in QUALITY_STATUSES:
            raise CampaignError(
                f"invalid quality gate status for {name}: {value['status']!r}"
            )
        if not isinstance(value["reason"], str) or not value["reason"].strip():
            raise CampaignError(f"quality gate reason is missing: {name}")
        if value["status"] == "gap":
            gaps.append(name)
    if terminal and gaps:
        raise CampaignError(
            "terminal checkpoint has unresolved quality gaps: "
            + ", ".join(gaps)
        )


def validate_source_coverage(raw: dict[str, Any]) -> None:
    coverage = raw.get("source_coverage")
    if not isinstance(coverage, list) or not coverage:
        raise CampaignError("checkpoint source_coverage must be a nonempty list")
    for index, value in enumerate(coverage):
        if not isinstance(value, dict):
            raise CampaignError(f"source_coverage[{index}] must be an object")
        area = value.get("area", value.get("path"))
        classification = value.get("classification")
        reason = value.get("reason", value.get("coverage"))
        if not isinstance(area, str) or not area.strip():
            raise CampaignError(f"source_coverage[{index}] area/path is missing")
        if classification not in SOURCE_CLASSIFICATIONS:
            raise CampaignError(
                f"invalid source classification at {area}: {classification!r}"
            )
        if not isinstance(reason, str) or not reason.strip():
            raise CampaignError(f"source_coverage reason is missing: {area}")


def validate_checkpoint(
    raw: dict[str, Any], staging: dict[str, Path]
) -> tuple[str, list[dict[str, str]], list[dict[str, Any]], str | None]:
    status = raw.get("status")
    if status not in {
        "continuing",
        "publish_and_locally_saturate",
        "locally_saturated",
        "blocked",
    }:
        raise CampaignError(f"invalid checkpoint status: {status!r}")
    evidence = raw.get("evidence_inspected")
    if not isinstance(evidence, list) or not evidence or not all(
        isinstance(value, str) and value.strip() for value in evidence
    ):
        raise CampaignError("checkpoint evidence_inspected must be nonempty")
    responsibilities = raw.get("mapped_responsibilities")
    if not isinstance(responsibilities, list) or not responsibilities or not all(
        isinstance(value, str) and value.strip() for value in responsibilities
    ):
        raise CampaignError("checkpoint mapped_responsibilities must be nonempty")
    relationships = raw.get("relationships")
    if not isinstance(relationships, list):
        raise CampaignError("checkpoint relationships must be a list")
    unresolved = raw.get("unresolved")
    if not isinstance(unresolved, list):
        raise CampaignError("checkpoint unresolved must be a list")
    validate_source_coverage(raw)
    raw_candidates = raw.get("candidates")
    if not isinstance(raw_candidates, list):
        raise CampaignError("checkpoint candidates must be a list")
    candidates: list[dict[str, str]] = []
    for value in raw_candidates:
        if not isinstance(value, dict) or set(value) != {"path", "operation"}:
            raise CampaignError("each candidate requires only path and operation")
        path = validate_path(value["path"])
        operation = value["operation"]
        if operation not in {"create", "replace"}:
            raise CampaignError(f"invalid candidate operation: {operation!r}")
        if path == "README.md":
            raise CampaignError("producer must not publish README.md")
        candidates.append({"path": path, "operation": operation})
    paths = [item["path"] for item in candidates]
    if len(paths) != len(set(paths)) or set(paths) != set(staging):
        raise CampaignError(
            f"checkpoint/staging paths differ: checkpoint={sorted(paths)}, "
            f"staging={sorted(staging)}"
        )
    frontier = raw.get("coverage_frontier", [])
    if not isinstance(frontier, list):
        raise CampaignError("coverage_frontier must be a list")
    inspected_evidence = set(evidence)
    for value in frontier:
        if not isinstance(value, dict):
            raise CampaignError("coverage_frontier entries must be objects")
        child_evidence = value.get("evidence")
        if (
            not isinstance(child_evidence, list)
            or not child_evidence
            or any(not isinstance(item, str) for item in child_evidence)
        ):
            raise CampaignError("coverage_frontier evidence must be nonempty")
        if not set(child_evidence).issubset(inspected_evidence):
            raise CampaignError(
                "coverage_frontier may cite only evidence inspected by this producer"
            )
    terminal_reason = raw.get("terminal_reason")
    if candidates and status not in {
        "continuing",
        "publish_and_locally_saturate",
    }:
        raise CampaignError(
            "candidate-bearing checkpoint must continue or publish-and-saturate"
        )
    if not candidates and status == "continuing":
        raise CampaignError("continuing checkpoint requires a candidate")
    if status == "publish_and_locally_saturate" and not candidates:
        raise CampaignError("publish-and-saturate checkpoint requires a candidate")
    if status in {"locally_saturated", "publish_and_locally_saturate"} and (
        not isinstance(terminal_reason, str)
        or not TERMINAL_REASON.match(terminal_reason.strip())
    ):
        raise CampaignError(
            "terminal saturation requires 'no useful node: <reason>'"
        )
    if status == "blocked" and (
        not isinstance(terminal_reason, str) or not terminal_reason.strip()
    ):
        raise CampaignError("blocked checkpoint requires terminal_reason")
    continuation = raw.get("continuation")
    if status == "continuing" and (
        not isinstance(continuation, str) or not continuation.strip()
    ):
        raise CampaignError("continuing checkpoint requires continuation")
    if status != "continuing" and continuation is not None:
        raise CampaignError("terminal checkpoint continuation must be null")
    validate_quality_gate(
        raw,
        terminal=status in {
            "locally_saturated",
            "publish_and_locally_saturate",
        },
    )
    return status, candidates, frontier, terminal_reason


def dependency_edges(ledger: dict[str, Any]) -> dict[str, set[str]]:
    edges = {branch_id: set() for branch_id in ledger["branches"]}
    for branch_id, item in ledger["branches"].items():
        parent = item.get("parent")
        if parent is not None:
            if parent not in edges:
                raise CampaignError(f"unknown parent for {branch_id}: {parent}")
            edges[parent].add(branch_id)
        prerequisite = item.get("prerequisite")
        if prerequisite:
            if prerequisite not in edges:
                raise CampaignError(
                    f"unknown prerequisite for {branch_id}: {prerequisite}"
                )
            edges[branch_id].add(prerequisite)
    return edges


def dependency_cycles(ledger: dict[str, Any]) -> list[list[str]]:
    edges = dependency_edges(ledger)
    state: dict[str, int] = {}
    stack: list[str] = []
    positions: dict[str, int] = {}
    cycles: set[tuple[str, ...]] = set()

    def canonical_cycle(values: list[str]) -> tuple[str, ...]:
        body = values[:-1]
        rotations = [tuple(body[index:] + body[:index]) for index in range(len(body))]
        return min(rotations)

    def visit(branch_id: str) -> None:
        state[branch_id] = 1
        positions[branch_id] = len(stack)
        stack.append(branch_id)
        for target in sorted(edges[branch_id]):
            target_state = state.get(target, 0)
            if target_state == 0:
                visit(target)
            elif target_state == 1:
                cycle = stack[positions[target] :] + [target]
                cycles.add(canonical_cycle(cycle))
        stack.pop()
        positions.pop(branch_id, None)
        state[branch_id] = 2

    for branch_id in sorted(edges):
        if state.get(branch_id, 0) == 0:
            visit(branch_id)
    return [list(value) + [value[0]] for value in sorted(cycles)]


def validate_dependency_graph(ledger: dict[str, Any]) -> None:
    cycles = dependency_cycles(ledger)
    if cycles:
        rendered = [" -> ".join(value) for value in cycles]
        raise CampaignError("campaign dependency cycle: " + "; ".join(rendered))


def run_checker(
    checker: Path,
    spine: Path,
    *,
    staging: Path | None = None,
    replacements: list[str] | None = None,
    ignored: set[str] | None = None,
) -> None:
    command = [sys.executable, str(checker), str(spine)]
    if staging is not None:
        command.extend(["--candidates", str(staging)])
    for path in replacements or []:
        command.extend(["--replace-existing", path])
    command.append("--json")
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    try:
        findings = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        detail = result.stderr.strip() or result.stdout.strip() or "no output"
        raise CampaignError(f"checker returned invalid JSON: {detail}") from error
    blocking = [
        finding
        for finding in findings
        if finding.get("code") not in (ignored or set())
    ]
    if blocking or (result.returncode != 0 and not findings):
        raise CampaignError(
            "checker blocked acceptance: "
            + json.dumps(blocking or findings, ensure_ascii=False)
        )


def checkpoint_digest(raw: dict[str, Any], files: dict[str, Path]) -> str:
    digest = hashlib.sha256()
    digest.update(
        json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        .encode("utf-8")
    )
    for relative, path in sorted(files.items()):
        digest.update(relative.encode("utf-8"))
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def add_frontier(ledger: dict[str, Any], parent: str, values: list[Any]) -> list[str]:
    added: list[str] = []
    for value in values:
        if not isinstance(value, dict):
            raise CampaignError("coverage_frontier entries must be objects")
        classification = value.get("classification")
        if classification not in {"fork_candidate", "documented", "blocked"}:
            raise CampaignError(f"invalid frontier classification: {classification!r}")
        branch_id = validate_id(value.get("id", ""))
        question = value.get("question")
        evidence = value.get("evidence")
        if not isinstance(question, str) or not question.strip():
            raise CampaignError(f"frontier question is missing: {branch_id}")
        if not isinstance(evidence, list) or not evidence:
            raise CampaignError(f"frontier evidence is missing: {branch_id}")
        reason = value.get("reason")
        if classification == "fork_candidate" and (
            not isinstance(reason, str) or not reason.strip()
        ):
            raise CampaignError(
                f"fork frontier requires a semantic relation reason: {branch_id}"
            )
        state = "complete" if classification == "documented" else (
            "blocked" if classification == "blocked" else "queued"
        )
        if classification == "documented" and not value.get("document"):
            raise CampaignError(
                f"documented frontier requires document: {branch_id}"
            )
        prerequisite = value.get("prerequisite")
        if prerequisite:
            require_branch(ledger, prerequisite)
        candidate = new_branch(
            branch_id,
            parent,
            question.strip(),
            state=state,
            origin=", ".join(str(item) for item in evidence),
            namespace=value.get("namespace"),
            prerequisite=prerequisite,
            resolution="already_documented" if state == "complete" else None,
            document=value.get("document"),
            discovered_from_branch=parent,
            discovered_by_owner=require_branch(ledger, parent).get("owner"),
            discovery_reason=reason.strip() if isinstance(reason, str) else None,
        )
        if state == "blocked":
            if not isinstance(reason, str) or not reason.strip():
                raise CampaignError(f"blocked frontier requires reason: {branch_id}")
            candidate["terminal_reason"] = reason.strip()
        existing = ledger["branches"].get(branch_id)
        if existing is not None:
            if existing["parent"] != parent or existing["question"] != question.strip():
                raise CampaignError(f"conflicting frontier branch: {branch_id}")
            if classification == "documented" and (
                existing.get("resolution") != "already_documented"
                or existing.get("document") != value.get("document")
            ):
                raise CampaignError(f"conflicting documented branch: {branch_id}")
            continue
        ledger["branches"][branch_id] = candidate
        added.append(branch_id)
    validate_dependency_graph(ledger)
    if added:
        ledger["frontier_epoch"] += len(added)
        ledger["discovery_pass"] = None
        ledger["documentation_pass"] = None
        ledger["integration_pass"] = None
    return added


def rollback(changes: list[tuple[Path, Path, Path | None]]) -> None:
    for source, destination, backup in reversed(changes):
        if destination.exists():
            source.parent.mkdir(parents=True, exist_ok=True)
            os.replace(destination, source)
        if backup is not None and backup.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(backup, destination)


def command_accept(args: argparse.Namespace) -> dict[str, Any]:
    spine = args.spine_root.resolve()
    staging_root = args.staging_root.resolve()
    if (
        spine == staging_root
        or spine.is_relative_to(staging_root)
        or staging_root.is_relative_to(spine)
    ):
        raise CampaignError("staging and live Spine must be disjoint")
    raw = read_json(args.checkpoint)
    files = candidate_files(staging_root)
    status, candidates, frontier, terminal_reason = validate_checkpoint(raw, files)
    digest = checkpoint_digest(raw, files)

    with locked(args.ledger):
        ledger = load(args.ledger)
        item = require_branch(ledger, args.branch)
        if item["state"] != "active":
            raise CampaignError(f"accept requires active branch: {args.branch}")
        working = copy.deepcopy(ledger)
        working_item = require_branch(working, args.branch)
        added = add_frontier(working, args.branch, frontier)
        requested = [value["path"] for value in candidates]
        replacements = [
            value["path"] for value in candidates if value["operation"] == "replace"
        ]
        occupied = {
            path
            for branch_id, branch in ledger["branches"].items()
            if branch_id != args.branch
            for path in branch.get("published", [])
        }
        conflict = sorted(set(requested) & occupied)
        if conflict:
            raise CampaignError("destination owned by another branch: " + ", ".join(conflict))
        for value in candidates:
            destination = args.spine_root / value["path"]
            if value["operation"] == "create" and destination.exists():
                raise CampaignError(f"create destination exists: {value['path']}")
            if value["operation"] == "replace" and not destination.is_file():
                raise CampaignError(f"replace destination is missing: {value['path']}")
            if destination.is_file() and destination.read_bytes() == files[value["path"]].read_bytes():
                raise CampaignError(f"candidate has no content change: {value['path']}")
        if candidates:
            run_checker(
                args.checker,
                args.spine_root,
                staging=staging_root,
                replacements=replacements,
            )
            stable_digest = checkpoint_digest(raw, candidate_files(staging_root))
            if stable_digest != digest:
                raise CampaignError("staging changed during checkpoint acceptance")

        backup_root = Path(tempfile.mkdtemp(prefix=".accept-", dir=args.ledger.parent))
        changes: list[tuple[Path, Path, Path | None]] = []
        try:
            for value in candidates:
                source = files[value["path"]]
                destination = args.spine_root / value["path"]
                backup = backup_root / value["path"] if destination.exists() else None
                changes.append((source, destination, backup))
                if backup is not None:
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(destination, backup)
                destination.parent.mkdir(parents=True, exist_ok=True)
                os.replace(source, destination)
            if candidates:
                run_checker(
                    args.checker,
                    args.spine_root,
                    ignored=DEFERRED_CODES,
                )
                working_item["published"] = sorted(
                    set(working_item.get("published", [])) | set(requested)
                )
                history = working.setdefault("publication_history", [])
                for value in candidates:
                    history.append(
                        {
                            "branch": args.branch,
                            "path": value["path"],
                            "operation": value["operation"],
                        }
                    )
            if status == "publish_and_locally_saturate":
                working_item["owner"] = None
                working_item["terminal_reason"] = terminal_reason
                working_item["state"] = "locally_saturated"
            elif not candidates:
                working_item["owner"] = None
                working_item["terminal_reason"] = terminal_reason
                working_item["state"] = (
                    "locally_saturated" if status == "locally_saturated" else "blocked"
                )
            working_item["last_checkpoint_digest"] = digest
            working_item["reported_relationships"] = raw["relationships"]
            if args.branch != working["root"] or candidates or added:
                working["documentation_pass"] = None
                working["integration_pass"] = None
            save(args.ledger, working)
        except BaseException:
            rollback(changes)
            raise
        finally:
            shutil.rmtree(backup_root, ignore_errors=True)
    return {
        "status": "accepted",
        "branch": args.branch,
        "digest": digest,
        "published": requested,
        "added_branches": added,
        "branch_state": working_item["state"],
        "revision": working["revision"],
    }


def command_close(args: argparse.Namespace) -> dict[str, Any]:
    def action(ledger: dict[str, Any]) -> bool:
        item = require_branch(ledger, args.id)
        if item["state"] != "locally_saturated":
            raise CampaignError(f"close requires locally_saturated state: {args.id}")
        unfinished = [
            child["id"]
            for child in ledger["branches"].values()
            if child.get("parent") == args.id and child["state"] != "complete"
        ]
        if unfinished:
            raise CampaignError("unfinished children: " + ", ".join(sorted(unfinished)))
        if args.id == ledger["root"]:
            discovery = ledger.get("discovery_pass")
            if not isinstance(discovery, dict) or discovery.get("frontier_epoch") != ledger["frontier_epoch"]:
                raise CampaignError("root close requires a current discovery pass")
            documentation = ledger.get("documentation_pass")
            if (
                not isinstance(documentation, dict)
                or documentation.get("frontier_epoch") != ledger["frontier_epoch"]
                or documentation.get("directions")
            ):
                raise CampaignError(
                    "root close requires a current empty documentation pass"
                )
            integration = ledger.get("integration_pass")
            if (
                not isinstance(integration, dict)
                or integration.get("frontier_epoch") != ledger["frontier_epoch"]
            ):
                raise CampaignError(
                    "root close requires a current graph integration pass"
                )
        item["state"] = "complete"
        return True

    return mutate(args.ledger, action)


def command_discovery(args: argparse.Namespace) -> dict[str, Any]:
    def action(ledger: dict[str, Any]) -> bool:
        if (
            ledger.get("spine_state") == "existing"
            and ledger.get("documentation_plan") is None
        ):
            raise CampaignError(
                "seed-from-spine is required before source discovery"
            )
        ledger["discovery_pass"] = {
            "frontier_epoch": ledger["frontier_epoch"],
            "evidence": args.evidence,
        }
        return True

    return mutate(args.ledger, action)


def command_integration_pass(args: argparse.Namespace) -> dict[str, Any]:
    report = read_json(args.report)
    spine_root = args.spine_root.resolve()
    markdown = {
        path.relative_to(spine_root).as_posix(): path
        for path in spine_root.rglob("*.md")
        if path.is_file()
    }
    inspected = report.get("evidence_inspected")
    if (
        not isinstance(inspected, list)
        or any(not isinstance(value, str) for value in inspected)
        or {validate_path(value) for value in inspected} != set(markdown)
    ):
        raise CampaignError(
            "integration report must inspect every live Markdown document"
        )
    organization = report.get("organization")
    if (
        not isinstance(organization, dict)
        or organization.get("status")
        not in {"flat_sufficient", "directories_sufficient", "reorganized"}
        or not isinstance(organization.get("reason"), str)
        or not organization["reason"].strip()
    ):
        raise CampaignError(
            "integration report needs a reasoned organization assessment"
        )
    reviews = report.get("relationship_review")
    if not isinstance(reviews, list):
        raise CampaignError("integration report relationship_review must be a list")
    normalized_reviews: dict[str, dict[str, str]] = {}
    for review in reviews:
        if not isinstance(review, dict):
            raise CampaignError("relationship review must be an object")
        branch = validate_id(review.get("branch", ""))
        disposition = review.get("disposition")
        reason = review.get("reason")
        if disposition not in {
            "integrated",
            "already_canonical",
            "navigation_only",
            "not_architectural",
        }:
            raise CampaignError(
                f"invalid relationship disposition for {branch}: {disposition!r}"
            )
        if not isinstance(reason, str) or not reason.strip():
            raise CampaignError(f"relationship review needs a reason: {branch}")
        if branch in normalized_reviews:
            raise CampaignError(f"duplicate relationship review: {branch}")
        normalized_reviews[branch] = {
            "disposition": disposition,
            "reason": reason,
        }
    run_checker(args.checker, spine_root)

    def action(ledger: dict[str, Any]) -> bool:
        unfinished = sorted(
            item["id"]
            for item in ledger["branches"].values()
            if item["id"] != ledger["root"] and item["state"] != "complete"
        )
        if unfinished:
            raise CampaignError(
                "integration pass requires all producer branches complete: "
                + ", ".join(unfinished)
            )
        required = {
            item["id"]
            for item in ledger["branches"].values()
            if item["id"] != ledger["root"]
            and (item.get("published") or item.get("reported_relationships"))
        }
        if set(normalized_reviews) != required:
            raise CampaignError(
                "integration report must disposition every publishing or "
                f"relationship-reporting branch; missing="
                f"{sorted(required - set(normalized_reviews))}, "
                f"unknown={sorted(set(normalized_reviews) - required)}"
            )
        ledger["integration_pass"] = {
            "frontier_epoch": ledger["frontier_epoch"],
            "digest": hashlib.sha256(
                json.dumps(report, sort_keys=True, ensure_ascii=False).encode("utf-8")
            ).hexdigest(),
            "documents": {
                relative: hashlib.sha256(path.read_bytes()).hexdigest()
                for relative, path in sorted(markdown.items())
            },
            "relationship_review": normalized_reviews,
            "organization": organization,
        }
        return True

    ledger = mutate(args.ledger, action)
    return {
        "status": "integrated",
        "campaign_id": ledger.get("campaign_id"),
        "documents": len(markdown),
        "reviewed_branches": sorted(normalized_reviews),
        "organization": organization["status"],
        "revision": ledger["revision"],
    }


def ready(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for item in ledger["branches"].values():
        prerequisite = item.get("prerequisite")
        if item["state"] == "queued" and (
            not prerequisite
            or require_branch(ledger, prerequisite)["state"] == "complete"
        ):
            result.append(item)
    return sorted(result, key=lambda item: item["id"])


def command_resume(args: argparse.Namespace) -> dict[str, Any]:
    released: list[str] = []

    def action(ledger: dict[str, Any]) -> bool:
        changed = False
        if not ledger.get("campaign_id"):
            ledger["campaign_id"] = str(uuid.uuid4())
            changed = True
        for item in ledger["branches"].values():
            if item["id"] != ledger["root"] and item["state"] == "active":
                item["state"] = "queued"
                item["owner"] = None
                released.append(item["id"])
                changed = True
        validate_dependency_graph(ledger)
        return changed

    ledger = mutate(args.ledger, action)
    return {
        "status": "ok",
        "campaign_id": ledger["campaign_id"],
        "released": sorted(released),
        "revision": ledger["revision"],
    }


def command_repair_prerequisite(args: argparse.Namespace) -> dict[str, Any]:
    before_cycles: list[list[str]] = []

    def action(ledger: dict[str, Any]) -> bool:
        nonlocal before_cycles
        item = require_branch(ledger, args.id)
        if args.clear:
            prerequisite = None
        else:
            prerequisite = validate_id(args.set)
            require_branch(ledger, prerequisite)
        if item.get("prerequisite") == prerequisite:
            return False
        before_cycles = dependency_cycles(ledger)
        previous = item.get("prerequisite")
        item["prerequisite"] = prerequisite
        after_cycles = dependency_cycles(ledger)
        if len(after_cycles) > len(before_cycles) or any(
            args.id in cycle for cycle in after_cycles
        ):
            raise CampaignError("prerequisite repair does not resolve target cycles")
        ledger.setdefault("recovery_history", []).append(
            {
                "operation": "repair_prerequisite",
                "branch": args.id,
                "from": previous,
                "to": prerequisite,
                "reason": args.reason.strip(),
            }
        )
        ledger["discovery_pass"] = None
        ledger["documentation_pass"] = None
        ledger["integration_pass"] = None
        return True

    ledger = mutate(args.ledger, action)
    return {
        "status": "repaired",
        "branch": args.id,
        "cycles_before": before_cycles,
        "cycles_after": dependency_cycles(ledger),
        "revision": ledger["revision"],
    }


def command_recover(args: argparse.Namespace) -> dict[str, Any]:
    source = load(args.source)
    with locked(args.destination):
        if args.destination.exists():
            raise CampaignError(
                f"recovery destination already exists: {args.destination}"
            )
        recovered = copy.deepcopy(source)
        recovered.setdefault("campaign_id", str(uuid.uuid4()))
        recovered.setdefault("recovery_history", []).append(
            {
                "operation": "recover",
                "source": str(args.source.resolve()),
                "source_revision": source.get("revision"),
                "reason": args.reason.strip(),
            }
        )
        for item in recovered["branches"].values():
            if item["id"] != recovered["root"] and item["state"] == "active":
                item["state"] = "queued"
                item["owner"] = None
        recovered["discovery_pass"] = None
        recovered["documentation_pass"] = None
        recovered["integration_pass"] = None
        recovered["revision"] = int(recovered.get("revision", 0)) + 1
        atomic_write(args.destination, recovered)
    return {
        "status": "recovered",
        "campaign_id": recovered["campaign_id"],
        "source_revision": source.get("revision"),
        "revision": recovered["revision"],
        "branches": len(recovered["branches"]),
    }


def audit_findings(ledger: dict[str, Any], final: bool) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not ledger.get("campaign_id"):
        findings.append(
            {
                "code": "missing_campaign_id",
                "branch": ledger.get("root", "root"),
                "message": "resume the legacy campaign before continuing",
            }
        )
    if (
        ledger.get("spine_state") == "existing"
        and ledger.get("documentation_plan") is None
    ):
        findings.append(
            {
                "code": "missing_documentation_plan",
                "branch": ledger.get("root", "root"),
                "message": (
                    "seed the frontier from the existing Spine before source discovery"
                ),
            }
        )
    try:
        cycles = dependency_cycles(ledger)
    except CampaignError as error:
        findings.append(
            {
                "code": "invalid_dependency",
                "branch": ledger.get("root", "root"),
                "message": str(error),
            }
        )
        cycles = []
    for cycle in cycles:
        findings.append(
            {
                "code": "dependency_cycle",
                "branch": cycle[0],
                "message": " -> ".join(cycle),
            }
        )
    for branch_id, item in ledger["branches"].items():
        if item.get("state") not in STATES:
            findings.append({"code": "invalid_state", "branch": branch_id, "message": str(item.get("state"))})
        if final and item.get("state") != "complete":
            findings.append({"code": "unfinished", "branch": branch_id, "message": f"state is {item.get('state')}"})
    if final:
        discovery = ledger.get("discovery_pass")
        if not isinstance(discovery, dict) or discovery.get("frontier_epoch") != ledger.get("frontier_epoch"):
            findings.append({"code": "stale_discovery", "branch": ledger["root"], "message": "current discovery pass is missing"})
        documentation = ledger.get("documentation_pass")
        if (
            not isinstance(documentation, dict)
            or documentation.get("frontier_epoch") != ledger.get("frontier_epoch")
            or documentation.get("directions")
        ):
            findings.append(
                {
                    "code": "stale_documentation_pass",
                    "branch": ledger["root"],
                    "message": "current final Spine review is missing or found directions",
                }
            )
        integration = ledger.get("integration_pass")
        if (
            not isinstance(integration, dict)
            or integration.get("frontier_epoch") != ledger.get("frontier_epoch")
        ):
            findings.append(
                {
                    "code": "stale_integration_pass",
                    "branch": ledger["root"],
                    "message": "current graph and organization integration is missing",
                }
            )
    return findings


def terminal_gates(ledger: dict[str, Any]) -> dict[str, bool]:
    epoch = ledger.get("frontier_epoch")
    documentation = ledger.get("documentation_pass")
    discovery = ledger.get("discovery_pass")
    integration = ledger.get("integration_pass")
    non_root = [
        item
        for item in ledger["branches"].values()
        if item["id"] != ledger["root"]
    ]
    return {
        "problem_list_empty": all(item["state"] == "complete" for item in non_root),
        "producer_branches_finished": not any(
            item["state"] == "active" for item in non_root
        ),
        "documentation_questions_empty": (
            isinstance(documentation, dict)
            and documentation.get("frontier_epoch") == epoch
            and not documentation.get("directions")
        ),
        "source_discovery_current": (
            isinstance(discovery, dict)
            and discovery.get("frontier_epoch") == epoch
        ),
        "graph_integrated": (
            isinstance(integration, dict)
            and integration.get("frontier_epoch") == epoch
        ),
        "root_complete": require_branch(ledger, ledger["root"])["state"]
        == "complete",
    }


def command_summary(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    states = {
        state: sorted(item["id"] for item in ledger["branches"].values() if item["state"] == state)
        for state in STATES
    }
    final_clean = not audit_findings(ledger, True)
    only_blocked = bool(states["blocked"]) and not states["queued"] and not states["active"] and not states["locally_saturated"]
    return {
        "campaign_id": ledger.get("campaign_id"),
        "revision": ledger["revision"],
        "terminal_gates": terminal_gates(ledger),
        "ready": [item["id"] for item in ready(ledger)],
        **states,
        "terminal": "saturated" if final_clean else "blocked" if only_blocked else None,
    }


def command_coverage_report(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    states = {
        state: sorted(
            item["id"]
            for item in ledger["branches"].values()
            if item["state"] == state
        )
        for state in STATES
    }
    unresolved = [
        {
            "id": item["id"],
            "state": item["state"],
            "question": item["question"],
            "parent": item.get("parent"),
            "prerequisite": item.get("prerequisite"),
            "reason": item.get("terminal_reason"),
        }
        for item in sorted(
            ledger["branches"].values(), key=lambda value: value["id"]
        )
        if item["state"] != "complete"
    ]
    return {
        "campaign_id": ledger.get("campaign_id"),
        "scope": ledger.get("scope"),
        "terminal": command_summary(args)["terminal"],
        "terminal_gates": terminal_gates(ledger),
        "counts": {state: len(values) for state, values in states.items()},
        "ready": [item["id"] for item in ready(ledger)],
        "unresolved": unresolved,
        "coverage_claim": (
            "mapped"
            if not unresolved
            else "partially_mapped"
            if any(item["state"] != "blocked" for item in unresolved)
            else "blocked"
        ),
    }


def compact(command: str, args: argparse.Namespace, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "ok",
        "command": command,
        "branch": getattr(args, "id", None),
        "revision": result.get("revision"),
    }


def add_identity_arguments(parser: argparse.ArgumentParser, *, document: bool = False) -> None:
    parser.add_argument("ledger", type=Path)
    parser.add_argument("id")
    parser.add_argument("--parent", required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--origin", required=True)
    parser.add_argument("--namespace")
    parser.add_argument("--prerequisite")
    if document:
        parser.add_argument("--document", required=True)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("ledger", type=Path)
    init.add_argument("--scope", required=True)
    init.add_argument("--root-question", required=True)
    init.add_argument("--spine-state", choices=sorted(SPINE_STATES), default="empty")
    seed = sub.add_parser("seed-from-spine")
    seed.add_argument("ledger", type=Path)
    seed.add_argument("spine_root", type=Path)
    seed.add_argument("plan", type=Path)
    documentation = sub.add_parser("documentation-pass")
    documentation.add_argument("ledger", type=Path)
    documentation.add_argument("spine_root", type=Path)
    documentation.add_argument("plan", type=Path)
    integration = sub.add_parser("integration-pass")
    integration.add_argument("ledger", type=Path)
    integration.add_argument("spine_root", type=Path)
    integration.add_argument("report", type=Path)
    integration.add_argument(
        "--checker", type=Path, default=Path(__file__).with_name("check_spine.py")
    )
    add_identity_arguments(sub.add_parser("add"))
    add_identity_arguments(sub.add_parser("documented"), document=True)
    assign = sub.add_parser("assign")
    assign.add_argument("ledger", type=Path)
    assign.add_argument("id")
    assign.add_argument("--owner", required=True)
    for name in ("release", "close"):
        command = sub.add_parser(name)
        command.add_argument("ledger", type=Path)
        command.add_argument("id")
    block = sub.add_parser("block")
    block.add_argument("ledger", type=Path)
    block.add_argument("id")
    block.add_argument("--reason", required=True)
    repair = sub.add_parser("repair-prerequisite")
    repair.add_argument("ledger", type=Path)
    repair.add_argument("id")
    repair_mode = repair.add_mutually_exclusive_group(required=True)
    repair_mode.add_argument("--clear", action="store_true")
    repair_mode.add_argument("--set")
    repair.add_argument("--reason", required=True)
    recover = sub.add_parser("recover")
    recover.add_argument("source", type=Path)
    recover.add_argument("destination", type=Path)
    recover.add_argument("--reason", required=True)
    accept = sub.add_parser("accept")
    accept.add_argument("ledger", type=Path)
    accept.add_argument("branch")
    accept.add_argument("checkpoint", type=Path)
    accept.add_argument("staging_root", type=Path)
    accept.add_argument("spine_root", type=Path)
    accept.add_argument("--checker", type=Path, default=Path(__file__).with_name("check_spine.py"))
    discovery = sub.add_parser("discovery-pass")
    discovery.add_argument("ledger", type=Path)
    discovery.add_argument("--evidence", required=True)
    for name in ("ready", "summary", "coverage-report", "resume", "audit"):
        command = sub.add_parser(name)
        command.add_argument("ledger", type=Path)
        if name == "audit":
            command.add_argument("--final", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        handlers = {
            "init": command_init,
            "seed-from-spine": command_seed_from_spine,
            "documentation-pass": command_documentation_pass,
            "integration-pass": command_integration_pass,
            "add": command_add,
            "documented": lambda value: command_add(value, documented=True),
            "assign": command_assign,
            "release": command_release,
            "block": command_block,
            "repair-prerequisite": command_repair_prerequisite,
            "recover": command_recover,
            "accept": command_accept,
            "close": command_close,
            "discovery-pass": command_discovery,
            "ready": lambda value: ready(load(value.ledger)),
            "summary": command_summary,
            "coverage-report": command_coverage_report,
            "resume": command_resume,
            "audit": lambda value: audit_findings(load(value.ledger), value.final),
        }
        result = handlers[args.command](args)
        emit(result)
        if args.command == "audit" and result:
            return 1
        return 0
    except (CampaignError, OSError, subprocess.SubprocessError) as error:
        emit({"error": str(error)}, error=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
