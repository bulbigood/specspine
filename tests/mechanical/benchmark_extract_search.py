#!/usr/bin/env python3
"""Deterministic scale benchmark for Extract retrieval without an AI agent."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DIAGNOSTIC_SEARCH = ROOT / "tools" / "specspine-extract" / "search_spine_diagnostics.py"
V2_SEARCH = ROOT / "skills" / "specspine-extract" / "scripts" / "search_spine_v2.py"
AGENT_BOOTSTRAP_TEMPLATE = (
    ROOT / "skills" / "specspine-connect" / "assets" / "templates" / "agent-bootstrap.md"
)


def write_agent_bootstrap(project_root: Path) -> None:
    rendered = AGENT_BOOTSTRAP_TEMPLATE.read_text(encoding="utf-8").replace(
        "{{SPINE_ROOT}}", "specspine"
    ).replace("{{DOCUMENTATION_LANGUAGE}}", "English").replace(
        "{{RETRIEVAL_ACCELERATOR}}", "auto"
    )
    if "{{" in rendered or "}}" in rendered:
        raise ValueError("agent bootstrap has unresolved template placeholders")
    (project_root / "AGENTS.md").write_text(rendered, encoding="utf-8")


def write_corpus(root: Path, document_count: int, query_count: int) -> list[dict[str, Any]]:
    if document_count < query_count * 2 + 1:
        raise ValueError("document count must exceed twice the query count")
    owners = [f"owner-{index}.md" for index in range(query_count)]
    (root / "README.md").write_text(
        "# Benchmark\n\n" + "\n".join(
            f"[Owner {index}]({path})" for index, path in enumerate(owners)
        ) + "\n",
        encoding="utf-8",
    )
    workload: list[dict[str, Any]] = []
    for index, path in enumerate(owners):
        semantic_id = f"CON-benchmark-{index}"
        (root / path).write_text(
            f"# Owner {index}\n\n## Constraints\n\n"
            f"- **{semantic_id}** — Owns capability{index} invariant{index} boundary.\n",
            encoding="utf-8",
        )
        workload.extend((
            {
                "kind": "hybrid",
                "must": [[f"capability{index}"], [f"invariant{index}"]],
                "expected": path,
            },
            {
                "kind": "semantic-id",
                "must": [[semantic_id]],
                "expected": path,
            },
            {
                "kind": "ambiguous",
                "must": [[f"capability{index}"], [f"invariant{index}"]],
                "should": [["timeout"]],
                "expected": path,
            },
        ))
        (root / f"ambiguous-{index}.md").write_text(
            f"# Ambiguous {index}\n\n"
            f"Transport timeout handling mentions capability{index} without invariant ownership.\n",
            encoding="utf-8",
        )
    for index in range(document_count - query_count * 2 - 1):
        (root / f"decoy-{index:05d}.md").write_text(
            f"# Decoy {index}\n\nGeneric change boundary material noise{index}.\n",
            encoding="utf-8",
        )
    return workload


def invoke(
    root: Path,
    cache: Path,
    item: dict[str, Any],
    ranking_system: str,
) -> tuple[dict[str, Any], int]:
    environment = os.environ.copy()
    environment["SPECSPINE_CACHE_DIR"] = str(cache)
    environment["SPECSPINE_PRODUCTION_SEARCH"] = str(V2_SEARCH)
    sidecar = cache.parent / "retrieval-telemetry.jsonl"
    sidecar.unlink(missing_ok=True)
    environment["SPECSPINE_RETRIEVAL_TELEMETRY_FILE"] = str(sidecar)
    completed = subprocess.run(
        [
            sys.executable,
            str(DIAGNOSTIC_SEARCH),
            "--telemetry",
            "full",
            str(root),
            "--queries-json",
            json.dumps([{
                "id": item["kind"],
                "must": item["must"],
                **({"should": item["should"]} if item.get("should") else {}),
            }]),
            "--ranking",
            ranking_system,
            "--graph-depth=0",
            "--graph-limit=0",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
        timeout=120,
    )
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    if completed.returncode != 0:
        raise RuntimeError(payload)
    return payload, int(payload["production_output_utf8_bytes"])


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    reciprocal_ranks = [
        0.0 if row["rank"] is None else 1.0 / row["rank"] for row in rows
    ]
    return {
        "queries": len(rows),
        "recall_at_1": sum(row["rank"] == 1 for row in rows) / len(rows),
        "recall_at_3": sum(row["rank"] is not None and row["rank"] <= 3 for row in rows) / len(rows),
        "recall_at_5": sum(row["rank"] is not None and row["rank"] <= 5 for row in rows) / len(rows),
        "mean_reciprocal_rank": statistics.fmean(reciprocal_ranks),
        "mean_direct_results": statistics.fmean(row["direct_results"] for row in rows),
        "mean_output_utf8_bytes": statistics.fmean(row["output_utf8_bytes"] for row in rows),
        "mean_total_seconds": statistics.fmean(row["total_seconds"] for row in rows),
        "mean_search_seconds": statistics.fmean(row["search_seconds"] for row in rows),
    }


def run_scale(
    document_count: int,
    query_count: int,
    ranking_system: str = "legacy",
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="specspine-extract-benchmark-") as directory:
        base = Path(directory)
        project = base / "project"
        spine = project / "specspine"
        cache = base / "cache"
        spine.mkdir(parents=True)
        write_agent_bootstrap(project)
        workload = write_corpus(spine, document_count, query_count)
        rows: list[dict[str, Any]] = []
        cold_payload: dict[str, Any] | None = None
        for item in workload:
            payload, output_bytes = invoke(spine, cache, item, ranking_system)
            cold_payload = cold_payload or payload
            routed = payload["slices"][0]
            paths = [candidate["path"] for candidate in routed["direct_matches"]]
            rows.append({
                "kind": item["kind"],
                "rank": paths.index(item["expected"]) + 1 if item["expected"] in paths else None,
                "direct_results": len(paths),
                "output_utf8_bytes": output_bytes,
                "total_seconds": payload["timings"]["total_seconds"],
                "search_seconds": payload["timings"]["search_seconds"],
            })
        assert cold_payload is not None
        by_kind = {
            kind: summarize([row for row in rows if row["kind"] == kind])
            for kind in sorted({row["kind"] for row in rows})
        }
        return {
            "documents": document_count,
            "ranking_system": ranking_system,
            "queries_per_kind": query_count,
            "cold": {
                "index_state": cold_payload["index_state"],
                "build_seconds": cold_payload["timings"]["build_seconds"],
                "discovery_seconds": cold_payload["timings"]["discovery_seconds"],
                "total_seconds": cold_payload["timings"]["total_seconds"],
            },
            "workloads": by_kind,
        }


def document_counts(value: str) -> list[int]:
    counts = [int(item) for item in value.split(",")]
    if not counts or any(count < 2 for count in counts):
        raise argparse.ArgumentTypeError("document counts must be integers greater than one")
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--documents", type=document_counts, default=[100, 1000, 10000])
    parser.add_argument("--queries", type=int, default=8, help="queries per workload kind")
    parser.add_argument("--jobs", type=int, default=0, help="parallel scales; 0 selects automatically")
    parser.add_argument(
        "--ranking",
        choices=("legacy", "faceted-bm25", "faceted-normalized"),
        default="legacy",
    )
    args = parser.parse_args()
    if args.queries < 1 or any(count < args.queries * 2 + 1 for count in args.documents):
        parser.error("queries must be positive and fit twice in every document count")
    workers = args.jobs or min(len(args.documents), os.cpu_count() or 1)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        scales = list(executor.map(
            lambda count: run_scale(count, args.queries, args.ranking),
            args.documents,
        ))
    print(json.dumps({"schema_version": 1, "scales": scales}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
