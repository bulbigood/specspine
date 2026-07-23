#!/usr/bin/env python3
"""Compare agent-level Extract v2 reports produced with different rankers."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import statistics
from pathlib import Path
from typing import Any


RANKINGS = ("legacy", "faceted-bm25", "faceted-normalized")
PATH_RE = re.compile(r"(?<![\w/.-])specspine/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*\.md")


class ComparisonError(ValueError):
    pass


def load_report(path: Path) -> dict[str, Any]:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ComparisonError(f"cannot read {path}: {exc}") from exc
    if not isinstance(report, dict) or report.get("schema_version") != 2:
        raise ComparisonError(f"{path}: unsupported report schema")
    return report


def normalized_command(command: str) -> tuple[str, ...]:
    tokens = shlex.split(command)
    result: list[str] = []
    skip = False
    for token in tokens:
        if skip:
            skip = False
            continue
        if token == "--ranking":
            skip = True
        elif not token.startswith("--ranking="):
            result.append(token)
    return tuple(result)


def sample_key(sample: dict[str, Any]) -> tuple[str, int]:
    return str(sample.get("case_id")), int(sample.get("sample_number", 0))


def agent_runs(sample: dict[str, Any]) -> list[dict[str, Any]]:
    runs = sample.get("agent_runs")
    return [run for run in runs if isinstance(run, dict)] if isinstance(runs, list) else []


def report_ranking(report: dict[str, Any]) -> str:
    rankings = {
        str(run.get("ranking_system"))
        for sample in report.get("samples", [])
        if isinstance(sample, dict)
        for run in agent_runs(sample)
        if run.get("ranking_system")
    }
    if len(rankings) != 1:
        raise ComparisonError(f"report must contain exactly one ranking system: {sorted(rankings)}")
    ranking = rankings.pop()
    if ranking not in RANKINGS:
        raise ComparisonError(f"unsupported ranking system: {ranking}")
    return ranking


def validate_reports(reports: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if len(reports) < 2:
        raise ComparisonError("at least two ranking reports are required")
    baseline = reports[0]
    baseline_cases = baseline.get("cases")
    baseline_runtime = baseline.get("runtime")
    baseline_fingerprints = baseline.get("fingerprints", {})
    baseline_runner = baseline_fingerprints.get("runner")
    baseline_command_files = baseline_fingerprints.get("agent_command_files")
    baseline_command = normalized_command(str(baseline.get("agent_command", "")))
    baseline_samples = {
        sample_key(sample)
        for sample in baseline.get("samples", [])
        if isinstance(sample, dict)
    }
    arms: dict[str, dict[str, Any]] = {}
    for report in reports:
        ranking = report_ranking(report)
        if ranking in arms:
            raise ComparisonError(f"duplicate ranking report: {ranking}")
        if report.get("cases") != baseline_cases:
            raise ComparisonError("case fingerprints or handoff judgments differ")
        if report.get("runtime") != baseline_runtime:
            raise ComparisonError("runner runtime/platform metadata differs")
        fingerprints = report.get("fingerprints", {})
        if fingerprints.get("runner") != baseline_runner:
            raise ComparisonError("runner fingerprints differ")
        if fingerprints.get("agent_command_files") != baseline_command_files:
            raise ComparisonError("agent command file fingerprints differ")
        if normalized_command(str(report.get("agent_command", ""))) != baseline_command:
            raise ComparisonError("agent commands differ beyond --ranking")
        samples = {
            sample_key(sample)
            for sample in report.get("samples", [])
            if isinstance(sample, dict)
        }
        if samples != baseline_samples:
            raise ComparisonError("sample identities differ")
        for sample in report.get("samples", []):
            if not isinstance(sample, dict) or not sample.get("environment_valid"):
                continue
            for run in agent_runs(sample):
                if run.get("ranking_system") != ranking:
                    raise ComparisonError(
                        f"inconsistent ranking for {sample_key(sample)}"
                    )
        arms[ranking] = report
    return arms


def response_paths(sample: dict[str, Any]) -> set[str]:
    diagnostics = sample.get("diagnostics")
    response = diagnostics.get("response", "") if isinstance(diagnostics, dict) else ""
    return set(PATH_RE.findall(str(response)))


def cost_value(sample: dict[str, Any], field: str) -> float | None:
    values = [
        ledger.get(field)
        for run in agent_runs(sample)
        for ledger in [run.get("cost_ledger")]
        if isinstance(ledger, dict)
        and isinstance(ledger.get(field), (int, float))
        and not isinstance(ledger.get(field), bool)
    ]
    return float(sum(values)) if values else None


def token_value(sample: dict[str, Any]) -> float | None:
    usage = sample.get("token_usage")
    if not isinstance(usage, dict):
        return None
    total = usage.get("total_tokens")
    if isinstance(total, int) and not isinstance(total, bool):
        return float(total)
    parts = [usage.get("input_tokens"), usage.get("output_tokens")]
    return float(sum(value for value in parts if isinstance(value, int))) if any(
        isinstance(value, int) for value in parts
    ) else None


def retrieval_calls(sample: dict[str, Any]) -> int:
    return sum(
        len(run.get("retrieval_attempts", []))
        for run in agent_runs(sample)
        if isinstance(run.get("retrieval_attempts"), list)
    )


def files_read(sample: dict[str, Any]) -> int:
    return sum(
        int(run["files_read"])
        for run in agent_runs(sample)
        if isinstance(run.get("files_read"), int)
        and not isinstance(run.get("files_read"), bool)
    )


def retrieval_slice_counts(sample: dict[str, Any]) -> tuple[int, int]:
    total = no_match = 0
    for run in agent_runs(sample):
        attempts = run.get("retrieval_attempts")
        for attempt in attempts if isinstance(attempts, list) else []:
            if not isinstance(attempt, dict):
                continue
            slices = attempt.get("slices")
            if isinstance(slices, list):
                total += len(slices)
                no_match += sum(
                    isinstance(item, dict) and item.get("status") == "no_match"
                    for item in slices
                )
    return total, no_match


def judgments(report: dict[str, Any], case_id: str) -> dict[str, set[str]]:
    cases = report.get("cases")
    case = cases.get(case_id) if isinstance(cases, dict) else None
    raw = case.get("handoff_judgments") if isinstance(case, dict) else None
    if not isinstance(raw, dict):
        raise ComparisonError(f"{case_id}: handoff_judgments missing from report")
    return {
        field: set(map(str, raw.get(field, [])))
        for field in ("required", "supporting", "relevant", "hard_negatives")
    }


def ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 1.0


def sample_metrics(report: dict[str, Any], sample: dict[str, Any]) -> dict[str, float]:
    case_id = str(sample.get("case_id"))
    gold = judgments(report, case_id)
    mentioned = response_paths(sample)
    core = gold["required"] | gold["supporting"]
    extras = mentioned - gold["relevant"] - {"specspine/README.md"}
    calls = retrieval_calls(sample)
    query_slices, no_match_slices = retrieval_slice_counts(sample)
    response_bytes = cost_value(sample, "final_response_utf8_bytes")
    retrieval_bytes = cost_value(sample, "retrieval_output_utf8_bytes")
    project_source_bytes = cost_value(sample, "project_source_file_bytes")
    tool_cycles = cost_value(sample, "tool_cycles")
    return {
        "behavior_pass": float(bool(sample.get("passed"))),
        "required_recall": ratio(len(mentioned & gold["required"]), len(gold["required"])),
        "core_recall": ratio(len(mentioned & core), len(core)),
        "relevant_precision": ratio(len(mentioned & gold["relevant"]), len(mentioned - {"specspine/README.md"})),
        "extra_documents": float(len(extras)),
        "hard_negatives": float(len(mentioned & gold["hard_negatives"])),
        "retrieval_calls": float(calls),
        "repeat_searches": float(max(0, calls - 1)),
        "tool_cycles": tool_cycles if tool_cycles is not None else 0.0,
        "files_read": float(files_read(sample)),
        "query_slices": float(query_slices),
        "no_match_slices": float(no_match_slices),
        "handoff_utf8_bytes": response_bytes if response_bytes is not None else 0.0,
        "retrieval_utf8_bytes": retrieval_bytes if retrieval_bytes is not None else 0.0,
        "project_source_utf8_bytes": (
            project_source_bytes if project_source_bytes is not None else 0.0
        ),
        "total_tokens": token_value(sample) or 0.0,
    }


def valid_samples(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        sample
        for sample in report.get("samples", [])
        if isinstance(sample, dict) and sample.get("environment_valid")
    ]


def mean_metric(report: dict[str, Any], field: str) -> float | None:
    values = [sample_metrics(report, sample)[field] for sample in valid_samples(report)]
    return statistics.mean(values) if values else None


def format_value(field: str, value: float | None) -> str:
    if value is None:
        return "n/a"
    if field in {"behavior_pass", "required_recall", "core_recall", "relevant_precision"}:
        return f"{value:.1%}"
    if field.endswith("_bytes"):
        return f"{value:.0f}"
    if field == "total_tokens":
        return f"{value:.0f}"
    return f"{value:.2f}"


def render(reports: list[dict[str, Any]]) -> str:
    arms = validate_reports(reports)
    order = [ranking for ranking in RANKINGS if ranking in arms]
    metrics = (
        ("behavior_pass", "Behavior pass"),
        ("required_recall", "Owner recall"),
        ("core_recall", "Owner + supporting recall"),
        ("relevant_precision", "Handoff document precision"),
        ("extra_documents", "Unnecessary documents"),
        ("hard_negatives", "Hard negatives"),
        ("retrieval_calls", "Retrieval tool calls"),
        ("repeat_searches", "Repeat searches"),
        ("tool_cycles", "All tool cycles"),
        ("files_read", "Inferred files read"),
        ("query_slices", "Query slices"),
        ("no_match_slices", "No-match slices"),
        ("handoff_utf8_bytes", "Final handoff bytes"),
        ("retrieval_utf8_bytes", "Retrieval output bytes"),
        ("project_source_utf8_bytes", "Separately read project-source bytes"),
        ("total_tokens", "Total model tokens"),
    )
    lines = [
        "# Extract v2 agent-level ranking A/B",
        "",
        "All arms use identical cases, prompts, skill package, model settings, and sample identities. "
        "Values are macro means over environment-valid samples.",
        "",
        "| Metric | " + " | ".join(order) + " |",
        "|---|" + "|".join("---:" for _ in order) + "|",
    ]
    for field, label in metrics:
        lines.append(
            f"| {label} | "
            + " | ".join(format_value(field, mean_metric(arms[arm], field)) for arm in order)
            + " |"
        )
    lines.extend(
        [
            "",
            "## Per-case outcomes",
            "",
            "| Ranking | Case | Sample | Pass | Owner recall | Core recall | Precision | Extra | Hard negative | Calls/repeats | Handoff bytes |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for arm in order:
        report = arms[arm]
        for sample in sorted(valid_samples(report), key=sample_key):
            values = sample_metrics(report, sample)
            lines.append(
                f"| {arm} | {sample_key(sample)[0]} | {sample_key(sample)[1]} | "
                f"{format_value('behavior_pass', values['behavior_pass'])} | "
                f"{format_value('required_recall', values['required_recall'])} | "
                f"{format_value('core_recall', values['core_recall'])} | "
                f"{format_value('relevant_precision', values['relevant_precision'])} | "
                f"{values['extra_documents']:.0f} | {values['hard_negatives']:.0f} | "
                f"{values['retrieval_calls']:.0f}/{values['repeat_searches']:.0f} | "
                f"{values['handoff_utf8_bytes']:.0f} |"
            )
    invalid = [
        (arm, sample_key(sample))
        for arm in order
        for sample in arms[arm].get("samples", [])
        if isinstance(sample, dict) and not sample.get("environment_valid")
    ]
    if invalid:
        lines.extend(
            [
                "",
                "> Environment-invalid samples excluded: "
                + ", ".join(f"{arm}:{case}#{number}" for arm, (case, number) in invalid)
                + ".",
            ]
        )
    lines.extend(
        [
            "",
            "Owner recall measures canonical documents; core recall additionally includes grade-2 supporting documents. "
            "Precision counts every cited SpecSpine document outside the judged relevant set as unnecessary. "
            "README.md is neutral because the skill must read the index.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        output = render([load_report(path) for path in args.reports])
    except ComparisonError as exc:
        parser.error(str(exc))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
