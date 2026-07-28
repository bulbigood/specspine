#!/usr/bin/env python3
"""Observe Extract closure search without changing its stdout contract."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import time
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
    spec = importlib.util.spec_from_file_location(
        "specspine_extract_production_search", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load production search: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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
    parser.add_argument("--query-json", required=True)
    args = parser.parse_args()
    if args.telemetry is None:
        parser.error(f"--telemetry or {LEVEL_ENV} is required")
    try:
        query = json.loads(args.query_json)
    except json.JSONDecodeError as error:
        parser.error(str(error))

    production_path = Path(
        os.environ.get(PRODUCTION_ENV, str(DEFAULT_PRODUCTION_SCRIPT))
    )
    production = load_production(production_path)
    started = time.perf_counter()
    result = production.build_closure(args.spine_root, query)
    elapsed = time.perf_counter() - started
    production_output = json.dumps(result, ensure_ascii=False) + "\n"
    telemetry = {
        "schema_version": 1,
        "mode": "closure",
        "exit_code": 1 if result.get("closure_status") == "invalid" else 0,
        "query_sha256": hashlib.sha256(
            args.query_json.encode("utf-8")
        ).hexdigest(),
        "reason_code": result.get("reason"),
        "documents": len(result.get("sources", [])),
        "closure_status": result.get("closure_status"),
        "coverage": result.get("coverage"),
        "production_output_utf8_bytes": len(production_output.encode("utf-8")),
        "timings": {"total_seconds": round(elapsed, 6)},
        "telemetry_level": args.telemetry,
    }
    append_sidecar(telemetry)
    print(production_output, end="")
    return int(telemetry["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
