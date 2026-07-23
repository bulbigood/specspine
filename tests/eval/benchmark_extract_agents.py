#!/usr/bin/env python3
"""Compare direct navigation, Extract fallback, and accelerated Extract."""

from __future__ import annotations

import argparse
import datetime
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = Path(__file__).resolve().parent
CASES = (
    "extract-backend-multislice",
    "extract-cli-multislice",
    "extract-mobile-multislice-ru",
    "extract-pipeline-multislice-zh-cn",
)
ARMS = (
    ("no-extract", "no-extract", "accelerated"),
    ("fallback", "fallback", "fallback"),
    ("accelerated", "extract", "accelerated"),
)


def report_command(
    output_dir: Path,
    label: str,
    execution_profile: str,
    retrieval_profile: str,
    *,
    samples: int,
    jobs: int,
    model: str,
    reasoning_effort: str,
    timestamp: str,
) -> tuple[list[str], Path]:
    report = output_dir / f"{label}.json"
    adapter = (
        f"{sys.executable} {EVAL_DIR / 'adapters' / 'codex.py'} "
        f"--model {model} --reasoning-effort {reasoning_effort} "
        f"--retrieval-profile {retrieval_profile}"
    )
    if execution_profile != "no-extract":
        adapter += " --retrieval-telemetry minimal"
    command = [
        sys.executable,
        str(EVAL_DIR / "run.py"),
        "--samples", str(samples),
        "--jobs", str(jobs),
        "--execution-profile", execution_profile,
        "--run-id", f"extract-agent-benchmark-{timestamp}-{label}",
        "--report-label", label,
        "--report-json", str(report),
        "--agent-command", adapter,
    ]
    for case in CASES:
        command.extend(("--case", case))
    return command, report


def numeric_values(report: dict[str, Any], path: tuple[str, ...]) -> list[float]:
    values: list[float] = []
    for sample in report["samples"]:
        current: Any = sample
        for field in path:
            if not isinstance(current, dict):
                current = None
                break
            current = current.get(field)
        if isinstance(current, (int, float)) and not isinstance(current, bool):
            values.append(float(current))
    return values


def run_values(report: dict[str, Any], section: str, field: str) -> list[float]:
    values: list[float] = []
    for sample in report["samples"]:
        for run in sample.get("agent_runs", []):
            source = run.get(section, {})
            value = source.get(field) if isinstance(source, dict) else None
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                values.append(float(value))
    return values


def mean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def summarize(report: dict[str, Any]) -> dict[str, Any]:
    samples = report["samples"]
    non_quality_checks = {
        "command_excludes",
        "command_includes",
        "response_sections_only",
        "trace_equals",
    }
    required_recalls: list[float] = []
    supporting_recalls: list[float] = []
    handoff_precisions: list[float] = []
    retrieval_attempts: list[float] = []
    unexpected_retries: list[float] = []
    cases = report.get("cases", {})
    for sample in samples:
        judgments = cases.get(sample.get("case_id"), {}).get("handoff_judgments", {})
        response = sample.get("diagnostics", {}).get("response", "")
        mentioned = set(re.findall(r"specspine/[A-Za-z0-9._/-]+\.md", response))
        required = set(judgments.get("required", []))
        supporting = set(judgments.get("supporting", []))
        relevant = set(judgments.get("relevant", [])) | required | supporting
        if required:
            required_recalls.append(len(required & mentioned) / len(required))
        if supporting:
            supporting_recalls.append(len(supporting & mentioned) / len(supporting))
        handoff_precisions.append(
            len(relevant & mentioned) / len(mentioned) if mentioned else 0.0
        )
        for run in sample.get("agent_runs", []):
            count = run.get("retrieval_attempt_count")
            if isinstance(count, int) and not isinstance(count, bool):
                retrieval_attempts.append(float(count))
            unexpected_retries.append(float(bool(run.get("unexpected_retry", False))))
    return {
        "samples": len(samples),
        "pass_rate": sum(bool(sample.get("passed")) for sample in samples) / len(samples),
        "quality_pass_rate": sum(
            not any(
                check.get("type") not in non_quality_checks
                for check in sample.get("failed_checks", [])
            )
            for sample in samples
        ) / len(samples),
        "mean_required_recall": mean(required_recalls),
        "mean_supporting_recall": mean(supporting_recalls),
        "mean_handoff_precision": mean(handoff_precisions),
        "mean_duration_seconds": mean(numeric_values(report, ("agent_duration_seconds",))),
        "mean_total_tokens": mean([
            float(usage.get("input_tokens", 0) + usage.get("output_tokens", 0))
            for sample in samples
            for usage in [sample.get("token_usage", {})]
            if isinstance(usage, dict)
            and (
                isinstance(usage.get("input_tokens"), int)
                or isinstance(usage.get("output_tokens"), int)
            )
        ]),
        "mean_uncached_input_tokens": mean([
            float(usage["input_tokens"] - usage.get("cached_input_tokens", 0))
            for sample in samples
            for usage in [sample.get("token_usage", {})]
            if isinstance(usage, dict) and isinstance(usage.get("input_tokens"), int)
        ]),
        "mean_output_tokens": mean(
            numeric_values(report, ("token_usage", "output_tokens"))
        ),
        "mean_files_read": mean([
            float(run["files_read"])
            for sample in samples
            for run in sample.get("agent_runs", [])
            if isinstance(run.get("files_read"), int)
        ]),
        "mean_tool_cycles": mean(run_values(report, "cost_ledger", "tool_cycles")),
        "mean_retrieval_attempts": mean(retrieval_attempts),
        "unexpected_retry_rate": mean(unexpected_retries),
        "mean_retrieval_bytes": mean(
            run_values(report, "cost_ledger", "retrieval_output_utf8_bytes")
        ),
        "mean_project_source_bytes": mean(
            run_values(report, "cost_ledger", "project_source_file_bytes")
        ),
    }


def format_value(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def write_comparison(output: Path, reports: dict[str, dict[str, Any]]) -> None:
    case_sets = [set(report.get("cases", {})) for report in reports.values()]
    if not case_sets or any(case_set != case_sets[0] for case_set in case_sets[1:]):
        raise ValueError("benchmark arms contain different cases")
    summaries = {label: summarize(report) for label, report in reports.items()}
    fields = (
        "pass_rate",
        "quality_pass_rate",
        "mean_required_recall",
        "mean_supporting_recall",
        "mean_handoff_precision",
        "mean_duration_seconds",
        "mean_total_tokens",
        "mean_uncached_input_tokens",
        "mean_output_tokens",
        "mean_files_read",
        "mean_tool_cycles",
        "mean_retrieval_attempts",
        "unexpected_retry_rate",
        "mean_retrieval_bytes",
        "mean_project_source_bytes",
    )
    lines = [
        "# Extract agent benchmark",
        "",
        "| Metric | No Extract | Extract fallback | Accelerated Extract |",
        "|---|---:|---:|---:|",
    ]
    for field in fields:
        lines.append(
            "| "
            + field
            + " | "
            + " | ".join(format_value(summaries[label][field]) for label, *_ in ARMS)
            + " |"
        )
    lines.extend(("", "Raw reports: `no-extract.json`, `fallback.json`, `accelerated.json`.", ""))
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--model", default="gpt-5.6-luna")
    parser.add_argument("--reasoning-effort", default="medium")
    args = parser.parse_args()
    if args.samples < 1 or args.jobs < 1:
        parser.error("--samples and --jobs must be positive")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    reports: dict[str, dict[str, Any]] = {}
    failed = False
    for label, execution_profile, retrieval_profile in ARMS:
        command, report_path = report_command(
            args.output_dir,
            label,
            execution_profile,
            retrieval_profile,
            samples=args.samples,
            jobs=args.jobs,
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
