#!/usr/bin/env python3
"""Compare saved extract eval metrics without running an agent."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import html
import json
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
    *TOKEN_METRICS,
    "files_read",
    "command_count",
    "command_output_chars",
)
COST_METRICS = (
    "prompt_utf8_bytes",
    "declared_skill_context_utf8_bytes",
    "retrieval_output_utf8_bytes",
    "project_source_file_bytes",
    "command_output_utf8_bytes",
    "final_response_utf8_bytes",
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


def accelerator_runtime_values(samples: Iterable[dict[str, Any]], field: str) -> str:
    values = sorted({
        str(runtime[field])
        for sample in samples
        for attempt in attempts(sample)
        for runtime in [attempt.get("runtime")]
        if isinstance(runtime, dict) and runtime.get(field) is not None
    })
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
    elif metric in {"command_count", "command_output_chars"}:
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
        and (
            bool(found[0].get("reason_code"))
            if expected_mode == "fallback"
            else not found[0].get("reason_code")
        )
    )


def cohort(
    samples: dict[tuple[str, int], dict[str, Any]], predicate: Callable[[dict[str, Any]], bool]
) -> list[dict[str, Any]]:
    return [sample for _, sample in sorted(samples.items()) if predicate(sample)]


def metric_values(samples: Iterable[dict[str, Any]], metric: str) -> list[float]:
    values = [metric_value(sample, metric) for sample in samples]
    return [value for value in values if value is not None]


def percentage(delta: float, baseline: float) -> str:
    return "n/a" if baseline == 0 else f"{100.0 * delta / baseline:+.1f}%"


def format_number(value: float | None, metric: str, *, signed: bool = False) -> str:
    if value is None:
        return "n/a"
    if metric == "agent_duration_seconds":
        return f"{value:+.3f}" if signed else f"{value:.3f}"
    return f"{value:+,.1f}" if signed else f"{value:,.1f}"


def metric_label(metric: str) -> str:
    return {
        "files_read": "Inferred distinct files read",
        "command_count": "Command executions",
        "command_output_chars": "Command output characters",
        "prompt_utf8_bytes": "Prompt bytes",
        "declared_skill_context_utf8_bytes": "Declared skill context bytes",
        "retrieval_output_utf8_bytes": "Retrieval output bytes",
        "project_source_file_bytes": "Inferred project source bytes",
        "command_output_utf8_bytes": "Command output bytes",
        "final_response_utf8_bytes": "Final response bytes",
        "tool_cycles": "Tool cycles",
    }.get(metric, metric.replace("_", " ").capitalize())


def range_text(values: list[float], metric: str) -> str:
    return "n/a" if not values else f"{format_number(min(values), metric)}–{format_number(max(values), metric)}"


def render_metric_table(
    lines: list[str],
    fallback_samples: list[dict[str, Any]],
    accelerated_samples: list[dict[str, Any]],
    left_label: str = "F",
    right_label: str = "A",
    metrics: tuple[str, ...] = METRICS,
) -> None:
    lines.extend([
        f"| Metric | {left_label} mean | {right_label} mean | Δ mean | {left_label} median | {right_label} median | {left_label} min–max | {right_label} min–max | {left_label} SD | {right_label} SD | Totals ratio {right_label}/{left_label} | n {left_label}/{right_label} |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for metric in metrics:
        left, right = metric_values(fallback_samples, metric), metric_values(accelerated_samples, metric)
        left_mean = statistics.fmean(left) if left else None
        right_mean = statistics.fmean(right) if right else None
        delta = None if left_mean is None or right_mean is None else right_mean - left_mean
        ratio = None if not left or not right or sum(left) == 0 else sum(right) / sum(left)
        label = metric_label(metric)
        lines.append(
            f"| {label} | {format_number(left_mean, metric)} | {format_number(right_mean, metric)} | "
            f"{('n/a' if delta is None or left_mean is None else percentage(delta, left_mean))} | "
            f"{format_number(statistics.median(left) if left else None, metric)} | "
            f"{format_number(statistics.median(right) if right else None, metric)} | "
            f"{range_text(left, metric)} | {range_text(right, metric)} | "
            f"{format_number(statistics.stdev(left) if len(left) > 1 else None, metric)} | "
            f"{format_number(statistics.stdev(right) if len(right) > 1 else None, metric)} | "
            f"{('n/a' if ratio is None else f'{ratio:.3f}')} | {len(left)}/{len(right)} |"
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


def prewarm_seconds(sample: dict[str, Any]) -> float:
    return sum(
        float(value)
        for run in agent_runs(sample)
        for value in [run.get("prewarm_seconds")]
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    )


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
        f"| Started | {markdown_text(run_left.get('started_at', 'unavailable'))} | {markdown_text(run_right.get('started_at', 'unavailable'))} |",
        f"| Finished | {markdown_text(run_left.get('finished_at', 'unavailable'))} | {markdown_text(run_right.get('finished_at', 'unavailable'))} |",
        f"| Cache profile | {markdown_text(cache_profile_text(run_left))} | {markdown_text(cache_profile_text(run_right))} |",
        f"| Configured jobs | {fallback.get('jobs')} | {accelerated.get('jobs')} |",
        f"| Samples | {len(left)} | {len(right)} |",
        f"| Model | {all_trace_values(left.values(), 'model')} | {all_trace_values(right.values(), 'model')} |",
        f"| Reasoning effort | {all_trace_values(left.values(), 'reasoning_effort')} | {all_trace_values(right.values(), 'reasoning_effort')} |",
        f"| Codex CLI | {all_runtime_values(left.values(), 'codex_cli')} | {all_runtime_values(right.values(), 'codex_cli')} |",
        f"| Accelerator Python | {accelerator_runtime_values(left.values(), 'python')} | {accelerator_runtime_values(right.values(), 'python')} |",
        f"| SQLite | {accelerator_runtime_values(left.values(), 'sqlite')} | {accelerator_runtime_values(right.values(), 'sqlite')} |",
        f"| Runner fingerprint | {markdown_text(str(report_fingerprint(fallback, 'runner'))[:12])} | {markdown_text(str(report_fingerprint(accelerated, 'runner'))[:12])} |",
        f"| Observed combined concurrency | {observed_concurrency(all_samples) or 'unavailable'} | {observed_concurrency(all_samples) or 'unavailable'} |",
    ]
    for number, directory in enumerate(source_directories, 1):
        lines.append(f"| Source report directory {number} | {markdown_path(directory)} | {markdown_path(directory)} |")
    warnings = compatibility_warnings(fallback, accelerated)
    if warnings:
        lines.extend(["", "> Compatibility warning: " + "; ".join(warnings) + "."])

    cohorts = (
        ("Environment-valid", lambda sample, mode: bool(sample.get("environment_valid"))),
        ("Behavior-passed", lambda sample, mode: bool(sample.get("environment_valid")) and bool(sample.get("passed"))),
        ("Expected retrieval path", lambda sample, mode: bool(sample.get("environment_valid")) and expected_path(sample, mode)),
        ("Single expected retrieval attempt", lambda sample, mode: bool(sample.get("environment_valid")) and single_expected_attempt(sample, mode)),
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
    render_metric_table(lines, valid_left, valid_right, metrics=COST_METRICS)

    lines.extend(["", "## Sample outcomes", "", "| Mode | Sample | Valid | Passed | Retrieval | Attempts | Index state | Inferred files | Commands | Tool output chars | Prewarm | Agent time | Total tokens | Queue | Outcome/reason |", "|---|---:|---:|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|"])
    for label, samples in (("fallback", left), ("accelerated", right)):
        for key, sample in sorted(samples.items()):
            found = attempts(sample)
            last = found[-1] if found else {}
            lines.append(
                f"| {label} | {key[1]} | {bool(sample.get('environment_valid'))} | {bool(sample.get('passed'))} | "
                f"{markdown_text(last.get('mode', 'unavailable'))} | {len(found)} | {markdown_text(last.get('index_state') or '—')} | "
                f"{format_number(metric_value(sample, 'files_read'), 'files_read')} | {format_number(metric_value(sample, 'command_count'), 'command_count')} | "
                f"{format_number(metric_value(sample, 'command_output_chars'), 'command_output_chars')} | {prewarm_seconds(sample):.3f} | {format_number(metric_value(sample, 'agent_duration_seconds'), 'agent_duration_seconds')} | "
                f"{format_number(metric_value(sample, 'total_tokens'), 'total_tokens')} | {float(sample.get('queue_seconds') or 0):.3f} | {markdown_text(failure_summary(sample))} |"
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
        "## Retrieval usefulness",
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
                if attempt.get("failure_kind") or attempt.get("reason_code"):
                    detail = attempt.get("reason") or attempt.get("output_excerpt") or ""
                    diagnostic_rows.append((label, key[1], f"retrieval-{attempt.get('attempt_number', '?')}", str(detail)[:1000]))
    if diagnostic_rows:
        lines.extend(["", "## Diagnostics", "", "| Mode | Sample | Kind | Detail |", "|---|---:|---|---|"])
        lines.extend(
            f"| {label} | {sample_number} | {markdown_text(kind)} | {markdown_text(detail)} |"
            for label, sample_number, kind, detail in diagnostic_rows
        )

    lines.extend(["", f"> Comparator fingerprint: `{hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}`.", "> Behavioral failures remain visible. Environment-invalid samples are excluded from metric cohorts. This is a measurement, not a CI threshold."])
    return "\n".join(lines)


def demote_report(report: str, title: str) -> str:
    lines = [("#" + line) if line.startswith("#") else line for line in report.splitlines()]
    lines[0] = f"## {title}"
    return "\n".join(lines)


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
    direct_lines = [
        "## Cold vs prewarmed accelerator",
        "",
        "Both profiles return the same routing contract; this comparison isolates cache-state effects.",
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
    parser.add_argument("--output", type=Path, help="preferred Markdown path; an existing file is never overwritten")
    args = parser.parse_args()
    report_paths = tuple(
        path for path in (args.fallback, args.accelerated, args.warm) if path is not None
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
        output_path = write_markdown(args.output or default_output_path(), rendered)
    except ComparisonError as error:
        print(f"cannot compare reports: {error}", file=sys.stderr)
        return 2
    print(f"Markdown report: {output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
