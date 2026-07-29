#!/usr/bin/env python3
"""Prepare, validate, and materialize semantic Map synthesis."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import campaign


SYNTHESIS_CONTRACT_VERSION = 7
MAX_EVIDENCE_STRATA = 8

def source_topics(
    corpus: dict[str, Any],
) -> tuple[
    list[dict[str, Any]],
    dict[str, list[str]],
    dict[str, dict[str, str]],
]:
    topics: list[dict[str, Any]] = []
    files: dict[str, list[str]] = {}
    leads: dict[str, dict[str, str]] = {}
    for result in corpus["leads"]:
        lead = result["lead"]
        leads[lead["id"]] = {
            key: lead[key]
            for key in ("title", "question", "reason")
        }
        seen: set[str] = set()
        for topic in result["topics"]:
            topic_id = topic["id"]
            if topic_id in seen:
                raise campaign.CampaignError(
                    f"discovery lead {lead['id']} repeats topic id: {topic_id}"
                )
            seen.add(topic_id)
            source_id = f"{lead['id']}/{topic_id}"
            if source_id in files:
                raise campaign.CampaignError(
                    f"duplicate synthesis source topic: {source_id}"
                )
            files[source_id] = topic["files"]
            topics.append(
                {
                    "source_id": source_id,
                    "title": topic["title"],
                    "responsibility": topic["responsibility"],
                    "reason": topic["reason"],
                    "lead_id": lead["id"],
                }
            )
    if len(topics) != len(corpus["topics"]):
        raise campaign.CampaignError(
            "discovery corpus flattened topics differ from lead topics"
        )
    return topics, files, leads


def load_corpus(path: Path) -> dict[str, Any]:
    raw = campaign.read_json(path)
    if not isinstance(raw, dict):
        raise campaign.CampaignError("discovery corpus must be an object")
    try:
        repository_root = Path(raw["repository_root"])
        spine_root = Path(raw["spine_root"])
    except (KeyError, TypeError) as error:
        raise campaign.CampaignError(
            "discovery corpus roots are invalid"
        ) from error
    return campaign.load_discovery_corpus(path, repository_root, spine_root)


def clean_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise campaign.CampaignError(f"{field} must be nonempty text")
    return value.strip()


def source_ids(value: Any, known: set[str], field: str) -> list[str]:
    values = campaign.string_list(value, field, nonempty=True)
    if len(values) != len(set(values)):
        raise campaign.CampaignError(f"{field} repeats source topics")
    unknown = sorted(set(values) - known)
    if unknown:
        raise campaign.CampaignError(f"{field} has unknown source topics: {unknown}")
    return sorted(values)


def representative_evidence_strata(
    source_topic_ids: list[str],
    file_map: dict[str, list[str]],
) -> list[dict[str, str]]:
    """Choose bounded samples from semantic scout topics, not individual files."""
    source_ids = sorted(source_topic_ids)
    if len(source_ids) > MAX_EVIDENCE_STRATA:
        last = len(source_ids) - 1
        source_ids = [
            source_ids[(index * last) // (MAX_EVIDENCE_STRATA - 1)]
            for index in range(MAX_EVIDENCE_STRATA)
        ]
    used: set[str] = set()
    result: list[dict[str, str]] = []
    for source_id in source_ids:
        candidates = sorted(
            file_map[source_id],
            key=lambda path: (
                path in used,
                ".test." in path or "/test/" in path or "/tests/" in path,
                len(Path(path).parts),
                path,
            ),
        )
        if not candidates:
            continue
        sample = candidates[0]
        used.add(sample)
        result.append(
            {
                "id": f"semantic-source-{len(result) + 1:02d}",
                "sample": sample,
            }
        )
    return result


def normalize_candidate(
    value: Any,
    known: set[str],
    *,
    field: str,
) -> dict[str, Any]:
    base_fields = {
        "id",
        "title",
        "responsibility",
        "reason",
        "source_topic_ids",
    }
    expected = base_fields | {"document", "relationships"}
    if not isinstance(value, dict) or set(value) != expected:
        raise campaign.CampaignError(
            f"{field} needs id, document, title, responsibility, reason, "
            "relationships, and source_topic_ids"
        )
    result = {
        "id": campaign.validate_id(value["id"]),
        "title": clean_text(value["title"], f"{field} title"),
        "responsibility": clean_text(
            value["responsibility"], f"{field} responsibility"
        ),
        "reason": clean_text(value["reason"], f"{field} reason"),
        "source_topic_ids": source_ids(
            value["source_topic_ids"], known, f"{field} source_topic_ids"
        ),
    }
    document = campaign.validate_relative_path(value["document"])
    if not document.endswith(".md"):
        raise campaign.CampaignError(
            f"{field} document must be canonical Markdown"
        )
    result["document"] = document
    result["relationships"] = normalize_relationships(
        value["relationships"],
        field=f"{field} relationships",
    )
    return result


def normalize_relationships(value: Any, *, field: str) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise campaign.CampaignError(f"{field} must be a list")
    normalized: list[dict[str, str]] = []
    keys: set[tuple[str, str]] = set()
    for index, row in enumerate(value, start=1):
        if not isinstance(row, dict) or set(row) != {"type", "target", "reason"}:
            raise campaign.CampaignError(
                f"{field} row {index} needs type, target, and reason"
            )
        relation = clean_text(row["type"], f"{field} row {index} type")
        if relation not in campaign.CORE_RELATIONS and campaign.re.fullmatch(
            r"x-[a-z0-9]+(?:-[a-z0-9]+)*", relation
        ) is None:
            raise campaign.CampaignError(
                f"{field} row {index} has invalid relation: {relation}"
            )
        target = campaign.validate_id(row["target"])
        key = (relation, target)
        if key in keys:
            raise campaign.CampaignError(
                f"{field} repeats relationship {relation} -> {target}"
            )
        keys.add(key)
        normalized.append(
            {
                "type": relation,
                "target": target,
                "reason": clean_text(row["reason"], f"{field} row {index} reason"),
            }
        )
    return sorted(
        normalized,
        key=lambda row: (row["type"], row["target"], row["reason"]),
    )


def command_prepare(args: argparse.Namespace) -> dict[str, Any]:
    corpus = load_corpus(args.corpus)
    repository_root = Path(corpus["repository_root"])
    campaign.require_map_runtime_path(
        args.corpus, repository_root, field="discovery corpus"
    )
    campaign.require_map_runtime_path(
        args.output, repository_root, field="synthesis packet"
    )
    topics, _, leads = source_topics(corpus)
    input_digest = campaign.digest_json(
        {
            "contract": SYNTHESIS_CONTRACT_VERSION,
            "corpus_digest": corpus["digest"],
        }
    )
    expected = {
        "synthesis_contract_version": SYNTHESIS_CONTRACT_VERSION,
        "corpus_digest": corpus["digest"],
        "operation": corpus["operation"],
        "spine_root": corpus["spine_root"],
        "existing_owners": [
            {"id": owner, **profile}
            for owner, profile in sorted(
                campaign.spine_owner_registry(Path(corpus["spine_root"])).items()
            )
        ],
        "allowed_relationship_types": sorted(campaign.CORE_RELATIONS),
        "source_topic_count": len(topics),
        "leads": leads,
        "source_topics": topics,
    }
    already_ready = args.output.is_file()
    if args.output.exists() and (
        not already_ready or campaign.read_json(args.output) != expected
    ):
        raise campaign.CampaignError(
            f"existing synthesis packet has different inputs: {args.output}"
        )
    campaign.atomic_write(args.output, expected)
    if args.ledger is not None:
        with campaign.locked_ledger(args.ledger) as ledger:
            recorded = campaign.same_artifact(
                ledger["artifacts"]["synthesis"].get("packet"),
                args.output,
                input_digest=input_digest,
            )
            campaign.record_artifact(
                ledger,
                "synthesis",
                "packet",
                args.output,
                input_digest=input_digest,
            )
            if not recorded:
                campaign.save_locked(args.ledger, ledger)
    return {
        "status": "already_ready" if already_ready else "written",
        "source_topics": len(topics),
        "output": str(args.output.resolve()),
    }


def normalize_open_leads(
    values: Any,
    repository_root: Path,
) -> list[dict[str, Any]]:
    if not isinstance(values, list):
        raise campaign.CampaignError("open_leads must be a list")
    result: list[dict[str, Any]] = []
    ids: set[str] = set()
    for index, value in enumerate(values, start=1):
        expected = {"id", "title", "question", "reason", "seed_files"}
        if not isinstance(value, dict) or set(value) != expected:
            raise campaign.CampaignError(f"open lead {index} has invalid shape")
        lead_id = campaign.validate_id(value["id"])
        if lead_id in ids:
            raise campaign.CampaignError(f"open lead repeats id: {lead_id}")
        ids.add(lead_id)
        files = [
            campaign.validate_relative_path(item)
            for item in campaign.string_list(
                value["seed_files"],
                f"open lead {lead_id} seed_files",
            )
        ]
        if len(files) != len(set(files)):
            raise campaign.CampaignError(
                f"open lead {lead_id} repeats seed_files"
            )
        if len(files) > campaign.MAX_SCOUT_SEED_FILES:
            raise campaign.CampaignError(
                f"open lead {lead_id} exceeds "
                f"{campaign.MAX_SCOUT_SEED_FILES} seed files"
            )
        campaign.validate_repository_files(
            repository_root,
            files,
            field=f"open lead {lead_id} seed file",
        )
        result.append(
            {
                "id": lead_id,
                "title": clean_text(value["title"], f"open lead {lead_id} title"),
                "question": clean_text(
                    value["question"], f"open lead {lead_id} question"
                ),
                "reason": clean_text(value["reason"], f"open lead {lead_id} reason"),
                "seed_files": sorted(files),
            }
        )
    return result


def normalize_coverage(
    value: Any,
    spine_root: Path,
    *,
    topic_id: str,
) -> tuple[str, list[dict[str, Any]]]:
    reason = clean_text(value.get("coverage_reason"), "coverage_reason")
    citations = value.get("coverage")
    if not isinstance(citations, list) or not citations:
        raise campaign.CampaignError(
            f"covered topic {topic_id} needs nonempty coverage"
        )
    normalized: list[dict[str, Any]] = []
    documents: set[str] = set()
    for citation in citations:
        if not isinstance(citation, dict) or set(citation) != {"document", "claims"}:
            raise campaign.CampaignError(
                f"covered topic {topic_id} citation is invalid"
            )
        document = campaign.validate_relative_path(citation["document"])
        if document in documents:
            raise campaign.CampaignError(
                f"covered topic {topic_id} repeats document: {document}"
            )
        documents.add(document)
        path = spine_root / document
        if not path.is_file():
            raise campaign.CampaignError(
                f"covered topic {topic_id} document does not exist: {document}"
            )
        claims = campaign.string_list(
            citation["claims"],
            f"covered topic {topic_id} claims",
            nonempty=True,
        )
        if len(claims) != len(set(claims)):
            raise campaign.CampaignError(
                f"covered topic {topic_id} repeats claims"
            )
        body = path.read_text(encoding="utf-8")
        for claim in claims:
            if campaign.COVERAGE_CLAIM_ID_RE.fullmatch(claim) is None:
                raise campaign.CampaignError(
                    f"covered topic {topic_id} has invalid claim: {claim}"
                )
            definition = campaign.re.compile(
                rf"^ {{0,3}}[-+*]\s+\*\*{campaign.re.escape(claim)}\*\*"
                rf"\s+—\s+\S",
                campaign.re.MULTILINE,
            )
            if definition.search(body) is None:
                raise campaign.CampaignError(
                    f"covered topic {topic_id} claim is not defined: {claim}"
                )
        normalized.append({"document": document, "claims": sorted(claims)})
    return reason, sorted(normalized, key=lambda item: item["document"])


def synthesis_diagnostics(
    *,
    corpus: dict[str, Any],
    source_count: int,
    semantic_values: list[dict[str, Any]],
    covered_count: int,
) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    existing_documents = [
        path
        for path in Path(corpus["spine_root"]).rglob("*.md")
        if path.name != "_INDEX.md"
    ]
    if source_count and existing_documents and covered_count == 0:
        diagnostics.append(
            {
                "code": "zero-existing-coverage",
                "message": (
                    "Existing SpecSpine documents were present but no topic was "
                    "classified as covered; recheck owner responsibilities."
                ),
            }
        )
    singleton_count = sum(
        len(value["source_topic_ids"]) == 1 for value in semantic_values
    )
    if source_count >= 20 and singleton_count / source_count >= 0.8:
        diagnostics.append(
            {
                "code": "high-singleton-ratio",
                "message": (
                    "At least 80% of source topics passed through as singleton "
                    "semantic topics; recheck cross-batch ownership and granularity."
                ),
            }
        )
    if source_count >= 20 and len(semantic_values) / source_count >= 0.9:
        diagnostics.append(
            {
                "code": "low-semantic-reduction",
                "message": (
                    "Final semantic topic count is at least 90% of source topic "
                    "count; recheck directory-shaped or aspect-shaped decomposition."
                ),
            }
        )
    return diagnostics


def publish_validated_plan(
    output: Path,
    plan: dict[str, Any],
    *,
    corpus: dict[str, Any],
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.",
        suffix=".tmp",
        dir=output.parent,
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        campaign.atomic_write(temporary, plan)
        campaign.validate_topic_plan(
            temporary,
            corpus["evidence_files"],
            Path(corpus["spine_root"]),
            corpus["operation"],
            corpus["deferred_leads"],
        )
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)


MAPPING_KEYS = {
    "topics",
    "covered",
    "supporting",
    "open_leads",
    "deferred_leads",
    "peer_family_review",
}


def normalize_mapping(value: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != MAPPING_KEYS:
        raise campaign.CampaignError(
            f"{field} needs exactly topics, covered, supporting, "
            "open_leads, and deferred_leads"
        )
    if not all(
        isinstance(value[key], list)
        for key in MAPPING_KEYS - {"peer_family_review"}
    ):
        raise campaign.CampaignError(f"{field} collections must be lists")
    return value


def normalize_peer_family_review(
    value: Any,
    *,
    completion: dict[str, Any],
    source_ids: set[str],
    open_lead_ids: set[str],
) -> dict[str, Any]:
    keys = {"status", "reason", "source_topic_ids", "open_lead_ids"}
    if not isinstance(value, dict) or set(value) != keys:
        raise campaign.CampaignError(
            "peer_family_review needs status, reason, source_topic_ids, "
            "and open_lead_ids"
        )
    status = value["status"]
    allowed = {"accounted", "none-found", "not-required"}
    if status not in allowed:
        raise campaign.CampaignError("peer_family_review status is invalid")
    reason = clean_text(value["reason"], "peer_family_review reason")
    reviewed_sources = value["source_topic_ids"]
    reviewed_leads = value["open_lead_ids"]
    if not isinstance(reviewed_sources, list) or not all(
        isinstance(item, str) for item in reviewed_sources
    ):
        raise campaign.CampaignError(
            "peer_family_review source_topic_ids must be a list of strings"
        )
    if not isinstance(reviewed_leads, list) or not all(
        isinstance(item, str) for item in reviewed_leads
    ):
        raise campaign.CampaignError(
            "peer_family_review open_lead_ids must be a list of strings"
        )
    if len(reviewed_sources) != len(set(reviewed_sources)) or len(
        reviewed_leads
    ) != len(set(reviewed_leads)):
        raise campaign.CampaignError("peer_family_review repeats IDs")
    unknown_sources = set(reviewed_sources) - source_ids
    unknown_leads = set(reviewed_leads) - open_lead_ids
    if unknown_sources or unknown_leads:
        raise campaign.CampaignError(
            "peer_family_review references unknown IDs: "
            f"{sorted(unknown_sources | unknown_leads)}"
        )
    exhaustive = completion["kind"] == "exhaustive"
    if exhaustive and status == "not-required":
        raise campaign.CampaignError(
            "exhaustive synthesis requires a peer-family review"
        )
    if status == "none-found" and (reviewed_sources or reviewed_leads):
        raise campaign.CampaignError(
            "none-found peer-family review cannot reference IDs"
        )
    if status == "accounted" and not (reviewed_sources or reviewed_leads):
        raise campaign.CampaignError(
            "accounted peer-family review needs at least one ID"
        )
    return {
        "status": status,
        "reason": reason,
        "source_topic_ids": sorted(reviewed_sources),
        "open_lead_ids": sorted(reviewed_leads),
    }


def command_materialize(args: argparse.Namespace) -> dict[str, Any]:
    corpus = load_corpus(args.corpus)
    repository_root = Path(corpus["repository_root"])
    for path, field in (
        (args.corpus, "discovery corpus"),
        (args.mapping, "synthesis mapping"),
        (args.output, "topic plan"),
    ):
        campaign.require_map_runtime_path(path, repository_root, field=field)
    topics, file_map, _ = source_topics(corpus)
    known = set(file_map)
    raw = normalize_mapping(
        campaign.read_json(args.mapping),
        field="semantic mapping",
    )
    final_topics: list[dict[str, Any]] = []
    final_covered: list[dict[str, Any]] = []
    final_ids: set[str] = set()
    used_sources: set[str] = set()
    topic_files: set[str] = set()

    def materialize_topic(
        value: Any,
        *,
        field: str,
        covered: bool,
    ) -> dict[str, Any]:
        base_keys = {
            "id",
            "document",
            "title",
            "responsibility",
            "reason",
            "relationships",
            "source_topic_ids",
        }
        required = base_keys | ({"coverage_reason", "coverage"} if covered else set())
        if not isinstance(value, dict) or set(value) != required:
            raise campaign.CampaignError(f"{field} has invalid shape")
        base = normalize_candidate(
            {key: value[key] for key in base_keys},
            known,
            field=field,
        )
        if base["id"] in final_ids:
            raise campaign.CampaignError(f"duplicate final topic id: {base['id']}")
        final_ids.add(base["id"])
        used_sources.update(base["source_topic_ids"])
        files = sorted(
            {
                path
                for source_id in base["source_topic_ids"]
                for path in file_map[source_id]
            }
        )
        if len(files) > campaign.MAX_UNIT_FILES:
            raise campaign.CampaignError(
                f"{field} {base['id']} materializes {len(files)} files; "
                f"maximum is {campaign.MAX_UNIT_FILES}"
            )
        topic_files.update(files)
        result = {
            key: base[key]
            for key in (
                "id",
                "document",
                "title",
                "responsibility",
                "reason",
                "relationships",
            )
        } | {"files": files}
        if not covered:
            result["evidence_strata"] = representative_evidence_strata(
                base["source_topic_ids"],
                file_map,
            )
        if covered:
            coverage_reason, coverage = normalize_coverage(
                value,
                Path(corpus["spine_root"]),
                topic_id=base["id"],
            )
            result |= {
                "coverage_reason": coverage_reason,
                "coverage": coverage,
            }
        return result

    for index, value in enumerate(raw["topics"], start=1):
        final_topics.append(
            materialize_topic(
                value,
                field=f"uncovered topic {index}",
                covered=False,
            )
        )
    for index, value in enumerate(raw["covered"], start=1):
        final_covered.append(
            materialize_topic(
                value,
                field=f"covered topic {index}",
                covered=True,
            )
        )

    supporting_sources: set[str] = set()
    supporting_reasons: list[str] = []
    for index, value in enumerate(raw["supporting"], start=1):
        if not isinstance(value, dict) or set(value) != {
            "reason",
            "source_topic_ids",
        }:
            raise campaign.CampaignError(
                f"supporting mapping {index} has invalid shape"
            )
        reason = clean_text(value["reason"], f"supporting mapping {index} reason")
        ids = source_ids(
            value["source_topic_ids"],
            known,
            f"supporting mapping {index} source_topic_ids",
        )
        overlap = supporting_sources & set(ids)
        if overlap:
            raise campaign.CampaignError(
                f"supporting mappings repeat source topics: {sorted(overlap)}"
            )
        supporting_sources.update(ids)
        supporting_reasons.append(reason)
    conflict = supporting_sources & used_sources
    if conflict:
        raise campaign.CampaignError(
            f"source topics cannot be both semantic and supporting: {sorted(conflict)}"
        )
    if used_sources | supporting_sources != known:
        raise campaign.CampaignError(
            "semantic mapping does not disposition every source topic: "
            f"{sorted(known - used_sources - supporting_sources)}"
        )

    supporting_files = {
        path
        for source_id in supporting_sources
        for path in file_map[source_id]
    }
    corpus_supporting = {
        path
        for value in corpus["supporting"]
        for path in value["files"]
    }
    material_supporting = sorted(
        (supporting_files | corpus_supporting) - topic_files
    )
    final_supporting = (
        [
            {
                "reason": (
                    "; ".join(sorted(set(supporting_reasons)))
                    if supporting_reasons
                    else "Discovery classified these files as supporting evidence."
                ),
                "files": material_supporting,
            }
        ]
        if material_supporting
        else []
    )
    open_leads = normalize_open_leads(
        raw["open_leads"],
        Path(corpus["repository_root"]),
    )
    peer_family_review = normalize_peer_family_review(
        raw["peer_family_review"],
        completion=corpus["operation"]["completion"],
        source_ids=known,
        open_lead_ids={lead["id"] for lead in open_leads},
    )
    if raw["deferred_leads"] != corpus["deferred_leads"]:
        raise campaign.CampaignError(
            "semantic mapping deferred_leads differ from discovery corpus"
        )
    plan = {
        "topics": sorted(final_topics, key=lambda value: value["id"]),
        "covered": sorted(final_covered, key=lambda value: value["id"]),
        "supporting": final_supporting,
        "open_leads": open_leads,
        "deferred_leads": raw["deferred_leads"],
        "peer_family_review": peer_family_review,
    }
    semantic_topics = final_topics + final_covered
    semantic_ids = {value["id"] for value in semantic_topics}
    existing_owners = campaign.spine_owner_registry(Path(corpus["spine_root"]))
    existing_ids = set(existing_owners)
    existing_documents = {
        profile["document"]: owner
        for owner, profile in existing_owners.items()
    }
    documents = [value["document"] for value in semantic_topics]
    if len(documents) != len(set(documents)):
        raise campaign.CampaignError("semantic mapping repeats canonical documents")
    for topic in semantic_topics:
        existing_document = existing_owners.get(topic["id"], {}).get("document")
        if existing_document is not None and topic["document"] != existing_document:
            raise campaign.CampaignError(
                f"existing owner {topic['id']} must keep canonical document "
                f"{existing_document}"
            )
        document_owner = existing_documents.get(topic["document"])
        if document_owner is not None and topic["id"] != document_owner:
            raise campaign.CampaignError(
                f"existing document {topic['document']} must keep owner "
                f"{document_owner}"
            )
        for relationship in topic["relationships"]:
            if relationship["target"] not in semantic_ids | existing_ids:
                raise campaign.CampaignError(
                    f"topic {topic['id']} relationship targets unknown "
                    f"owner: {relationship['target']}"
                )
            if relationship["target"] == topic["id"]:
                raise campaign.CampaignError(
                    f"topic {topic['id']} cannot relate to itself"
                )
    if not open_leads:
        publish_validated_plan(args.output, plan, corpus=corpus)
    else:
        campaign.atomic_write(args.output, plan)
    semantic_values = raw["topics"] + raw["covered"]
    singleton_passthrough = sum(
        len(value["source_topic_ids"]) == 1
        for value in semantic_values
    )
    diagnostics = synthesis_diagnostics(
        corpus=corpus,
        source_count=len(topics),
        semantic_values=semantic_values,
        covered_count=len(final_covered),
    )
    return {
        "status": "written",
        "source_topics": len(topics),
        "final_topics": len(final_topics) + len(final_covered),
        "singleton_topics": singleton_passthrough,
        "open_leads": len(open_leads),
        "diagnostics": diagnostics,
        "output": str(args.output.resolve()),
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("corpus", type=Path)
    prepare.add_argument("output", type=Path)
    prepare.add_argument("--ledger", type=Path)
    materialize = sub.add_parser("materialize")
    materialize.add_argument("corpus", type=Path)
    materialize.add_argument("mapping", type=Path)
    materialize.add_argument("output", type=Path)
    return result


def main() -> int:
    args = parser().parse_args()
    commands = {
        "prepare": command_prepare,
        "materialize": command_materialize,
    }
    try:
        value = commands[args.command](args)
    except (campaign.CampaignError, OSError, UnicodeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(value, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
