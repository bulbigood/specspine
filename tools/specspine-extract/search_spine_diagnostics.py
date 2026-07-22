#!/usr/bin/env python3
"""Observe the Extract production search without changing its stdout contract."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import sys
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PRODUCTION_SCRIPT = (
    ROOT / "skills" / "specspine-extract" / "scripts" / "search_spine.py"
)
TRACE_ENV = "SPECSPINE_RETRIEVAL_TELEMETRY_FILE"
PRODUCTION_ENV = "SPECSPINE_PRODUCTION_SEARCH"
LEVEL_ENV = "SPECSPINE_RETRIEVAL_TELEMETRY_LEVEL"


def load_production(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("specspine_extract_production_search", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load production search: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def rounded_timings(outcome: object) -> dict[str, float]:
    timings = getattr(outcome, "timings", None)
    return {
        str(key): round(float(value), 6)
        for key, value in (timings.items() if isinstance(timings, dict) else ())
    }


def minimal_telemetry(
    outcome: object, query: str, production_output_bytes: int
) -> dict[str, object]:
    direct = tuple(getattr(outcome, "direct_matches", ()))
    graph = tuple(getattr(outcome, "graph_neighbors", ()))
    return {
        "schema_version": 1,
        "mode": getattr(outcome, "mode"),
        "exit_code": getattr(outcome, "exit_code"),
        "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
        "reason_code": getattr(outcome, "reason_code"),
        "index_state": getattr(outcome, "index_state"),
        "documents": getattr(outcome, "documents"),
        "refreshed": getattr(outcome, "refreshed"),
        "direct_count": len(direct),
        "graph_count": len(graph),
        "production_output_utf8_bytes": production_output_bytes,
        "timings": rounded_timings(outcome),
    }


def full_telemetry(
    outcome: object, query: str, production_output_bytes: int, production: ModuleType
) -> dict[str, object]:
    payload = minimal_telemetry(outcome, query, production_output_bytes)
    payload.update(
        {
            "schema_version": 2,
            "query": query,
            "reason": getattr(outcome, "reason"),
            "retrieval_strategy": getattr(outcome, "retrieval_strategy"),
            "selection": getattr(outcome, "selection") or {},
            "runtime": {
                "python": platform.python_version(),
                "sqlite": production.sqlite3.sqlite_version,
                "fts5": True,
            },
            "direct_matches": list(getattr(outcome, "direct_matches", ())),
            "graph_neighbors": list(getattr(outcome, "graph_neighbors", ())),
        }
    )
    return payload


def append_sidecar(payload: dict[str, object]) -> None:
    configured = os.environ.get(TRACE_ENV)
    if not configured:
        return
    path = Path(configured)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
    descriptor = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, line.encode("utf-8"))
    finally:
        os.close(descriptor)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--telemetry",
        choices=("minimal", "full"),
        default=os.environ.get(LEVEL_ENV),
        help=f"telemetry level; defaults to ${LEVEL_ENV}",
    )
    parser.add_argument("spine_root", type=Path)
    parser.add_argument("--query", required=True, nargs="+")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--graph-limit", type=int, default=2)
    parser.add_argument("--graph-depth", type=int, choices=(0, 1, 2), default=1)
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    if args.telemetry is None:
        parser.error(f"--telemetry or {LEVEL_ENV} is required")
    production_path = Path(
        os.environ.get(PRODUCTION_ENV, str(DEFAULT_PRODUCTION_SCRIPT))
    )
    production = load_production(production_path)
    query = " ".join(args.query)
    outcome = production.execute_search(
        args.spine_root,
        query,
        limit=args.limit,
        graph_limit=args.graph_limit,
        graph_depth=args.graph_depth,
        rebuild=args.rebuild,
    )
    compact = production.compact_payload(outcome)
    compact_json = json.dumps(compact, ensure_ascii=False)
    telemetry = (
        minimal_telemetry(outcome, query, len((compact_json + "\n").encode("utf-8")))
        if args.telemetry == "minimal"
        else full_telemetry(
            outcome,
            query,
            len((compact_json + "\n").encode("utf-8")),
            production,
        )
    )
    telemetry["telemetry_level"] = args.telemetry
    append_sidecar(telemetry)
    print(
        compact_json
        if args.telemetry == "minimal"
        else json.dumps(telemetry, ensure_ascii=False)
    )
    return int(outcome.exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
