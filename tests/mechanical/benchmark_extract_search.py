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
SEARCH = ROOT / "skills" / "specspine-extract" / "scripts" / "search_spine.py"


def write_corpus(root: Path, document_count: int, query_count: int) -> list[dict[str, str]]:
    if document_count < query_count + 1:
        raise ValueError("document count must exceed query count")
    owners = [f"owner-{index}.md" for index in range(query_count)]
    (root / "README.md").write_text(
        "# Benchmark\n\n" + "\n".join(
            f"[Owner {index}]({path})" for index, path in enumerate(owners)
        ) + "\n",
        encoding="utf-8",
    )
    workload: list[dict[str, str]] = []
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
                "query": f"change capability{index} invariant{index}",
                "expected": path,
            },
            {"kind": "semantic-id", "query": semantic_id, "expected": path},
        ))
    for index in range(document_count - query_count - 1):
        (root / f"decoy-{index:05d}.md").write_text(
            f"# Decoy {index}\n\nGeneric change boundary material noise{index}.\n",
            encoding="utf-8",
        )
    return workload


def invoke(root: Path, cache: Path, query: str) -> tuple[dict[str, Any], int]:
    environment = os.environ.copy()
    environment["SPECSPINE_CACHE_DIR"] = str(cache)
    completed = subprocess.run(
        [
            sys.executable,
            str(SEARCH),
            str(root),
            f"--query={query}",
            "--graph-depth=0",
            "--graph-limit=0",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
        timeout=120,
    )
    payload = json.loads(completed.stdout)
    if completed.returncode != 0:
        raise RuntimeError(payload)
    return payload, len(completed.stdout.encode("utf-8"))


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


def run_scale(document_count: int, query_count: int) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="specspine-extract-benchmark-") as directory:
        base = Path(directory)
        spine = base / "specspine"
        cache = base / "cache"
        spine.mkdir()
        workload = write_corpus(spine, document_count, query_count)
        rows: list[dict[str, Any]] = []
        cold_payload: dict[str, Any] | None = None
        for item in workload:
            payload, output_bytes = invoke(spine, cache, item["query"])
            cold_payload = cold_payload or payload
            paths = [candidate["path"] for candidate in payload["direct_matches"]]
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
    args = parser.parse_args()
    if args.queries < 1 or any(count <= args.queries for count in args.documents):
        parser.error("queries must be positive and smaller than every document count")
    workers = args.jobs or min(len(args.documents), os.cpu_count() or 1)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        scales = list(executor.map(lambda count: run_scale(count, args.queries), args.documents))
    print(json.dumps({"schema_version": 1, "scales": scales}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
