#!/usr/bin/env python3
"""Run the representative Extract v2 agent-level ranking benchmark."""

from __future__ import annotations

import argparse
import datetime
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = Path(__file__).resolve().parent
RANKINGS = ("legacy", "faceted-bm25", "faceted-normalized")
CASES = (
    "extract-v2-backend-multislice",
    "extract-v2-cli-multislice",
    "extract-v2-mobile-multislice-ru",
    "extract-v2-pipeline-multislice-zh-cn",
)


def run_command(command: list[str]) -> int:
    print("+", " ".join(command), flush=True)
    completed = subprocess.run(command, cwd=ROOT, check=False)
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--model", default="gpt-5.6-luna")
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument("--ranking", action="append", choices=RANKINGS)
    args = parser.parse_args()
    if args.samples < 1 or args.jobs < 1:
        parser.error("--samples and --jobs must be positive")
    rankings = tuple(args.ranking or RANKINGS)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_paths: list[Path] = []
    failed_arms: list[str] = []
    for ranking in rankings:
        report = args.output_dir / f"{ranking}.json"
        report_paths.append(report)
        agent_command = (
            f"{sys.executable} {EVAL_DIR / 'adapters' / 'codex.py'} "
            f"--model {args.model} --reasoning-effort {args.reasoning_effort} "
            f"--accelerator-mode enabled --ranking {ranking}"
        )
        command = [
            sys.executable,
            str(EVAL_DIR / "run.py"),
            "--samples",
            str(args.samples),
            "--jobs",
            str(args.jobs),
            "--run-id",
            f"extract-v2-ranking-ab-{timestamp}-{ranking}",
            "--report-label",
            ranking,
            "--report-json",
            str(report),
            "--agent-command",
            agent_command,
        ]
        for case in CASES:
            command.extend(("--case", case))
        if run_command(command):
            if not report.is_file():
                raise SystemExit(f"{ranking}: runner failed without a JSON report")
            failed_arms.append(ranking)
    if len(report_paths) >= 2:
        comparison_status = run_command(
            [
                sys.executable,
                str(EVAL_DIR / "compare_extract_rankings.py"),
                *map(str, report_paths),
                "--output",
                str(args.output_dir / "comparison.md"),
            ]
        )
        if comparison_status:
            raise SystemExit(comparison_status)
        print(args.output_dir / "comparison.md")
    if failed_arms:
        print("Behavioral failures:", ", ".join(failed_arms), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
