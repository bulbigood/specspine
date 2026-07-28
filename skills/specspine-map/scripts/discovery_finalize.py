#!/usr/bin/env python3
"""Normalize one scout draft and atomically publish its canonical result."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import campaign


DRAFT_FIELDS = {
    "disposition",
    "reason",
    "queries",
    "topics",
    "supporting",
    "child_leads",
}
DRAFT_DISPOSITIONS = {"mapped", "duplicate", "out_of_scope"}


def object_list(value: Any, field: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or any(
        not isinstance(item, dict) for item in value
    ):
        raise campaign.CampaignError(f"{field} must be a list of objects")
    return value


def deduplicated_paths(value: Any, field: str) -> tuple[list[str], int]:
    paths = [
        campaign.validate_relative_path(item)
        for item in campaign.string_list(value, field)
    ]
    unique = sorted(set(paths))
    return unique, len(paths) - len(unique)


def normalize_topics(
    values: Any,
) -> tuple[list[dict[str, Any]], set[str], int]:
    topics: list[dict[str, Any]] = []
    files: set[str] = set()
    removed = 0
    for index, value in enumerate(
        object_list(values, "discovery draft topics"),
        start=1,
    ):
        expected = {"id", "title", "responsibility", "reason", "files"}
        if set(value) != expected:
            raise campaign.CampaignError(
                f"discovery draft topic {index} needs "
                "id, title, responsibility, reason, and files"
            )
        normalized_files, duplicates = deduplicated_paths(
            value["files"],
            f"discovery draft topic {index} files",
        )
        removed += duplicates
        topic = campaign.normalize_candidate_topic(
            value | {"files": normalized_files},
            field=f"discovery draft topic {index}",
        )
        topics.append(topic)
        files.update(topic["files"])
    return topics, files, removed


def normalize_supporting(
    values: Any,
    topic_files: set[str],
) -> tuple[list[dict[str, Any]], set[str], int, int]:
    supporting: list[dict[str, Any]] = []
    claimed: set[str] = set()
    removed_duplicates = 0
    removed_topic_overlap = 0
    for index, value in enumerate(
        object_list(values, "discovery draft supporting"),
        start=1,
    ):
        if set(value) != {"reason", "files"}:
            raise campaign.CampaignError(
                f"discovery draft supporting {index} needs reason and files"
            )
        reason = value["reason"]
        if not isinstance(reason, str) or not reason.strip():
            raise campaign.CampaignError(
                f"discovery draft supporting {index} needs a reason"
            )
        paths, duplicates = deduplicated_paths(
            value["files"],
            f"discovery draft supporting {index} files",
        )
        removed_duplicates += duplicates
        overlap = set(paths) & topic_files
        removed_topic_overlap += len(overlap)
        remaining = set(paths) - topic_files
        repeated = remaining & claimed
        removed_duplicates += len(repeated)
        remaining -= claimed
        if not remaining:
            continue
        claimed.update(remaining)
        supporting.append(
            {
                "reason": reason.strip(),
                "files": sorted(remaining),
            }
        )
    return (
        supporting,
        claimed,
        removed_duplicates,
        removed_topic_overlap,
    )


def normalize_child_leads(
    values: Any,
) -> tuple[list[dict[str, Any]], set[str], int]:
    children: list[dict[str, Any]] = []
    files: set[str] = set()
    removed = 0
    expected = {"id", "title", "question", "reason", "seed_files"}
    for index, value in enumerate(
        object_list(values, "discovery draft child_leads"),
        start=1,
    ):
        if set(value) != expected:
            raise campaign.CampaignError(
                f"discovery draft child lead {index} needs "
                "id, title, question, reason, and seed_files"
            )
        seed_files, duplicates = deduplicated_paths(
            value["seed_files"],
            f"discovery draft child lead {index} seed_files",
        )
        removed += duplicates
        child = value | {"seed_files": seed_files}
        children.append(child)
        files.update(seed_files)
    return children, files, removed


def canonical_result(
    packet: dict[str, Any],
    draft: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, int]]:
    if set(draft) != DRAFT_FIELDS:
        raise campaign.CampaignError(
            "discovery draft needs exactly disposition, reason, queries, "
            "topics, supporting, and child_leads"
        )
    disposition = draft["disposition"]
    if disposition not in DRAFT_DISPOSITIONS:
        raise campaign.CampaignError(
            f"invalid discovery draft disposition: {disposition!r}"
        )
    reason = draft["reason"]
    if not isinstance(reason, str) or not reason.strip():
        raise campaign.CampaignError("discovery draft needs a reason")
    raw_queries = campaign.string_list(
        draft["queries"],
        "discovery draft queries",
    )
    queries = list(dict.fromkeys(raw_queries))
    topics, topic_files, topic_duplicates = normalize_topics(draft["topics"])
    (
        supporting,
        supporting_files,
        supporting_duplicates,
        topic_supporting_overlap,
    ) = normalize_supporting(draft["supporting"], topic_files)
    children, child_files, child_duplicates = normalize_child_leads(
        draft["child_leads"]
    )
    if disposition != "mapped" and (topics or supporting or children):
        raise campaign.CampaignError(
            f"discovery draft disposition {disposition} "
            "cannot publish topics, supporting files, or child leads"
        )
    status = (
        disposition
        if disposition != "mapped"
        else ("expanded" if children else "leaf")
    )
    lead = campaign.normalize_discovery_lead(
        packet.get("lead"),
        field="discovery packet lead",
    )
    canonical = {
        "lead_id": lead["id"],
        "status": status,
        "reason": reason.strip(),
        "inspected": {
            "files": sorted(topic_files | supporting_files | child_files),
            "queries": queries,
        },
        "topics": topics,
        "supporting": supporting,
        "child_leads": children,
    }
    normalized = campaign.validate_discovery_result(
        packet,
        canonical,
        Path(packet["repository_root"]).resolve(),
    )
    result = {
        "lead_id": normalized["lead"]["id"],
        "status": normalized["status"],
        "reason": normalized["reason"],
        "inspected": normalized["inspected"],
        "topics": normalized["topics"],
        "supporting": normalized["supporting"],
        "child_leads": normalized["child_leads"],
    }
    return result, {
        "duplicate_queries": len(raw_queries) - len(queries),
        "duplicate_topic_files": topic_duplicates,
        "duplicate_supporting_files": supporting_duplicates,
        "duplicate_child_seed_files": child_duplicates,
        "topic_supporting_overlaps": topic_supporting_overlap,
    }


def finalize(args: argparse.Namespace) -> dict[str, Any]:
    if args.result.exists():
        raise campaign.CampaignError(
            f"discovery result already exists: {args.result}"
        )
    packet = campaign.read_json(args.packet)
    if (
        set(packet)
        != {
            "discovery_contract_version",
            "repository_root",
            "spine_root",
            "operation",
            "lead",
            "source_refs",
        }
        or packet.get("discovery_contract_version")
        != campaign.DISCOVERY_CONTRACT_VERSION
    ):
        raise campaign.CampaignError("discovery packet contract is invalid")
    campaign.validate_operation_spec(packet.get("operation"))
    for field in ("repository_root", "spine_root"):
        value = packet[field]
        if not isinstance(value, str) or not value.strip():
            raise campaign.CampaignError(
                f"discovery packet {field} must be a non-empty string"
            )
    campaign.string_list(packet["source_refs"], "discovery packet source_refs")
    repository_root = Path(packet["repository_root"]).resolve()
    if not repository_root.is_dir():
        raise campaign.CampaignError(
            f"discovery repository root is not a directory: {repository_root}"
        )
    draft = campaign.read_json(args.draft)
    result, normalization = canonical_result(packet, draft)
    campaign.atomic_write(args.result, result)
    return {
        "status": "ready",
        "lead_id": result["lead_id"],
        "result": str(args.result.resolve()),
        "normalization": normalization,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("packet", type=Path)
    result.add_argument("draft", type=Path)
    result.add_argument("result", type=Path)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        value = finalize(args)
    except (campaign.CampaignError, OSError, UnicodeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(value, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
