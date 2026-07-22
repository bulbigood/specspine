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
METRICS = ("agent_duration_seconds", *TOKEN_METRICS, "files_read")


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
        if part == "--accelerator-mode":
            skip = True
        elif not part.startswith("--accelerator-mode="):
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
    fallback: dict[str, Any], accelerated: dict[str, Any]
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
        if left[key].get("environment_valid") and trace_values(left[key], "accelerator_mode") != {"fallback"}:
            raise ComparisonError(f"fallback mode is not recorded for {key}")
        if right[key].get("environment_valid") and trace_values(right[key], "accelerator_mode") != {"enabled"}:
            raise ComparisonError(f"enabled mode is not recorded for {key}")
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
    if metric == "agent_duration_seconds":
        value = sample.get(metric)
    elif metric == "files_read":
        values = [run.get("files_read") for run in agent_runs(sample)]
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


def single_successful_attempt(sample: dict[str, Any], expected_mode: str) -> bool:
    found = attempts(sample)
    return (
        len(found) == 1
        and found[0].get("mode") == expected_mode
        and found[0].get("failure_kind") is None
        and found[0].get("exit_code") in {0, 2}
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


def range_text(values: list[float], metric: str) -> str:
    return "n/a" if not values else f"{format_number(min(values), metric)}–{format_number(max(values), metric)}"


def render_metric_table(
    lines: list[str], fallback_samples: list[dict[str, Any]], accelerated_samples: list[dict[str, Any]]
) -> None:
    lines.extend([
        "| Metric | F mean | A mean | Δ mean | F median | A median | F min–max | A min–max | F SD | A SD | Totals ratio A/F | n F/A |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for metric in METRICS:
        left, right = metric_values(fallback_samples, metric), metric_values(accelerated_samples, metric)
        left_mean = statistics.fmean(left) if left else None
        right_mean = statistics.fmean(right) if right else None
        delta = None if left_mean is None or right_mean is None else right_mean - left_mean
        ratio = None if not left or not right or sum(left) == 0 else sum(right) / sum(left)
        label = metric.replace("_", " ").capitalize()
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
        started, finished = parse_time(sample.get("started_at")), parse_time(sample.get("finished_at"))
        if started is None or finished is None:
            continue
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


def render_comparison(
    fallback: dict[str, Any], accelerated: dict[str, Any], source_directories: tuple[Path, ...] = ()
) -> str:
    left, right = validate_comparable(fallback, accelerated)
    all_samples = [*left.values(), *right.values()]
    run_left, run_right = fallback.get("run", {}), accelerated.get("run", {})
    lines = [
        "# Extract retrieval performance", "",
        "Independent stochastic samples use matched case identities; sample numbers are not statistical pairs.", "",
        "## Configuration", "", "| Setting | Forced fallback | SQLite FTS5 + graph |", "|---|---|---|",
        f"| Run ID | {markdown_text(run_left.get('run_id', 'unavailable'))} | {markdown_text(run_right.get('run_id', 'unavailable'))} |",
        f"| Started | {markdown_text(run_left.get('started_at', 'unavailable'))} | {markdown_text(run_right.get('started_at', 'unavailable'))} |",
        f"| Finished | {markdown_text(run_left.get('finished_at', 'unavailable'))} | {markdown_text(run_right.get('finished_at', 'unavailable'))} |",
        f"| Cache profile | {markdown_text(run_left.get('cache_profile', []))} | {markdown_text(run_right.get('cache_profile', []))} |",
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
        ("Single successful retrieval attempt", lambda sample, mode: bool(sample.get("environment_valid")) and single_successful_attempt(sample, mode)),
    )
    for title, predicate in cohorts:
        left_samples = cohort(left, lambda sample, p=predicate: p(sample, "fallback"))
        right_samples = cohort(right, lambda sample, p=predicate: p(sample, "sqlite-fts5"))
        lines.extend(["", f"## {title}", "", f"Fallback n={len(left_samples)}; accelerated n={len(right_samples)}.", ""])
        render_metric_table(lines, left_samples, right_samples)

    lines.extend(["", "## Sample outcomes", "", "| Mode | Sample | Valid | Passed | Retrieval | Attempts | Index state | Files | Agent time | Total tokens | Queue | Failure |", "|---|---:|---:|---:|---|---:|---|---:|---:|---:|---:|---|"])
    for label, samples in (("fallback", left), ("accelerated", right)):
        for key, sample in sorted(samples.items()):
            found = attempts(sample)
            last = found[-1] if found else {}
            lines.append(
                f"| {label} | {key[1]} | {bool(sample.get('environment_valid'))} | {bool(sample.get('passed'))} | "
                f"{markdown_text(last.get('mode', 'unavailable'))} | {len(found)} | {markdown_text(last.get('index_state') or '—')} | "
                f"{format_number(metric_value(sample, 'files_read'), 'files_read')} | {format_number(metric_value(sample, 'agent_duration_seconds'), 'agent_duration_seconds')} | "
                f"{format_number(metric_value(sample, 'total_tokens'), 'total_tokens')} | {float(sample.get('queue_seconds') or 0):.3f} | {markdown_text(failure_summary(sample))} |"
            )

    lines.extend(["", "## Retrieval attempts", "", "| Mode | Sample | Attempt | Result | Exit | Failure/reason | Index | Documents | Refreshed | Total/Search (s) | Candidates |", "|---|---:|---:|---|---:|---|---|---:|---:|---:|---|"])
    for label, samples in (("fallback", left), ("accelerated", right)):
        for key, sample in sorted(samples.items()):
            for attempt in attempts(sample):
                timings = attempt.get("timings") if isinstance(attempt.get("timings"), dict) else {}
                candidate_text = "; ".join(
                    f"{candidate.get('path')} ({candidate.get('score', 'n/a')}; {','.join(map(str, candidate.get('origins', [])))})"
                    for candidate in attempt.get("candidates", [])[:5]
                    if isinstance(candidate, dict)
                ) or "—"
                failure = attempt.get("failure_kind") or attempt.get("reason_code") or "—"
                lines.append(
                    f"| {label} | {key[1]} | {attempt.get('attempt_number', '?')} | {markdown_text(attempt.get('mode', 'unknown'))} | "
                    f"{attempt.get('exit_code', 'n/a')} | {markdown_text(failure)} | {markdown_text(attempt.get('index_state') or '—')} | "
                    f"{attempt.get('documents') if attempt.get('documents') is not None else 'n/a'} | {attempt.get('refreshed') if attempt.get('refreshed') is not None else 'n/a'} | "
                    f"{timings.get('total_seconds', 'n/a')}/{timings.get('search_seconds', 'n/a')} | {markdown_text(candidate_text)} |"
                )

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
    parser.add_argument("--output", type=Path, help="preferred Markdown path; an existing file is never overwritten")
    args = parser.parse_args()
    directories = report_directories((args.fallback, args.accelerated))
    print("Source report directories: " + ", ".join(str(path) for path in directories))
    try:
        rendered = render_comparison(load_report(args.fallback), load_report(args.accelerated), directories)
        output_path = write_markdown(args.output or default_output_path(), rendered)
    except ComparisonError as error:
        print(f"cannot compare reports: {error}", file=sys.stderr)
        return 2
    print(f"Markdown report: {output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
