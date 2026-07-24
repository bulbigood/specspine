#!/usr/bin/env python3
"""Validate and atomically import one exhaustive Map producer checkpoint."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import frontier


STATUSES = {"continuing", "locally_saturated", "blocked"}
SOURCE_CLASSIFICATIONS = {
    "mapped_here",
    "owned_by",
    "child_branch",
    "no_durable_value",
}
FRONTIER_CLASSIFICATIONS = {"fork_candidate", "documented", "blocked"}
TOP_LEVEL_KEYS = {
    "status",
    "evidence_inspected",
    "candidates",
    "mapped_responsibilities",
    "relationships",
    "source_coverage",
    "continuation",
    "coverage_frontier",
    "unresolved",
    "terminal_reason",
}


class CheckpointError(ValueError):
    pass


def require_object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CheckpointError(f"{name} must be an object")
    return value


def require_string(value: Any, name: str, *, optional: bool = False) -> str | None:
    if optional and value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise CheckpointError(f"{name} must be a nonempty string")
    return value.strip()


def require_string_list(value: Any, name: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value):
        qualifier = "nonempty " if nonempty else ""
        raise CheckpointError(f"{name} must be a {qualifier}list")
    result: list[str] = []
    for index, item in enumerate(value):
        result.append(require_string(item, f"{name}[{index}]") or "")
    return result


def exact_keys(value: dict[str, Any], allowed: set[str], name: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise CheckpointError(f"{name} has unknown fields: {', '.join(unknown)}")


def validate(payload: Any) -> dict[str, Any]:
    checkpoint = require_object(payload, "checkpoint")
    exact_keys(checkpoint, TOP_LEVEL_KEYS, "checkpoint")
    missing = sorted(TOP_LEVEL_KEYS - set(checkpoint))
    if missing:
        raise CheckpointError(
            "checkpoint is missing fields: " + ", ".join(missing)
        )

    status = require_string(checkpoint["status"], "status")
    if status not in STATUSES:
        raise CheckpointError(f"invalid status: {status}")
    evidence = require_string_list(
        checkpoint["evidence_inspected"], "evidence_inspected", nonempty=True
    )
    mapped = require_string_list(
        checkpoint["mapped_responsibilities"],
        "mapped_responsibilities",
        nonempty=True,
    )
    relationships = require_string_list(checkpoint["relationships"], "relationships")
    unresolved = require_string_list(checkpoint["unresolved"], "unresolved")
    continuation = require_string(
        checkpoint["continuation"], "continuation", optional=True
    )
    terminal_reason = require_string(
        checkpoint["terminal_reason"], "terminal_reason", optional=True
    )

    candidates: list[dict[str, str]] = []
    if not isinstance(checkpoint["candidates"], list):
        raise CheckpointError("candidates must be a list")
    for index, raw in enumerate(checkpoint["candidates"]):
        item = require_object(raw, f"candidates[{index}]")
        exact_keys(item, {"path", "operation"}, f"candidates[{index}]")
        if set(item) != {"path", "operation"}:
            raise CheckpointError(
                f"candidates[{index}] requires path and operation"
            )
        path = frontier.validate_relative_path(
            require_string(item["path"], f"candidates[{index}].path") or ""
        )
        operation = require_string(
            item["operation"], f"candidates[{index}].operation"
        )
        if operation not in {"create", "replace"}:
            raise CheckpointError(
                f"candidates[{index}].operation must be create or replace"
            )
        if path == "README.md":
            raise CheckpointError("producer checkpoint must not contain README.md")
        candidates.append({"path": path, "operation": operation})
    candidate_paths = [item["path"] for item in candidates]
    if len(candidate_paths) != len(set(candidate_paths)):
        raise CheckpointError("candidate paths must be unique")

    frontier_items: list[dict[str, Any]] = []
    if not isinstance(checkpoint["coverage_frontier"], list):
        raise CheckpointError("coverage_frontier must be a list")
    frontier_ids: set[str] = set()
    for index, raw in enumerate(checkpoint["coverage_frontier"]):
        item = require_object(raw, f"coverage_frontier[{index}]")
        allowed = {
            "id",
            "question",
            "evidence",
            "prerequisite",
            "namespace",
            "classification",
            "document",
            "reason",
        }
        exact_keys(item, allowed, f"coverage_frontier[{index}]")
        branch_id = frontier.validate_id(
            require_string(item.get("id"), f"coverage_frontier[{index}].id") or ""
        )
        if branch_id in frontier_ids:
            raise CheckpointError(f"duplicate coverage frontier id: {branch_id}")
        frontier_ids.add(branch_id)
        classification = require_string(
            item.get("classification"),
            f"coverage_frontier[{index}].classification",
        )
        if classification not in FRONTIER_CLASSIFICATIONS:
            raise CheckpointError(
                f"invalid frontier classification: {classification}"
            )
        document = require_string(
            item.get("document"),
            f"coverage_frontier[{index}].document",
            optional=True,
        )
        reason = require_string(
            item.get("reason"),
            f"coverage_frontier[{index}].reason",
            optional=True,
        )
        if classification == "documented" and not document:
            raise CheckpointError("documented frontier item requires document")
        if classification == "blocked" and not reason:
            raise CheckpointError("blocked frontier item requires reason")
        frontier_items.append(
            {
                "id": branch_id,
                "question": require_string(
                    item.get("question"),
                    f"coverage_frontier[{index}].question",
                ),
                "evidence": require_string_list(
                    item.get("evidence"),
                    f"coverage_frontier[{index}].evidence",
                    nonempty=True,
                ),
                "prerequisite": require_string(
                    item.get("prerequisite"),
                    f"coverage_frontier[{index}].prerequisite",
                    optional=True,
                ),
                "namespace": require_string(
                    item.get("namespace"),
                    f"coverage_frontier[{index}].namespace",
                    optional=True,
                ),
                "classification": classification,
                "document": document,
                "reason": reason,
            }
        )

    source_coverage: list[dict[str, Any]] = []
    if not isinstance(checkpoint["source_coverage"], list) or not checkpoint[
        "source_coverage"
    ]:
        raise CheckpointError("source_coverage must be a nonempty list")
    for index, raw in enumerate(checkpoint["source_coverage"]):
        item = require_object(raw, f"source_coverage[{index}]")
        exact_keys(
            item,
            {"paths", "classification", "owner", "branch_id", "reason"},
            f"source_coverage[{index}]",
        )
        classification = require_string(
            item.get("classification"),
            f"source_coverage[{index}].classification",
        )
        if classification not in SOURCE_CLASSIFICATIONS:
            raise CheckpointError(
                f"invalid source coverage classification: {classification}"
            )
        owner = require_string(
            item.get("owner"), f"source_coverage[{index}].owner", optional=True
        )
        child_id = require_string(
            item.get("branch_id"),
            f"source_coverage[{index}].branch_id",
            optional=True,
        )
        reason = require_string(
            item.get("reason"), f"source_coverage[{index}].reason", optional=True
        )
        if classification == "owned_by" and not owner:
            raise CheckpointError("owned_by source coverage requires owner")
        if classification == "child_branch":
            if not child_id:
                raise CheckpointError(
                    "child_branch source coverage requires branch_id"
                )
            frontier.validate_id(child_id)
            if child_id not in frontier_ids:
                raise CheckpointError(
                    f"source coverage child is absent from coverage_frontier: {child_id}"
                )
        if classification == "no_durable_value" and not reason:
            raise CheckpointError(
                "no_durable_value source coverage requires reason"
            )
        source_coverage.append(
            {
                "paths": require_string_list(
                    item.get("paths"),
                    f"source_coverage[{index}].paths",
                    nonempty=True,
                ),
                "classification": classification,
                "owner": owner,
                "branch_id": child_id,
                "reason": reason,
            }
        )

    if candidates and status != "continuing":
        raise CheckpointError("a checkpoint with candidates must be continuing")
    if status == "locally_saturated":
        if candidates or continuation is not None:
            raise CheckpointError(
                "locally_saturated checkpoint must be candidate-free "
                "with no continuation"
            )
        if not terminal_reason or not frontier.TERMINAL_REFUSAL.match(
            terminal_reason
        ):
            raise CheckpointError(
                "locally_saturated requires "
                "'no useful node: <evidence-based reason>'"
            )
    elif status == "blocked":
        if candidates or not terminal_reason:
            raise CheckpointError(
                "blocked checkpoint must be candidate-free and state its blocker"
            )
    elif terminal_reason is not None:
        raise CheckpointError("continuing checkpoint must not have terminal_reason")

    return {
        "status": status,
        "evidence_inspected": evidence,
        "candidates": sorted(candidates, key=lambda item: item["path"]),
        "mapped_responsibilities": mapped,
        "relationships": relationships,
        "source_coverage": source_coverage,
        "continuation": continuation,
        "coverage_frontier": sorted(
            frontier_items, key=lambda item: item["id"]
        ),
        "unresolved": unresolved,
        "terminal_reason": terminal_reason,
    }


def digest(checkpoint: dict[str, Any]) -> str:
    canonical = json.dumps(
        checkpoint, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def compatible(existing: dict[str, Any], expected: dict[str, Any]) -> bool:
    keys = {"id", "parent", "question", "origin", "prerequisite", "namespace"}
    return all(existing.get(key) == expected.get(key) for key in keys)


def import_checkpoint(
    ledger_path: Path, branch_id: str, checkpoint_path: Path
) -> dict[str, Any]:
    try:
        raw = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CheckpointError(f"cannot read checkpoint: {error}") from error
    checkpoint = validate(raw)
    checkpoint_digest = digest(checkpoint)
    ledger = frontier.load(ledger_path)
    item = frontier.require_branch(ledger, branch_id)
    if item.get("state") != "active":
        raise CheckpointError("checkpoint import requires an active branch")
    pending = item.get("pending_checkpoint")
    if pending:
        if pending.get("digest") == checkpoint_digest:
            return {
                "status": "already_imported",
                "branch": branch_id,
                "digest": checkpoint_digest,
                "revision": ledger.get("revision"),
            }
        raise CheckpointError("branch already has an unpublished checkpoint")

    added: list[str] = []
    for child in checkpoint["coverage_frontier"]:
        if child["prerequisite"]:
            frontier.require_branch(ledger, child["prerequisite"])
        origin = "; ".join(child["evidence"])
        classification = child["classification"]
        state = "queued"
        extra: dict[str, Any] = {
            "origin": origin,
            "prerequisite": child["prerequisite"],
            "namespace": child["namespace"],
        }
        if classification == "documented":
            state = "complete"
            extra.update(
                resolution="already_documented", document=child["document"]
            )
        elif classification == "blocked":
            state = "blocked"
            extra.update(
                resolution=None, terminal_reason=child["reason"]
            )
        candidate = frontier.branch(
            child["id"],
            branch_id,
            child["question"],
            state=state,
            **extra,
        )
        existing = frontier.branches(ledger).get(child["id"])
        if existing is None:
            frontier.branches(ledger)[child["id"]] = candidate
            ledger["frontier_epoch"] = ledger.get("frontier_epoch", 0) + 1
            added.append(child["id"])
        elif not compatible(existing, candidate):
            raise CheckpointError(
                f"conflicting coverage frontier id: {child['id']}"
            )

    candidate_paths = [entry["path"] for entry in checkpoint["candidates"]]
    replacements = [
        entry["path"]
        for entry in checkpoint["candidates"]
        if entry["operation"] == "replace"
    ]
    if candidate_paths:
        item["pending_checkpoint"] = {
            "digest": checkpoint_digest,
            "paths": candidate_paths,
            "replacements": replacements,
            "status": checkpoint["status"],
        }
    elif checkpoint["status"] == "locally_saturated":
        item["state"] = "locally_saturated"
        item["owner"] = None
        item["terminal_reason"] = checkpoint["terminal_reason"]
        item["resolution"] = "independently_refused"
        item["last_checkpoint_digest"] = checkpoint_digest
    elif checkpoint["status"] == "blocked":
        item["state"] = "blocked"
        item["owner"] = None
        item["terminal_reason"] = checkpoint["terminal_reason"]
        item["last_checkpoint_digest"] = checkpoint_digest
    else:
        item["last_checkpoint_digest"] = checkpoint_digest

    frontier.save(ledger_path, ledger)
    return {
        "status": "imported",
        "branch": branch_id,
        "digest": checkpoint_digest,
        "added_branches": added,
        "candidate_paths": candidate_paths,
        "revision": ledger["revision"],
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("ledger", type=Path)
    result.add_argument("branch")
    result.add_argument("checkpoint", type=Path)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        result = import_checkpoint(args.ledger, args.branch, args.checkpoint)
    except (CheckpointError, frontier.LedgerError, OSError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
