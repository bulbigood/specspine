#!/usr/bin/env python3
"""Issue a final receipt for a verified SpecSpine Map operation."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import campaign


class FinalizeError(ValueError):
    pass


FACET_STATES = {"complete", "partial", "missing", "not-applicable"}


def reconstruction_readiness(spine_root: Path) -> dict[str, object]:
    manifest_path = spine_root / "specspine.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise FinalizeError(
            f"cannot read reconstruction readiness from {manifest_path}: {error}"
        ) from error

    areas = manifest.get("areas")
    if not isinstance(areas, list):
        raise FinalizeError("manifest areas are unavailable after clean checker")

    facet_counts = {state: 0 for state in sorted(FACET_STATES)}
    ready_areas = 0
    incomplete_areas = 0
    blocked_areas = 0
    for area in areas:
        facets = area.get("facets", {}) if isinstance(area, dict) else {}
        blockers = area.get("blockers", []) if isinstance(area, dict) else []
        for state in facets.values():
            if state in facet_counts:
                facet_counts[state] += 1
        if blockers:
            blocked_areas += 1
        elif facets and all(
            state in {"complete", "not-applicable"} for state in facets.values()
        ):
            ready_areas += 1
        else:
            incomplete_areas += 1

    status = (
        "blocked"
        if blocked_areas
        else "ready"
        if areas and ready_areas == len(areas)
        else "incomplete"
    )
    return {
        "status": status,
        "areas": {
            "total": len(areas),
            "ready": ready_areas,
            "incomplete": incomplete_areas,
            "blocked": blocked_areas,
        },
        "facets": facet_counts,
    }


def finalize(args: argparse.Namespace) -> dict[str, object]:
    ledger = campaign.load(args.ledger)
    summary = campaign.campaign_summary(args.ledger)
    if summary["terminal"] not in {"increment_verified", "scope_verified"}:
        raise FinalizeError(
            "operation is not verified: "
            + json.dumps(summary["terminal_gates"], ensure_ascii=False)
        )

    integration = ledger.get("integration_pass")
    if not isinstance(integration, dict):
        raise FinalizeError("current integration pass is missing")
    actual_documents = campaign.document_hashes(args.spine_root.resolve())
    if integration.get("documents") != actual_documents:
        raise FinalizeError(
            "Spine changed after the final integration pass; integrate it again"
        )

    dirty_staging: list[str] = []
    for root in args.staging_root:
        if root.exists():
            dirty_staging.extend(
                str(path)
                for path in root.rglob("*")
                if path.is_file() or path.is_symlink()
            )
    if dirty_staging:
        raise FinalizeError(
            "staging contains unpublished entries: "
            + ", ".join(sorted(dirty_staging))
        )

    checker_command = [
        sys.executable,
        str(args.checker),
        str(args.spine_root),
        "--json",
    ]
    repository_root = campaign.repository_root_from_ledger(ledger)
    if repository_root is not None:
        checker_command.extend(["--repository-root", str(repository_root)])
    result = subprocess.run(
        checker_command,
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        findings = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        detail = result.stderr.strip() or result.stdout.strip() or "no output"
        raise FinalizeError(f"checker returned invalid JSON: {detail}") from error
    if result.returncode != 0 or findings:
        raise FinalizeError(
            "final Spine checker is not clean: "
            + json.dumps(findings, ensure_ascii=False)
        )

    publication_history = ledger["publication_history"]
    created = sum(
        value.get("operation") == "create" for value in publication_history
    )
    replaced = sum(
        value.get("operation") == "replace" for value in publication_history
    )
    published = sorted(
        {value["path"] for value in publication_history if "path" in value}
    )
    document_change_history = ledger["document_change_history"]
    changed_documents = sorted(
        {
            value["path"]
            for value in document_change_history
            if isinstance(value, dict) and isinstance(value.get("path"), str)
        }
    )
    ledger_digest = hashlib.sha256(campaign.canonical_json(ledger)).hexdigest()
    source = ledger["source_pass"]
    verified_units = sum(
        ledger["tasks"][task_id]["state"] == "complete"
        for task_id in source["todo"]
    )
    return {
        "status": "finalized",
        "campaign_id": ledger["campaign_id"],
        "ledger_digest": ledger_digest,
        "revision": ledger["revision"],
        "terminal": summary["terminal"],
        "terminal_claim": (
            "selected observation scope completed"
            if summary["terminal"] == "scope_verified"
            else "selected observation increment completed"
        ),
        "reconstruction_readiness": reconstruction_readiness(
            args.spine_root.resolve()
        ),
        "terminal_gates": summary["terminal_gates"],
        "published": published,
        "changed_documents": changed_documents,
        "document_change_history": document_change_history,
        "changes": {
            "created": created,
            "replaced": replaced,
            "published_paths": len(published),
            "changed_document_paths": len(changed_documents),
            "document_change_events": len(document_change_history),
            "markdown_total": len(actual_documents),
        },
        "scope": source["scope"],
        "completion": source["completion"],
        "deferred_leads": len(
            source["topic_plan"]["deferred_leads"]
        ),
        "evidence_files": len(source["evidence_files"]),
        "discovery_leads": len(
            source["discovery_corpus"]["leads"]
        ),
        "verified_topics": verified_units,
        "existing_spine_covered_topics": len(
            source["topic_plan"]["covered"]
        ),
        "spine_root": str(args.spine_root.resolve()),
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("ledger", type=Path)
    result.add_argument("spine_root", type=Path)
    result.add_argument("--staging-root", action="append", type=Path, default=[])
    result.add_argument(
        "--checker",
        type=Path,
        default=Path(__file__).with_name("check_spine.py"),
    )
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        receipt = finalize(args)
    except (FinalizeError, campaign.CampaignError, OSError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(receipt, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
