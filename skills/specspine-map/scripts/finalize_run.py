#!/usr/bin/env python3
"""Issue a final exhaustive Map receipt for a scope-verified campaign."""

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


def finalize(args: argparse.Namespace) -> dict[str, object]:
    ledger = campaign.load(args.ledger)
    summary_args = argparse.Namespace(ledger=args.ledger)
    summary = campaign.command_summary(summary_args)
    if summary["terminal"] != "scope_verified":
        raise FinalizeError(
            "campaign is not scope_verified: "
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

    publication_history = ledger.get("publication_history", [])
    created = sum(
        value.get("operation") == "create" for value in publication_history
    )
    replaced = sum(
        value.get("operation") == "replace" for value in publication_history
    )
    published = sorted(
        {value["path"] for value in publication_history if "path" in value}
    )
    document_change_history = ledger.get("document_change_history", [])
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
        ledger["tasks"].get(task_id, {}).get("state") == "complete"
        for task_id in source.get("todo", [])
    )
    return {
        "status": "finalized",
        "campaign_id": ledger["campaign_id"],
        "ledger_digest": ledger_digest,
        "revision": ledger["revision"],
        "terminal": summary["terminal"],
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
        "scope": source.get("scope"),
        "evidence_files": len(source.get("evidence_files", [])),
        "discovery_leads": len(
            source.get("discovery_corpus", {}).get("leads", [])
        ),
        "verified_topics": verified_units,
        "existing_spine_covered_topics": len(
            source.get("topic_plan", {}).get("covered", [])
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
