#!/usr/bin/env python3
"""Prepare, validate, and materialize semantic Map synthesis."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import campaign


DEFAULT_BATCH_SIZE = 25
SYNTHESIS_CONTRACT_VERSION = 1


def source_topics(corpus: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    topics: list[dict[str, Any]] = []
    files: dict[str, list[str]] = {}
    for result in corpus["leads"]:
        lead = result["lead"]
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
                    "lead": {
                        key: lead[key]
                        for key in ("id", "title", "question", "reason")
                    },
                }
            )
    if len(topics) != len(corpus["topics"]):
        raise campaign.CampaignError(
            "discovery corpus flattened topics differ from lead topics"
        )
    return topics, files


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
) -> dict[str, Any]:
    expected = {
        "id",
        "title",
        "responsibility",
        "reason",
        "source_topic_ids",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise campaign.CampaignError(
            f"{field} needs id, title, responsibility, reason, and source_topic_ids"
        )
    return {
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


def command_prepare(args: argparse.Namespace) -> dict[str, Any]:
    corpus = load_corpus(args.corpus)
    topics, _ = source_topics(corpus)
    if args.output_dir.exists():
        raise campaign.CampaignError(
            f"synthesis packet directory already exists: {args.output_dir}"
        )
    args.output_dir.mkdir(parents=True)
    packets: list[str] = []
    for offset in range(0, len(topics), args.batch_size):
        batch = topics[offset : offset + args.batch_size]
        batch_id = f"batch-{offset // args.batch_size + 1:04d}"
        path = args.output_dir / f"{batch_id}.json"
        campaign.atomic_write(
            path,
            {
                "synthesis_contract_version": SYNTHESIS_CONTRACT_VERSION,
                "corpus_digest": corpus["digest"],
                "batch_id": batch_id,
                "source_topics": batch,
            },
        )
        packets.append(str(path.resolve()))
    return {
        "status": "written",
        "source_topics": len(topics),
        "batches": len(packets),
        "packets": packets,
    }


def normalize_reducer_result(
    raw: Any,
    packet: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(raw, dict) or set(raw) != {"batch_id", "candidates"}:
        raise campaign.CampaignError(
            "reducer result needs exactly batch_id and candidates"
        )
    if raw["batch_id"] != packet["batch_id"]:
        raise campaign.CampaignError("reducer batch_id differs from packet")
    known = {value["source_id"] for value in packet["source_topics"]}
    if not isinstance(raw["candidates"], list) or not raw["candidates"]:
        raise campaign.CampaignError("reducer candidates must be nonempty")
    candidates = [
        normalize_candidate(
            value,
            known,
            field=f"reducer candidate {index}",
        )
        for index, value in enumerate(raw["candidates"], start=1)
    ]
    ids = [value["id"] for value in candidates]
    if len(ids) != len(set(ids)):
        raise campaign.CampaignError("reducer repeats candidate ids")
    dispositioned = [
        source_id
        for value in candidates
        for source_id in value["source_topic_ids"]
    ]
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
    return {"batch_id": raw["batch_id"], "candidates": candidates}


def command_merge(args: argparse.Namespace) -> dict[str, Any]:
    corpus = load_corpus(args.corpus)
    topics, _ = source_topics(corpus)
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
    dispositioned = {
        source_id
        for value in candidates
        for source_id in value["source_topic_ids"]
    }
    if dispositioned != known:
        raise campaign.CampaignError(
            "reducer wave does not cover the complete synthesis source"
        )
    campaign.atomic_write(
        args.output,
        {
            "synthesis_contract_version": SYNTHESIS_CONTRACT_VERSION,
            "corpus_digest": corpus["digest"],
            "operation": corpus["operation"],
            "spine_root": corpus["spine_root"],
            "source_topic_count": len(topics),
            "source_topics": topics,
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


def command_materialize(args: argparse.Namespace) -> dict[str, Any]:
    corpus = load_corpus(args.corpus)
    topics, file_map = source_topics(corpus)
    known = set(file_map)
    raw = campaign.read_json(args.mapping)
    expected = {
        "topics",
        "covered",
        "supporting",
        "open_leads",
        "deferred_leads",
    }
    if not isinstance(raw, dict) or set(raw) != expected:
        raise campaign.CampaignError(
            "semantic mapping needs exactly topics, covered, supporting, "
            "open_leads, and deferred_leads"
        )
    if not all(isinstance(raw[key], list) for key in expected):
        raise campaign.CampaignError("semantic mapping collections must be lists")
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
            "title",
            "responsibility",
            "reason",
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
            for key in ("id", "title", "responsibility", "reason")
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
    if not open_leads:
        campaign.validate_topic_plan(
            _write_plan(args.output, plan),
            corpus["evidence_files"],
            Path(corpus["spine_root"]),
            corpus["operation"],
            corpus["deferred_leads"],
        )
    else:
        campaign.atomic_write(args.output, plan)
    singleton_passthrough = sum(
        len(value["source_topic_ids"]) == 1
        for value in raw["topics"] + raw["covered"]
    )
    campaign.atomic_write(args.output, plan)
    return {
        "status": "written",
        "source_topics": len(topics),
        "final_topics": len(final_topics) + len(final_covered),
        "singleton_topics": singleton_passthrough,
        "open_leads": len(open_leads),
        "output": str(args.output.resolve()),
    }


def _write_plan(path: Path, value: dict[str, Any]) -> Path:
    campaign.atomic_write(path, value)
    return path


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
