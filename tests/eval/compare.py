#!/usr/bin/env python3
"""Run isolated downstream comparisons for the SpecSpine product hypothesis."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import importlib.util
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
COMPARISONS_DIR = Path(__file__).resolve().parent / "comparisons"
RUNNER_PATH = Path(__file__).resolve().parent / "run.py"
REQUIRED_ARMS = {
    "repository-only",
    "architecture-document",
    "full-spine",
    "minimal-handoff",
}

SPEC = importlib.util.spec_from_file_location("specspine_eval_runner", RUNNER_PATH)
assert SPEC and SPEC.loader
RUNNER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNNER
SPEC.loader.exec_module(RUNNER)


def load_comparisons() -> list[dict[str, Any]]:
    comparisons: list[dict[str, Any]] = []
    for path in sorted(COMPARISONS_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        data["_manifest"] = path
        comparisons.append(data)
    return comparisons


def validate_comparison(comparison: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {
        "id",
        "status",
        "prompt",
        "initial_files",
        "arms",
        "assertions",
        "architectural_rubric",
    }
    missing = sorted(required - comparison.keys())
    if missing:
        return [f"missing fields: {', '.join(missing)}"]
    if comparison["status"] not in {"executable", "planned"}:
        errors.append("status must be executable or planned")
    if not isinstance(comparison["prompt"], str) or not comparison["prompt"].strip():
        errors.append("prompt must be a non-empty string")
    if not isinstance(comparison.get("samples", 1), int) or comparison.get("samples", 1) < 1:
        errors.append("samples must be a positive integer")
    if not isinstance(comparison["initial_files"], dict):
        errors.append("initial_files must be an object")
    else:
        for path in comparison["initial_files"]:
            if not RUNNER.safe_relative_path(path):
                errors.append(f"unsafe initial file path: {path}")
    rubric = comparison.get("architectural_rubric")
    if not isinstance(rubric, dict) or not rubric:
        errors.append("architectural_rubric must be a non-empty object")
    arms = comparison["arms"]
    if not isinstance(arms, list):
        return errors + ["arms must be a list"]
    arm_ids = [arm.get("id") for arm in arms if isinstance(arm, dict)]
    missing_arms = sorted(REQUIRED_ARMS - set(arm_ids))
    unexpected_arms = sorted(set(arm_ids) - REQUIRED_ARMS)
    if missing_arms:
        errors.append(f"missing comparison arms: {', '.join(missing_arms)}")
    if unexpected_arms:
        errors.append(f"unexpected comparison arms: {', '.join(unexpected_arms)}")
    if len(arm_ids) != len(set(arm_ids)):
        errors.append("comparison arm IDs must be unique")
    for index, arm in enumerate(arms, 1):
        if not isinstance(arm, dict):
            errors.append(f"arm {index} must be an object")
            continue
        context_files = arm.get("context_files", {})
        if not isinstance(context_files, dict):
            errors.append(f"arm {index} context_files must be an object")
            continue
        for path in context_files:
            if not RUNNER.safe_relative_path(path):
                errors.append(f"arm {index} has unsafe context path: {path}")
    return errors


def write_files(workspace: Path, files: dict[str, str]) -> None:
    for relative, content in files.items():
        path = workspace / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def build_prompt(comparison: dict[str, Any]) -> str:
    return (
        "You are running a blinded downstream coding evaluation.\n"
        "Treat the current directory as the repository root. Implement the request, use repository evidence and any supplied architectural context as needed, run relevant checks, and do not modify supplied architectural context.\n\n"
        f"{comparison['prompt'].strip()}\n"
    )


def content_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def snapshot_hash(files: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    for path, content in sorted(files.items()):
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(content_hash(content).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def unified_diff(before: dict[str, bytes], after: dict[str, bytes]) -> str:
    chunks: list[str] = []
    for path in sorted(RUNNER.changed_paths(before, after)):
        old = before.get(path, b"")
        new = after.get(path, b"")
        try:
            old_lines = old.decode("utf-8").splitlines(keepends=True)
            new_lines = new.decode("utf-8").splitlines(keepends=True)
        except UnicodeDecodeError:
            chunks.append(f"Binary file changed: {path}\n")
            continue
        chunks.extend(
            difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=f"a/{path}" if path in before else "/dev/null",
                tofile=f"b/{path}" if path in after else "/dev/null",
            )
        )
    return "".join(chunks)


def write_run_artifacts(
    target: Path,
    prompt: str,
    response: str,
    stderr: str,
    patch: str,
    trace: dict[str, Any] | None,
    judge_bundle: dict[str, Any],
) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for optional in ("stderr.txt", "trace.json"):
        optional_path = target / optional
        if optional_path.exists():
            optional_path.unlink()
    (target / "prompt.md").write_text(prompt, encoding="utf-8")
    (target / "response.md").write_text(response, encoding="utf-8")
    (target / "diff.patch").write_text(patch, encoding="utf-8")
    (target / "judge-input.json").write_text(
        json.dumps(judge_bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if stderr:
        (target / "stderr.txt").write_text(stderr, encoding="utf-8")
    if trace is not None:
        (target / "trace.json").write_text(
            json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )


def trace_metrics(trace: dict[str, Any] | None, irrelevant: list[str]) -> dict[str, Any]:
    files_read = [] if trace is None else [str(item) for item in trace.get("files_read", [])]
    unique_files = sorted(set(files_read))
    irrelevant_reads = sorted(
        path for path in unique_files if any(RUNNER.fnmatch.fnmatch(path, pattern) for pattern in irrelevant)
    )
    token_usage = {} if trace is None else trace.get("token_usage", {})
    return {
        "files_read": len(unique_files),
        "irrelevant_files_read": irrelevant_reads,
        "input_tokens": token_usage.get("input_tokens") if isinstance(token_usage, dict) else None,
        "output_tokens": token_usage.get("output_tokens") if isinstance(token_usage, dict) else None,
    }


def run_arm(
    comparison: dict[str, Any],
    arm: dict[str, Any],
    sample: int,
    command: list[str],
    keep_workspace: bool,
    artifacts_dir: Path | None = None,
) -> dict[str, Any]:
    workspace = Path(tempfile.mkdtemp(prefix=f"specspine-compare-{comparison['id']}-"))
    retained = False
    try:
        write_files(workspace, comparison["initial_files"])
        write_files(workspace, arm.get("context_files", {}))
        (workspace / ".eval").mkdir(exist_ok=True)
        context_paths = sorted(arm.get("context_files", {}))
        context_before = {
            path: (workspace / path).read_bytes()
            for path in context_paths
        }
        before = RUNNER.snapshot(workspace)
        started = time.monotonic()
        prompt = build_prompt(comparison)
        completed = subprocess.run(
            command,
            cwd=workspace,
            input=prompt,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={
                **os.environ,
                "SPECSPINE_COMPARISON": comparison["id"],
                "SPECSPINE_COMPARISON_SAMPLE": str(sample),
                "SPECSPINE_EVAL_CASE": comparison["id"],
                "SPECSPINE_EVAL_RUN": str(sample),
                "SPECSPINE_EVAL_WORKSPACE": str(workspace),
            },
            timeout=comparison.get("timeout_seconds", 600),
            check=False,
        )
        elapsed = time.monotonic() - started
        after = RUNNER.snapshot(workspace)
        trace = RUNNER.read_trace(workspace)
        patch = unified_diff(before, after)
        judge_bundle = {
            "request": comparison["prompt"].strip(),
            "diff": patch,
            "rubric": comparison["architectural_rubric"],
        }
        assertions = comparison["assertions"] + arm.get("assertions", [])
        checks = [
            RUNNER.evaluate_assertion(item, workspace, before, after, completed.stdout, trace)
            for item in assertions
        ]
        changed_context = [
            path
            for path, content in context_before.items()
            if not (workspace / path).is_file() or (workspace / path).read_bytes() != content
        ]
        checks.append(
            RUNNER.CheckResult(
                not changed_context,
                f"supplied context changed: {changed_context}"
                if changed_context
                else "supplied context unchanged",
            )
        )
        passed = completed.returncode == 0 and all(check.passed for check in checks)
        result = {
            "comparison": comparison["id"],
            "arm": arm["id"],
            "sample": sample,
            "passed": passed,
            "agent_exit": completed.returncode,
            "duration_seconds": round(elapsed, 3),
            "prompt": prompt,
            "prompt_sha256": content_hash(prompt.encode("utf-8")),
            "fixture_sha256": snapshot_hash(
                {path: content.encode("utf-8") for path, content in comparison["initial_files"].items()}
            ),
            "context_sha256": snapshot_hash(
                {path: content.encode("utf-8") for path, content in arm.get("context_files", {}).items()}
            ),
            "context_words": sum(
                len(content.split()) for content in arm.get("context_files", {}).values()
            ),
            "changed_files": sorted(RUNNER.changed_paths(before, after)),
            "diff": patch,
            "response": completed.stdout,
            "checks": [{"passed": check.passed, "message": check.message} for check in checks],
            **trace_metrics(trace, comparison.get("irrelevant_read_patterns", [])),
        }
        if trace is not None:
            result["actual_model"] = trace.get("model")
            result["actual_reasoning"] = trace.get("reasoning_effort")
        if artifacts_dir is not None:
            artifact_target = artifacts_dir / comparison["id"] / arm["id"] / f"sample-{sample}"
            write_run_artifacts(
                artifact_target,
                prompt,
                completed.stdout,
                completed.stderr,
                patch,
                trace,
                judge_bundle,
            )
            result["artifacts"] = str(artifact_target)
        if not passed and keep_workspace:
            result["workspace"] = str(workspace)
            retained = True
        return result
    finally:
        if not retained:
            shutil.rmtree(workspace)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def summarize_arms(results: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for arm in sorted(REQUIRED_ARMS):
        samples = [item for item in results if item["arm"] == arm]
        token_values = [item["input_tokens"] for item in samples if item["input_tokens"] is not None]
        summary[arm] = {
            "samples": len(samples),
            "outcome_pass_rate": sum(bool(item["passed"]) for item in samples) / len(samples),
            "median_context_words": median(item["context_words"] for item in samples),
            "median_files_read": median(item["files_read"] for item in samples),
            "median_irrelevant_files_read": median(len(item["irrelevant_files_read"]) for item in samples),
            "median_input_tokens": median(token_values) if token_values else None,
            "median_duration_seconds": median(item["duration_seconds"] for item in samples),
        }
    return summary


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        comparison: summarize_arms(
            [item for item in results if item["comparison"] == comparison]
        )
        for comparison in sorted({item["comparison"] for item in results})
    }


def actual_settings(results: list[dict[str, Any]]) -> dict[str, str]:
    models = {
        str(item["actual_model"])
        for item in results
        if item.get("actual_model") not in {None, "", "unknown"}
    }
    reasoning_levels = {
        str(item["actual_reasoning"])
        for item in results
        if item.get("actual_reasoning") not in {None, "", "unknown"}
    }
    if len(models) > 1:
        raise ValueError(f"inconsistent actual models: {', '.join(sorted(models))}")
    if len(reasoning_levels) > 1:
        raise ValueError(
            f"inconsistent actual reasoning levels: {', '.join(sorted(reasoning_levels))}"
        )
    complete = all(
        item.get("actual_model") not in {None, "", "unknown"}
        and item.get("actual_reasoning") not in {None, "", "unknown"}
        for item in results
    )
    return {
        "model": next(iter(models)) if complete and models else "unknown",
        "reasoning": next(iter(reasoning_levels)) if complete and reasoning_levels else "unknown",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--comparison", action="append", default=[])
    parser.add_argument("--agent-command")
    parser.add_argument("--jobs", type=positive_int, default=4)
    parser.add_argument("--samples", type=positive_int, help="override manifest sample count per arm")
    parser.add_argument("--keep-workspace", action="store_true")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--artifacts-dir", type=Path)
    args = parser.parse_args()

    comparisons = load_comparisons()
    known = {item["id"] for item in comparisons}
    unknown = sorted(set(args.comparison) - known)
    if unknown:
        parser.error(f"unknown comparison(s): {', '.join(unknown)}")
    validation = {
        item["id"]: validate_comparison(item)
        for item in comparisons
        if validate_comparison(item)
    }
    if args.list:
        for item in comparisons:
            print(f"{item['id']}: {item['status']} ({item.get('samples', 1)} sample(s) per arm)")
    if args.validate:
        for identifier, errors in validation.items():
            for error in errors:
                print(f"INVALID {identifier}: {error}")
        if not validation:
            print(f"valid comparisons: {len(comparisons)}")
    if args.agent_command:
        if validation:
            return 2
        if not args.comparison:
            parser.error("--agent-command requires at least one --comparison")
        selected = [item for item in comparisons if item["id"] in args.comparison]
        selected = [item for item in selected if item["status"] == "executable"]
        if not selected:
            print("No selected executable comparisons")
            return 2
        command = shlex.split(args.agent_command)
        artifacts_dir = args.artifacts_dir
        if artifacts_dir is None and args.json_output is not None:
            artifacts_dir = args.json_output.parent / f"{args.json_output.stem}-artifacts"
        jobs = [
            (item, arm, sample)
            for item in selected
            for sample in range(1, (args.samples or item.get("samples", 1)) + 1)
            for arm in item["arms"]
        ]
        with ThreadPoolExecutor(max_workers=min(args.jobs, len(jobs))) as executor:
            results = list(
                executor.map(
                    lambda job: run_arm(*job, command, args.keep_workspace, artifacts_dir),
                    jobs,
                )
            )
        for result in results:
            print(
                f"{'PASS' if result['passed'] else 'FAIL'} {result['comparison']} "
                f"arm={result['arm']} sample={result['sample']} "
                f"files={result['files_read']} input_tokens={result['input_tokens']}"
            )
        try:
            settings = actual_settings(results)
        except ValueError as error:
            print(f"INVALID RUN: {error}", file=sys.stderr)
            return 2
        report = {
            **settings,
            "comparisons": [item["id"] for item in selected],
            "summary": summarize(results),
            "results": results,
        }
        if args.json_output:
            args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        # Outcome failures are benchmark data, not harness failures. Reserve a
        # non-zero exit for agents that could not complete their runs.
        return 0 if all(item["agent_exit"] == 0 for item in results) else 1
    if not any((args.list, args.validate)):
        parser.print_help()
    return 2 if validation else 0


if __name__ == "__main__":
    raise SystemExit(main())
