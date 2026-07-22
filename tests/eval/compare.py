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
import tarfile
import tempfile
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from statistics import mean, median
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
COMPARISONS_DIR = Path(__file__).resolve().parent / "comparisons"
TASKS_DIR = Path(__file__).resolve().parent / "tasks"
REPOSITORIES_DIR = Path(__file__).resolve().parent / "repositories"
CONTEXT_BUNDLES_DIR = Path(__file__).resolve().parent / "context-bundles"
RUNNER_PATH = Path(__file__).resolve().parent / "run.py"
ARM_ORDER = (
    "native-repository",
    "full-spine",
)
EXPERIMENT_ARMS = {
    "value": frozenset({"native-repository", "full-spine"}),
}
ARM_DESCRIPTIONS = {
    "native-repository": "Frozen repository with its native README, API documentation, tests, comments, and configuration; no SpecSpine.",
    "full-spine": "The same native repository plus the complete reviewed SpecSpine, navigated by the agent from its index.",
}
JUDGE_SCORE_MIN = 0
JUDGE_SCORE_MAX = 2
DEFAULT_JSON_OUTPUT = Path("comparison-results.json")

SPEC = importlib.util.spec_from_file_location("specspine_eval_runner", RUNNER_PATH)
assert SPEC and SPEC.loader
RUNNER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNNER
SPEC.loader.exec_module(RUNNER)


def load_comparisons() -> list[dict[str, Any]]:
    tasks = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(TASKS_DIR.glob("*.json"))
    }
    comparisons: list[dict[str, Any]] = []
    for path in sorted(COMPARISONS_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        task_id = data.get("task")
        if task_id in tasks:
            data = {**tasks[task_id], **data}
        data["_manifest"] = path
        comparisons.append(data)
    return comparisons


def load_repositories() -> dict[str, dict[str, Any]]:
    return {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(REPOSITORIES_DIR.glob("*.json"))
    }


def validate_comparison(comparison: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {
        "id",
        "description",
        "status",
        "experiment",
        "task",
        "repository",
        "prompt",
        "arms",
        "architectural_rubric",
    }
    missing = sorted(required - comparison.keys())
    if missing:
        return [f"missing fields: {', '.join(missing)}"]
    if comparison["status"] not in {"executable", "planned"}:
        errors.append("status must be executable or planned")
    experiment = comparison.get("experiment")
    if experiment not in EXPERIMENT_ARMS:
        errors.append(f"experiment must be one of: {', '.join(sorted(EXPERIMENT_ARMS))}")
    if not isinstance(comparison["description"], str) or not comparison["description"].strip():
        errors.append("description must be a non-empty string")
    if not isinstance(comparison["prompt"], str) or not comparison["prompt"].strip():
        errors.append("prompt must be a non-empty string")
    if not isinstance(comparison.get("samples", 1), int) or comparison.get("samples", 1) < 1:
        errors.append("samples must be a positive integer")
    initial_files = comparison.get("initial_files", {})
    if not isinstance(initial_files, dict):
        errors.append("initial_files must be an object when present")
    else:
        for path in initial_files:
            if not RUNNER.safe_relative_path(path):
                errors.append(f"unsafe initial file path: {path}")
    if comparison.get("repository") not in load_repositories():
        errors.append(f"unknown repository fixture: {comparison.get('repository')}")
    rubric = comparison.get("architectural_rubric")
    if not isinstance(rubric, dict) or not rubric:
        errors.append("architectural_rubric must be a non-empty object")
    arms = comparison["arms"]
    if not isinstance(arms, list):
        return errors + ["arms must be a list"]
    arm_ids = [arm.get("id") for arm in arms if isinstance(arm, dict)]
    required_arms = EXPERIMENT_ARMS.get(experiment, frozenset())
    missing_arms = sorted(required_arms - set(arm_ids))
    unexpected_arms = sorted(set(arm_ids) - required_arms)
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
        bundle = arm.get("context_bundle")
        if bundle is not None and (
            not RUNNER.safe_relative_path(bundle)
            or not (CONTEXT_BUNDLES_DIR / bundle).is_dir()
        ):
            errors.append(f"arm {index} has unknown context bundle: {bundle}")
        if arm.get("id") == "native-repository" and (context_files or bundle):
            errors.append("native-repository must not add context")
    return errors


def write_files(workspace: Path, files: dict[str, str]) -> None:
    for relative, content in files.items():
        path = workspace / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def fixture_cache_root() -> Path:
    configured = os.environ.get("SPECSPINE_EVAL_FIXTURES_DIR")
    return Path(configured) if configured else Path.home() / ".cache" / "specspine-eval" / "fixtures"


def _safe_extract(archive: tarfile.TarFile, target: Path) -> None:
    target_resolved = target.resolve()
    for member in archive.getmembers():
        destination = (target / member.name).resolve()
        if destination != target_resolved and target_resolved not in destination.parents:
            raise ValueError(f"unsafe fixture archive member: {member.name}")
        if member.issym() or member.islnk():
            raise ValueError(f"fixture archive links are not allowed: {member.name}")
    archive.extractall(target, filter="data")


def materialize_repository(repository_id: str) -> Path:
    descriptor = load_repositories()[repository_id]
    expected = descriptor["archive_sha256"]
    cached = fixture_cache_root() / repository_id / expected
    ready = cached / descriptor["archive_root"]
    if ready.is_dir():
        return ready
    cached.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"specspine-fixture-{repository_id}-") as directory:
        temporary = Path(directory)
        archive_path = temporary / "repository.tar.gz"
        urllib.request.urlretrieve(descriptor["archive_url"], archive_path)
        actual = content_hash(archive_path.read_bytes())
        if actual != expected:
            raise ValueError(
                f"fixture archive hash mismatch for {repository_id}: expected {expected}, got {actual}"
            )
        extracted = temporary / "extracted"
        extracted.mkdir()
        with tarfile.open(archive_path, "r:gz") as archive:
            _safe_extract(archive, extracted)
        source = extracted / descriptor["archive_root"]
        if not source.is_dir():
            raise ValueError(f"fixture archive root missing: {descriptor['archive_root']}")
        staging = cached.parent / f".{expected}-{os.getpid()}"
        if staging.exists():
            shutil.rmtree(staging)
        shutil.copytree(extracted, staging)
        try:
            staging.rename(cached)
        except FileExistsError:
            shutil.rmtree(staging)
    return ready


def context_files(arm: dict[str, Any]) -> dict[str, str]:
    files = dict(arm.get("context_files", {}))
    bundle = arm.get("context_bundle")
    if bundle:
        root = CONTEXT_BUNDLES_DIR / bundle
        for path in root.rglob("*"):
            if path.is_file():
                files[path.relative_to(root).as_posix()] = path.read_text(encoding="utf-8")
    return files


def build_prompt(comparison: dict[str, Any], arm: dict[str, Any]) -> str:
    return (
        "You are running a blinded downstream coding evaluation.\n"
        + RUNNER.WORKSPACE_BOUNDARY_INSTRUCTIONS
        + "Before planning or editing: if specspine/README.md exists, read it and navigate the documentation graph to the specifications relevant to this request; otherwise use the repository's native documentation normally. Treat accepted constraints and blocking questions in supplied architectural context as authoritative.\n"
        + "Treat the current directory as the repository root. Implement the request, use repository evidence and any supplied architectural context as needed, run relevant checks, and do not modify supplied architectural context.\n\n"
        + f"{comparison['prompt'].strip()}\n"
    )


def build_judge_prompt(bundle: dict[str, Any]) -> str:
    return (
        "You are a blind semantic evaluator. "
        "The submission is an implementation. Evaluate the diff and final response as evidence of the resulting behavior and architecture. "
        + "Score only the submitted work; "
        "do not infer which experimental arm produced it. Use only the request, diff, "
        "final response, and rubric below. Do not inspect the filesystem or any external source. "
        "For every rubric criterion, assign an integer score: "
        "0 = contradicted, 1 = partially satisfied or unclear from the submitted evidence, "
        "2 = fully satisfied. Return JSON only, with exactly this shape: "
        '{"scores":{"<criterion>":{"score":0,"rationale":"concise evidence"}},'
        '"summary":"concise overall assessment"}. Include every rubric key exactly once.\n\n'
        + json.dumps(bundle, indent=2, sort_keys=True)
        + "\n"
    )


def parse_judge_response(response: str, rubric: dict[str, str]) -> dict[str, Any]:
    text = response.strip()
    if text.startswith("```json") and text.endswith("```"):
        text = text[7:-3].strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError(f"judge returned invalid JSON: {error.msg}") from error
    if not isinstance(data, dict):
        raise ValueError("judge result must be an object")
    if set(data) != {"scores", "summary"}:
        raise ValueError("judge result must contain exactly: scores, summary")
    scores = data.get("scores")
    if not isinstance(scores, dict):
        raise ValueError("judge result requires an object field: scores")
    expected = set(rubric)
    actual = set(scores)
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        raise ValueError(
            f"judge score keys differ from rubric; missing={missing}, unexpected={unexpected}"
        )
    normalized: dict[str, dict[str, Any]] = {}
    for criterion in rubric:
        value = scores[criterion]
        if not isinstance(value, dict):
            raise ValueError(f"judge score for {criterion} must be an object")
        if set(value) != {"score", "rationale"}:
            raise ValueError(
                f"judge score for {criterion} must contain exactly: score, rationale"
            )
        score = value.get("score")
        rationale = value.get("rationale")
        if (
            not isinstance(score, int)
            or isinstance(score, bool)
            or not JUDGE_SCORE_MIN <= score <= JUDGE_SCORE_MAX
        ):
            raise ValueError(
                f"judge score for {criterion} must be an integer {JUDGE_SCORE_MIN}..{JUDGE_SCORE_MAX}"
            )
        if not isinstance(rationale, str) or not rationale.strip():
            raise ValueError(f"judge rationale for {criterion} must be non-empty")
        normalized[criterion] = {"score": score, "rationale": rationale.strip()}
    summary = data.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError("judge result requires a non-empty summary")
    total_score = sum(item["score"] for item in normalized.values())
    return {
        "scores": normalized,
        "summary": summary.strip(),
        "total_score": total_score,
        "max_score": len(normalized) * JUDGE_SCORE_MAX,
        "partial_criteria_count": sum(
            item["score"] < JUDGE_SCORE_MAX for item in normalized.values()
        ),
        "passed": all(item["score"] == JUDGE_SCORE_MAX for item in normalized.values()),
    }


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


def comparison_snapshot(workspace: Path) -> dict[str, bytes]:
    return {
        path: content
        for path, content in RUNNER.snapshot(workspace).items()
        if "__pycache__" not in Path(path).parts and Path(path).suffix != ".pyc"
    }


def judge_bundle(result: dict[str, Any], comparison: dict[str, Any]) -> dict[str, Any]:
    return {
        "submission_type": "implementation",
        "request": comparison["prompt"].strip(),
        "diff": result["diff"],
        "response": result["response"],
        "rubric": comparison["architectural_rubric"],
    }


def judge_cache_key(result: dict[str, Any], comparison: dict[str, Any]) -> str:
    encoded = json.dumps(
        judge_bundle(result, comparison), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return content_hash(encoded)


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
    adapter_artifacts: Path,
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
    if adapter_artifacts.is_dir():
        shutil.copytree(adapter_artifacts, target / "agent", dirs_exist_ok=True)


def trace_metrics(trace: dict[str, Any] | None, irrelevant: list[str]) -> dict[str, Any]:
    files_read = [] if trace is None else [str(item) for item in trace.get("files_read", [])]
    unique_files = sorted(set(files_read))
    irrelevant_reads = sorted(
        path for path in unique_files if any(RUNNER.fnmatch.fnmatch(path, pattern) for pattern in irrelevant)
    )
    token_usage = {} if trace is None else trace.get("token_usage", {})
    scope_violations = [] if trace is None else [
        str(item) for item in trace.get("scope_violations", [])
    ]
    environment_errors = [] if trace is None else [
        str(item) for item in trace.get("environment_errors", [])
    ]
    return {
        "files_read": len(unique_files),
        "files_read_paths": unique_files,
        "irrelevant_files_read": irrelevant_reads,
        "input_tokens": token_usage.get("input_tokens") if isinstance(token_usage, dict) else None,
        "cached_input_tokens": token_usage.get("cached_input_tokens") if isinstance(token_usage, dict) else None,
        "output_tokens": token_usage.get("output_tokens") if isinstance(token_usage, dict) else None,
        "scope_violations": scope_violations,
        "environment_errors": environment_errors,
        "execution_environment": None if trace is None else trace.get("execution_environment"),
    }


def context_protocol_assertions(arm: dict[str, Any]) -> list[dict[str, Any]]:
    """Return objective reads required to ensure the intended context intervention occurred."""
    if arm["id"] == "full-spine":
        return [{"type": "read_includes", "paths": ["specspine/README.md"]}]
    return []


def run_arm(
    comparison: dict[str, Any],
    arm: dict[str, Any],
    sample: int,
    command: list[str],
    keep_workspace: bool,
    artifacts_dir: Path | None = None,
) -> dict[str, Any]:
    workspace = RUNNER.create_workspace(prefix=f"specspine-compare-{comparison['id']}-")
    retained = False
    try:
        repository = materialize_repository(comparison["repository"])
        shutil.copytree(repository, workspace, dirs_exist_ok=True)
        write_files(workspace, comparison.get("initial_files", {}))
        supplied_context = context_files(arm)
        write_files(workspace, supplied_context)
        (workspace / ".eval").mkdir(exist_ok=True)
        RUNNER.initialize_git_workspace(workspace)
        context_paths = sorted(supplied_context)
        context_before = {
            path: (workspace / path).read_bytes()
            for path in context_paths
        }
        before = comparison_snapshot(workspace)
        started = time.monotonic()
        prompt = build_prompt(comparison, arm)
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
        after = comparison_snapshot(workspace)
        trace = RUNNER.read_trace(workspace)
        patch = unified_diff(before, after)
        blind_judge_bundle = judge_bundle(
            {"diff": patch, "response": completed.stdout}, comparison
        )
        assertions = (
            comparison.get("assertions", [])
            + arm.get("assertions", [])
            + context_protocol_assertions(arm)
        )
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
        mechanical_passed = completed.returncode == 0 and all(check.passed for check in checks)
        result = {
            "comparison": comparison["id"],
            "experiment": comparison["experiment"],
            "arm": arm["id"],
            "sample": sample,
            "mechanical_passed": mechanical_passed,
            "passed": mechanical_passed,
            "agent_exit": completed.returncode,
            "duration_seconds": round(elapsed, 3),
            "prompt": prompt,
            "prompt_sha256": content_hash(prompt.encode("utf-8")),
            "fixture_sha256": snapshot_hash(
                {
                    path: content
                    for path, content in before.items()
                    if path not in supplied_context
                }
            ),
            "context_sha256": snapshot_hash(
                {path: content.encode("utf-8") for path, content in supplied_context.items()}
            ),
            "context_words": sum(
                len(content.split()) for content in supplied_context.values()
            ),
            "changed_files": sorted(RUNNER.changed_paths(before, after)),
            "diff": patch,
            "response": completed.stdout,
            "checks": [{"passed": check.passed, "message": check.message} for check in checks],
            **trace_metrics(trace, comparison.get("irrelevant_read_patterns", [])),
        }
        result["valid"] = not result["scope_violations"] and not result["environment_errors"]
        result["invalid_reasons"] = [
            f"workspace boundary violation: {message}"
            for message in result["scope_violations"]
        ] + [
            f"execution environment failure: {message}"
            for message in result["environment_errors"]
        ]
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
                blind_judge_bundle,
                workspace / ".eval",
            )
            result["artifacts"] = str(artifact_target)
        if (not mechanical_passed or not result["valid"]) and keep_workspace:
            result["workspace"] = str(workspace)
            retained = True
        return result
    finally:
        if not retained:
            shutil.rmtree(workspace)


def run_judge(
    result: dict[str, Any],
    comparison: dict[str, Any],
    command: list[str],
    keep_workspace: bool,
) -> dict[str, Any]:
    workspace = RUNNER.create_workspace(prefix="specspine-judge-")
    retained = False
    bundle = judge_bundle(result, comparison)
    prompt = build_judge_prompt(bundle)
    started = time.monotonic()
    try:
        (workspace / ".eval").mkdir()
        env = os.environ.copy()
        for name in (
            "SPECSPINE_COMPARISON",
            "SPECSPINE_COMPARISON_SAMPLE",
            "SPECSPINE_EVAL_CASE",
            "SPECSPINE_EVAL_RUN",
            "SPECSPINE_EVAL_STAGE",
            "SPECSPINE_EVAL_WORKSPACE",
        ):
            env.pop(name, None)
        completed = subprocess.run(
            command,
            cwd=workspace,
            input=prompt,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            timeout=comparison.get("judge_timeout_seconds", 600),
            check=False,
        )
        elapsed = time.monotonic() - started
        trace = RUNNER.read_trace(workspace)
        judge: dict[str, Any] = {
            "valid": False,
            "agent_exit": completed.returncode,
            "duration_seconds": round(elapsed, 3),
            "response": completed.stdout,
        }
        if completed.returncode:
            judge["error"] = f"judge command exited with {completed.returncode}"
        else:
            try:
                judge.update(
                    parse_judge_response(completed.stdout, comparison["architectural_rubric"])
                )
                judge["valid"] = True
            except ValueError as error:
                judge["error"] = str(error)
        if trace is not None:
            judge["actual_model"] = trace.get("model")
            judge["actual_reasoning"] = trace.get("reasoning_effort")
            token_usage = trace.get("token_usage", {})
            if isinstance(token_usage, dict):
                judge["input_tokens"] = token_usage.get("input_tokens")
                judge["output_tokens"] = token_usage.get("output_tokens")
        artifact_value = result.get("artifacts")
        if artifact_value:
            artifact_path = Path(artifact_value)
            (artifact_path / "judge-prompt.md").write_text(prompt, encoding="utf-8")
            (artifact_path / "judge-response.json").write_text(
                completed.stdout + ("\n" if completed.stdout and not completed.stdout.endswith("\n") else ""),
                encoding="utf-8",
            )
            if completed.stderr:
                (artifact_path / "judge-stderr.txt").write_text(
                    completed.stderr, encoding="utf-8"
                )
            if trace is not None:
                (artifact_path / "judge-trace.json").write_text(
                    json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8"
                )
            shutil.copytree(workspace / ".eval", artifact_path / "judge", dirs_exist_ok=True)
        if not judge["valid"] and keep_workspace:
            judge["workspace"] = str(workspace)
            retained = True
        return judge
    finally:
        if not retained:
            shutil.rmtree(workspace)


def archive_reused_judgment(
    result: dict[str, Any],
    comparison: dict[str, Any],
    judgment: dict[str, Any],
    cache_key: str,
    source_result: dict[str, Any],
) -> None:
    artifact_value = result.get("artifacts")
    if not artifact_value:
        return
    artifact_path = Path(artifact_value)
    prompt = build_judge_prompt(judge_bundle(result, comparison))
    (artifact_path / "judge-prompt.md").write_text(prompt, encoding="utf-8")
    response = str(judgment.get("response", ""))
    (artifact_path / "judge-response.json").write_text(
        response + ("\n" if response and not response.endswith("\n") else ""),
        encoding="utf-8",
    )
    (artifact_path / "judge-reused.json").write_text(
        json.dumps({"judge_input_sha256": cache_key}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    source_artifact = source_result.get("artifacts")
    if source_artifact:
        source_judge = Path(source_artifact) / "judge"
        if source_judge.is_dir():
            shutil.copytree(source_judge, artifact_path / "judge", dirs_exist_ok=True)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def summarize_arms(results: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for arm in ARM_ORDER:
        all_samples = [item for item in results if item["arm"] == arm]
        samples = [item for item in all_samples if item.get("valid", True)]
        if not samples:
            summary[arm] = {"samples": 0, "invalid_samples": len(all_samples)}
            continue
        token_values = [item["input_tokens"] for item in samples if item["input_tokens"] is not None]
        cached_values = [
            item["cached_input_tokens"]
            for item in samples
            if item.get("cached_input_tokens") is not None
        ]
        uncached_values = [
            item["input_tokens"] - item["cached_input_tokens"]
            for item in samples
            if item.get("input_tokens") is not None
            and item.get("cached_input_tokens") is not None
        ]
        arm_summary = {
            "samples": len(samples),
            "invalid_samples": len(all_samples) - len(samples),
            "outcome_pass_rate": sum(bool(item["passed"]) for item in samples) / len(samples),
            "mechanical_pass_rate": sum(
                bool(item.get("mechanical_passed", item["passed"])) for item in samples
            ) / len(samples),
            "median_context_words": median(item["context_words"] for item in samples),
            "median_files_read": median(item["files_read"] for item in samples),
            "median_irrelevant_files_read": median(len(item["irrelevant_files_read"]) for item in samples),
            "median_input_tokens": median(token_values) if token_values else None,
            "median_cached_input_tokens": median(cached_values) if cached_values else None,
            "median_uncached_input_tokens": median(uncached_values) if uncached_values else None,
            "median_duration_seconds": median(item["duration_seconds"] for item in samples),
        }
        judged = [item["judge"] for item in samples if "judge" in item]
        valid_judgments = [item for item in judged if item.get("valid")]
        if judged:
            arm_summary.update(
                {
                    "judge_valid_rate": len(valid_judgments) / len(judged),
                    "semantic_pass_rate": (
                        sum(bool(item["passed"]) for item in valid_judgments)
                        / len(valid_judgments)
                        if valid_judgments
                        else None
                    ),
                    "median_semantic_score": (
                        median(item["total_score"] for item in valid_judgments)
                        if valid_judgments
                        else None
                    ),
                    "median_partial_criteria": (
                        median(item["partial_criteria_count"] for item in valid_judgments)
                        if valid_judgments
                        else None
                    ),
                }
            )
        summary[arm] = arm_summary
    return summary


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        comparison: summarize_arms(
            [item for item in results if item["comparison"] == comparison]
        )
        for comparison in sorted({item["comparison"] for item in results})
    }


def markdown_cell(value: Any) -> str:
    if value is None:
        return "—"
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def allocate_run_directory(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    numbers = [
        int(path.name)
        for path in root.iterdir()
        if path.is_dir() and path.name.isdigit()
    ]
    number = max(numbers, default=0) + 1
    while True:
        candidate = root / f"{number:03d}"
        try:
            candidate.mkdir()
            return candidate
        except FileExistsError:
            number += 1


def format_rate(passed: int, total: int) -> str:
    return f"{passed}/{total} ({passed / total:.0%})" if total else "—"


def markdown_report(report: dict[str, Any]) -> str:
    results = report["results"]
    valid_results = [item for item in results if item.get("valid", True)]
    passed = sum(bool(item["passed"]) for item in valid_results)
    valid_judges = [item["judge"] for item in results if item.get("judge", {}).get("valid")]
    judge_passed = sum(bool(item["passed"]) for item in valid_judges)
    lines = [
        "# Comparative evaluation report",
        "",
        f"- Run: **{markdown_cell(report.get('run', 'unknown'))}**",
        f"- Agent: `{markdown_cell(report.get('model'))}` (`{markdown_cell(report.get('reasoning'))}`)",
    ]
    judge = report.get("judge")
    if judge:
        lines.append(
            f"- Judge: `{markdown_cell(judge.get('model'))}` "
            f"(`{markdown_cell(judge.get('reasoning'))}`), calls: {judge.get('calls', 0)}"
        )
    execution_environment = report.get("execution_environment")
    if execution_environment:
        lines.append(
            f"- Execution: `{markdown_cell(execution_environment.get('kind'))}` / "
            f"`{markdown_cell(execution_environment.get('image'))}` / "
            f"`{markdown_cell(execution_environment.get('image_id'))}`"
        )
    lines.extend(
        [
            f"- Valid samples: **{len(valid_results)}/{len(results)}**",
            f"- Overall: **{passed}/{len(valid_results)} valid samples passed**",
            f"- Semantic judgment: **{judge_passed}/{len(valid_judges)} passed**"
            if valid_judges
            else "- Semantic judgment: not available",
            "",
            "## Legend and methodology",
            "",
            "### Arms",
            "",
            "| Arm | Meaning |",
            "|---|---|",
        ]
    )
    present_arms = {item["arm"] for item in results}
    for arm in ARM_ORDER:
        if arm not in present_arms:
            continue
        lines.append(f"| {arm} | {markdown_cell(ARM_DESCRIPTIONS[arm])} |")
    lines.extend(["", "### Comparisons", ""])
    comparison_legend = report.get("comparison_legend", {})
    for comparison in report.get(
        "comparisons", sorted({item["comparison"] for item in results})
    ):
        lines.append(
            f"- `{comparison}` — {markdown_cell(comparison_legend.get(comparison, 'No description recorded.'))}"
        )
    lines.extend(
        [
            "",
            "### Testing process",
            "",
            "1. Every arm/sample starts from the same clean fixture and receives the same user request; only the supplied architectural context differs.",
            "2. Both arms use the same downstream coding agent. All work occurs in isolated temporary workspaces.",
            "3. Mechanical checks cover only objective execution, workspace, context-consumption, and repository-integrity facts; they do not interpret prose or architectural meaning.",
            "4. A blind model judge receives only the submission type, request, diff, final response, and matching frozen semantic rubric—not the arm name or supplied context—and scores each criterion from 0 to 2.",
            "5. Samples that violate the workspace boundary are marked invalid, excluded from aggregates, and not sent to the judge.",
            "6. Overall pass requires both mechanical and semantic pass; file reads, token usage, and duration remain separate efficiency metrics.",
            "",
            "## Results",
            "",
            "### Summary by arm",
            "",
            "Each valid sample has equal weight within its arm.",
            "",
            "| Experiment | Arm | Valid/total | Overall | Mechanics | Semantics | Avg judge | Avg partial criteria | Avg context words | Avg files read | Avg irrelevant reads | Avg total input | Avg cached | Avg uncached | Avg duration |",
            "|---|---|---:|:---:|:---:|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    experiment_order = ("value",)
    for experiment, arm in (
        (experiment, arm) for experiment in experiment_order for arm in ARM_ORDER
    ):
        all_arm_results = [
            item
            for item in results
            if item["arm"] == arm and item.get("experiment", "value") == experiment
        ]
        if not all_arm_results:
            continue
        arm_results = [item for item in all_arm_results if item.get("valid", True)]
        if not arm_results:
            lines.append(
                f"| {experiment} | {arm} | 0/{len(all_arm_results)} | — | — | — | — | — | — | — | — | — | — | — | — |"
            )
            continue
        arm_judges = [
            item["judge"]
            for item in arm_results
            if item.get("judge", {}).get("valid")
        ]
        token_values = [
            item["input_tokens"]
            for item in arm_results
            if item.get("input_tokens") is not None
        ]
        cached_values = [
            item["cached_input_tokens"]
            for item in arm_results
            if item.get("cached_input_tokens") is not None
        ]
        uncached_values = [
            item["input_tokens"] - item["cached_input_tokens"]
            for item in arm_results
            if item.get("input_tokens") is not None
            and item.get("cached_input_tokens") is not None
        ]
        average_score = (
            f"{mean(item['total_score'] for item in arm_judges):.1f}/"
            f"{mean(item['max_score'] for item in arm_judges):.1f}"
            if arm_judges
            else "—"
        )
        lines.append(
            "| "
            + " | ".join(
                markdown_cell(value)
                for value in (
                    experiment,
                    arm,
                    f"{len(arm_results)}/{len(all_arm_results)}",
                    format_rate(sum(bool(item["passed"]) for item in arm_results), len(arm_results)),
                    format_rate(sum(bool(item.get("mechanical_passed", item["passed"])) for item in arm_results), len(arm_results)),
                    format_rate(sum(bool(item["passed"]) for item in arm_judges), len(arm_judges)),
                    average_score,
                    f"{mean(item['partial_criteria_count'] for item in arm_judges):.1f}"
                    if arm_judges
                    else None,
                    f"{mean(item['context_words'] for item in arm_results):.0f}",
                    f"{mean(item['files_read'] for item in arm_results):.1f}",
                    f"{mean(len(item['irrelevant_files_read']) for item in arm_results):.1f}",
                    f"{mean(token_values):.0f}" if token_values else None,
                    f"{mean(cached_values):.0f}" if cached_values else None,
                    f"{mean(uncached_values):.0f}" if uncached_values else None,
                    f"{mean(item['duration_seconds'] for item in arm_results):.1f}s",
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "### Individual results",
            "",
            "| Experiment | Comparison | Arm | Sample | Validity | Overall | Mechanics | Judge | Partial criteria | Context words | Files read | Irrelevant reads | Total input | Cached | Uncached | Duration |",
            "|---|---|---|---:|:---:|:---:|:---:|:---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for item in results:
        item_judge = item.get("judge", {})
        judge_score = (
            f"{item_judge['total_score']}/{item_judge['max_score']}"
            if item_judge.get("valid")
            else "invalid"
            if item_judge
            else "—"
        )
        lines.append(
            "| "
            + " | ".join(
                markdown_cell(value)
                for value in (
                    item.get("experiment", "value"),
                    item["comparison"],
                    item["arm"],
                    item["sample"],
                    "VALID" if item.get("valid", True) else "INVALID",
                    ("PASS" if item["passed"] else "FAIL")
                    if item.get("valid", True)
                    else "—",
                    "PASS" if item.get("mechanical_passed", item["passed"]) else "FAIL",
                    judge_score,
                    item_judge.get("partial_criteria_count") if item_judge.get("valid") else None,
                    item["context_words"],
                    item["files_read"],
                    len(item["irrelevant_files_read"]),
                    item["input_tokens"],
                    item.get("cached_input_tokens"),
                    item["input_tokens"] - item["cached_input_tokens"]
                    if item.get("input_tokens") is not None
                    and item.get("cached_input_tokens") is not None
                    else None,
                    f"{item['duration_seconds']:.1f}s",
                )
            )
            + " |"
        )

    findings: list[str] = []
    for item in results:
        failed_checks = [
            check["message"] for check in item.get("checks", []) if not check.get("passed")
        ]
        item_judge = item.get("judge", {})
        violations = [
            f"{name} ({value['score']}/2): {value['rationale']}"
            for name, value in item_judge.get("scores", {}).items()
            if value["score"] < JUDGE_SCORE_MAX
        ]
        invalid_reasons = item.get("invalid_reasons", [])
        if failed_checks or violations or invalid_reasons:
            findings.extend(["", f"### {item['comparison']} / {item['arm']} / sample {item['sample']}", ""])
            findings.extend(f"- Invalid: {markdown_cell(message)}" for message in invalid_reasons)
            findings.extend(f"- Mechanics: {markdown_cell(message)}" for message in failed_checks)
            findings.extend(f"- Judge: {markdown_cell(message)}" for message in violations)
    if findings:
        lines.extend(["", "## Findings", *findings])
    return "\n".join(lines) + "\n"


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


def judge_settings(results: list[dict[str, Any]]) -> dict[str, str]:
    judgments = [item["judge"] for item in results if "judge" in item]
    models = {
        str(item["actual_model"])
        for item in judgments
        if item.get("actual_model") not in {None, "", "unknown"}
    }
    reasoning_levels = {
        str(item["actual_reasoning"])
        for item in judgments
        if item.get("actual_reasoning") not in {None, "", "unknown"}
    }
    if len(models) > 1:
        raise ValueError(f"inconsistent judge models: {', '.join(sorted(models))}")
    if len(reasoning_levels) > 1:
        raise ValueError(
            f"inconsistent judge reasoning levels: {', '.join(sorted(reasoning_levels))}"
        )
    complete = bool(judgments) and all(
        item.get("actual_model") not in {None, "", "unknown"}
        and item.get("actual_reasoning") not in {None, "", "unknown"}
        for item in judgments
    )
    return {
        "model": next(iter(models)) if complete and models else "unknown",
        "reasoning": next(iter(reasoning_levels)) if complete and reasoning_levels else "unknown",
    }


def execution_environment_settings(results: list[dict[str, Any]]) -> dict[str, str] | None:
    eligible = [item for item in results if item.get("valid", True)]
    environments = [
        item["execution_environment"]
        for item in eligible
        if isinstance(item.get("execution_environment"), dict)
    ]
    if not environments:
        return None
    required = ("kind", "image", "image_id", "source_sha256")
    if any(
        not isinstance(item.get(field), str)
        or not item[field].strip()
        or item[field] == "unknown"
        for item in environments
        for field in required
    ):
        raise ValueError("incomplete execution environment metadata")
    identities = {
        (
            item["kind"],
            item["image"],
            item["image_id"],
            item["source_sha256"],
        )
        for item in environments
    }
    if len(identities) != 1 or len(environments) != len(eligible):
        raise ValueError("inconsistent or missing execution environment metadata")
    kind, image, image_id, source_sha256 = next(iter(identities))
    return {
        "kind": kind,
        "image": image,
        "image_id": image_id,
        "source_sha256": source_sha256,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--comparison", action="append", default=[])
    parser.add_argument(
        "--experiment",
        action="append",
        choices=sorted(EXPERIMENT_ARMS),
        default=[],
        help="select all executable comparisons in an experiment (repeatable)",
    )
    parser.add_argument("--all", action="store_true", help="run every executable comparison")
    parser.add_argument("--agent-command")
    parser.add_argument("--judge-command")
    parser.add_argument("--jobs", type=positive_int, default=8)
    parser.add_argument("--judge-jobs", type=positive_int, default=8)
    parser.add_argument("--samples", type=positive_int, help="override manifest sample count per arm")
    parser.add_argument("--keep-workspace", action="store_true")
    parser.add_argument(
        "--json-output",
        type=Path,
        default=DEFAULT_JSON_OUTPUT,
        help="JSON report filename inside each numbered run (default: comparison-results.json)",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("comparison-results.md"),
        help="write a Markdown table report and suppress per-result terminal output",
    )
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=Path("comparison-runs"),
        help="parent directory for sequentially numbered runs",
    )
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=Path("artifacts"),
        help="artifacts subdirectory inside each numbered run",
    )
    args = parser.parse_args()

    if os.environ.get("SPECSPINE_EVAL_DOCKER_CONTROLLER") != "1":
        parser.error("run comparisons through tests/eval/docker/run-comparisons.sh")

    if args.judge_command and not args.agent_command:
        parser.error("--judge-command requires --agent-command")
    if args.all and (args.comparison or args.experiment):
        parser.error("use --all or explicit --comparison/--experiment selectors")

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
            print(
                f"{item['id']}: {item['status']} / {item['experiment']} "
                f"({item.get('samples', 1)} sample(s) per arm)"
            )
    if args.validate:
        for identifier, errors in validation.items():
            for error in errors:
                print(f"INVALID {identifier}: {error}")
        if not validation:
            print(f"valid comparisons: {len(comparisons)}")
    if args.agent_command:
        if validation:
            return 2
        if not (args.comparison or args.experiment or args.all):
            parser.error("--agent-command requires --all, --experiment, or --comparison")
        selected = comparisons if args.all else [
            item
            for item in comparisons
            if item["id"] in args.comparison or item["experiment"] in args.experiment
        ]
        selected = [item for item in selected if item["status"] == "executable"]
        if not selected:
            print("No selected executable comparisons")
            return 2
        for repository_id in sorted({item["repository"] for item in selected}):
            materialize_repository(repository_id)
        command = shlex.split(args.agent_command)
        run_dir = allocate_run_directory(args.runs_dir)
        artifacts_dir = run_dir / args.artifacts_dir.name
        jobs = [
            (item, arm, sample)
            for item in selected
            for sample in range(1, (args.samples or item.get("samples", 1)) + 1)
            for arm in sorted(item["arms"], key=lambda arm: ARM_ORDER.index(arm["id"]))
        ]
        with ThreadPoolExecutor(max_workers=min(args.jobs, len(jobs))) as executor:
            results = list(
                executor.map(
                    lambda job: run_arm(*job, command, args.keep_workspace, artifacts_dir),
                    jobs,
                )
            )
        if args.judge_command:
            judge_command = shlex.split(args.judge_command)
            comparisons_by_id = {item["id"]: item for item in selected}
            judge_groups: dict[str, list[int]] = {}
            for index, result in enumerate(results):
                if not result.get("valid", True):
                    continue
                comparison = comparisons_by_id[result["comparison"]]
                judge_groups.setdefault(judge_cache_key(result, comparison), []).append(index)
            representative_indices = [indices[0] for indices in judge_groups.values()]
            judgments: list[dict[str, Any]] = []
            if representative_indices:
                with ThreadPoolExecutor(
                    max_workers=min(args.judge_jobs, len(representative_indices))
                ) as executor:
                    judgments = list(
                        executor.map(
                            lambda index: run_judge(
                                results[index],
                                comparisons_by_id[results[index]["comparison"]],
                                judge_command,
                                args.keep_workspace,
                            ),
                            representative_indices,
                        )
                    )
            for (cache_key, indices), judgment in zip(judge_groups.items(), judgments):
                for position, index in enumerate(indices):
                    result = results[index]
                    result["judge"] = {**judgment, "reused": position > 0}
                    result["passed"] = bool(result["mechanical_passed"] and judgment.get("passed"))
                    if position > 0:
                        archive_reused_judgment(
                            result,
                            comparisons_by_id[result["comparison"]],
                            judgment,
                            cache_key,
                            results[indices[0]],
                        )
        try:
            settings = actual_settings(results)
            observed_judge_settings = judge_settings(results) if args.judge_command else None
            observed_environment = execution_environment_settings(results)
        except ValueError as error:
            print(f"INVALID RUN: {error}", file=sys.stderr)
            return 2
        report = {
            **settings,
            "run": run_dir.name,
            "comparisons": [item["id"] for item in selected],
            "experiments": sorted({item["experiment"] for item in selected}),
            "comparison_legend": {
                item["id"]: item["description"] for item in selected
            },
            "summary": summarize(results),
            "results": results,
        }
        if observed_environment is not None:
            report["execution_environment"] = observed_environment
        if observed_judge_settings is not None:
            report["judge"] = {
                **observed_judge_settings,
                "calls": len(judge_groups),
                "results": sum(item.get("valid", True) for item in results),
        }
        if args.json_output:
            (run_dir / args.json_output.name).write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        if args.markdown_output:
            (run_dir / args.markdown_output.name).write_text(
                markdown_report(report), encoding="utf-8"
            )
        # Outcome failures are benchmark data. Execution/judge failures and
        # invalid samples are harness-integrity failures.
        agents_completed = all(item["agent_exit"] == 0 for item in results)
        judges_completed = all(
            item.get("judge", {}).get("valid", False) for item in results
            if item.get("valid", True)
        ) if args.judge_command else True
        samples_valid = all(item.get("valid", True) for item in results)
        return 0 if agents_completed and judges_completed and samples_valid else 1
    if not any((args.list, args.validate)):
        parser.print_help()
    return 2 if validation else 0


if __name__ == "__main__":
    raise SystemExit(main())
