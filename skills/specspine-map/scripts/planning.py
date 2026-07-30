#!/usr/bin/env python3
"""Prepare and finalize one isolated semantic discovery plan."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import campaign

PLANNER_CONTRACT_VERSION = 1


class PlanningError(ValueError):
    pass


def read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise PlanningError(f"cannot read JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise PlanningError(f"JSON root must be an object: {path}")
    return value


def atomic_plan(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def command_prepare(args: argparse.Namespace) -> dict[str, Any]:
    ledger = campaign.load(args.ledger)
    repository_root = args.repository_root.resolve()
    spine_root = args.spine_root.resolve()
    for path, field in (
        (args.output, "planner packet"),
        (args.ledger, "campaign ledger"),
    ):
        campaign.require_map_runtime_path(path, repository_root, field=field)
    if campaign.repository_root_from_ledger(ledger) != repository_root:
        raise PlanningError("planner repository root differs from campaign")
    packet = {
        "planner_contract_version": PLANNER_CONTRACT_VERSION,
        "operation": campaign.validate_operation_spec(ledger["operation"]),
        "repository_root": str(repository_root),
        "spine_root": str(spine_root),
    }
    already_ready = args.output.is_file()
    if args.output.exists() and (
        not already_ready or read_object(args.output) != packet
    ):
        raise PlanningError("existing planner packet has different inputs")
    campaign.atomic_write(args.output, packet)
    input_digest = campaign.digest_json(packet)
    receipt_ready = campaign.commit_receipt(
        args.output.with_name(f".{args.output.name}.receipt.json"),
        "planning-prepare",
        input_digest=input_digest,
        outputs=[args.output],
    )
    return {
        "status": "already_ready" if already_ready and receipt_ready else "written",
        "packet": str(args.output.resolve()),
    }


def command_finalize(args: argparse.Namespace) -> dict[str, Any]:
    packet = read_object(args.packet)
    if packet.get("planner_contract_version") != PLANNER_CONTRACT_VERSION:
        raise PlanningError("planner packet contract is invalid")
    repository_root = Path(packet["repository_root"]).resolve()
    for path, field in (
        (args.packet, "planner packet"),
        (args.draft, "planner draft"),
        (args.output, "initial discovery plan"),
    ):
        campaign.require_map_runtime_path(path, repository_root, field=field)
    draft = read_object(args.draft)
    plan = campaign.validate_initial_discovery_plan(draft)
    if args.output.exists():
        if read_object(args.output) != plan:
            raise PlanningError("existing initial plan has different content")
        status = "already_ready"
    else:
        atomic_plan(args.output, plan)
        status = "ready"
    receipt_ready = campaign.commit_receipt(
        args.output.with_name(f".{args.output.name}.receipt.json"),
        "planning-finalize",
        input_digest=campaign.digest_json(
            {
                "packet": campaign.path_digest(args.packet),
                "draft": campaign.path_digest(args.draft),
            }
        ),
        inputs=[args.packet, args.draft],
        outputs=[args.output],
    )
    if status == "already_ready" and not receipt_ready:
        status = "ready"
    return {
        "status": status,
        "leads": len(plan["leads"]),
        "digest": hashlib.sha256(args.output.read_bytes()).hexdigest(),
        "output": str(args.output.resolve()),
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    sub = result.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("ledger", type=Path)
    prepare.add_argument("repository_root", type=Path)
    prepare.add_argument("spine_root", type=Path)
    prepare.add_argument("output", type=Path)
    finalize = sub.add_parser("finalize")
    finalize.add_argument("packet", type=Path)
    finalize.add_argument("draft", type=Path)
    finalize.add_argument("output", type=Path)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        value = {
            "prepare": command_prepare,
            "finalize": command_finalize,
        }[args.command](args)
    except (PlanningError, campaign.CampaignError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 2
    print(json.dumps(value, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
