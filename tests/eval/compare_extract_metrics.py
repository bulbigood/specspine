#!/usr/bin/env python3
"""Compare saved extract eval metrics without running an agent."""

from __future__ import annotations

import argparse
import json
import shlex
import statistics
import sys
from pathlib import Path
from typing import Any


TOKEN_METRICS = (
    "total_tokens",
    "input_tokens",
    "cached_input_tokens",
    "uncached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
)


class ComparisonError(ValueError):
    pass


def load_report(path: Path) -> dict[str, Any]:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ComparisonError(f"cannot read report {path}: {error}") from error
    if not isinstance(report, dict) or report.get("schema_version") != 1:
        raise ComparisonError(f"unsupported report: {path}")
    if not isinstance(report.get("samples"), list) or not report["samples"]:
        raise ComparisonError(f"report has no samples: {path}")
    return report


def normalized_command(value: Any) -> list[str]:
    if not isinstance(value, str):
        return []
    parts = shlex.split(value)
    normalized: list[str] = []
    skip = False
    for part in parts:
        if skip:
            skip = False
            continue
        if part == "--accelerator-mode":
            skip = True
            continue
        if part.startswith("--accelerator-mode="):
            continue
        normalized.append(part)
    return normalized


def sample_key(sample: dict[str, Any]) -> tuple[str, int]:
    return str(sample.get("case_id", "")), int(sample.get("sample_number", 0))


def trace_values(sample: dict[str, Any], field: str) -> set[str]:
    runs = sample.get("agent_runs")
    if not isinstance(runs, list):
        return set()
    return {
        str(run[field])
        for run in runs
        if isinstance(run, dict) and isinstance(run.get(field), str)
    }


def validate_comparable(
    fallback: dict[str, Any], accelerated: dict[str, Any]
) -> tuple[dict[tuple[str, int], dict[str, Any]], dict[tuple[str, int], dict[str, Any]]]:
    if fallback.get("cases") != accelerated.get("cases"):
        raise ComparisonError("case fingerprints differ")
    if fallback.get("samples_requested") != accelerated.get("samples_requested"):
        raise ComparisonError("requested sample counts differ")
    if fallback.get("jobs") != accelerated.get("jobs"):
        raise ComparisonError("parallelism differs")
    if normalized_command(fallback.get("agent_command")) != normalized_command(
        accelerated.get("agent_command")
    ):
        raise ComparisonError("agent commands differ beyond accelerator mode")

    left = {sample_key(sample): sample for sample in fallback["samples"]}
    right = {sample_key(sample): sample for sample in accelerated["samples"]}
    if len(left) != len(fallback["samples"]) or len(right) != len(accelerated["samples"]):
        raise ComparisonError("duplicate sample identities")
    if set(left) != set(right):
        raise ComparisonError("sample identities differ")
    for key in sorted(left):
        left_valid = bool(left[key].get("environment_valid"))
        right_valid = bool(right[key].get("environment_valid"))
        if left_valid and trace_values(left[key], "accelerator_mode") != {"fallback"}:
            raise ComparisonError(f"fallback mode is not recorded for {key}")
        if right_valid and trace_values(right[key], "accelerator_mode") != {"enabled"}:
            raise ComparisonError(f"enabled mode is not recorded for {key}")
        if left_valid and right_valid:
            for field in ("model", "reasoning_effort"):
                if trace_values(left[key], field) != trace_values(right[key], field):
                    raise ComparisonError(f"{field} differs for {key}")
    return left, right


def metric_value(sample: dict[str, Any], metric: str) -> float | None:
    if not sample.get("environment_valid"):
        return None
    if metric == "agent_duration_seconds":
        value = sample.get(metric)
    elif metric == "files_read":
        runs = sample.get("agent_runs")
        values = [run.get("files_read") for run in runs] if isinstance(runs, list) else []
        numeric = [value for value in values if isinstance(value, int)]
        return float(sum(numeric)) if numeric else None
    else:
        usage = sample.get("token_usage")
        if not isinstance(usage, dict):
            return None
        if metric == "uncached_input_tokens":
            input_tokens = usage.get("input_tokens")
            cached_tokens = usage.get("cached_input_tokens")
            if not isinstance(input_tokens, int) or not isinstance(cached_tokens, int):
                return None
            value = input_tokens - cached_tokens
        else:
            value = usage.get(metric)
            if metric == "total_tokens" and not isinstance(value, int):
                input_tokens = usage.get("input_tokens")
                output_tokens = usage.get("output_tokens")
                if isinstance(input_tokens, int) and isinstance(output_tokens, int):
                    value = input_tokens + output_tokens
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def paired_metric(
    left: dict[tuple[str, int], dict[str, Any]],
    right: dict[tuple[str, int], dict[str, Any]],
    metric: str,
) -> tuple[list[float], list[float]]:
    fallback_values: list[float] = []
    accelerated_values: list[float] = []
    for key in sorted(left):
        fallback_value = metric_value(left[key], metric)
        accelerated_value = metric_value(right[key], metric)
        if fallback_value is None or accelerated_value is None:
            continue
        fallback_values.append(fallback_value)
        accelerated_values.append(accelerated_value)
    return fallback_values, accelerated_values


def percentage(delta: float, baseline: float) -> str:
    return "n/a" if baseline == 0 else f"{100.0 * delta / baseline:+.1f}%"


def render_comparison(fallback: dict[str, Any], accelerated: dict[str, Any]) -> str:
    left, right = validate_comparable(fallback, accelerated)
    lines = [
        "metric | forced fallback | accelerated | delta | delta % | pairs",
        "--- | ---: | ---: | ---: | ---: | ---:",
    ]
    metrics = (
        ("agent time mean (s)", "agent_duration_seconds", "mean"),
        ("agent time median (s)", "agent_duration_seconds", "median"),
        *((metric.replace("_", " "), metric, "mean") for metric in TOKEN_METRICS),
        ("files read", "files_read", "mean"),
    )
    for label, metric, aggregation in metrics:
        fallback_values, accelerated_values = paired_metric(left, right, metric)
        if not fallback_values:
            lines.append(f"{label} | n/a | n/a | n/a | n/a | 0")
            continue
        reducer = statistics.median if aggregation == "median" else statistics.fmean
        baseline = float(reducer(fallback_values))
        treatment = float(reducer(accelerated_values))
        delta = treatment - baseline
        lines.append(
            f"{label} | {baseline:.3f} | {treatment:.3f} | {delta:+.3f} | "
            f"{percentage(delta, baseline)} | {len(fallback_values)}"
        )

    lines.append("")
    for label, samples in (("forced fallback", left), ("accelerated", right)):
        valid = [sample for sample in samples.values() if sample.get("environment_valid")]
        passed = sum(bool(sample.get("passed")) for sample in valid)
        failed = len(valid) - passed
        invalid = len(samples) - len(valid)
        lines.append(
            f"{label}: samples={len(samples)}, valid={len(valid)}, passed={passed}, "
            f"failed={failed}, environment-invalid={invalid}"
        )
    lines.append("Failed behavioral samples are included in metric averages.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fallback", type=Path, required=True)
    parser.add_argument("--accelerated", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(render_comparison(load_report(args.fallback), load_report(args.accelerated)))
    except ComparisonError as error:
        print(f"cannot compare reports: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
