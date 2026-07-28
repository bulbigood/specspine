#!/usr/bin/env python3
"""Compare Extract agent workflows on a large external Grafana SpecSpine."""

from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
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
    ("source-search", "source-search", "accelerated"),
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
        "source_required_groups": [
            ["pkg/storage/legacysql/dualwrite/storage_service.go"],
            [
                "pkg/storage/unified/migrations/status_reader.go",
                "pkg/storage/unified/migrations/contract/migrations.go",
            ],
            ["pkg/services/apiserver/builder/helper.go"],
        ],
        "source_supporting": [
            "pkg/setting/setting_unified_storage.go",
            "pkg/storage/legacysql/dualwrite/dualwriter.go",
        ],
        "source_hard_negatives": [
            "pkg/registry/apis/provisioning/resources/dualwriter.go"
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
        "source_required_groups": [
            [
                "pkg/plugins/backendplugin/grpcplugin/client.go",
                "pkg/plugins/backendplugin/grpcplugin/client_v2.go",
            ],
            [
                "pkg/plugins/manager/pipeline/initialization/steps.go",
                "pkg/plugins/backendplugin/grpcplugin/grpc_plugin.go",
            ],
            ["pkg/plugins/instrumentationutils/request_status.go"],
        ],
        "source_supporting": [
            "pkg/plugins/manager/process/process.go",
            "pkg/services/pluginsintegration/clientmiddleware/metrics_middleware.go",
        ],
        "source_hard_negatives": [
            "pkg/plugins/httpresponsesender/http_response_sender.go"
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
        "source_required_groups": [
            [
                "pkg/services/ngalert/state/state.go",
                "pkg/services/ngalert/state/manager.go",
            ],
            [
                "pkg/services/ngalert/sender/router.go",
                "pkg/services/ngalert/notifier/alertmanager.go",
            ],
        ],
        "source_supporting": [
            "pkg/services/ngalert/eval/eval.go",
            "pkg/services/ngalert/notifier/multiorg_alertmanager.go",
        ],
        "source_hard_negatives": [
            "pkg/registry/apps/alerting/notifications/register.go"
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
        "source_required_groups": [
            [
                "packages/grafana-api-clients/src/clients/rtkq/createBaseQuery.ts",
                "packages/grafana-api-clients/src/utils/utils.ts",
            ],
            [
                "packages/grafana-runtime/src/services/backendSrv.ts",
                "public/app/app.ts",
            ],
            [
                "public/app/store/configureStore.ts",
                "public/app/core/services/backend_srv.ts",
            ],
        ],
        "source_supporting": [
            "public/app/core/reducers/root.ts",
            "packages/grafana-api-clients/src/clients/rtkq/index.ts",
        ],
        "source_hard_negatives": ["packages/grafana-sql/src/index.ts"],
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
        "source_required_groups": [
            [
                "pkg/services/authn/clients/session.go",
                "pkg/services/auth/authimpl/auth_token.go",
            ],
            [
                "pkg/services/apiserver/auth/authorizer/resource.go",
                "pkg/services/authz/rbac/service.go",
            ],
        ],
        "source_supporting": [
            "pkg/services/authn/authnimpl/service.go",
            "pkg/services/accesscontrol/authorizer.go",
        ],
        "source_hard_negatives": ["pkg/services/anonymous/anonimpl/impl.go"],
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
        "source_required_groups": [
            ["kinds/gen.go"],
            ["hack/update-codegen.sh"],
            [
                "pkg/services/apiserver/appinstaller/installer.go",
                "pkg/services/apiserver/builder/scheme.go",
            ],
            [
                "packages/grafana-openapi/src/scripts/process-specs.ts",
                "packages/grafana-openapi/package.json",
            ],
        ],
        "source_supporting": [
            "hack/openapi-codegen.sh",
            "pkg/services/apiserver/builder/openapi.go",
        ],
        "source_hard_negatives": ["pkg/plugins/codegen/jenny_plugingotypes.go"],
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
        "source_required_groups": [
            [
                "pkg/registry/apis/folders/cascade_delete.go",
                "pkg/registry/apis/folders/cascade_delete_storage.go",
            ],
            [
                "pkg/services/folder/cleaner/contents_cleaner.go",
                "pkg/services/dashboards/service/dashboard_service.go",
            ],
            [
                "public/app/features/browse-dashboards/api/browseDashboardsAPI.ts",
                "public/app/features/browse-dashboards/components/DashboardsTree.tsx",
            ],
        ],
        "source_supporting": [
            "pkg/services/folder/cleaner/provider.go",
            "public/app/features/browse-dashboards/BrowseDashboardsPage.tsx",
        ],
        "source_hard_negatives": [
            "pkg/registry/apis/dashboard/libary_panel.go"
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


def materialize_source_fixture(grafana_root: Path, target: Path) -> Path:
    source = grafana_root.expanduser().resolve()
    agents = source / "AGENTS.md"
    if not agents.is_file():
        raise ValueError(f"Grafana source fixture requires AGENTS.md: {source}")
    try:
        listed = subprocess.run(
            ["git", "-C", str(source), "ls-files", "-z"],
            check=True,
            capture_output=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as error:
        raise ValueError(
            f"Grafana source fixture requires a readable Git worktree: {source}"
        ) from error
    paths = [
        Path(os.fsdecode(value))
        for value in listed.split(b"\0")
        if value and not os.fsdecode(value).startswith("specspine/")
    ]
    target.mkdir(parents=True)
    for relative in paths:
        source_path = source / relative
        if not source_path.is_file():
            continue
        target_path = target / relative
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
    target_agents = target / "AGENTS.md"
    content = target_agents.read_text(encoding="utf-8")
    content = re.sub(
        r"\n?<!-- specspine:begin -->.*?<!-- specspine:end -->\n?",
        "\n",
        content,
        flags=re.DOTALL,
    )
    target_agents.write_text(content, encoding="utf-8")
    return target


def grafana_case(
    fixture: Path, profile: str, scenario: dict[str, Any] = SCENARIOS[0]
) -> dict[str, Any]:
    source_search = profile == "source-search"
    required_groups = (
        [list(group) for group in scenario["source_required_groups"]]
        if source_search
        else []
    )
    required = [] if source_search else list(scenario["required"])
    supporting = list(
        scenario["source_supporting"] if source_search else scenario["supporting"]
    )
    hard_negatives = list(
        scenario["source_hard_negatives"]
        if source_search
        else scenario["hard_negatives"]
    )
    relevant = required + supporting + [
        path for group in required_groups for path in group
    ]
    required_assertions = (
        [
            {"type": "response_contains_any", "values": group}
            for group in required_groups
        ]
        if source_search
        else [{"type": "response_contains", "values": required}]
    )
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
            "required_groups": required_groups,
            "supporting": supporting,
            "relevant": relevant,
            "hard_negatives": hard_negatives,
            "open_world_relevance": source_search,
        },
        "assertions": [
            {"type": "max_changed_files", "max": 0},
            {
                "type": "read_only",
                "paths": ["specspine/**"],
                "profiles": ["extract", "fallback", "no-extract"],
            },
            {
                "type": "read_only",
                "paths": ["**"],
                "profiles": ["source-search"],
            },
            {
                "type": "command_includes",
                "value": "search_spine.py",
                "profiles": ["extract", "fallback"],
            },
            {
                "type": "command_excludes",
                "value": "search_spine.py",
                "profiles": ["no-extract", "source-search"],
            },
            {
                "type": "trace_equals",
                "field": "retrieval_attempt_count",
                "value": 1,
                "profiles": ["extract"],
            },
            *required_assertions,
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
    parser.add_argument("--jobs", type=int, default=3)
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
            source_fixture = (
                materialize_source_fixture(
                    args.grafana_root,
                    fixture_root / "source-project",
                )
                if any(arm[1] == "source-search" for arm in selected_arms)
                else None
            )
        except ValueError as error:
            parser.error(str(error))
        for label, execution_profile, retrieval_profile in selected_arms:
            fixture = (
                source_fixture
                if execution_profile == "source-search"
                else documentation_fixture
            )
            assert fixture is not None
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
