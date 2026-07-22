#!/usr/bin/env python3
"""Compare saved extract eval metrics without running an agent."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import html
import json
import random
import shlex
import statistics
import sys
from pathlib import Path
from typing import Any, Callable, Iterable


DEFAULT_OUTPUT_DIRECTORY = Path(__file__).with_name("reports")
TOKEN_METRICS = (
    "total_tokens",
    "input_tokens",
    "cached_input_tokens",
    "uncached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
)
METRICS = (
    "agent_duration_seconds",
    "total_tokens",
    "uncached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "files_read",
    "agent_message_count",
    "command_count",
    "command_output_chars",
)
COST_METRICS = (
    "project_agent_instruction_utf8_bytes",
    "retrieval_output_utf8_bytes",
    "project_source_file_bytes",
    "command_output_utf8_bytes",
    "tool_cycles",
)


class ComparisonError(ValueError):
    pass


def report_directories(paths: Iterable[Path]) -> tuple[Path, ...]:
    return tuple(dict.fromkeys(path.resolve().parent for path in paths))


def markdown_text(value: object) -> str:
    return html.escape(str(value)).replace("|", "&#124;").replace("\n", " ")


def markdown_path(path: Path) -> str:
    return f"<code>{markdown_text(path)}</code>"


def without_sections(lines: list[str], titles: set[str]) -> list[str]:
    result: list[str] = []
    skipping = False
    for line in lines:
        if line in titles:
            skipping = True
            continue
        if skipping and line.startswith("## "):
            skipping = False
        if not skipping:
            result.append(line)
    return result


def load_report(path: Path) -> dict[str, Any]:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ComparisonError(f"cannot read report {path}: {error}") from error
    if not isinstance(report, dict) or report.get("schema_version") != 2:
        raise ComparisonError(f"unsupported report schema (expected 2): {path}")
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
        if part in {"--accelerator-mode", "--cache-profile"}:
            skip = True
        elif not part.startswith(("--accelerator-mode=", "--cache-profile=")):
            normalized.append(part)
    return normalized


def sample_key(sample: dict[str, Any]) -> tuple[str, int]:
    return str(sample.get("case_id", "")), int(sample.get("sample_number", 0))


def agent_runs(sample: dict[str, Any]) -> list[dict[str, Any]]:
    runs = sample.get("agent_runs")
    return [run for run in runs if isinstance(run, dict)] if isinstance(runs, list) else []


def trace_values(sample: dict[str, Any], field: str) -> set[str]:
    return {
        str(run[field]) for run in agent_runs(sample)
        if isinstance(run.get(field), str)
    }


def retrieval_queries(samples: dict[tuple[str, int], dict[str, Any]]) -> list[str]:
    return sorted({
        str(attempt["query"])
        for sample in samples.values()
        if sample.get("environment_valid")
        for attempt in attempts(sample)
        if isinstance(attempt.get("query"), str) and attempt["query"].strip()
    })


def runtime_values(sample: dict[str, Any], field: str) -> set[str]:
    return {
        str(runtime[field])
        for run in agent_runs(sample)
        for runtime in [run.get("runtime")]
        if isinstance(runtime, dict) and runtime.get(field) is not None
    }


def all_trace_values(samples: Iterable[dict[str, Any]], field: str) -> str:
    values = sorted(set().union(*(trace_values(sample, field) for sample in samples)))
    return ", ".join(values) or "unavailable"


def all_runtime_values(samples: Iterable[dict[str, Any]], field: str) -> str:
    values = sorted(set().union(*(runtime_values(sample, field) for sample in samples)))
    return ", ".join(values) or "unavailable"


def report_fingerprint(report: dict[str, Any], key: str) -> Any:
    fingerprints = report.get("fingerprints")
    return fingerprints.get(key) if isinstance(fingerprints, dict) else None


def validate_comparable(
    fallback: dict[str, Any],
    accelerated: dict[str, Any],
    *,
    compare_cache_profile: bool = True,
    left_mode: str = "fallback",
    right_mode: str = "enabled",
) -> tuple[dict[tuple[str, int], dict[str, Any]], dict[tuple[str, int], dict[str, Any]]]:
    if fallback.get("cases") != accelerated.get("cases"):
        raise ComparisonError("case/skill fingerprints differ")
    if fallback.get("samples_requested") != accelerated.get("samples_requested"):
        raise ComparisonError("requested sample counts differ")
    if fallback.get("jobs") != accelerated.get("jobs"):
        raise ComparisonError("configured parallelism differs")
    if normalized_command(fallback.get("agent_command")) != normalized_command(
        accelerated.get("agent_command")
    ):
        raise ComparisonError("agent commands differ beyond accelerator mode")
    if report_fingerprint(fallback, "agent_command_files") != report_fingerprint(
        accelerated, "agent_command_files"
    ):
        raise ComparisonError("agent adapter fingerprints differ")

    left = {sample_key(sample): sample for sample in fallback["samples"]}
    right = {sample_key(sample): sample for sample in accelerated["samples"]}
    if len(left) != len(fallback["samples"]) or len(right) != len(accelerated["samples"]):
        raise ComparisonError("duplicate sample identities")
    if set(left) != set(right):
        raise ComparisonError("matched sample identities differ")
    for key in sorted(left):
        if left[key].get("environment_valid") and trace_values(left[key], "accelerator_mode") != {left_mode}:
            raise ComparisonError(f"{left_mode} mode is not recorded for {key}")
        if right[key].get("environment_valid") and trace_values(right[key], "accelerator_mode") != {right_mode}:
            raise ComparisonError(f"{right_mode} mode is not recorded for {key}")
        if left[key].get("environment_valid") and right[key].get("environment_valid"):
            fields = ["model", "reasoning_effort"]
            if compare_cache_profile:
                fields.append("cache_profile")
            for field in fields:
                if trace_values(left[key], field) != trace_values(right[key], field):
                    raise ComparisonError(f"{field} differs for {key}")
            if runtime_values(left[key], "codex_cli") != runtime_values(right[key], "codex_cli"):
                raise ComparisonError(f"Codex CLI version differs for {key}")
    return left, right


def validate_no_extract_comparable(
    baseline: dict[str, Any],
    compared: dict[str, Any],
    *,
    compared_mode: str,
) -> tuple[dict[tuple[str, int], dict[str, Any]], dict[tuple[str, int], dict[str, Any]]]:
    if baseline.get("cases") != compared.get("cases"):
        raise ComparisonError("case/skill fingerprints differ")
    if baseline.get("samples_requested") != compared.get("samples_requested"):
        raise ComparisonError("requested sample counts differ")
    if baseline.get("jobs") != compared.get("jobs"):
        raise ComparisonError("configured parallelism differs")
    if normalized_command(baseline.get("agent_command")) != normalized_command(
        compared.get("agent_command")
    ):
        raise ComparisonError("agent commands differ beyond accelerator mode")
    if report_fingerprint(baseline, "agent_command_files") != report_fingerprint(
        compared, "agent_command_files"
    ):
        raise ComparisonError("agent adapter fingerprints differ")
    if report_fingerprint(baseline, "runner") != report_fingerprint(compared, "runner"):
        raise ComparisonError("runner fingerprints differ")
    if baseline.get("runtime") != compared.get("runtime"):
        raise ComparisonError("runner runtime/platform metadata differs")
    baseline_run = baseline.get("run")
    compared_run = compared.get("run")
    if not isinstance(baseline_run, dict) or baseline_run.get("execution_profile") != [
        "no-extract"
    ]:
        raise ComparisonError("no-extract report profile metadata is missing")
    if not isinstance(compared_run, dict) or compared_run.get("execution_profile") != [
        "extract"
    ]:
        raise ComparisonError("extract report profile metadata is missing")
    left = {sample_key(sample): sample for sample in baseline["samples"]}
    right = {sample_key(sample): sample for sample in compared["samples"]}
    if len(left) != len(baseline["samples"]) or len(right) != len(compared["samples"]):
        raise ComparisonError("duplicate sample identities")
    if set(left) != set(right):
        raise ComparisonError("matched sample identities differ")
    for key in sorted(left):
        if left[key].get("environment_valid"):
            if trace_values(left[key], "evaluation_profile") != {"no-extract"}:
                raise ComparisonError(f"no-extract profile is not recorded for {key}")
            if attempts(left[key]):
                raise ComparisonError(f"no-extract profile attempted retrieval for {key}")
        if right[key].get("environment_valid"):
            if trace_values(right[key], "evaluation_profile") != {"extract"}:
                raise ComparisonError(f"extract profile is not recorded for {key}")
            if trace_values(right[key], "accelerator_mode") != {compared_mode}:
                raise ComparisonError(f"{compared_mode} mode is not recorded for {key}")
        if left[key].get("environment_valid") and right[key].get("environment_valid"):
            for field in ("model", "reasoning_effort", "cache_profile"):
                if trace_values(left[key], field) != trace_values(right[key], field):
                    raise ComparisonError(f"{field} differs for {key}")
            if runtime_values(left[key], "codex_cli") != runtime_values(right[key], "codex_cli"):
                raise ComparisonError(f"Codex CLI version differs for {key}")
    return left, right


def compatibility_warnings(fallback: dict[str, Any], accelerated: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if report_fingerprint(fallback, "runner") != report_fingerprint(accelerated, "runner"):
        warnings.append("runner fingerprints differ")
    if fallback.get("runtime") != accelerated.get("runtime"):
        warnings.append("runner runtime/platform metadata differs")
    return warnings


def metric_value(sample: dict[str, Any], metric: str) -> float | None:
    if metric in COST_METRICS:
        values = [
            ledger.get(metric)
            for run in agent_runs(sample)
            for ledger in [run.get("cost_ledger")]
            if isinstance(ledger, dict)
        ]
        numeric = [
            value for value in values
            if isinstance(value, int) and not isinstance(value, bool)
        ]
        return float(sum(numeric)) if numeric else None
    if metric == "agent_duration_seconds":
        value = sample.get(metric)
    elif metric == "files_read":
        values = [run.get("files_read") for run in agent_runs(sample)]
        numeric = [value for value in values if isinstance(value, int) and not isinstance(value, bool)]
        return float(sum(numeric)) if numeric else None
    elif metric in {"agent_message_count", "command_count", "command_output_chars"}:
        values = [
            metrics.get(metric)
            for run in agent_runs(sample)
            for metrics in [run.get("event_metrics")]
            if isinstance(metrics, dict)
        ]
        numeric = [value for value in values if isinstance(value, int) and not isinstance(value, bool)]
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
                inputs, outputs = usage.get("input_tokens"), usage.get("output_tokens")
                value = inputs + outputs if isinstance(inputs, int) and isinstance(outputs, int) else None
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def attempts(sample: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        attempt for run in agent_runs(sample)
        for attempt in run.get("retrieval_attempts", [])
        if isinstance(attempt, dict)
    ]


def expected_path(sample: dict[str, Any], expected_mode: str) -> bool:
    return bool(attempts(sample)) and attempts(sample)[-1].get("mode") == expected_mode


def single_expected_attempt(sample: dict[str, Any], expected_mode: str) -> bool:
    found = attempts(sample)
    expected_exit = 2 if expected_mode == "fallback" else 0
    return (
        len(found) == 1
        and found[0].get("mode") == expected_mode
        and found[0].get("failure_kind") is None
        and found[0].get("exit_code") == expected_exit
        and (expected_mode == "fallback" or not found[0].get("reason_code"))
    )


def cohort(
    samples: dict[tuple[str, int], dict[str, Any]], predicate: Callable[[dict[str, Any]], bool]
) -> list[dict[str, Any]]:
    return [sample for _, sample in sorted(samples.items()) if predicate(sample)]


def metric_values(samples: Iterable[dict[str, Any]], metric: str) -> list[float]:
    values = [metric_value(sample, metric) for sample in samples]
    return [value for value in values if value is not None]


def format_number(value: float | None, metric: str, *, signed: bool = False) -> str:
    if value is None:
        return "n/a"
    if metric == "agent_duration_seconds":
        return f"{value:+.3f}" if signed else f"{value:.3f}"
    return f"{value:+,.1f}" if signed else f"{value:,.1f}"


def metric_label(metric: str) -> str:
    return {
        "files_read": "Inferred distinct files read",
        "agent_message_count": "Agent message events",
        "command_count": "Command executions",
        "command_output_chars": "Command output characters",
        "prompt_utf8_bytes": "Prompt bytes",
        "declared_skill_context_utf8_bytes": "Declared skill context bytes",
        "project_agent_instruction_utf8_bytes": "Project AGENTS.md bytes",
        "retrieval_output_utf8_bytes": "Retrieval output bytes",
        "project_source_file_bytes": "Inferred project source bytes",
        "command_output_utf8_bytes": "Command output bytes",
        "final_response_utf8_bytes": "Final response bytes",
        "tool_cycles": "Tool cycles",
    }.get(metric, metric.replace("_", " ").capitalize())


def relative_effect(
    left: list[float], right: list[float], center: Callable[[list[float]], float]
) -> float | None:
    if not left or not right:
        return None
    baseline = center(left)
    return None if baseline == 0 else (center(right) - baseline) / baseline


def percentile(sorted_values: list[float], probability: float) -> float:
    position = (len(sorted_values) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    fraction = position - lower
    return sorted_values[lower] * (1 - fraction) + sorted_values[upper] * fraction


def bootstrap_median_effect(
    left: list[float],
    right: list[float],
    metric: str,
    iterations: int = 20_000,
) -> tuple[float, float] | None:
    if not left or not right or statistics.median(left) == 0:
        return None
    seed = int.from_bytes(hashlib.sha256(metric.encode("utf-8")).digest()[:8])
    generator = random.Random(seed)
    effects = []
    for _ in range(iterations):
        sampled_left = [generator.choice(left) for _ in left]
        sampled_right = [generator.choice(right) for _ in right]
        effect = relative_effect(sampled_left, sampled_right, statistics.median)
        if effect is not None:
            effects.append(effect)
    effects.sort()
    return (
        percentile(effects, 0.025),
        percentile(effects, 0.975),
    )


def render_metric_table(
    lines: list[str],
    fallback_samples: list[dict[str, Any]],
    accelerated_samples: list[dict[str, Any]],
    left_label: str = "F",
    right_label: str = "A",
    metrics: tuple[str, ...] = METRICS,
    show_uncertainty: bool = True,
) -> None:
    uncertainty_header = " | 95% bootstrap Δ median" if show_uncertainty else ""
    lines.extend([
        f"| Metric | {left_label} median | {right_label} median | Δ median | {left_label} mean | {right_label} mean | Δ mean{uncertainty_header} | n {left_label}/{right_label} |",
        "|---|---:|---:|---:|---:|---:|---:|"
        + ("---:|" if show_uncertainty else "")
        + "---:|",
    ])
    for metric in metrics:
        left, right = metric_values(fallback_samples, metric), metric_values(accelerated_samples, metric)
        left_median = statistics.median(left) if left else None
        right_median = statistics.median(right) if right else None
        left_mean = statistics.fmean(left) if left else None
        right_mean = statistics.fmean(right) if right else None
        median_effect = relative_effect(left, right, statistics.median)
        mean_effect = relative_effect(left, right, statistics.fmean)
        interval = bootstrap_median_effect(left, right, metric) if show_uncertainty else None
        label = metric_label(metric)
        uncertainty_cell = (
            ""
            if not show_uncertainty
            else f"{('—' if interval is None else f'{interval[0]:+.1%}–{interval[1]:+.1%}')} | "
        )
        lines.append(
            f"| {label} | {format_number(left_median, metric)} | {format_number(right_median, metric)} | "
            f"{('n/a' if median_effect is None else f'{median_effect:+.1%}')} | "
            f"{format_number(left_mean, metric)} | {format_number(right_mean, metric)} | "
            f"{('n/a' if mean_effect is None else f'{mean_effect:+.1%}')} | "
            f"{uncertainty_cell}"
            f"{len(left)}/{len(right)} |"
        )


def parse_time(value: Any) -> datetime.datetime | None:
    try:
        return datetime.datetime.fromisoformat(value) if isinstance(value, str) else None
    except ValueError:
        return None


def observed_concurrency(samples: Iterable[dict[str, Any]]) -> int | None:
    events: list[tuple[datetime.datetime, int]] = []
    for sample in samples:
        intervals = [
            (parse_time(run.get("started_at")), parse_time(run.get("finished_at")))
            for run in agent_runs(sample)
        ] or [(parse_time(sample.get("started_at")), parse_time(sample.get("finished_at")))]
        for started, finished in intervals:
            if started is not None and finished is not None:
                events.extend(((started, 1), (finished, -1)))
    if not events:
        return None
    active = maximum = 0
    for _, delta in sorted(events, key=lambda item: (item[0], item[1])):
        active += delta
        maximum = max(maximum, active)
    return maximum


def failure_summary(sample: dict[str, Any]) -> str:
    checks = sample.get("failed_checks")
    kinds = [str(check.get("type")) for check in checks if isinstance(check, dict) and check.get("type")] if isinstance(checks, list) else []
    kinds.extend(
        str(attempt.get("failure_kind") or attempt.get("reason_code"))
        for attempt in attempts(sample)
        if attempt.get("failure_kind") or attempt.get("reason_code")
    )
    if any(run.get("unexpected_retry") for run in agent_runs(sample)):
        kinds.append("unexpected_retry")
    return ", ".join(dict.fromkeys(kinds)) or "—"


def cache_profile_text(run: dict[str, Any]) -> str:
    value = run.get("cache_profile")
    if isinstance(value, list):
        return ", ".join(map(str, value)) or "unavailable"
    return str(value) if value else "unavailable"


def aggregate_usefulness(sample: dict[str, Any]) -> dict[str, object]:
    ledgers = [
        run.get("retrieval_usefulness")
        for run in agent_runs(sample)
        if isinstance(run.get("retrieval_usefulness"), dict)
    ]
    fields = (
        "returned_direct",
        "returned_graph",
        "read_returned_direct",
        "read_returned_graph",
        "read_outside_results",
        "unread_returned_direct",
        "unread_returned_graph",
    )
    result: dict[str, object] = {
        field: sum(
            int(ledger[field])
            for ledger in ledgers
            if isinstance(ledger.get(field), int) and not isinstance(ledger.get(field), bool)
        )
        for field in fields
    }
    result["read_outside_result_paths"] = sorted({
        str(path)
        for ledger in ledgers
        for path in ledger.get("read_outside_result_paths", [])
    })
    return result if ledgers else {}


def render_comparison(
    fallback: dict[str, Any],
    accelerated: dict[str, Any],
    source_directories: tuple[Path, ...] = (),
    *,
    compare_cache_profile: bool = True,
) -> str:
    left, right = validate_comparable(
        fallback,
        accelerated,
        compare_cache_profile=compare_cache_profile,
    )
    all_samples = [*left.values(), *right.values()]
    run_left, run_right = fallback.get("run", {}), accelerated.get("run", {})
    lines = [
        "# Extract retrieval performance", "",
        "Independent stochastic samples use matched case identities; sample numbers are not statistical pairs.", "",
        "## Configuration", "", "| Setting | Forced fallback | SQLite FTS5 + graph |", "|---|---|---|",
        f"| Run ID | {markdown_text(run_left.get('run_id', 'unavailable'))} | {markdown_text(run_right.get('run_id', 'unavailable'))} |",
        f"| Cache profile | {markdown_text(cache_profile_text(run_left))} | {markdown_text(cache_profile_text(run_right))} |",
        f"| Cache scope | {all_trace_values(left.values(), 'cache_scope')} | {all_trace_values(right.values(), 'cache_scope')} |",
        f"| Evaluation profile | {all_trace_values(left.values(), 'evaluation_profile')} | {all_trace_values(right.values(), 'evaluation_profile')} |",
        f"| Retrieval telemetry | {all_trace_values(left.values(), 'retrieval_telemetry')} | {all_trace_values(right.values(), 'retrieval_telemetry')} |",
        f"| Configured jobs | {fallback.get('jobs')} | {accelerated.get('jobs')} |",
        f"| Samples | {len(left)} | {len(right)} |",
        f"| Model | {all_trace_values(left.values(), 'model')} | {all_trace_values(right.values(), 'model')} |",
        f"| Reasoning effort | {all_trace_values(left.values(), 'reasoning_effort')} | {all_trace_values(right.values(), 'reasoning_effort')} |",
        f"| Codex CLI | {all_runtime_values(left.values(), 'codex_cli')} | {all_runtime_values(right.values(), 'codex_cli')} |",
        f"| Observed combined concurrency | {observed_concurrency(all_samples) or 'unavailable'} | {observed_concurrency(all_samples) or 'unavailable'} |",
    ]
    for number, directory in enumerate(source_directories, 1):
        lines.append(f"| Source report directory {number} | {markdown_path(directory)} | {markdown_path(directory)} |")
    warnings = compatibility_warnings(fallback, accelerated)
    if warnings:
        lines.extend(["", "> Compatibility warning: " + "; ".join(warnings) + "."])

    cohorts = (
        ("All valid samples", lambda sample, mode: bool(sample.get("environment_valid"))),
        (
            "Clean retrieval path",
            lambda sample, mode: (
                bool(sample.get("environment_valid"))
                and bool(sample.get("passed"))
                and single_expected_attempt(sample, mode)
            ),
        ),
    )
    for title, predicate in cohorts:
        left_samples = cohort(left, lambda sample, p=predicate: p(sample, "fallback"))
        right_samples = cohort(right, lambda sample, p=predicate: p(sample, "sqlite-fts5"))
        lines.extend(["", f"## {title}", "", f"Fallback n={len(left_samples)}; accelerated n={len(right_samples)}.", ""])
        render_metric_table(lines, left_samples, right_samples)

    valid_left = cohort(left, lambda sample: bool(sample.get("environment_valid")))
    valid_right = cohort(right, lambda sample: bool(sample.get("environment_valid")))
    lines.extend([
        "",
        "## Deterministic cost ledger",
        "",
        "Byte and cycle proxies are measured independently from stochastic model token counters.",
        "",
    ])
    render_metric_table(
        lines, valid_left, valid_right, metrics=COST_METRICS, show_uncertainty=False
    )

    lines.extend(["", "## Sample outcomes", "", "| Mode | Sample | Passed | Retrieval | Files | Agent messages | Agent time | Total tokens | Outcome |", "|---|---:|---:|---|---:|---:|---:|---:|---|"])
    for label, samples in (("fallback", left), ("accelerated", right)):
        for key, sample in sorted(samples.items()):
            found = attempts(sample)
            last = found[-1] if found else {}
            lines.append(
                f"| {label} | {key[1]} | {bool(sample.get('passed'))} | "
                f"{markdown_text(last.get('mode', 'unavailable'))} | "
                f"{format_number(metric_value(sample, 'files_read'), 'files_read')} | {format_number(metric_value(sample, 'agent_message_count'), 'agent_message_count')} | "
                f"{format_number(metric_value(sample, 'agent_duration_seconds'), 'agent_duration_seconds')} | "
                f"{format_number(metric_value(sample, 'total_tokens'), 'total_tokens')} | {markdown_text(failure_summary(sample))} |"
            )

    lines.extend([
        "",
        "## Retrieval summary",
        "",
        "| Mode | Expected single attempt | Direct median | Graph median | Retrieval bytes median | Behavior failures |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for label, samples, expected_mode in (
        ("fallback", left, "fallback"),
        ("accelerated", right, "sqlite-fts5"),
    ):
        sample_values = list(samples.values())
        direct_counts = [
            float(attempt.get("direct_count"))
            for sample in sample_values
            for attempt in attempts(sample)
            if isinstance(attempt.get("direct_count"), int)
        ]
        graph_counts = [
            float(attempt.get("graph_count"))
            for sample in sample_values
            for attempt in attempts(sample)
            if isinstance(attempt.get("graph_count"), int)
        ]
        retrieval_bytes = metric_values(sample_values, "retrieval_output_utf8_bytes")
        lines.append(
            f"| {label} | {sum(single_expected_attempt(sample, expected_mode) for sample in sample_values)}/{len(sample_values)} | "
            f"{format_number(statistics.median(direct_counts) if direct_counts else None, 'files_read')} | "
            f"{format_number(statistics.median(graph_counts) if graph_counts else None, 'files_read')} | "
            f"{format_number(statistics.median(retrieval_bytes) if retrieval_bytes else None, 'retrieval_output_utf8_bytes')} | "
            f"{sum(not bool(sample.get('passed')) for sample in sample_values)} |"
        )

    lines.extend([
        "",
        "## Retrieval usefulness",
        "",
        "Median counts; README.md is excluded from routed reads.",
        "",
        "| Mode | Returned direct | Returned graph | Read direct | Read graph | Read outside |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for label, samples in (("fallback", left), ("accelerated", right)):
        ledgers = [aggregate_usefulness(sample) for sample in samples.values()]
        fields = (
            "returned_direct",
            "returned_graph",
            "read_returned_direct",
            "read_returned_graph",
            "read_outside_results",
        )
        values = [
            statistics.median([
                float(ledger[field]) for ledger in ledgers
                if isinstance(ledger.get(field), int)
            ])
            for field in fields
        ]
        lines.append(
            f"| {label} | " + " | ".join(format_number(value, "files_read") for value in values) + " |"
        )

    lines.extend(["", "## Retrieval attempts", "", "| Mode | Sample | Attempt | Query | Result | Strategy | Exit | Failure/reason | Index | Documents | Refreshed | Direct/graph | Total/Search (s) | Candidates |", "|---|---:|---:|---|---|---|---:|---|---|---:|---:|---:|---:|---|"])
    for label, samples in (("fallback", left), ("accelerated", right)):
        for key, sample in sorted(samples.items()):
            for attempt in attempts(sample):
                timings = attempt.get("timings") if isinstance(attempt.get("timings"), dict) else {}
                direct = attempt.get("direct_matches")
                graph = attempt.get("graph_neighbors")
                if isinstance(direct, list) or isinstance(graph, list):
                    rendered_candidates = [
                        f"D:{candidate.get('path')} ({candidate.get('score', 'n/a')}; {','.join(map(str, candidate.get('origins', [])))}; signals={json.dumps(candidate.get('signals', {}), ensure_ascii=False, sort_keys=True)})"
                        for candidate in direct or []
                        if isinstance(candidate, dict)
                    ]
                    rendered_candidates.extend(
                        f"G:{candidate.get('path')} ({candidate.get('score', 'n/a')}; transitions={json.dumps(candidate.get('transitions', []), ensure_ascii=False, sort_keys=True)})"
                        for candidate in graph or []
                        if isinstance(candidate, dict)
                    )
                else:
                    rendered_candidates = [
                        f"{candidate.get('path')} ({candidate.get('score', 'n/a')}; {','.join(map(str, candidate.get('origins', [])))})"
                        for candidate in attempt.get("candidates", [])
                        if isinstance(candidate, dict)
                    ]
                candidate_text = "; ".join(rendered_candidates) or "—"
                failure = attempt.get("failure_kind") or attempt.get("reason_code") or "—"
                selection = attempt.get("selection") if isinstance(attempt.get("selection"), dict) else {}
                lines.append(
                    f"| {label} | {key[1]} | {attempt.get('attempt_number', '?')} | {markdown_text(attempt.get('query') or '—')} | {markdown_text(attempt.get('mode', 'unknown'))} | {markdown_text(attempt.get('retrieval_strategy') or '—')} | "
                    f"{attempt.get('exit_code', 'n/a')} | {markdown_text(failure)} | {markdown_text(attempt.get('index_state') or '—')} | "
                    f"{attempt.get('documents') if attempt.get('documents') is not None else 'n/a'} | {attempt.get('refreshed') if attempt.get('refreshed') is not None else 'n/a'} | "
                    f"{attempt.get('direct_count', 'n/a')}/{attempt.get('graph_count', 'n/a')} | "
                    f"{timings.get('total_seconds', 'n/a')}/{timings.get('search_seconds', 'n/a')} | "
                    f"{markdown_text(candidate_text)} [selected {selection.get('direct_returned', 'n/a')}/{selection.get('direct_considered', 'n/a')} direct; {selection.get('graph_returned', 'n/a')}/{selection.get('graph_considered', 'n/a')} graph] |"
                )

    lines.extend([
        "",
        "## Retrieval usefulness details",
        "",
        "README.md is excluded because the skill reads it independently of accelerator routing.",
        "",
        "| Mode | Sample | Returned direct | Returned graph | Read direct | Read graph | Read outside | Unread direct | Unread graph | Outside paths |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ])
    for label, samples in (("fallback", left), ("accelerated", right)):
        for key, sample in sorted(samples.items()):
            usefulness = aggregate_usefulness(sample)
            lines.append(
                f"| {label} | {key[1]} | {usefulness.get('returned_direct', 'n/a')} | "
                f"{usefulness.get('returned_graph', 'n/a')} | {usefulness.get('read_returned_direct', 'n/a')} | "
                f"{usefulness.get('read_returned_graph', 'n/a')} | {usefulness.get('read_outside_results', 'n/a')} | "
                f"{usefulness.get('unread_returned_direct', 'n/a')} | {usefulness.get('unread_returned_graph', 'n/a')} | "
                f"{markdown_text(', '.join(map(str, usefulness.get('read_outside_result_paths', []))) or '—')} |"
            )

    command_rows: list[str] = []
    for label, samples in (("fallback", left), ("accelerated", right)):
        for key, sample in sorted(samples.items()):
            for run in agent_runs(sample):
                event_metrics = run.get("event_metrics")
                commands = event_metrics.get("command_metrics", []) if isinstance(event_metrics, dict) else []
                for command in commands if isinstance(commands, list) else []:
                    if not isinstance(command, dict):
                        continue
                    command_rows.append(
                        f"| {label} | {key[1]} | {command.get('number', '?')} | {markdown_text(command.get('category', 'unknown'))} | "
                        f"{command.get('exit_code', 'n/a')} | {command.get('output_chars', 'n/a')} | {command.get('inferred_file_count', 'n/a')} | "
                        f"{markdown_text(command.get('command_excerpt', ''))} |"
                    )
    if command_rows:
        lines.extend(["", "## Command executions", "", "| Mode | Sample | Command | Category | Exit | Output chars | Inferred files | Command |", "|---|---:|---:|---|---:|---:|---:|---|"])
        lines.extend(command_rows)

    diagnostic_rows: list[tuple[str, int, str, str]] = []
    for label, samples in (("fallback", left), ("accelerated", right)):
        for key, sample in sorted(samples.items()):
            checks = sample.get("failed_checks")
            for check in checks if isinstance(checks, list) else []:
                if isinstance(check, dict):
                    diagnostic_rows.append((label, key[1], str(check.get("type", "check")), str(check.get("message", ""))[:1000]))
            for run in agent_runs(sample):
                for value in run.get("environment_errors", []):
                    diagnostic_rows.append((label, key[1], "environment", str(value)[:1000]))
                for value in run.get("scope_violations", []):
                    diagnostic_rows.append((label, key[1], "scope", str(value)[:1000]))
            for attempt in attempts(sample):
                reason_code = attempt.get("reason_code")
                if attempt.get("failure_kind") or reason_code not in {None, "cache_unusable"}:
                    detail = attempt.get("reason") or attempt.get("output_excerpt") or ""
                    diagnostic_rows.append((label, key[1], f"retrieval-{attempt.get('attempt_number', '?')}", str(detail)[:1000]))
    if diagnostic_rows:
        lines.extend(["", "## Diagnostics", "", "| Mode | Sample | Kind | Detail |", "|---|---:|---|---|"])
        lines.extend(
            f"| {label} | {sample_number} | {markdown_text(kind)} | {markdown_text(detail)} |"
            for label, sample_number, kind, detail in diagnostic_rows
        )

    lines = without_sections(
        lines,
        {"## Retrieval attempts", "## Retrieval usefulness details", "## Command executions"},
    )
    lines.extend(["", f"> Comparator fingerprint: `{hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}`.", "> Behavioral failures remain visible. Environment-invalid samples are excluded from metric cohorts. This is a measurement, not a CI threshold."])
    return "\n".join(lines)


def demote_report(report: str, title: str) -> str:
    lines = [("#" + line) if line.startswith("#") else line for line in report.splitlines()]
    lines[0] = f"## {title}"
    return "\n".join(lines)


def render_no_extract_pair(
    baseline: dict[str, Any],
    compared: dict[str, Any],
    *,
    compared_mode: str,
    compared_label: str,
) -> str:
    left, right = validate_no_extract_comparable(
        baseline, compared, compared_mode=compared_mode
    )
    valid_left = cohort(left, lambda sample: bool(sample.get("environment_valid")))
    valid_right = cohort(right, lambda sample: bool(sample.get("environment_valid")))
    passed_left = cohort(
        left,
        lambda sample: bool(sample.get("environment_valid"))
        and bool(sample.get("passed")),
    )
    passed_right = cohort(
        right,
        lambda sample: bool(sample.get("environment_valid"))
        and bool(sample.get("passed")),
    )
    lines = [
        f"### No Extract vs {compared_label}",
        "",
        "The no-Extract profile receives the same scenario and project fixture, but no "
        "skill package or retrieval instructions. Profile-specific checks remove only "
        "the Extract response schema, retrieval command, and accelerator budget; the "
        "required documents, semantic constraint, exclusions, read-only behavior, and "
        "response budget remain checked.",
        "",
        f"Run IDs: no Extract `{markdown_text(baseline.get('run', {}).get('run_id', 'unavailable'))}`; "
        f"{compared_label} `{markdown_text(compared.get('run', {}).get('run_id', 'unavailable'))}`.",
        "",
        f"Behavior passed: no Extract {len(passed_left)}/{len(valid_left)}; "
        f"{compared_label} {len(passed_right)}/{len(valid_right)}.",
        "",
    ]
    render_metric_table(lines, valid_left, valid_right, "N", "E")
    lines.extend(["", "Deterministic cost ledger:", ""])
    render_metric_table(
        lines,
        valid_left,
        valid_right,
        "N",
        "E",
        metrics=COST_METRICS,
        show_uncertainty=False,
    )
    lines.extend(
        [
            "",
            "| Profile | Sample | Passed | Files | Agent messages | Agent time | Total tokens | Outcome |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for label, samples in (("no-extract", left), (compared_label, right)):
        for key, sample in sorted(samples.items()):
            lines.append(
                f"| {label} | {key[1]} | {bool(sample.get('passed'))} | "
                f"{format_number(metric_value(sample, 'files_read'), 'files_read')} | "
                f"{format_number(metric_value(sample, 'agent_message_count'), 'agent_message_count')} | "
                f"{format_number(metric_value(sample, 'agent_duration_seconds'), 'agent_duration_seconds')} | "
                f"{format_number(metric_value(sample, 'total_tokens'), 'total_tokens')} | "
                f"{markdown_text(failure_summary(sample))} |"
            )
    return "\n".join(lines)


def render_no_extract_comparisons(
    baseline: dict[str, Any],
    fallback: dict[str, Any],
    cold: dict[str, Any],
) -> str:
    return "\n\n".join(
        (
            "## Direct documentation baseline",
            render_no_extract_pair(
                baseline,
                fallback,
                compared_mode="fallback",
                compared_label="Extract fallback",
            ),
            render_no_extract_pair(
                baseline,
                cold,
                compared_mode="enabled",
                compared_label="Extract + SQLite",
            ),
        )
    )


def render_three_way(
    fallback: dict[str, Any],
    cold: dict[str, Any],
    warm: dict[str, Any],
    source_directories: tuple[Path, ...] = (),
) -> str:
    cold_report = render_comparison(fallback, cold, source_directories)
    warm_report = render_comparison(
        fallback,
        warm,
        source_directories,
        compare_cache_profile=False,
    )
    cold_samples, warm_samples = validate_comparable(
        cold,
        warm,
        compare_cache_profile=False,
        left_mode="enabled",
        right_mode="enabled",
    )
    cold_queries = retrieval_queries(cold_samples)
    warm_queries = retrieval_queries(warm_samples)
    queries_match = bool(cold_queries) and cold_queries == warm_queries
    direct_lines = [
        "## Cold vs prewarmed accelerator",
        "",
        (
            "Exact retrieval queries match across profiles; routing differences can be "
            "attributed to cache state, while agent metrics remain stochastic."
            if queries_match
            else "Agent-generated retrieval queries differ across profiles; this comparison "
            "is confounded by model stochasticity and does not isolate cache-state effects."
        ),
        "",
        "| Cold retrieval queries | Prewarmed retrieval queries | Exact sets match |",
        "|---|---|---|",
        f"| {markdown_text(' ; '.join(cold_queries) or 'unavailable')} | "
        f"{markdown_text(' ; '.join(warm_queries) or 'unavailable')} | "
        f"{'yes' if queries_match else 'no'} |",
        "",
    ]
    render_metric_table(
        direct_lines,
        cohort(cold_samples, lambda sample: bool(sample.get("environment_valid"))),
        cohort(warm_samples, lambda sample: bool(sample.get("environment_valid"))),
        "C",
        "W",
    )
    all_samples = [
        *fallback.get("samples", []),
        *cold.get("samples", []),
        *warm.get("samples", []),
    ]
    return "\n\n".join(
        (
            "# Extract retrieval performance: cold and prewarmed\n\n"
            f"Observed concurrency across all three groups: {observed_concurrency(all_samples) or 'unavailable'}.",
            "\n".join(direct_lines),
            demote_report(cold_report, "Cold accelerator vs fallback"),
            demote_report(warm_report, "Prewarmed accelerator vs fallback"),
        )
    )


def default_output_path(now: datetime.datetime | None = None) -> Path:
    instant = now or datetime.datetime.now(datetime.timezone.utc)
    timestamp = instant.astimezone(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    return DEFAULT_OUTPUT_DIRECTORY / f"extract-metrics-{timestamp}.md"


def available_output_path(path: Path) -> Path:
    if not path.exists():
        return path
    for number in range(1, 10_000):
        candidate = path.with_name(f"{path.stem}-{number}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise ComparisonError(f"cannot allocate a unique report path beside {path}")


def write_markdown(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    candidate = available_output_path(path)
    try:
        with candidate.open("x", encoding="utf-8") as output:
            output.write(content.rstrip() + "\n")
    except FileExistsError:
        return write_markdown(path, content)
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fallback", type=Path, required=True)
    parser.add_argument("--accelerated", type=Path, required=True)
    parser.add_argument("--warm", type=Path, help="optional prewarmed accelerator report")
    parser.add_argument(
        "--no-extract",
        type=Path,
        help="optional direct-documentation report produced without the Extract skill",
    )
    parser.add_argument("--output", type=Path, help="preferred Markdown path; an existing file is never overwritten")
    args = parser.parse_args()
    report_paths = tuple(
        path
        for path in (args.fallback, args.accelerated, args.warm, args.no_extract)
        if path is not None
    )
    directories = report_directories(report_paths)
    print("Source report directories: " + ", ".join(str(path) for path in directories))
    try:
        fallback = load_report(args.fallback)
        accelerated = load_report(args.accelerated)
        rendered = (
            render_three_way(
                fallback,
                accelerated,
                load_report(args.warm),
                directories,
            )
            if args.warm
            else render_comparison(fallback, accelerated, directories)
        )
        if args.no_extract:
            rendered += "\n\n" + render_no_extract_comparisons(
                load_report(args.no_extract), fallback, accelerated
            )
        output_path = write_markdown(args.output or default_output_path(), rendered)
    except ComparisonError as error:
        print(f"cannot compare reports: {error}", file=sys.stderr)
        return 2
    print(f"Markdown report: {output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
