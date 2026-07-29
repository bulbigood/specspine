#!/usr/bin/env python3
"""Prepare, validate, and materialize semantic Map synthesis."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import campaign


DEFAULT_BATCH_SIZE = 25
SYNTHESIS_CONTRACT_VERSION = 3
CORE_RELATIONS = {
    "contains",
    "decomposes-into",
    "performs",
    "depends-on",
    "exposes",
    "consumes",
    "publishes",
    "reads-from",
    "writes-to",
    "owns-data",
    "constrained-by",
    "implemented-by",
    "has-evidence",
    "superseded-by",
    "related-to",
    "refines",
    "satisfies",
    "verified-by",
    "specified-by",
    "compatible-with",
    "migrates-from",
}

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


def normalize_candidate(
    value: Any,
    known: set[str],
    *,
    field: str,
    graph: bool = True,
) -> dict[str, Any]:
    base_fields = {
        "id",
        "title",
        "responsibility",
        "reason",
        "source_topic_ids",
    }
    expected = base_fields | ({"document", "relationships"} if graph else set())
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
    if graph:
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
        if relation not in CORE_RELATIONS and campaign.re.fullmatch(
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
        args.output_dir, repository_root, field="synthesis packet root"
    )
    topics, _, leads = source_topics(corpus)
    input_digest = campaign.digest_json(
        {
            "contract": SYNTHESIS_CONTRACT_VERSION,
            "corpus_digest": corpus["digest"],
            "batch_size": args.batch_size,
        }
    )
    manifest = {"kind": "synthesis-packets", "input_digest": input_digest}
    manifest_path = args.output_dir / "_artifact.json"
    already_ready = manifest_path.is_file()
    if args.output_dir.exists() and (
        not already_ready or campaign.read_json(manifest_path) != manifest
    ):
        raise campaign.CampaignError(
            f"existing synthesis packet directory has different inputs: "
            f"{args.output_dir}"
        )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    packets: list[str] = []
    for offset in range(0, len(topics), args.batch_size):
        batch = topics[offset : offset + args.batch_size]
        batch_id = f"batch-{offset // args.batch_size + 1:04d}"
        batch_lead_ids = {value["lead_id"] for value in batch}
        path = args.output_dir / f"{batch_id}.json"
        expected = {
            "synthesis_contract_version": SYNTHESIS_CONTRACT_VERSION,
            "corpus_digest": corpus["digest"],
            "batch_id": batch_id,
            "leads": {
                lead_id: leads[lead_id]
                for lead_id in sorted(batch_lead_ids)
            },
            "source_topics": batch,
        }
        if path.exists() and campaign.read_json(path) != expected:
            raise campaign.CampaignError(
                f"existing synthesis packet conflicts: {path}"
            )
        campaign.atomic_write(path, expected)
        packets.append(str(path.resolve()))
    campaign.atomic_write(manifest_path, manifest)
    if args.ledger is not None:
        with campaign.locked_ledger(args.ledger) as ledger:
            recorded = campaign.same_artifact(
                ledger["artifacts"]["synthesis"].get("packets"),
                args.output_dir,
                input_digest=input_digest,
            )
            campaign.record_artifact(
                ledger,
                "synthesis",
                "packets",
                args.output_dir,
                input_digest=input_digest,
            )
            if not recorded:
                campaign.save_locked(args.ledger, ledger)
    return {
        "status": "already_ready" if already_ready else "written",
        "source_topics": len(topics),
        "batches": len(packets),
        "packets": packets,
    }


def normalize_reducer_result(
    raw: Any,
    packet: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(raw, dict) or set(raw) != {
        "batch_id",
        "passthrough",
        "merged",
    }:
        raise campaign.CampaignError(
            "reducer result needs exactly batch_id, passthrough, and merged"
        )
    if raw["batch_id"] != packet["batch_id"]:
        raise campaign.CampaignError("reducer batch_id differs from packet")
    known = {value["source_id"] for value in packet["source_topics"]}
    if not isinstance(raw["passthrough"], list):
        raise campaign.CampaignError("reducer passthrough must be a list")
    passthrough = source_ids(
        raw["passthrough"],
        known,
        "reducer passthrough",
    ) if raw["passthrough"] else []
    if not isinstance(raw["merged"], list):
        raise campaign.CampaignError("reducer merged must be a list")
    merged = [
        normalize_candidate(
            value,
            known,
            field=f"reducer merged candidate {index}",
            graph=False,
        )
        for index, value in enumerate(raw["merged"], start=1)
    ]
    for value in merged:
        if len(value["source_topic_ids"]) < 2:
            raise campaign.CampaignError(
                f"reducer merged candidate {value['id']} needs at least two sources"
            )
    ids = [value["id"] for value in merged]
    if len(ids) != len(set(ids)):
        raise campaign.CampaignError("reducer repeats merged candidate ids")
    dispositioned = [
        source_id
        for value in merged
        for source_id in value["source_topic_ids"]
    ] + passthrough
    if len(dispositioned) != len(set(dispositioned)):
        raise campaign.CampaignError(
            "reducer assigns a source topic to multiple candidates"
        )
    if set(dispositioned) != known:
        raise campaign.CampaignError(
            "reducer source disposition is incomplete: "
            f"missing={sorted(known - set(dispositioned))}, "
            f"unknown={sorted(set(dispositioned) - known)}"
        )
    source_index = {
        value["source_id"]: value
        for value in packet["source_topics"]
    }
    candidates = [
        {
            "id": (
                "source-"
                + hashlib.sha256(source_id.encode()).hexdigest()[:16]
            ),
            "title": source_index[source_id]["title"],
            "responsibility": source_index[source_id]["responsibility"],
            "reason": source_index[source_id]["reason"],
            "source_topic_ids": [source_id],
        }
        for source_id in passthrough
    ] + merged
    return {
        "batch_id": raw["batch_id"],
        "candidates": candidates,
        "merged_source_ids": sorted(
            {
                source_id
                for value in merged
                for source_id in value["source_topic_ids"]
            }
        ),
    }


def command_merge(args: argparse.Namespace) -> dict[str, Any]:
    corpus = load_corpus(args.corpus)
    repository_root = Path(corpus["repository_root"])
    for path, field in (
        (args.corpus, "discovery corpus"),
        (args.packets_dir, "synthesis packet root"),
        (args.results_dir, "reducer result root"),
        (args.output, "global synthesis packet"),
    ):
        campaign.require_map_runtime_path(path, repository_root, field=field)
    topics, _, leads = source_topics(corpus)
    known = {value["source_id"] for value in topics}
    packets = sorted(args.packets_dir.glob("batch-*.json"))
    if not packets and known:
        raise campaign.CampaignError("no synthesis reducer packets found")
    results: list[dict[str, Any]] = []
    for packet_path in packets:
        packet = campaign.read_json(packet_path)
        if (
            not isinstance(packet, dict)
            or packet.get("synthesis_contract_version")
            != SYNTHESIS_CONTRACT_VERSION
            or packet.get("corpus_digest") != corpus["digest"]
            or not isinstance(packet.get("leads"), dict)
        ):
            raise campaign.CampaignError(
                f"invalid synthesis reducer packet: {packet_path}"
            )
        result_path = args.results_dir / packet_path.name
        result = normalize_reducer_result(
            campaign.read_json(result_path),
            packet,
        )
        results.append(result)
    candidates = [
        value
        for result in results
        for value in result["candidates"]
    ]
    candidate_ids = [value["id"] for value in candidates]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise campaign.CampaignError(
            "reducer wave repeats candidate ids across batches"
        )
    dispositioned = {
        source_id
        for value in candidates
        for source_id in value["source_topic_ids"]
    }
    if dispositioned != known:
        raise campaign.CampaignError(
            "reducer wave does not cover the complete synthesis source"
        )
    merged_source_ids = {
        source_id
        for result in results
        for source_id in result["merged_source_ids"]
    }
    topic_index = {value["source_id"]: value for value in topics}
    relevant_lead_ids = {
        topic_index[source_id]["lead_id"]
        for source_id in merged_source_ids
    }
    campaign.atomic_write(
        args.output,
        {
            "synthesis_contract_version": SYNTHESIS_CONTRACT_VERSION,
            "corpus_digest": corpus["digest"],
            "operation": corpus["operation"],
            "spine_root": corpus["spine_root"],
            "source_topic_count": len(topics),
            "leads": {
                lead_id: leads[lead_id]
                for lead_id in sorted(relevant_lead_ids)
            },
            "merged_source_topics": [
                topic_index[source_id]
                for source_id in sorted(merged_source_ids)
            ],
            "candidates": candidates,
        },
    )
    return {
        "status": "written",
        "source_topics": len(topics),
        "reduced_candidates": len(candidates),
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
        if path.name != "README.md"
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
}


def normalize_mapping(value: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != MAPPING_KEYS:
        raise campaign.CampaignError(
            f"{field} needs exactly topics, covered, supporting, "
            "open_leads, and deferred_leads"
        )
    if not all(isinstance(value[key], list) for key in MAPPING_KEYS):
        raise campaign.CampaignError(f"{field} collections must be lists")
    return value


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
    }
    semantic_topics = final_topics + final_covered
    semantic_ids = {value["id"] for value in semantic_topics}
    existing_ids = set(
        campaign.spine_owner_registry(Path(corpus["spine_root"]))
    )
    documents = [value["document"] for value in semantic_topics]
    if len(documents) != len(set(documents)):
        raise campaign.CampaignError("semantic mapping repeats canonical documents")
    for topic in semantic_topics:
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


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("corpus", type=Path)
    prepare.add_argument("output_dir", type=Path)
    prepare.add_argument("--ledger", type=Path)
    prepare.add_argument(
        "--batch-size",
        type=positive_int,
        default=DEFAULT_BATCH_SIZE,
    )
    merge = sub.add_parser("merge")
    merge.add_argument("corpus", type=Path)
    merge.add_argument("packets_dir", type=Path)
    merge.add_argument("results_dir", type=Path)
    merge.add_argument("output", type=Path)
    materialize = sub.add_parser("materialize")
    materialize.add_argument("corpus", type=Path)
    materialize.add_argument("mapping", type=Path)
    materialize.add_argument("output", type=Path)
    return result


def main() -> int:
    args = parser().parse_args()
    commands = {
        "prepare": command_prepare,
        "merge": command_merge,
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
