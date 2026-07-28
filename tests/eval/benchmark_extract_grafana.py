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
SCENARIOS = (
    {
        "id": "extract-grafana-resource-migration",
        "scenario": "tests/eval/extract-grafana-resource-migration.md",
        "required": [
            "specspine/persistence/resource-dualwrite-lifecycle.md",
            "specspine/persistence/resource-api-contracts.md",
            "specspine/persistence/unified-storage-search.md",
        ],
        "supporting": [
            "specspine/persistence/persistence-resource-platform.md",
            "specspine/resources/resource-api-evolution-intent.md",
        ],
        "hard_negatives": [
            "specspine/operations/resource-provisioning-reconciliation.md"
        ],
    },
    {
        "id": "extract-grafana-plugin-backend-request",
        "scenario": "tests/eval/extract-grafana-plugin-backend-request.md",
        "required": [
            "specspine/plugins/plugin-backend-protocol.md",
            "specspine/plugins/plugin-request-status-classification.md",
            "specspine/plugins/plugin-host-environment.md",
        ],
        "supporting": ["specspine/plugins/plugin-runtime.md"],
        "hard_negatives": [
            "specspine/plugins/plugin-resource-http-response-adapter.md"
        ],
    },
    {
        "id": "extract-grafana-alert-evaluation-delivery",
        "scenario": "tests/eval/extract-grafana-alert-evaluation-delivery.md",
        "required": [
            "specspine/alerting/alert-rules-evaluation-state.md",
            "specspine/alerting/alert-notification-delivery.md",
        ],
        "supporting": ["specspine/alerting/alerting.md"],
        "hard_negatives": [
            "specspine/alerting/alerting-notifications-app-api-adapter.md"
        ],
    },
    {
        "id": "extract-grafana-frontend-api-boundary",
        "scenario": "tests/eval/extract-grafana-frontend-api-boundary.md",
        "required": [
            "specspine/frontend/frontend-api-clients.md",
            "specspine/frontend/frontend-runtime-api.md",
            "specspine/frontend/frontend-state-platform.md",
        ],
        "supporting": ["specspine/frontend/frontend-platform.md"],
        "hard_negatives": [
            "specspine/querying/sql-datasource-frontend-contract.md"
        ],
    },
    {
        "id": "extract-grafana-session-authorization",
        "scenario": "tests/eval/extract-grafana-session-authorization.md",
        "required": [
            "specspine/identity-access/authentication-sessions.md",
            "specspine/identity-access/authorization-policy-engine.md",
        ],
        "supporting": ["specspine/identity-access/identity-access.md"],
        "hard_negatives": [
            "specspine/identity-access/anonymous-device-management.md"
        ],
    },
    {
        "id": "extract-grafana-resource-schema-publication",
        "scenario": "tests/eval/extract-grafana-resource-schema-publication.md",
        "required": [
            "specspine/resources/core-kind-schema-generation.md",
            "specspine/resources/kubernetes-api-code-generation.md",
            "specspine/resources/openapi-spec-publication.md",
            "specspine/persistence/resource-schema-installation.md",
        ],
        "supporting": ["specspine/resources/grafana-schema-contract.md"],
        "hard_negatives": ["specspine/plugins/plugin-cue-schema-generation.md"],
    },
    {
        "id": "extract-grafana-folder-deletion",
        "scenario": "tests/eval/extract-grafana-folder-deletion.md",
        "required": [
            "specspine/content/folder-cascade-deletion.md",
            "specspine/content/content-dashboard-lifecycle.md",
            "specspine/content/content-browse.md",
        ],
        "supporting": ["specspine/content/content-management.md"],
        "hard_negatives": [
            "specspine/content/library-panel-resource-transition.md"
        ],
    },
)


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


def grafana_case(
    fixture: Path, profile: str, scenario: dict[str, Any] = SCENARIOS[0]
) -> dict[str, Any]:
    required = list(scenario["required"])
    supporting = list(scenario["supporting"])
    hard_negatives = list(scenario["hard_negatives"])
    return {
        "id": scenario["id"],
        "scenario": scenario["scenario"],
        "skill": "skills/specspine-extract",
        "status": "executable",
        "category": "expensive",
        "runs": 1,
        "initial_tree": str(fixture),
        "_execution_profile": profile,
        "handoff_judgments": {
            "required": required,
            "supporting": supporting,
            "relevant": required + supporting,
            "hard_negatives": hard_negatives,
        },
        "assertions": [
            {"type": "max_changed_files", "max": 0},
            {
                "type": "read_only",
                "paths": ["specspine/**"],
                "profiles": ["extract", "fallback", "no-extract"],
            },
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
            {"type": "response_contains", "values": required},
            {
                "type": "response_not_contains",
                "values": hard_negatives,
            },
            {"type": "response_word_budget", "max": 700},
        ],
    }


def adapter_command(
    retrieval_profile: str,
    model: str,
    reasoning_effort: str,
    *,
    instrument_retrieval: bool = True,
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
    if instrument_retrieval:
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
    scenarios: tuple[dict[str, Any], ...] = SCENARIOS,
) -> tuple[dict[str, Any], bool]:
    cases = [
        grafana_case(fixture, execution_profile, scenario) for scenario in scenarios
    ]
    command = adapter_command(
        retrieval_profile,
        model,
        reasoning_effort,
        instrument_retrieval=execution_profile in {"extract", "fallback"},
    )
    queued = __import__("time").monotonic()
    reports = []
    with ThreadPoolExecutor(max_workers=min(jobs, samples * len(cases))) as executor:
        futures = [
            executor.submit(
                RUNNER.run_case_captured,
                case,
                command,
                False,
                sample,
                queued,
            )
            for case in cases
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
        cases,
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
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--jobs", type=int, default=6)
    parser.add_argument("--model", default="gpt-5.6-luna")
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument(
        "--scenario",
        action="append",
        choices=[scenario["id"] for scenario in SCENARIOS],
        help="run only this scenario; repeat to select multiple scenarios",
    )
    parser.add_argument(
        "--arm",
        action="append",
        choices=[label for label, *_ in ARMS],
        help="run only this arm; repeat to select multiple arms",
    )
    args = parser.parse_args()
    if args.samples < 1 or args.jobs < 1:
        parser.error("--samples and --jobs must be positive")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    reports: dict[str, dict[str, Any]] = {}
    passed = True
    selected_scenarios = tuple(
        scenario
        for scenario in SCENARIOS
        if args.scenario is None or scenario["id"] in args.scenario
    )
    selected_arms = tuple(
        arm for arm in ARMS if args.arm is None or arm[0] in args.arm
    )
    with tempfile.TemporaryDirectory(prefix="specspine-grafana-fixture-") as directory:
        fixture_root = Path(directory)
        try:
            documentation_fixture = materialize_fixture(
                args.grafana_root,
                fixture_root / "documentation-project",
            )
        except ValueError as error:
            parser.error(str(error))
        for label, execution_profile, retrieval_profile in selected_arms:
            report, arm_passed = run_arm(
                args.output_dir,
                documentation_fixture,
                label,
                execution_profile,
                retrieval_profile,
                samples=args.samples,
                jobs=args.jobs,
                model=args.model,
                reasoning_effort=args.reasoning_effort,
                timestamp=timestamp,
                scenarios=selected_scenarios,
            )
            reports[label] = report
            passed &= arm_passed
    comparison = args.output_dir / "comparison.md"
    AGENT_BENCHMARK.write_comparison(comparison, reports, selected_arms)
    print(comparison)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
