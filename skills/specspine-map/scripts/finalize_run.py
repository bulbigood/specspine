#!/usr/bin/env python3
"""Issue the final exhaustive Map receipt only for a clean normalized run."""

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
    campaign_id = ledger.get("campaign_id")
    if not isinstance(campaign_id, str) or not campaign_id:
        raise FinalizeError(
            "campaign identity is missing; resume the original ledger before finalizing"
        )
    findings = campaign.audit_findings(ledger, final=True)
    if findings:
        raise FinalizeError(
            "final frontier audit failed: "
            + json.dumps(findings, ensure_ascii=False)
        )
    discovery = ledger.get("discovery_pass")
    if (
        not isinstance(discovery, dict)
        or discovery.get("frontier_epoch") != ledger.get("frontier_epoch", 0)
    ):
        raise FinalizeError("current scope-level discovery pass is missing")
    documentation = ledger.get("documentation_pass")
    if not isinstance(documentation, dict):
        raise FinalizeError("current final Spine review is missing")
    expected_documents = documentation.get("documents")
    actual_documents = {
        path.relative_to(args.spine_root).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in args.spine_root.rglob("*.md")
        if path.is_file()
    }
    if expected_documents != actual_documents:
        raise FinalizeError(
            "Spine changed after the final documentation pass; review it again"
        )
    integration = ledger.get("integration_pass")
    if (
        not isinstance(integration, dict)
        or integration.get("documents") != actual_documents
    ):
        raise FinalizeError(
            "Spine changed after graph integration; integrate it again"
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

    result = subprocess.run(
        [sys.executable, str(args.checker), str(args.spine_root), "--json"],
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        checker_findings = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        detail = result.stderr.strip() or result.stdout.strip() or "no output"
        raise FinalizeError(f"checker returned invalid JSON: {detail}") from error
    if result.returncode != 0 or checker_findings:
        raise FinalizeError(
            "final Spine checker is not clean: "
            + json.dumps(checker_findings, ensure_ascii=False)
        )
    ledger_digest = hashlib.sha256(
        json.dumps(
            ledger,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    published = sorted(
        {
            path
            for branch in ledger["branches"].values()
            for path in branch.get("published", [])
        }
    )
    publication_history = ledger.get("publication_history", [])
    created = sum(
        1 for value in publication_history if value.get("operation") == "create"
    )
    replaced = sum(
        1 for value in publication_history if value.get("operation") == "replace"
    )
    return {
        "status": "finalized",
        "campaign_id": campaign_id,
        "ledger_digest": ledger_digest,
        "revision": ledger.get("revision"),
        "frontier_epoch": ledger.get("frontier_epoch"),
        "terminal_gates": campaign.terminal_gates(ledger),
        "published": published,
        "changes": {
            "created": created,
            "replaced": replaced,
            "published_paths": len(published),
            "markdown_total": len(list(args.spine_root.rglob("*.md"))),
        },
        "recovery_history": ledger.get("recovery_history", []),
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
