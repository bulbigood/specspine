#!/usr/bin/env python3
"""Compare Extract agent workflows on a large external Grafana SpecSpine."""

from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import shlex
import shutil
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = Path(__file__).resolve().parent


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


RUNNER = load_module("specspine_eval_run", EVAL_DIR / "run.py")
AGENT_BENCHMARK = load_module(
    "specspine_extract_agent_benchmark", EVAL_DIR / "benchmark_extract_agents.py"
)
ARMS = (
    ("no-extract", "no-extract", "accelerated"),
    # ("fallback", "fallback", "fallback"),
    ("accelerated", "extract", "accelerated"),
)
CASE_ID = "extract-grafana-large"


def materialize_fixture(grafana_root: Path, target: Path) -> Path:
    source = grafana_root.expanduser().resolve()
    agents = source / "AGENTS.md"
    spine = source / "specspine"
    index = spine / "README.md"
    if not agents.is_file() or not index.is_file():
        raise ValueError(
            f"Grafana fixture requires AGENTS.md and specspine/README.md: {source}"
        )
    target.mkdir(parents=True)
    shutil.copy2(agents, target / "AGENTS.md")
    shutil.copytree(spine, target / "specspine")
    return target


def grafana_case(fixture: Path, profile: str) -> dict[str, Any]:
    return {
        "id": CASE_ID,
        "scenario": "tests/eval/extract-grafana-large.md",
        "skill": "skills/specspine-extract",
        "status": "executable",
        "category": "expensive",
        "runs": 1,
        "initial_tree": str(fixture),
        "_execution_profile": profile,
        "handoff_judgments": {
            "required": [
                "specspine/resource-dualwrite-lifecycle.md",
                "specspine/resource-api-contracts.md",
                "specspine/unified-storage-search.md",
            ],
            "supporting": [
                "specspine/persistence-resource-platform.md",
                "specspine/resource-api-evolution-intent.md",
            ],
            "relevant": [
                "specspine/persistence-resource-platform.md",
                "specspine/resource-api-contracts.md",
                "specspine/resource-api-evolution-intent.md",
                "specspine/resource-dualwrite-lifecycle.md",
                "specspine/unified-storage-search.md",
            ],
            "hard_negatives": [
                "specspine/resource-provisioning-reconciliation.md",
            ],
        },
        "assertions": [
            {"type": "max_changed_files", "max": 0},
            {"type": "read_only", "paths": ["specspine/**"]},
            {
                "type": "command_includes",
                "value": "search_spine.py",
                "profiles": ["extract", "fallback"],
            },
            {
                "type": "command_excludes",
                "value": "search_spine.py",
                "profiles": ["no-extract"],
            },
            {
                "type": "trace_equals",
                "field": "retrieval_attempt_count",
                "value": 1,
                "profiles": ["extract"],
            },
            {
                "type": "response_contains",
                "values": [
                    "specspine/resource-dualwrite-lifecycle.md",
                    "specspine/resource-api-contracts.md",
                    "specspine/unified-storage-search.md",
                ],
            },
            {
                "type": "response_not_contains",
                "value": "specspine/resource-provisioning-reconciliation.md",
            },
            {"type": "response_word_budget", "max": 700},
        ],
    }


def adapter_command(
    retrieval_profile: str, model: str, reasoning_effort: str
) -> list[str]:
    command = [
        sys.executable,
        str(EVAL_DIR / "adapters" / "codex.py"),
        "--model",
        model,
        "--reasoning-effort",
        reasoning_effort,
        "--retrieval-profile",
        retrieval_profile,
    ]
    if retrieval_profile in {"fallback", "accelerated"}:
        command.extend(("--retrieval-telemetry", "minimal"))
    return command


def run_arm(
    output_dir: Path,
    fixture: Path,
    label: str,
    execution_profile: str,
    retrieval_profile: str,
    *,
    samples: int,
    jobs: int,
    model: str,
    reasoning_effort: str,
    timestamp: str,
) -> tuple[dict[str, Any], bool]:
    case = grafana_case(fixture, execution_profile)
    command = adapter_command(retrieval_profile, model, reasoning_effort)
    queued = __import__("time").monotonic()
    reports = []
    with ThreadPoolExecutor(max_workers=min(jobs, samples)) as executor:
        futures = [
            executor.submit(
                RUNNER.run_case_captured,
                case,
                command,
                False,
                sample,
                queued,
            )
            for sample in range(1, samples + 1)
        ]
        for future in as_completed(futures):
            report = future.result()
            reports.append(report)
            print(report.output, end="", flush=True)
    report_path = output_dir / f"{label}.json"
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    RUNNER.write_json_report(
        report_path,
        label,
        shlex.join(command),
        reports,
        [case],
        samples,
        jobs,
        run_id=f"extract-grafana-{timestamp}-{label}",
        started_at=started,
        finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    return payload, all(report.passed for report in reports)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--grafana-root",
        type=Path,
        default=Path("~/projects/grafana"),
        help="Grafana checkout containing AGENTS.md and specspine/ (default: %(default)s)",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--jobs", type=int, default=3)
    parser.add_argument("--model", default="gpt-5.6-luna")
    parser.add_argument("--reasoning-effort", default="medium")
    args = parser.parse_args()
    if args.samples < 1 or args.jobs < 1:
        parser.error("--samples and --jobs must be positive")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    reports: dict[str, dict[str, Any]] = {}
    passed = True
    with tempfile.TemporaryDirectory(prefix="specspine-grafana-fixture-") as directory:
        try:
            fixture = materialize_fixture(args.grafana_root, Path(directory) / "project")
        except ValueError as error:
            parser.error(str(error))
        for label, execution_profile, retrieval_profile in ARMS:
            report, arm_passed = run_arm(
                args.output_dir,
                fixture,
                label,
                execution_profile,
                retrieval_profile,
                samples=args.samples,
                jobs=args.jobs,
                model=args.model,
                reasoning_effort=args.reasoning_effort,
                timestamp=timestamp,
            )
            reports[label] = report
            passed &= arm_passed
    comparison = args.output_dir / "comparison.md"
    AGENT_BENCHMARK.write_comparison(comparison, reports, ARMS)
    print(comparison)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
