#!/usr/bin/env python3
"""Compare direct Map with orchestrated Map Deep on one small repository."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import shlex
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = Path(__file__).resolve().parent
ARMS = (
    ("map", "map-direct-comparison-small"),
    ("map-deep", "map-deep-rolling-small"),
)
DEFAULT_ORCHESTRATOR_MODEL = "gpt-5.6-terra"
DEFAULT_ORCHESTRATOR_REASONING_EFFORT = "medium"
DEFAULT_SUBAGENT_ROLE = "weak"
SUBAGENT_ROLES = ("weak", "medium", "strong")
QUALITY_DIMENSIONS = (
    "architectural_fidelity",
    "evidence_and_epistemic_discipline",
    "responsibility_and_boundary_clarity",
    "coverage_of_material_concerns",
    "coherence_navigation_and_relationships",
    "signal_to_noise_and_usefulness",
)


def load_case(case_id: str) -> dict[str, Any]:
    return json.loads(
        (EVAL_DIR / "cases" / f"{case_id}.json").read_text(encoding="utf-8")
    )


def fixture_files(case: dict[str, Any]) -> dict[str, str]:
    initial_files = case.get("initial_files")
    if isinstance(initial_files, dict):
        return {str(path): str(content) for path, content in initial_files.items()}
    initial_tree = case.get("initial_tree")
    if not isinstance(initial_tree, str):
        raise ValueError("Map benchmark case has no fixture")
    root = ROOT / initial_tree
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def validate_equal_fixtures() -> None:
    fixtures = [fixture_files(load_case(case_id)) for _, case_id in ARMS]
    if not fixtures or any(fixture != fixtures[0] for fixture in fixtures[1:]):
        raise ValueError("Map benchmark arms must use identical fixtures")


def report_command(
    output_dir: Path,
    label: str,
    case_id: str,
    *,
    samples: int,
    model: str,
    reasoning_effort: str,
    subagent_role: str,
    timestamp: str,
) -> tuple[list[str], Path]:
    report = output_dir / f"{label}.json"
    adapter = (
        f"{sys.executable} {EVAL_DIR / 'adapters' / 'codex.py'} "
        f"--model {model} --reasoning-effort {reasoning_effort} "
        f"--subagent-role {subagent_role}"
    )
    return [
        sys.executable, str(EVAL_DIR / "run.py"),
        "--case", case_id,
        "--samples", str(samples),
        "--jobs", "1",
        "--run-id", f"map-mode-benchmark-{timestamp}-{label}",
        "--report-label", label,
        "--report-json", str(report),
        "--agent-command", adapter,
    ], report


def mean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def common_value(values: list[Any]) -> Any:
    unique = {value for value in values if value is not None}
    return next(iter(unique)) if len(unique) == 1 else ("mixed" if unique else None)


def summarize(report: dict[str, Any], *, uses_subagents: bool = True) -> dict[str, Any]:
    samples = report["samples"]
    quality_checks = {
        "glob_count",
        "glob_contains",
        "unchanged",
        "changed_only",
        "markdown_links_valid",
        "semantic_ids_valid",
        "workspace_boundary",
    }
    token_rows = [
        sample.get("token_usage", {})
        for sample in samples
        if isinstance(sample.get("token_usage"), dict)
    ]
    runs = [
        run for sample in samples for run in sample.get("agent_runs", [])
        if isinstance(run, dict)
    ]
    producer_rows = [
        producer
        for run in runs
        for telemetry in [run.get("agent_telemetry")]
        if isinstance(telemetry, dict)
        for producer in telemetry.get("producers", [])
        if isinstance(producer, dict)
    ]
    artifact_sets = [
        sample.get("artifacts", {})
        for sample in samples
        if isinstance(sample.get("artifacts"), dict)
    ]
    per_document_words = [
        len(content.split())
        for artifacts in artifact_sets
        for content in artifacts.values()
        if isinstance(content, str)
    ]
    total_document_words = [
        sum(len(content.split()) for content in artifacts.values() if isinstance(content, str))
        for artifacts in artifact_sets
    ]
    return {
        "top_level_model": common_value([run.get("model") for run in runs]),
        "top_level_reasoning_effort": common_value(
            [run.get("reasoning_effort") for run in runs]
        ),
        "subagent_model": (
            common_value([run.get("subagent_model") for run in runs])
            if uses_subagents else None
        ),
        "subagent_role": (
            common_value([run.get("subagent_role") for run in runs])
            if uses_subagents else None
        ),
        "subagent_reasoning_effort": (
            common_value([run.get("subagent_reasoning_effort") for run in runs])
            if uses_subagents else None
        ),
        "pass_rate": mean([float(bool(sample.get("passed"))) for sample in samples]),
        "mechanical_quality_pass_rate": mean([
            float(not any(
                check.get("type") in quality_checks
                for check in sample.get("failed_checks", [])
            ))
            for sample in samples
        ]),
        "mean_document_words": mean([float(value) for value in per_document_words]),
        "mean_total_document_words": mean([float(value) for value in total_document_words]),
        "mean_case_wall_time_seconds": mean([
            float(sample["case_duration_seconds"]) for sample in samples
            if isinstance(sample.get("case_duration_seconds"), (int, float))
        ]),
        "mean_agent_tree_wall_time_seconds": mean([
            float(sample["agent_duration_seconds"]) for sample in samples
            if isinstance(sample.get("agent_duration_seconds"), (int, float))
        ]),
        "mean_agent_tree_total_tokens": mean([
            float(row.get("input_tokens", 0) + row.get("output_tokens", 0))
            for row in token_rows
        ]),
        "mean_agent_tree_input_tokens": mean([
            float(row.get("input_tokens", 0)) for row in token_rows
        ]),
        "mean_agent_tree_cached_input_tokens": mean([
            float(row.get("cached_input_tokens", 0)) for row in token_rows
        ]),
        "mean_agent_tree_cache_write_input_tokens": mean([
            float(row.get("cache_write_input_tokens", 0)) for row in token_rows
        ]),
        "mean_agent_tree_uncached_input_tokens": mean([
            float(row.get("input_tokens", 0) - row.get("cached_input_tokens", 0))
            for row in token_rows
        ]),
        "mean_agent_tree_output_tokens": mean([
            float(row.get("output_tokens", 0)) for row in token_rows
        ]),
        "mean_agent_tree_reasoning_tokens": mean([
            float(row.get("reasoning_output_tokens", 0)) for row in token_rows
        ]),
        "mean_initial_files_read": mean([
            float(run["files_read"]) for run in runs
            if isinstance(run.get("files_read"), int)
        ]),
        "mean_generated_files_read": mean([
            float(run["generated_files_read"]) for run in runs
            if isinstance(run.get("generated_files_read"), int)
        ]),
        "mean_tool_cycles": mean([
            float(run["cost_ledger"]["tool_cycles"]) for run in runs
            if isinstance(run.get("cost_ledger"), dict)
            and isinstance(run["cost_ledger"].get("tool_cycles"), int)
        ]),
        "parallelism_evidence": (
            "observed"
            if any(
                run.get("agent_telemetry", {}).get("coverage", {}).get(
                    "spawn_observed_count", 0
                ) > 0
                for run in runs
                if isinstance(run.get("agent_telemetry"), dict)
            )
            else "behaviorally_confirmed"
            if uses_subagents
            and any(
                run.get("event_metrics", {}).get("wait_call_count", 0) > 0
                for run in runs
                if isinstance(run.get("event_metrics"), dict)
            )
            else "unavailable"
            if uses_subagents
            else "not_applicable"
        ),
        "mean_observed_spawned_agents": mean([
            float(run["spawned_agent_count"])
            for run in runs
            if isinstance(run.get("spawned_agent_count"), int)
            and run.get("agent_telemetry", {}).get("coverage", {}).get(
                "spawn_observed_count", 0
            ) > 0
        ]),
        "mean_observed_producer_wall_time_seconds": mean([
            float(producer["observed_duration_seconds"])
            for producer in producer_rows
            if isinstance(producer.get("observed_duration_seconds"), (int, float))
        ]),
        "producer_duration_coverage_rate": (
            sum(
                isinstance(producer.get("observed_duration_seconds"), (int, float))
                for producer in producer_rows
            )
            / len(producer_rows)
            if producer_rows
            else None
        ),
        "mean_producer_prompt_utf8_bytes": mean([
            float(producer["prompt_utf8_bytes"])
            for producer in producer_rows
            if isinstance(producer.get("prompt_utf8_bytes"), int)
        ]),
    }


def quality_prompt(
    fixture: dict[str, str],
    candidate_a: dict[str, str],
    candidate_b: dict[str, str],
) -> str:
    rubric = "\n".join(f"- {name}: integer 1-10" for name in QUALITY_DIMENSIONS)
    return f"""Act as a blind senior architecture-documentation reviewer.
Compare two SpecSpine outputs produced from the same small repository. Use the
rubric and ordinary engineering judgment. Judge architectural documentation,
not the implementation strategy that produced it.

Score:
{rubric}
- overall: integer 1-10 based on the whole result, not a mechanical average

Prefer accurate, evidence-grounded, clear, complete, coherent, useful
architecture documentation. Do not penalize length by itself: a longer document
is often better when the additional text adds architectural meaning. Penalize
only repetition, irrelevant implementation detail, unsupported claims, or text
that makes the Spine less usable. Do not reward brevity by itself. Mechanical
validity is already checked separately.

Return exactly one JSON object with this schema and no Markdown:
{{"A":{{"<dimension>":1,"overall":1}},"B":{{"<dimension>":1,"overall":1}},
"preferred":"A|B|tie","rationale":"concise evidence-based explanation"}}

Repository fixture:
{json.dumps(fixture, ensure_ascii=False, sort_keys=True)}

Candidate A:
{json.dumps(candidate_a, ensure_ascii=False, sort_keys=True)}

Candidate B:
{json.dumps(candidate_b, ensure_ascii=False, sort_keys=True)}
"""


def parse_quality_judgment(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("quality judge returned no JSON object")
    result = json.loads(text[start : end + 1])
    expected_scores = {*QUALITY_DIMENSIONS, "overall"}
    for label in ("A", "B"):
        scores = result.get(label)
        if not isinstance(scores, dict) or set(scores) != expected_scores:
            raise ValueError(f"quality judge {label} scores do not match rubric")
        if any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or not 1 <= value <= 10
            for value in scores.values()
        ):
            raise ValueError(f"quality judge {label} scores must be integers 1..10")
    if result.get("preferred") not in {"A", "B", "tie"}:
        raise ValueError("quality judge preference must be A, B, or tie")
    if not isinstance(result.get("rationale"), str) or not result["rationale"].strip():
        raise ValueError("quality judge rationale is missing")
    return result


def judge_reports(
    reports: dict[str, dict[str, Any]],
    command: str,
    fixture: dict[str, str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_arm = {
        label: {
            int(sample["sample_number"]): sample
            for sample in report["samples"]
        }
        for label, report in reports.items()
    }
    sample_numbers = sorted(set(by_arm["map"]) & set(by_arm["map-deep"]))
    judgments: list[dict[str, Any]] = []
    token_usage: dict[str, int] = {}
    started = time.monotonic()
    for sample_number in sample_numbers:
        order_material = json.dumps(
            {
                label: by_arm[label][sample_number].get("artifacts", {})
                for label in ("map", "map-deep")
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        order = (
            ("map", "map-deep")
            if hashlib.sha256(order_material.encode()).digest()[0] % 2
            else ("map-deep", "map")
        )
        with tempfile.TemporaryDirectory(prefix="specspine-map-quality-judge-") as directory:
            workspace = Path(directory)
            completed = subprocess.run(
                shlex.split(command),
                cwd=workspace,
                input=quality_prompt(
                    fixture,
                    by_arm[order[0]][sample_number].get("artifacts", {}),
                    by_arm[order[1]][sample_number].get("artifacts", {}),
                ),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if completed.returncode:
                raise RuntimeError(
                    f"quality judge failed for sample {sample_number}: "
                    f"{completed.stderr.strip()}"
                )
            raw = parse_quality_judgment(completed.stdout)
            trace_path = workspace / ".eval" / "trace.json"
            if trace_path.is_file():
                usage = json.loads(trace_path.read_text(encoding="utf-8")).get(
                    "token_usage", {}
                )
                for field, value in usage.items():
                    if isinstance(value, int) and not isinstance(value, bool):
                        token_usage[field] = token_usage.get(field, 0) + value
        scores = {
            order[0]: raw["A"],
            order[1]: raw["B"],
        }
        preferred = (
            "tie"
            if raw["preferred"] == "tie"
            else order[0 if raw["preferred"] == "A" else 1]
        )
        judgments.append(
            {
                "sample_number": sample_number,
                "blind_order": {"A": order[0], "B": order[1]},
                "scores": scores,
                "preferred": preferred,
                "rationale": raw["rationale"],
            }
        )
    return judgments, {
        "wall_time_seconds": time.monotonic() - started,
        "token_usage": token_usage,
    }


def format_value(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}" if isinstance(value, float) else str(value)


def write_comparison(
    output: Path,
    reports: dict[str, dict[str, Any]],
    judgments: list[dict[str, Any]] | None = None,
    judge_cost: dict[str, Any] | None = None,
) -> None:
    summaries = {
        label: summarize(report, uses_subagents=label == "map-deep")
        for label, report in reports.items()
    }
    judgments = judgments or []
    for label in summaries:
        for dimension in (*QUALITY_DIMENSIONS, "overall"):
            summaries[label][f"documentation_quality_{dimension}"] = mean(
                [
                    float(item["scores"][label][dimension])
                    for item in judgments
                    if label in item.get("scores", {})
                ]
            )
        summaries[label]["documentation_quality_preference_rate"] = mean(
            [
                1.0 if item.get("preferred") == label else 0.5
                if item.get("preferred") == "tie" else 0.0
                for item in judgments
            ]
        )
    lines = [
        "# Map vs Map Deep benchmark",
        "",
        "| Metric | Map | Map Deep |",
        "|---|---:|---:|",
    ]
    for field in next(iter(summaries.values())):
        lines.append(
            f"| {field} | {format_value(summaries['map'][field])} | "
            f"{format_value(summaries['map-deep'][field])} |"
        )
    lines.extend((
        "",
        "Documentation quality is a blind holistic LLM judgment over the complete "
        "generated Spine. Scores use common architecture-writing criteria and do "
        "not penalize length by itself.",
        "",
        "Token counters are cumulative for the complete agent tree: orchestrator "
        "plus every nested producer.",
        "",
        "Producer wall time is the observed interval from successful spawn to "
        "terminal lifecycle notification; coverage is reported explicitly. "
        "`codex exec --json` exposes only cumulative agent-tree tokens, so exact "
        "orchestrator-only and per-producer token counters remain unavailable "
        "and are not estimated. Raw reports retain every observed producer "
        "thread, model, assignment, prompt size/hash, status, and collaboration-call "
        "duration.",
        "",
        "Raw reports: `map.json`, `map-deep.json`.",
        "",
    ))
    if judge_cost:
        usage = judge_cost.get("token_usage", {})
        lines.extend(
            (
                "Quality-judge cost is excluded from both benchmark arms.",
                "",
                f"- wall time: {format_value(judge_cost.get('wall_time_seconds'))} seconds",
                f"- input tokens: {usage.get('input_tokens', 'n/a')}",
                f"- output tokens: {usage.get('output_tokens', 'n/a')}",
                "",
            )
        )
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--model", default=DEFAULT_ORCHESTRATOR_MODEL)
    parser.add_argument(
        "--reasoning-effort", default=DEFAULT_ORCHESTRATOR_REASONING_EFFORT
    )
    parser.add_argument(
        "--subagent-role",
        choices=SUBAGENT_ROLES,
        default=DEFAULT_SUBAGENT_ROLE,
    )
    parser.add_argument(
        "--judge-command",
        help="command that accepts the blind quality-review prompt on stdin; defaults to the Codex adapter",
    )
    parser.add_argument(
        "--skip-quality-judge",
        action="store_true",
        help="run only mechanical/cost comparison; documentation quality will be unscored",
    )
    args = parser.parse_args()
    if args.samples < 1:
        parser.error("--samples must be positive")
    validate_equal_fixtures()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    reports: dict[str, dict[str, Any]] = {}
    failed = False
    for label, case_id in ARMS:
        command, report_path = report_command(
            args.output_dir, label, case_id,
            samples=args.samples,
            model=args.model,
            reasoning_effort=args.reasoning_effort,
            subagent_role=args.subagent_role,
            timestamp=timestamp,
        )
        print("+", " ".join(command), flush=True)
        completed = subprocess.run(command, cwd=ROOT, check=False)
        if not report_path.is_file():
            return completed.returncode or 2
        reports[label] = json.loads(report_path.read_text(encoding="utf-8"))
        failed |= completed.returncode != 0
    judgments: list[dict[str, Any]] = []
    judge_cost: dict[str, Any] = {}
    if not args.skip_quality_judge:
        judge_command = args.judge_command or (
            f"{sys.executable} {EVAL_DIR / 'adapters' / 'codex.py'} "
            f"--model {args.model} --reasoning-effort {args.reasoning_effort} "
            f"--subagent-role {args.subagent_role}"
        )
        try:
            judgments, judge_cost = judge_reports(
                reports,
                judge_command,
                fixture_files(load_case(ARMS[0][1])),
            )
        except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
            print(f"Quality judge failed: {error}", file=sys.stderr)
            return 2
        (args.output_dir / "quality-judgments.json").write_text(
            json.dumps(
                {"judgments": judgments, "cost": judge_cost},
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    comparison = args.output_dir / "comparison.md"
    write_comparison(comparison, reports, judgments, judge_cost)
    print(comparison)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
