#!/usr/bin/env python3
"""A/B-test Grow with and without Extract on an external Grafana SpecSpine."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import json
import shlex
import shutil
import sys
import tempfile
import time
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


RUNNER = load_module("specspine_eval_run_grow_ab", EVAL_DIR / "run.py")
ADAPTER_BENCHMARK = load_module(
    "specspine_extract_agent_benchmark_grow_ab",
    EVAL_DIR / "benchmark_extract_agents.py",
)
GRAFANA_BENCHMARK = load_module(
    "specspine_extract_grafana_benchmark_grow_ab",
    EVAL_DIR / "benchmark_extract_grafana.py",
)

ARMS = (
    ("without-extract", False),
    ("with-extract", True),
)

SCENARIOS = (
    {
        "id": "extract-grow-grafana-plugin-capability",
        "scenario": "tests/eval/extract-grow-grafana-plugin-capability.md",
        "target": "specspine/plugins/plugin-backend-protocol.md",
        "required_terms": [
            "ErrMethodNotImplemented",
            "Unimplemented",
            "перезапуск",
        ],
        "forbidden_terms": [
            "plugin-resource-http-response-adapter.md",
            "срок реализации",
        ],
    },
    {
        "id": "extract-grow-grafana-session-recovery",
        "scenario": "tests/eval/extract-grow-grafana-session-recovery.md",
        "target": "specspine/identity-access/authentication-sessions.md",
        "required_terms": [
            "best-effort",
            "cleanup",
            "sql-persistence-migrations.md",
        ],
        "required_any": [
            ["идемпотент", "idempotent"],
        ],
        "forbidden_terms": [
            "anonymous-device-management.md",
            "срок реализации",
        ],
    },
    {
        "id": "extract-grow-grafana-folder-cascade",
        "scenario": "tests/eval/extract-grow-grafana-folder-cascade.md",
        "target": "specspine/content/folder-cascade-deletion.md",
        "required_terms": [
            "depth-first",
            "NotFound",
            "folder-terminating",
        ],
        "forbidden_terms": [
            "library-panel-resource-transition.md",
            "background job",
        ],
    },
)

RUBRIC_FIELDS = (
    "accepted_decisions",
    "source_grounding",
    "scope_discipline",
    "specspine_quality",
    "preservation_and_coherence",
)


def grow_case(
    fixture: Path, with_extract: bool, scenario: dict[str, Any]
) -> dict[str, Any]:
    assertions: list[dict[str, Any]] = [
        {"type": "path_exists", "path": scenario["target"]},
        {"type": "changed_only", "paths": [scenario["target"]]},
        {"type": "max_changed_files", "max": 1},
        {
            "type": "file_contains",
            "path": scenario["target"],
            "values": scenario["required_terms"],
        },
        {
            "type": "file_not_contains",
            "path": scenario["target"],
            "values": scenario["forbidden_terms"],
        },
        {
            "type": "spine_mechanical_valid",
            "glob": "specspine/**/*.md",
        },
        {
            "type": "command_includes" if with_extract else "command_excludes",
            "value": "search_spine.py",
        },
    ]
    if with_extract:
        assertions.append(
            {
                "type": "trace_equals",
                "field": "retrieval_attempt_count",
                "value": 1,
            }
        )
    for alternatives in scenario.get("required_any", []):
        assertions.append(
            {
                "type": "file_contains_any",
                "path": scenario["target"],
                "values": alternatives,
            }
        )
    return {
        "id": scenario["id"],
        "scenario": scenario["scenario"],
        "skill": "skills/specspine-grow",
        "companion_skills": (
            ["skills/specspine-extract"] if with_extract else []
        ),
        "status": "executable",
        "category": "expensive",
        "runs": 1,
        "subagents": "disabled",
        "initial_tree": str(fixture),
        "_execution_profile": "extract",
        "report_artifacts": [scenario["target"]],
        "assertions": assertions,
    }


def adapter_command(
    model: str, reasoning_effort: str, *, with_extract: bool
) -> list[str]:
    command = [
        sys.executable,
        str(EVAL_DIR / "adapters" / "codex.py"),
        "--model",
        model,
        "--reasoning-effort",
        reasoning_effort,
        "--retrieval-profile",
        "accelerated",
    ]
    if with_extract:
        command.extend(("--retrieval-telemetry", "minimal"))
    return command


def run_arm(
    output_dir: Path,
    fixture: Path,
    label: str,
    with_extract: bool,
    *,
    samples: int,
    jobs: int,
    model: str,
    reasoning_effort: str,
    timestamp: str,
    scenarios: tuple[dict[str, Any], ...],
) -> tuple[dict[str, Any], bool]:
    cases = [grow_case(fixture, with_extract, scenario) for scenario in scenarios]
    command = adapter_command(model, reasoning_effort, with_extract=with_extract)
    started_at = datetime.datetime.now(datetime.timezone.utc)
    queued = time.monotonic()
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
    RUNNER.write_json_report(
        report_path,
        label,
        shlex.join(command),
        reports,
        cases,
        samples,
        jobs,
        run_id=f"extract-grow-grafana-{timestamp}-{label}",
        started_at=started_at.isoformat(),
        finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    return payload, all(report.passed for report in reports)


def candidate_id(pair_id: str, label: str, timestamp: str) -> str:
    digest = hashlib.sha256(f"{timestamp}:{pair_id}:{label}".encode()).hexdigest()
    return f"candidate-{digest[:12]}"


def write_blind_package(
    output_dir: Path,
    reports: dict[str, dict[str, Any]],
    grafana_root: Path,
    scenarios: tuple[dict[str, Any], ...],
    timestamp: str,
) -> None:
    review_dir = output_dir / "blind-review"
    review_dir.mkdir(exist_ok=True)
    context_root = review_dir / "specspine"
    if context_root.exists():
        shutil.rmtree(context_root)
    shutil.copytree(grafana_root.expanduser().resolve() / "specspine", context_root)
    payload_cases: list[dict[str, Any]] = []
    key: dict[str, str] = {}
    scenario_by_id = {scenario["id"]: scenario for scenario in scenarios}
    samples_by_arm = {
        label: {
            (sample["case_id"], sample["sample_number"]): sample
            for sample in report["samples"]
        }
        for label, report in reports.items()
    }
    pairs = sorted(set.intersection(*(
        set(samples) for samples in samples_by_arm.values()
    )))
    for case_id, sample_number in pairs:
        scenario = scenario_by_id[case_id]
        pair_id = f"{case_id}-sample-{sample_number}"
        initial = (
            grafana_root.expanduser().resolve() / scenario["target"]
        ).read_text(encoding="utf-8")
        candidates: dict[str, str] = {}
        for label, _ in ARMS:
            opaque = candidate_id(pair_id, label, timestamp)
            artifact = samples_by_arm[label][(case_id, sample_number)][
                "artifacts"
            ].get(scenario["target"], "")
            candidates[opaque] = artifact
            key[opaque] = label
        payload_cases.append(
            {
                "pair_id": pair_id,
                "architecture_context_root": "specspine",
                "target_path": scenario["target"],
                "user_request": RUNNER.scenario_user_request(
                    {"scenario": scenario["scenario"]}
                ),
                "initial_document": initial,
                "candidates": candidates,
            }
        )
    (review_dir / "cases.json").write_text(
        json.dumps({"cases": payload_cases}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "blind-review-key.json").write_text(
        json.dumps({"candidate_arms": key}, indent=2) + "\n",
        encoding="utf-8",
    )
    (review_dir / "judge-prompt.md").write_text(
        """# Blind judge protocol

Оцени каждый pair независимо. Не пытайся определить, каким инструментом создан
candidate. Используй user request, initial document, два candidates из
`cases.json` и полный исходный SpecSpine snapshot в `specspine/`. Судья должен
работать в новой сессии на `gpt-5.6-terra` с reasoning effort `medium`.

До выставления оценки найди в полном SpecSpine все ограничения, решения,
canonical owners, relationships, semantic IDs, known divergences и open
questions, которые могут быть затронуты изменением. Candidate не должен
противоречить ни одному релевантному документу, дублировать чужую ownership,
терять uncertainty или выдавать intent за подтверждённую реализацию.

Для каждого candidate поставь целые оценки 0–4:

- `accepted_decisions`: полнота и точность всех явно принятых решений;
- `source_grounding`: согласованность с initial document, корректные владельцы
  и ссылки, отсутствие утверждений о реализации без evidence;
- `scope_discipline`: отсутствие запрещённых областей, новых решений,
  implementation plan, тестов, rollout и сроков;
- `specspine_quality`: ясные responsibility/boundary/behavior/failure semantics,
  intended claims и сохранённая каноническая ownership;
- `preservation_and_coherence`: сохранение ID, Observed claims и несвязного
  содержания без дублирования и противоречий.

`0` означает отсутствие/критическую ошибку, `2` — частичное приемлемое
выполнение, `4` — полное точное выполнение. Выбери preferred candidate либо
`tie`. Верни только JSON:

```json
{
  "judgments": [
    {
      "pair_id": "...",
      "scores": {
        "candidate-...": {
          "accepted_decisions": 0,
          "source_grounding": 0,
          "scope_discipline": 0,
          "specspine_quality": 0,
          "preservation_and_coherence": 0
        }
      },
      "preferred_candidate": "candidate-... | tie",
      "rationale": "Краткое сравнение без догадок об инструментах"
    }
  ]
}
```
""",
        encoding="utf-8",
    )


def score_judgments(output_dir: Path, judgments_path: Path) -> dict[str, Any]:
    cases = json.loads(
        (output_dir / "blind-review" / "cases.json").read_text(encoding="utf-8")
    )["cases"]
    key = json.loads(
        (output_dir / "blind-review-key.json").read_text(encoding="utf-8")
    )["candidate_arms"]
    judgments = json.loads(judgments_path.read_text(encoding="utf-8"))["judgments"]
    expected = {
        case["pair_id"]: set(case["candidates"])
        for case in cases
    }
    totals: dict[str, list[float]] = {label: [] for label, _ in ARMS}
    wins: dict[str, int] = {label: 0 for label, _ in ARMS}
    seen: set[str] = set()
    for judgment in judgments:
        pair_id = judgment["pair_id"]
        if pair_id in seen or pair_id not in expected:
            raise ValueError(f"unexpected or duplicate pair_id: {pair_id}")
        seen.add(pair_id)
        scores = judgment["scores"]
        if set(scores) != expected[pair_id]:
            raise ValueError(f"candidate set mismatch for {pair_id}")
        for candidate, fields in scores.items():
            if set(fields) != set(RUBRIC_FIELDS):
                raise ValueError(f"rubric fields mismatch for {candidate}")
            values = list(fields.values())
            if any(type(value) is not int or not 0 <= value <= 4 for value in values):
                raise ValueError(f"invalid score for {candidate}")
            totals[key[candidate]].append(float(sum(values)))
        preferred = judgment["preferred_candidate"]
        if preferred != "tie":
            if preferred not in expected[pair_id]:
                raise ValueError(f"invalid preferred_candidate for {pair_id}")
            wins[key[preferred]] += 1
    if seen != set(expected):
        raise ValueError("judgments do not cover every blind pair")
    result = {
        label: {
            "mean_blind_quality_0_20": sum(values) / len(values),
            "blind_wins": wins[label],
        }
        for label, values in totals.items()
    }
    (output_dir / "blind-scores.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result


def navigation_file_count(sample: dict[str, Any]) -> int:
    """Count direct Spine reads, excluding the whole-Spine checker and diff."""
    paths: set[str] = set()
    for run in sample.get("agent_runs", []):
        metrics = run.get("event_metrics", {}).get("command_metrics", [])
        for metric in metrics if isinstance(metrics, list) else []:
            if not isinstance(metric, dict):
                continue
            command = str(metric.get("command_excerpt") or "")
            if "check_spine.py" in command or "git diff" in command:
                continue
            paths.update(
                str(path)
                for path in metric.get("inferred_file_paths", [])
                if str(path).startswith("specspine/")
            )
    return len(paths)


def write_comparison(
    output: Path,
    reports: dict[str, dict[str, Any]],
    blind_scores: dict[str, Any] | None = None,
) -> None:
    summaries = {
        label: ADAPTER_BENCHMARK.summarize(report)
        for label, report in reports.items()
    }
    for label, report in reports.items():
        samples = report["samples"]
        started = datetime.datetime.fromisoformat(report["run"]["started_at"])
        finished = datetime.datetime.fromisoformat(report["run"]["finished_at"])
        navigation_reads = [navigation_file_count(sample) for sample in samples]
        summaries[label].update(
            total_wall_seconds=(finished - started).total_seconds(),
            total_agent_seconds=sum(
                float(sample.get("agent_duration_seconds") or 0)
                for sample in samples
            ),
            total_tokens=sum(
                int(usage.get("input_tokens") or 0)
                + int(usage.get("output_tokens") or 0)
                for sample in samples
                for usage in [sample.get("token_usage", {})]
                if isinstance(usage, dict)
            ),
            total_tool_cycles=sum(
                int(ledger.get("tool_cycles") or 0)
                for sample in samples
                for run in sample.get("agent_runs", [])
                for ledger in [run.get("cost_ledger", {})]
                if isinstance(ledger, dict)
            ),
            total_agent_calls=sum(
                len(sample.get("agent_runs", [])) for sample in samples
            ),
            mean_navigation_files_read=(
                sum(navigation_reads) / len(navigation_reads)
                if navigation_reads
                else None
            ),
        )
    fields = (
        "pass_rate",
        "quality_pass_rate",
        "total_wall_seconds",
        "total_agent_seconds",
        "total_tokens",
        "total_tool_cycles",
        "total_agent_calls",
        "mean_duration_seconds",
        "mean_total_tokens",
        "mean_uncached_input_tokens",
        "mean_output_tokens",
        "mean_navigation_files_read",
        "mean_files_read",
        "mean_tool_cycles",
        "mean_retrieval_attempts",
    )
    labels = [label for label, _ in ARMS]
    lines = [
        "# Extract → Grow Grafana A/B benchmark",
        "",
        "| Metric | Without Extract | With Extract |",
        "|---|---:|---:|",
    ]
    for field in fields:
        lines.append(
            f"| {field} | "
            + " | ".join(
                ADAPTER_BENCHMARK.format_value(summaries[label][field])
                for label in labels
            )
            + " |"
        )
    if blind_scores is not None:
        for field in ("mean_blind_quality_0_20", "blind_wins"):
            lines.append(
                f"| {field} | "
                + " | ".join(
                    ADAPTER_BENCHMARK.format_value(blind_scores[label][field])
                    for label in labels
                )
                + " |"
            )
    lines.extend(
        (
            "",
            "Blind review input: `blind-review/`. Keep "
            "`blind-review-key.json` hidden from the judge.",
            "",
            "Raw reports: `without-extract.json`, `with-extract.json`.",
            "",
        )
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--grafana-root",
        type=Path,
        default=Path("~/projects/grafana"),
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--model", default="gpt-5.6-luna")
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument(
        "--scenario",
        action="append",
        choices=[scenario["id"] for scenario in SCENARIOS],
    )
    parser.add_argument(
        "--judgments",
        type=Path,
        help="score an existing run with blind judge JSON; no agents are run",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    comparison = args.output_dir / "comparison.md"
    if args.judgments:
        reports = {
            label: json.loads(
                (args.output_dir / f"{label}.json").read_text(encoding="utf-8")
            )
            for label, _ in ARMS
        }
        scores = score_judgments(args.output_dir, args.judgments)
        write_comparison(comparison, reports, scores)
        print(comparison)
        return 0
    if args.samples < 1 or args.jobs < 1:
        parser.error("--samples and --jobs must be positive")
    selected = tuple(
        scenario
        for scenario in SCENARIOS
        if args.scenario is None or scenario["id"] in args.scenario
    )
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )
    reports: dict[str, dict[str, Any]] = {}
    passed = True
    with tempfile.TemporaryDirectory(
        prefix="specspine-grow-grafana-fixture-"
    ) as directory:
        try:
            fixture = GRAFANA_BENCHMARK.materialize_fixture(
                args.grafana_root,
                Path(directory) / "documentation-project",
            )
        except ValueError as error:
            parser.error(str(error))
        for label, with_extract in ARMS:
            report, arm_passed = run_arm(
                args.output_dir,
                fixture,
                label,
                with_extract,
                samples=args.samples,
                jobs=args.jobs,
                model=args.model,
                reasoning_effort=args.reasoning_effort,
                timestamp=timestamp,
                scenarios=selected,
            )
            reports[label] = report
            passed &= arm_passed
        write_blind_package(
            args.output_dir,
            reports,
            args.grafana_root,
            selected,
            timestamp,
        )
    write_comparison(comparison, reports)
    print(comparison)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
