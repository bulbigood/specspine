#!/usr/bin/env python3
"""Run the production retrieval benchmark over representative corpora."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import statistics
import sys
import tempfile
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
SEARCH_PATH = (
    ROOT / "skills" / "specspine-extract" / "scripts" / "search_spine.py"
)
VALIDATOR_PATH = ROOT / "tools" / "specspine-extract" / "validate_corpus.py"


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SEARCH = load_module("specspine_corpus_search", SEARCH_PATH)
VALIDATOR = load_module("specspine_corpus_validator", VALIDATOR_PATH)


def dcg(grades: list[int]) -> float:
    return sum(
        (2**grade - 1) / math.log2(index + 2)
        for index, grade in enumerate(grades)
    )


def ndcg_at(paths: list[str], grades: dict[str, int], limit: int) -> float:
    gains = {
        path: grade if grade >= 2 else 0
        for path, grade in grades.items()
    }
    actual = dcg([gains.get(path, 0) for path in paths[:limit]])
    ideal = dcg(sorted(gains.values(), reverse=True)[:limit])
    return actual / ideal if ideal else 1.0


def mean(rows: list[dict[str, object]], key: str) -> float:
    values = [float(row[key]) for row in rows]
    return statistics.fmean(values) if values else 0.0


def evaluate_slice(
    manifest_slice: dict[str, object],
    routed: object,
) -> dict[str, object]:
    judgments = {
        str(item["path"]): int(item["grade"])
        for item in manifest_slice["judgments"]
    }
    direct = [str(item["path"]) for item in routed.direct_matches]
    graph = [str(item["path"]) for item in routed.graph_neighbors]
    owner = next(
        (path for path, grade in judgments.items() if grade == 3),
        None,
    )
    owner_rank = (
        direct.index(owner) + 1 if owner is not None and owner in direct else None
    )
    considered = direct[:3]
    relevant_at_3 = sum(judgments.get(path, 0) >= 2 for path in considered)
    support = {path for path, grade in judgments.items() if grade == 2}
    returned = set(direct) | set(graph)
    hard_negatives = {
        str(item["path"])
        for item in manifest_slice["judgments"]
        if item.get("hard_negative", False)
    }
    status = "matched" if direct else "no_match"
    timings = routed.timings or {}
    return {
        "id": str(manifest_slice["id"]),
        "evaluation": str(manifest_slice["evaluation"]),
        "expected_status": str(manifest_slice["expected_status"]),
        "actual_status": status,
        "status_correct": status == manifest_slice["expected_status"],
        "owner": owner,
        "owner_rank": owner_rank,
        "owner_recall_at_1": owner_rank == 1,
        "owner_recall_at_3": owner_rank is not None and owner_rank <= 3,
        "owner_recall_at_5": owner_rank is not None and owner_rank <= 5,
        "reciprocal_rank": 0.0 if owner_rank is None else 1.0 / owner_rank,
        "precision_at_3": (
            relevant_at_3 / len(considered) if considered else 0.0
        ),
        "ndcg_at_5": ndcg_at(direct, judgments, 5),
        "support_recall": (
            len(support & returned) / len(support) if support else 1.0
        ),
        "graph_support_recall": (
            len(support & set(graph)) / len(support) if support else 1.0
        ),
        "graph_broader_precision": (
            sum(judgments.get(path, 0) >= 1 for path in graph) / len(graph)
            if graph else 1.0
        ),
        "graph_core_precision": (
            sum(judgments.get(path, 0) >= 2 for path in graph) / len(graph)
            if graph else 1.0
        ),
        "unnecessary_graph_count": sum(
            judgments.get(path, 0) <= 0 for path in graph
        ),
        "graph_hard_negative": bool(set(graph) & hard_negatives),
        "returned_hard_negative": bool(returned & hard_negatives),
        "hard_negative_at_3": any(
            judgments.get(path, 0) == 0
            and any(
                item["path"] == path and item.get("hard_negative", False)
                for item in manifest_slice["judgments"]
            )
            for path in direct[:3]
        ),
        "direct_paths": direct,
        "graph_paths": graph,
        "direct_count": len(direct),
        "graph_count": len(graph),
        "search_seconds": float(timings.get("search_seconds", 0.0)),
    }


def summarize(scenarios: list[dict[str, object]]) -> dict[str, object]:
    slices = [
        item
        for scenario in scenarios
        for item in scenario["slices"]
    ]
    ranking = [item for item in slices if item["evaluation"] == "ranking"]
    protocol = [item for item in slices if item["evaluation"] == "protocol"]
    return {
        "ranking_slices": len(ranking),
        "protocol_slices": len(protocol),
        "owner_recall_at_1": mean(ranking, "owner_recall_at_1"),
        "owner_recall_at_3": mean(ranking, "owner_recall_at_3"),
        "owner_recall_at_5": mean(ranking, "owner_recall_at_5"),
        "mean_reciprocal_rank": mean(ranking, "reciprocal_rank"),
        "mean_precision_at_3": mean(ranking, "precision_at_3"),
        "mean_ndcg_at_5": mean(ranking, "ndcg_at_5"),
        "mean_support_recall": mean(ranking, "support_recall"),
        "mean_graph_support_recall": mean(ranking, "graph_support_recall"),
        "mean_graph_broader_precision": mean(ranking, "graph_broader_precision"),
        "mean_graph_core_precision": mean(ranking, "graph_core_precision"),
        "mean_unnecessary_graph_count": mean(ranking, "unnecessary_graph_count"),
        "graph_hard_negative_rate": mean(ranking, "graph_hard_negative"),
        "returned_hard_negative_rate": mean(ranking, "returned_hard_negative"),
        "hard_negative_rate_at_3": mean(ranking, "hard_negative_at_3"),
        "status_accuracy": mean(slices, "status_correct"),
        "protocol_status_accuracy": mean(protocol, "status_correct"),
        "mean_direct_count": mean(slices, "direct_count"),
        "mean_graph_count": mean(slices, "graph_count"),
        "mean_search_seconds": mean(slices, "search_seconds"),
        "mean_output_utf8_bytes": mean(scenarios, "output_utf8_bytes"),
    }


def run_manifest(
    manifest_path: Path,
    cache: Path,
) -> dict[str, object]:
    manifest = VALIDATOR.validate_manifest(manifest_path)
    corpus = manifest["corpus"]
    assert isinstance(corpus, dict)
    spine = manifest_path.resolve().parent / "project" / "specspine"
    scenarios: list[dict[str, object]] = []
    previous_cache = os.environ.get("SPECSPINE_CACHE_DIR")
    os.environ["SPECSPINE_CACHE_DIR"] = str(cache)
    try:
        for scenario in manifest["scenarios"]:
            raw_slices = [
                {
                    "id": item["id"],
                    "must": item["must"],
                    **({"should": item["should"]} if "should" in item else {}),
                }
                for item in scenario["slices"]
            ]
            slices = SEARCH.RANKING.parse_query_slices(
                json.dumps(raw_slices, ensure_ascii=False)
            )
            outcome = SEARCH.execute_searches(
                spine,
                slices,
            )
            if outcome.mode != "sqlite-fts5":
                raise RuntimeError(
                    f"{corpus['id']}/{scenario['id']}: {outcome.reason_code}"
                )
            routed_by_id = {
                item.identifier: item.outcome for item in outcome.slices
            }
            evaluated = [
                evaluate_slice(item, routed_by_id[str(item["id"])])
                for item in scenario["slices"]
            ]
            rendered = SEARCH.render_batch_output(
                spine,
                outcome,
            )
            scenarios.append({
                "id": str(scenario["id"]),
                "tags": list(scenario["tags"]),
                "output_utf8_bytes": len(rendered.encode("utf-8")),
                "truncated": '"truncated":true' in rendered,
                "slices": evaluated,
            })
    finally:
        if previous_cache is None:
            os.environ.pop("SPECSPINE_CACHE_DIR", None)
        else:
            os.environ["SPECSPINE_CACHE_DIR"] = previous_cache
    return {
        "corpus_id": str(corpus["id"]),
        "project_type": str(corpus["project_type"]),
        "documentation_language": str(corpus["documentation_language"]),
        "size_tier": str(corpus["size_tier"]),
        "scenarios": scenarios,
        "summary": summarize(scenarios),
    }


def aggregate(results: list[dict[str, object]]) -> dict[str, object]:
    scenarios = [
        scenario
        for result in results
        for scenario in result["scenarios"]
    ]
    return {
        "corpora": len(results),
        **summarize(scenarios),
    }


def aggregate_by(
    results: list[dict[str, object]],
    field: str,
) -> dict[str, dict[str, object]]:
    values = sorted({str(result[field]) for result in results})
    return {
        value: aggregate([
            result
            for result in results
            if str(result[field]) == value
        ])
        for value in values
    }


def discover_manifests(values: list[Path]) -> list[Path]:
    if values:
        paths = [
            value / "manifest.json" if value.is_dir() else value
            for value in values
        ]
    else:
        paths = sorted(
            (Path(__file__).parent / "corpora").glob("*/manifest.json")
        )
    if not paths:
        raise ValueError("no corpus manifests found")
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", action="append", type=Path, default=[])
    args = parser.parse_args()
    try:
        manifests = discover_manifests(args.manifest)
    except ValueError as error:
        parser.error(str(error))
    with tempfile.TemporaryDirectory(
        prefix="specspine-retrieval-corpora-"
    ) as directory:
        cache_root = Path(directory)
        results = [
            run_manifest(
                manifest,
                cache_root / manifest.parent.name,
            )
            for manifest in manifests
        ]
    payload = {
        "schema_version": 1,
        "manifests": [str(path.resolve()) for path in manifests],
        "summary": aggregate(results),
        "breakdowns": {
            "documentation_language": aggregate_by(
                results,
                "documentation_language",
            ),
            "project_type": aggregate_by(
                results,
                "project_type",
            ),
        },
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
