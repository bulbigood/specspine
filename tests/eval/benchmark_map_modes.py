#!/usr/bin/env python3
"""Compare direct Map with orchestrated Map Large on one small repository."""

from __future__ import annotations

import argparse
import datetime
import json
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = Path(__file__).resolve().parent
ARMS = (
    ("map", "map-direct-comparison-small"),
    ("map-large", "map-large-rolling-small"),
)


def load_case(case_id: str) -> dict[str, Any]:
    return json.loads(
        (EVAL_DIR / "cases" / f"{case_id}.json").read_text(encoding="utf-8")
    )


def validate_equal_fixtures() -> None:
    fixtures = [load_case(case_id).get("initial_files") for _, case_id in ARMS]
    if not fixtures or any(fixture != fixtures[0] for fixture in fixtures[1:]):
        raise ValueError("Map benchmark arms must use identical initial_files")


def report_command(
    output_dir: Path,
    label: str,
    case_id: str,
    *,
    samples: int,
    model: str,
    reasoning_effort: str,
    timestamp: str,
) -> tuple[list[str], Path]:
    report = output_dir / f"{label}.json"
    adapter = (
        f"{sys.executable} {EVAL_DIR / 'adapters' / 'codex.py'} "
        f"--model {model} --reasoning-effort {reasoning_effort}"
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


def summarize(report: dict[str, Any]) -> dict[str, Any]:
    samples = report["samples"]
    quality_checks = {
        "glob_count",
        "glob_contains",
        "unchanged",
        "changed_only",
        "word_budget",
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
    return {
        "pass_rate": mean([float(bool(sample.get("passed"))) for sample in samples]),
        "quality_pass_rate": mean([
            float(not any(
                check.get("type") in quality_checks
                for check in sample.get("failed_checks", [])
            ))
            for sample in samples
        ]),
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
        "mean_files_read": mean([
            float(run["files_read"]) for run in runs
            if isinstance(run.get("files_read"), int)
        ]),
        "mean_tool_cycles": mean([
            float(run["cost_ledger"]["tool_cycles"]) for run in runs
            if isinstance(run.get("cost_ledger"), dict)
            and isinstance(run["cost_ledger"].get("tool_cycles"), int)
        ]),
        "mean_spawned_agents": mean([
            float(run["spawned_agent_count"]) for run in runs
            if isinstance(run.get("spawned_agent_count"), int)
        ]),
    }


def format_value(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}" if isinstance(value, float) else str(value)


def write_comparison(output: Path, reports: dict[str, dict[str, Any]]) -> None:
    summaries = {label: summarize(report) for label, report in reports.items()}
    lines = [
        "# Map vs Map Large benchmark",
        "",
        "| Metric | Map | Map Large |",
        "|---|---:|---:|",
    ]
    for field in next(iter(summaries.values())):
        lines.append(
            f"| {field} | {format_value(summaries['map'][field])} | "
            f"{format_value(summaries['map-large'][field])} |"
        )
    lines.extend((
        "",
        "Token counters are cumulative for the complete agent tree: orchestrator "
        "plus every nested producer.",
        "",
        "`codex exec --json` currently exposes neither per-thread token usage nor "
        "per-thread execution duration. Exact orchestrator-only and per-producer "
        "breakdowns are therefore unavailable and are not estimated.",
        "",
        "Raw reports: `map.json`, `map-large.json`.",
        "",
    ))
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--model", default="gpt-5.6-luna")
    parser.add_argument("--reasoning-effort", default="medium")
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
            timestamp=timestamp,
        )
        print("+", " ".join(command), flush=True)
        completed = subprocess.run(command, cwd=ROOT, check=False)
        if not report_path.is_file():
            return completed.returncode or 2
        reports[label] = json.loads(report_path.read_text(encoding="utf-8"))
        failed |= completed.returncode != 0
    comparison = args.output_dir / "comparison.md"
    write_comparison(comparison, reports)
    print(comparison)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
