#!/usr/bin/env python3
"""Prepare and finalize a repository-exhaustive topology coverage audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import campaign

COVERAGE_CONTRACT_VERSION = 1


class CoverageError(ValueError):
    pass


def read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CoverageError(f"cannot read JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise CoverageError(f"JSON root must be an object: {path}")
    return value


def require_repository_exhaustive(operation: dict[str, Any]) -> None:
    normalized = campaign.validate_operation_spec(operation)
    if (
        normalized["scope"]["kind"] != "repository"
        or normalized["completion"]["kind"] != "exhaustive"
    ):
        raise CoverageError(
            "repository coverage audit is only for repository exhaustive"
        )


def command_prepare(args: argparse.Namespace) -> dict[str, Any]:
    campaign.require_stage_receipt(args.corpus, "discovery-collect")
    campaign.require_stage_receipt(args.topic_plan, "synthesis-materialize")
    corpus = read_object(args.corpus)
    plan = read_object(args.topic_plan)
    operation = corpus["operation"]
    require_repository_exhaustive(operation)
    if plan.get("open_leads") or plan.get("deferred_leads"):
        raise CoverageError("coverage audit requires a closed topic plan")
    repository_root = Path(corpus["repository_root"]).resolve()
    for path, field in (
        (args.corpus, "discovery corpus"),
        (args.topic_plan, "topic plan"),
        (args.output, "coverage packet"),
    ):
        campaign.require_map_runtime_path(path, repository_root, field=field)
    packet = {
        "coverage_contract_version": COVERAGE_CONTRACT_VERSION,
        "topic_plan_digest": hashlib.sha256(args.topic_plan.read_bytes()).hexdigest(),
        "operation": operation,
        "repository_root": str(repository_root),
        "spine_root": corpus["spine_root"],
        "topic_plan": [
            {
                key: topic[key]
                for key in ("id", "document", "title", "responsibility")
            }
            for topic in plan["topics"] + plan["covered"]
        ],
        "existing_owners": [
            {"id": owner, **profile}
            for owner, profile in sorted(
                campaign.spine_owner_registry(Path(corpus["spine_root"])).items()
            )
        ],
    }
    already_ready = args.output.is_file()
    if args.output.exists() and (
        not already_ready or read_object(args.output) != packet
    ):
        raise CoverageError("existing coverage packet has different inputs")
    campaign.atomic_write(args.output, packet)
    receipt_ready = campaign.commit_receipt(
        args.output.with_name(f".{args.output.name}.receipt.json"),
        "coverage-prepare",
        input_digest=campaign.digest_json(
            {
                "corpus": campaign.path_digest(args.corpus),
                "topic_plan": campaign.path_digest(args.topic_plan),
            }
        ),
        inputs=[args.corpus, args.topic_plan],
        outputs=[args.output],
    )
    return {
        "status": "already_ready" if already_ready and receipt_ready else "written",
        "topics": len(packet["topic_plan"]),
        "packet": str(args.output.resolve()),
    }


def normalize_lead(
    value: Any,
    repository_root: Path,
    *,
    index: int,
) -> dict[str, Any]:
    expected = {"id", "title", "question", "reason", "seed_files"}
    if not isinstance(value, dict) or set(value) != expected:
        raise CoverageError(f"coverage lead {index} has invalid shape")
    lead = campaign.normalize_discovery_lead(
        value | {"parent_ids": []},
        field=f"coverage lead {index}",
    )
    campaign.validate_repository_files(
        repository_root,
        lead["seed_files"],
        field=f"coverage lead {lead['id']} seed file",
    )
    return {key: lead[key] for key in expected}


def command_finalize(args: argparse.Namespace) -> dict[str, Any]:
    packet = read_object(args.packet)
    if packet.get("coverage_contract_version") != COVERAGE_CONTRACT_VERSION:
        raise CoverageError("coverage packet contract is invalid")
    repository_root = Path(packet["repository_root"]).resolve()
    for path, field in (
        (args.packet, "coverage packet"),
        (args.draft, "coverage draft"),
        (args.output, "coverage review"),
    ):
        campaign.require_map_runtime_path(path, repository_root, field=field)
    raw = read_object(args.draft)
    expected = {"status", "reason", "inspected_roots", "open_leads"}
    if not isinstance(raw, dict) or set(raw) != expected:
        raise CoverageError("coverage review has invalid shape")
    if raw["status"] not in {"clear", "gaps"}:
        raise CoverageError("coverage status must be clear or gaps")
    if not isinstance(raw["reason"], str) or not raw["reason"].strip():
        raise CoverageError("coverage reason must be nonempty")
    roots = campaign.string_list(
        raw["inspected_roots"],
        "coverage inspected_roots",
        nonempty=True,
    )
    leads = [
        normalize_lead(value, repository_root, index=index)
        for index, value in enumerate(raw["open_leads"], start=1)
    ]
    if len({lead["id"] for lead in leads}) != len(leads):
        raise CoverageError("coverage review repeats lead IDs")
    if raw["status"] == "clear" and leads:
        raise CoverageError("clear coverage review cannot contain open leads")
    if raw["status"] == "gaps" and not leads:
        raise CoverageError("gaps coverage review needs open leads")
    review = {
        "coverage_contract_version": COVERAGE_CONTRACT_VERSION,
        "topic_plan_digest": packet["topic_plan_digest"],
        "status": raw["status"],
        "reason": raw["reason"].strip(),
        "inspected_roots": sorted(set(roots)),
        "open_leads": sorted(leads, key=lambda value: value["id"]),
    }
    already_ready = args.output.is_file()
    if args.output.exists() and (
        not already_ready or read_object(args.output) != review
    ):
        raise CoverageError("existing coverage review has different content")
    campaign.atomic_write(args.output, review)
    receipt_ready = campaign.commit_receipt(
        args.output.with_name(f".{args.output.name}.receipt.json"),
        "coverage-finalize",
        input_digest=campaign.digest_json(
            {
                "packet": campaign.path_digest(args.packet),
                "draft": campaign.path_digest(args.draft),
            }
        ),
        inputs=[args.packet, args.draft],
        outputs=[args.output],
    )
    return {
        "status": "already_ready" if already_ready and receipt_ready else "ready",
        "result": review["status"],
        "open_leads": len(leads),
        "output": str(args.output.resolve()),
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    sub = result.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("corpus", type=Path)
    prepare.add_argument("topic_plan", type=Path)
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
    except (CoverageError, campaign.CampaignError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 2
    print(json.dumps(value, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
