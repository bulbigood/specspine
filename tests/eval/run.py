#!/usr/bin/env python3
"""Dependency-free runner for repeatable SpecSpine agent evaluations."""

from __future__ import annotations

import argparse
import datetime
import fnmatch
import hashlib
import io
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO


ROOT = Path(__file__).resolve().parents[2]
CASES_DIR = Path(__file__).resolve().parent / "cases"
SCENARIOS_DIR = ROOT / "tests" / "scenarios"
CASE_CATEGORIES = {"core", "extended", "expensive", "planned"}
WORKSPACE_BOUNDARY_INSTRUCTIONS = (
    "SECURITY BOUNDARY: the current working directory is the complete and only "
    "authorized project. Never read, list, search, inspect, or infer from any path "
    "outside it, including parent/sibling directories, system temporary directories, "
    "the home directory, and other repositories. Never use `..`, `$HOME`, `~`, or an "
    "absolute path outside the current project to discover context. If required "
    "information is absent, report that it is unavailable. The `.eval` directory "
    "is evaluator-owned: only read `.eval/skill/`, `.eval/companions/`, and an "
    "explicitly instructed `.eval/tools/` command when the "
    "prompt explicitly requires them; never inspect any other `.eval` content.\n"
)
NO_SKILL_BOUNDARY_INSTRUCTIONS = (
    "SECURITY BOUNDARY: the current working directory is the complete and only "
    "authorized project. Never read, list, search, inspect, or infer from any path "
    "outside it, including parent/sibling directories, system temporary directories, "
    "the home directory, and other repositories. Never use `..`, `$HOME`, `~`, or an "
    "absolute path outside the current project to discover context. If required "
    "information is absent, report that it is unavailable. The `.eval` directory is "
    "evaluator-owned and contains no skill for this profile; never inspect it.\n"
)
EXECUTION_PROFILES = {"extract", "fallback", "no-extract"}
SPECSPINE_BEGIN_MARKER = "<!-- specspine:begin -->"
SPECSPINE_END_MARKER = "<!-- specspine:end -->"
SEMANTIC_ID_ERROR_CODES = {
    "DUPLICATE_ID",
    "ID_FRAGMENT",
    "ID_REGION_END",
    "ID_REGION_NESTED",
    "ID_REGION_UNCLOSED",
    "ID_SECTION",
    "INVALID_ID",
    "INVALID_ID_REFERENCE",
    "MULTIPLE_ID_REGIONS",
    "UNRESOLVED_ID",
}
PREFLIGHT_ERROR_CODES = {"INDEX_MISSING", "READ_ERROR", "ROOT_MISSING"}


@dataclass(frozen=True)
class CheckResult:
    passed: bool
    message: str


@dataclass(frozen=True)
class CaseReport:
    case_id: str
    passed: bool
    output: str
    duration_seconds: float
    token_usage: dict[str, int]
    sample_number: int = 1
    agent_runs: tuple[dict[str, Any], ...] = ()
    failed_checks: tuple[dict[str, str], ...] = ()
    started_at: str | None = None
    finished_at: str | None = None
    queue_seconds: float = 0.0
    response: str = ""
    stderr: str = ""


TOKEN_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)


def add_token_usage(total: dict[str, int], trace: dict[str, Any] | None) -> None:
    """Add one agent invocation's cumulative Codex counters to a case total."""
    usage = None if trace is None else trace.get("token_usage")
    if not isinstance(usage, dict):
        return
    for field in TOKEN_FIELDS:
        value = usage.get(field)
        if isinstance(value, int) and not isinstance(value, bool):
            total[field] = total.get(field, 0) + value


def aggregate_token_usage(reports: list[CaseReport]) -> dict[str, int]:
    total: dict[str, int] = {}
    for report in reports:
        for field, value in report.token_usage.items():
            if field in TOKEN_FIELDS and isinstance(value, int) and not isinstance(value, bool):
                total[field] = total.get(field, 0) + value
    return total


def compact_agent_trace(trace: dict[str, Any] | None) -> dict[str, Any]:
    if trace is None:
        return {}
    duration = trace.get("duration_seconds")
    files_read = trace.get("files_read")
    usage = trace.get("token_usage")
    attempts = trace.get("retrieval_attempts")
    event_metrics = trace.get("event_metrics")
    cost_ledger = trace.get("cost_ledger")
    usefulness = trace.get("retrieval_usefulness")
    return {
        "evaluation_profile": trace.get("evaluation_profile"),
        "ranking_system": trace.get("ranking_system"),
        "graph_depth": trace.get("graph_depth"),
        "graph_limit": trace.get("graph_limit"),
        "retrieval_telemetry": trace.get("retrieval_telemetry"),
        "retrieval_profile": trace.get("retrieval_profile"),
        "retrieval_mode": trace.get("retrieval_mode"),
        "retrieval_attempts": attempts if isinstance(attempts, list) else [],
        "retrieval_attempt_count": trace.get("retrieval_attempt_count"),
        "unexpected_retry": bool(trace.get("unexpected_retry", False)),
        "unknown_attempt_count": trace.get("unknown_attempt_count"),
        "event_metrics": event_metrics if isinstance(event_metrics, dict) else {},
        "collab_tool_count": (
            event_metrics.get("collab_tool_count")
            if isinstance(event_metrics, dict)
            else None
        ),
        "spawned_agent_count": (
            event_metrics.get("spawned_agent_count")
            if isinstance(event_metrics, dict)
            else None
        ),
        "cost_ledger": cost_ledger if isinstance(cost_ledger, dict) else {},
        "retrieval_usefulness": usefulness if isinstance(usefulness, dict) else {},
        "duration_seconds": duration if isinstance(duration, (int, float)) else None,
        "started_at": trace.get("started_at"),
        "finished_at": trace.get("finished_at"),
        "environment_invalid": bool(trace.get("environment_invalid", False)),
        "files_read": len(set(map(str, files_read))) if isinstance(files_read, list) else None,
        "file_paths_read": sorted(set(map(str, files_read))) if isinstance(files_read, list) else [],
        "model": trace.get("model"),
        "reasoning_effort": trace.get("reasoning_effort"),
        "subagent_model": trace.get("subagent_model"),
        "subagent_reasoning_effort": trace.get("subagent_reasoning_effort"),
        "cache_scope": trace.get("cache_scope"),
        "runtime": trace.get("runtime") if isinstance(trace.get("runtime"), dict) else {},
        "environment_errors": trace.get("environment_errors", []),
        "scope_violations": trace.get("scope_violations", []),
        "token_usage": {
            field: value
            for field, value in (usage.items() if isinstance(usage, dict) else ())
            if field in TOKEN_FIELDS and isinstance(value, int) and not isinstance(value, bool)
        },
    }


def directory_digest(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(
        candidate for candidate in path.rglob("*")
        if candidate.is_file()
        and "__pycache__" not in candidate.relative_to(path).parts
        and candidate.suffix != ".pyc"
    ):
        digest.update(item.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def case_fingerprint(case: dict[str, Any]) -> str:
    case = {key: value for key, value in case.items() if key != "_execution_profile"}
    manifest = {key: value for key, value in case.items() if not key.startswith("_")}
    prompts = (
        [build_prompt(case, stage) for stage in case.get("stages", []) if "skill" in stage]
        if "stages" in case
        else [build_prompt(case)]
    )
    skill_paths = {case["skill"]} if "skill" in case else {
        stage["skill"] for stage in case.get("stages", []) if "skill" in stage
    }
    companion_paths = set(case.get("companion_skills", []))
    for stage in case.get("stages", []):
        companion_paths.update(stage.get("companion_skills", []))
    payload = {
        "manifest": manifest,
        "prompts": prompts,
        "initial_tree": (
            directory_digest(ROOT / case["initial_tree"])
            if case.get("initial_tree")
            else None
        ),
        "skills": {path: directory_digest(ROOT / path) for path in sorted(skill_paths)},
        "companions": {
            path: directory_digest(ROOT / path) for path in sorted(companion_paths)
        },
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def write_json_report(
    path: Path,
    label: str,
    agent_command: str,
    reports: list[CaseReport],
    cases: list[dict[str, Any]],
    samples_requested: int,
    jobs: int,
    *,
    run_id: str | None = None,
    started_at: str | None = None,
    finished_at: str | None = None,
) -> None:
    case_by_id = {case["id"]: case for case in cases}
    samples: list[dict[str, Any]] = []
    for report in sorted(reports, key=lambda item: (item.case_id, item.sample_number)):
        durations = [
            run.get("duration_seconds")
            for run in report.agent_runs
            if isinstance(run.get("duration_seconds"), (int, float))
        ]
        samples.append(
            {
                "agent_duration_seconds": sum(durations) if durations else None,
                "agent_runs": list(report.agent_runs),
                "case_duration_seconds": report.duration_seconds,
                "case_id": report.case_id,
                "environment_valid": bool(report.agent_runs)
                and not any(run.get("environment_invalid") for run in report.agent_runs),
                "passed": report.passed,
                "failed_checks": list(report.failed_checks),
                "sample_number": report.sample_number,
                "token_usage": report.token_usage,
                "started_at": report.started_at,
                "finished_at": report.finished_at,
                "queue_seconds": report.queue_seconds,
                "diagnostics": {
                    "response": report.response[:20_000],
                    "stderr": report.stderr[:4_000],
                },
            }
        )
    command_fingerprints: dict[str, str] = {}
    for part in shlex.split(agent_command):
        candidate = Path(part).expanduser()
        if candidate.is_file():
            command_fingerprints[str(candidate.resolve())] = hashlib.sha256(
                candidate.read_bytes()
            ).hexdigest()
    payload = {
        "agent_command": agent_command,
        "cases": {
            case_id: {
                "fingerprint": case_fingerprint(case_by_id[case_id]),
                **(
                    {"handoff_judgments": case_by_id[case_id]["handoff_judgments"]}
                    if "handoff_judgments" in case_by_id[case_id]
                    else {}
                ),
            }
            for case_id in sorted({report.case_id for report in reports})
        },
        "jobs": jobs,
        "label": label,
        "samples": samples,
        "samples_requested": samples_requested,
        "schema_version": 2,
        "run": {
            "run_id": run_id or str(uuid.uuid4()),
            "started_at": started_at,
            "finished_at": finished_at,
            "execution_profile": sorted({execution_profile(case) for case in cases}),
            "prompt_fingerprints": {
                case["id"]: hashlib.sha256(
                    build_prompt(case).encode("utf-8")
                ).hexdigest()
                for case in cases
                if "stages" not in case
            },
        },
        "runtime": {
            "python": platform.python_version(),
            "platform": sys.platform,
        },
        "fingerprints": {
            "runner": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "agent_command_files": command_fingerprints,
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def format_token_usage(token_usage: dict[str, int]) -> str:
    if not token_usage:
        return "Codex tokens unavailable"
    total = token_usage.get("total_tokens")
    if total is None:
        total = token_usage.get("input_tokens", 0) + token_usage.get("output_tokens", 0)
    parts = [f"total {total}"]
    if "input_tokens" in token_usage:
        value = f"input {token_usage['input_tokens']}"
        if "cached_input_tokens" in token_usage:
            value += f" (cached {token_usage['cached_input_tokens']})"
        if "cache_write_input_tokens" in token_usage:
            value += f" (cache write {token_usage['cache_write_input_tokens']})"
        parts.append(value)
    if "output_tokens" in token_usage:
        value = f"output {token_usage['output_tokens']}"
        if "reasoning_output_tokens" in token_usage:
            value += f" (reasoning {token_usage['reasoning_output_tokens']})"
        parts.append(value)
    return f"Codex tokens: {'; '.join(parts)}"


def format_metrics(duration_seconds: float, token_usage: dict[str, int]) -> str:
    return f"case time: {duration_seconds:.3f}s; {format_token_usage(token_usage)}"


def format_stage_metrics(trace: dict[str, Any]) -> str:
    duration = trace.get("duration_seconds")
    duration_text = f"{duration:.3f}s" if isinstance(duration, (int, float)) else "unavailable"
    usage = trace.get("token_usage")
    token_text = format_token_usage(usage if isinstance(usage, dict) else {})
    commands = trace.get("commands")
    reads = trace.get("files_read")
    command_count = len(commands) if isinstance(commands, list) else 0
    read_count = len(set(str(item) for item in reads)) if isinstance(reads, list) else 0
    return (
        f"stage time: {duration_text}; {token_text}; "
        f"commands {command_count}; files read {read_count}"
    )


def summarized_values(values: list[str], maximum: int = 80) -> str:
    rendered = ", ".join(repr(value) for value in values)
    return rendered if len(rendered) <= maximum else rendered[: maximum - 3] + "..."


def load_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for path in sorted(CASES_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        data["_manifest"] = path
        cases.append(data)
    return cases


def validate_case(case: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {"id", "scenario", "status", "category"}
    missing = sorted(required - case.keys())
    if missing:
        errors.append(f"missing fields: {', '.join(missing)}")
        return errors
    fixture_fields = [field for field in ("initial_files", "initial_tree") if field in case]
    if len(fixture_fields) != 1:
        errors.append("case requires exactly one of initial_files or initial_tree")
    if case["status"] not in {"executable", "planned"}:
        errors.append("status must be executable or planned")
    if case.get("category") not in CASE_CATEGORIES:
        errors.append(f"category must be one of: {', '.join(sorted(CASE_CATEGORIES))}")
    if case.get("status") == "planned" and case.get("category") != "planned":
        errors.append("planned cases must use category planned")
    if case.get("status") == "executable" and case.get("category") == "planned":
        errors.append("executable cases cannot use category planned")
    if not isinstance(case.get("runs", 1), int) or case.get("runs", 1) < 1:
        errors.append("runs must be a positive integer")
    judgments = case.get("handoff_judgments")
    if judgments is not None:
        if not isinstance(judgments, dict):
            errors.append("handoff_judgments must be an object")
        else:
            allowed = {"required", "supporting", "relevant", "hard_negatives"}
            unexpected = sorted(set(judgments) - allowed)
            if unexpected:
                errors.append(
                    "handoff_judgments has unsupported fields: "
                    + ", ".join(unexpected)
                )
            for field in sorted(allowed):
                values = judgments.get(field, [])
                if (
                    not isinstance(values, list)
                    or any(not isinstance(value, str) or not value for value in values)
                    or len(values) != len(set(values))
                ):
                    errors.append(
                        f"handoff_judgments.{field} must be a unique string list"
                    )
            required = set(judgments.get("required", []))
            supporting = set(judgments.get("supporting", []))
            relevant = set(judgments.get("relevant", []))
            hard_negatives = set(judgments.get("hard_negatives", []))
            if not required:
                errors.append("handoff_judgments.required must not be empty")
            if not required | supporting <= relevant:
                errors.append(
                    "handoff_judgments.relevant must contain required and supporting paths"
                )
            overlap = relevant & hard_negatives
            if overlap:
                errors.append(
                    "handoff_judgments relevant/hard-negative overlap: "
                    + ", ".join(sorted(overlap))
                )
    scenario = ROOT / case["scenario"]
    if not scenario.is_file():
        errors.append(f"scenario does not exist: {case['scenario']}")
    stages = case.get("stages")
    if stages is not None:
        if not isinstance(stages, list) or not stages:
            errors.append("stages must be a non-empty list")
        else:
            stage_ids = [stage.get("id") for stage in stages if isinstance(stage, dict)]
            duplicates = sorted({value for value in stage_ids if value and stage_ids.count(value) > 1})
            for value in duplicates:
                errors.append(f"duplicate stage id: {value}")
            for index, stage in enumerate(stages, 1):
                errors.extend(validate_stage(stage, index))
        assertion_count = len(case.get("final_assertions", [])) + sum(
            len(stage.get("assertions", [])) for stage in stages if isinstance(stage, dict)
        ) if isinstance(stages, list) else 0
        if case["status"] == "executable" and not assertion_count:
            errors.append("executable staged case has no assertions")
    else:
        if "skill" not in case or "assertions" not in case:
            errors.append("non-staged case requires skill and assertions")
        else:
            errors.extend(validate_skill(case["skill"], case.get("entrypoint", "SKILL.md"), case.get("companion_skills", [])))
            if case["status"] == "executable" and not case["assertions"]:
                errors.append("executable case has no assertions")
        if "prompt" not in case and scenario.is_file():
            try:
                scenario_user_request(case)
            except ValueError as error:
                errors.append(str(error))
    assertions = list(case.get("assertions", [])) + list(case.get("final_assertions", []))
    if isinstance(stages, list):
        assertions.extend(
            assertion
            for stage in stages
            if isinstance(stage, dict)
            for assertion in stage.get("assertions", [])
        )
    for index, assertion in enumerate(assertions, 1):
        profiles = assertion.get("profiles") if isinstance(assertion, dict) else None
        if profiles is not None and (
            not isinstance(profiles, list)
            or not profiles
            or any(profile not in EXECUTION_PROFILES for profile in profiles)
        ):
            errors.append(
                f"assertion {index} profiles must be a non-empty subset of: "
                f"{', '.join(sorted(EXECUTION_PROFILES))}"
            )
        condition = assertion.get("when_trace") if isinstance(assertion, dict) else None
        if condition is not None and (not isinstance(condition, dict) or not condition):
            errors.append(f"assertion {index} when_trace must be a non-empty object")
    for rel in case.get("initial_files", {}):
        if not safe_relative_path(rel):
            errors.append(f"unsafe initial file path: {rel}")
    initial_tree = case.get("initial_tree")
    if initial_tree is not None:
        if not isinstance(initial_tree, str) or not safe_relative_path(initial_tree):
            errors.append(f"unsafe initial tree path: {initial_tree}")
        elif not (ROOT / initial_tree).is_dir():
            errors.append(f"initial tree does not exist: {initial_tree}")
        elif (ROOT / initial_tree / "specspine" / "README.md").is_file():
            errors.extend(validate_agent_bootstrap(ROOT / initial_tree, "specspine"))
    return errors


def validate_agent_bootstrap(root: Path, spine_root: str) -> list[str]:
    path = root / "AGENTS.md"
    if not path.is_file():
        return [f"benchmark fixture is missing agent bootstrap: {path}"]
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return [f"cannot read benchmark agent bootstrap {path}: {error}"]
    errors: list[str] = []
    if content.count(SPECSPINE_BEGIN_MARKER) != 1 or content.count(
        SPECSPINE_END_MARKER
    ) != 1:
        errors.append(f"benchmark agent bootstrap markers are invalid: {path}")
    if "{{" in content or "}}" in content:
        errors.append(f"benchmark agent bootstrap has unresolved placeholders: {path}")
    if f"{spine_root}/README.md" not in content:
        errors.append(f"benchmark agent bootstrap has the wrong index path: {path}")
    return errors


def safe_relative_path(value: str) -> bool:
    path = Path(value)
    return bool(value) and not path.is_absolute() and ".." not in path.parts


def validate_skill(skill: str, entrypoint: str, companions: list[str]) -> list[str]:
    errors: list[str] = []
    if not (ROOT / skill / entrypoint).is_file():
        errors.append(f"evaluation entrypoint does not exist: {skill}/{entrypoint}")
    for companion in companions:
        if not (ROOT / companion / "SKILL.md").is_file():
            errors.append(f"companion skill does not exist: {companion}")
    return errors


def validate_stage(stage: Any, index: int) -> list[str]:
    label = f"stage {index}"
    if not isinstance(stage, dict):
        return [f"{label} must be an object"]
    errors: list[str] = []
    if not stage.get("id"):
        errors.append(f"{label} requires id")
    agent_stage = "skill" in stage
    fixture_stage = "fixture" in stage
    if agent_stage == fixture_stage:
        errors.append(f"{label} must define exactly one of skill or fixture")
        return errors
    if agent_stage:
        if not isinstance(stage.get("prompt"), str) or not stage["prompt"].strip():
            errors.append(f"{label} agent stage requires prompt")
        errors.extend(
            validate_skill(
                stage["skill"],
                stage.get("entrypoint", "SKILL.md"),
                stage.get("companion_skills", []),
            )
        )
    else:
        fixture = stage["fixture"]
        if not isinstance(fixture, dict):
            errors.append(f"{label} fixture must be an object")
            return errors
        unknown = sorted(set(fixture) - {"write_files", "remove_files"})
        if unknown:
            errors.append(f"{label} fixture has unknown operations: {', '.join(unknown)}")
        for rel in list(fixture.get("write_files", {})) + list(fixture.get("remove_files", [])):
            if not safe_relative_path(rel):
                errors.append(f"{label} has unsafe fixture path: {rel}")
    return errors


def validate_collection(cases: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for field in ("id", "scenario"):
        values = [case.get(field) for case in cases]
        duplicates = sorted({value for value in values if value is not None and values.count(value) > 1})
        for value in duplicates:
            errors.append(f"duplicate {field}: {value}")
    return errors


def scenario_coverage(cases: list[dict[str, Any]]) -> tuple[set[str], set[str], set[str]]:
    documented = {str(path.relative_to(ROOT)) for path in SCENARIOS_DIR.glob("*.md")}
    registered = {case["scenario"] for case in cases}
    executable = {case["scenario"] for case in cases if case["status"] == "executable"}
    return documented, registered, executable


def execution_profile(case: dict[str, Any]) -> str:
    return str(case.get("_execution_profile", "extract"))


def active_assertions(
    assertions: list[dict[str, Any]], case: dict[str, Any]
) -> list[dict[str, Any]]:
    profile = execution_profile(case)
    return [
        assertion
        for assertion in assertions
        if "profiles" not in assertion or profile in assertion["profiles"]
    ]


def write_fixture(case: dict[str, Any], workspace: Path) -> None:
    initial_tree = case.get("initial_tree")
    if initial_tree:
        shutil.copytree(ROOT / initial_tree, workspace, dirs_exist_ok=True)
    for rel, content in case.get("initial_files", {}).items():
        path = workspace / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    (workspace / ".eval").mkdir(exist_ok=True)
    if "stages" not in case and execution_profile(case) != "no-extract":
        install_stage_skill(case, workspace)


def install_stage_skill(stage: dict[str, Any], workspace: Path) -> None:
    skill_target = workspace / ".eval" / "skill"
    companions_target = workspace / ".eval" / "companions"
    if skill_target.exists():
        shutil.rmtree(skill_target)
    if companions_target.exists():
        shutil.rmtree(companions_target)
    shutil.copytree(ROOT / stage["skill"], skill_target)
    for companion in stage.get("companion_skills", []):
        companion_source = ROOT / companion
        shutil.copytree(companion_source, companions_target / companion_source.name)


def apply_fixture_mutation(fixture: dict[str, Any], workspace: Path) -> None:
    for rel, content in fixture.get("write_files", {}).items():
        path = workspace / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    for rel in fixture.get("remove_files", []):
        path = workspace / rel
        if path.is_file() or path.is_symlink():
            path.unlink()


def snapshot(workspace: Path) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for path in workspace.rglob("*"):
        if path.is_file() and not {".eval", ".git"}.intersection(
            path.relative_to(workspace).parts
        ):
            result[str(path.relative_to(workspace))] = path.read_bytes()
    return result


def changed_paths(before: dict[str, bytes], after: dict[str, bytes]) -> set[str]:
    return {path for path in before.keys() | after.keys() if before.get(path) != after.get(path)}


def matches_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def markdown_h2_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    fence: str | None = None
    for line in text.splitlines():
        fence_match = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence_match:
            marker = fence_match.group(1)
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            continue
        if fence is not None:
            continue
        heading = re.match(r"^ {0,3}##(?:[ \t]+(.*)|[ \t]*)$", line)
        if heading:
            value = re.sub(r"[ \t]+#+[ \t]*$", "", heading.group(1) or "").strip()
            current = value.casefold()
            sections.setdefault(current, [])
        elif current is not None:
            sections[current].append(line)
    return {heading: "\n".join(lines).strip() for heading, lines in sections.items()}


def markdown_files(workspace: Path, glob: str = "**/*.md") -> list[Path]:
    return [path for path in workspace.glob(glob) if path.is_file() and ".eval" not in path.parts]


def project_files(workspace: Path, glob: str) -> list[Path]:
    return [
        path
        for path in workspace.glob(glob)
        if path.is_file() and ".eval" not in path.relative_to(workspace).parts
    ]


def doctor_findings(workspace: Path, spine_path: str = "specspine") -> tuple[list[dict[str, Any]] | None, str]:
    checker = ROOT / "skills" / "specspine-doctor" / "scripts" / "check_spine.py"
    completed = subprocess.run(
        [sys.executable, str(checker), str(workspace / spine_path), "--json"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    try:
        findings = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None, f"Doctor checker returned invalid JSON: {completed.stderr.strip()}"
    if not isinstance(findings, list):
        return None, "Doctor checker returned a non-list JSON result"
    return findings, ""


def check_doctor_findings(
    workspace: Path,
    assertion: dict[str, Any],
    *,
    selected_codes: set[str] | None = None,
    check_name: str = "spine_mechanical_valid",
    success_message: str = "spine_mechanical_valid: no unexpected Doctor errors",
) -> CheckResult:
    spine_path = assertion.get("path")
    if spine_path is None:
        glob = assertion.get("glob", "specspine/**/*.md")
        spine_path = glob.split("*", 1)[0].rstrip("/") or "specspine"
    findings, error = doctor_findings(workspace, spine_path)
    if findings is None:
        return CheckResult(False, error)
    allowed = set(assertion.get("allowed_codes", []))
    forbidden = set(assertion.get("forbidden_codes", []))
    unexpected = []
    for item in findings:
        code = str(item.get("code", ""))
        if code in forbidden or (
            item.get("severity") == "error"
            and code not in allowed
            and (selected_codes is None or code in selected_codes)
        ):
            unexpected.append(f"{code}:{item.get('path')}")
    return CheckResult(
        not unexpected,
        f"{check_name}: unexpected Doctor findings: {unexpected}"
        if unexpected
        else success_message,
    )


def evaluate_assertion(
    assertion: dict[str, Any],
    workspace: Path,
    before: dict[str, bytes],
    after: dict[str, bytes],
    response: str,
    trace: dict[str, Any] | None,
) -> CheckResult:
    trace_condition = assertion.get("when_trace")
    if trace_condition is not None:
        if not isinstance(trace_condition, dict) or not trace_condition:
            raise ValueError("when_trace must be a non-empty object")
        if trace is None:
            return CheckResult(False, "conditional assertion requires an agent trace")
        mismatches = {
            field: {"expected": expected, "actual": trace.get(field)}
            for field, expected in trace_condition.items()
            if trace.get(field) != expected
        }
        if mismatches:
            return CheckResult(True, f"assertion not applicable for trace: {mismatches}")
    kind = assertion["type"]
    changed = changed_paths(before, after)
    path = workspace / assertion.get("path", "")
    if kind == "path_exists":
        return CheckResult(path.exists(), f"exists: {assertion['path']}")
    if kind == "path_exists_any":
        existing = [item for item in assertion["paths"] if (workspace / item).exists()]
        return CheckResult(bool(existing), f"existing alternatives: {existing}" if existing else f"none exist: {assertion['paths']}")
    if kind == "path_absent":
        return CheckResult(not path.exists(), f"absent: {assertion['path']}")
    if kind == "glob_count":
        count = len(project_files(workspace, assertion["glob"]))
        minimum = assertion.get("min", 0)
        maximum = assertion.get("max", sys.maxsize)
        return CheckResult(minimum <= count <= maximum, f"{assertion['glob']}: {count}, expected {minimum}..{maximum}")
    if kind == "word_budget":
        if "path" in assertion:
            files = [path] if path.is_file() else []
            target = assertion["path"]
        else:
            files = project_files(workspace, assertion["glob"])
            target = assertion["glob"]
        if not files:
            return CheckResult(False, f"word budget matched no files: {target}")
        counts = {
            str(item.relative_to(workspace)): len(item.read_text(encoding="utf-8").split())
            for item in files
        }
        total = sum(counts.values())
        maximum_each = assertion.get("max_each", sys.maxsize)
        maximum_total = assertion.get("max_total", sys.maxsize)
        oversized = {name: count for name, count in counts.items() if count > maximum_each}
        passed = not oversized and total <= maximum_total
        details = f"word counts: {counts}; total: {total}, maximum total: {maximum_total}"
        if oversized:
            details += f"; over per-file maximum {maximum_each}: {oversized}"
        return CheckResult(passed, details)
    if kind == "glob_contains":
        files = project_files(workspace, assertion["glob"])
        content = "\n".join(path.read_text(encoding="utf-8") for path in files)
        needles = assertion.get("values", [assertion.get("value", "")])
        missing = [needle for needle in needles if needle not in content]
        return CheckResult(
            not missing,
            f"glob_contains {assertion['glob']} missing: {summarized_values(missing)}"
            if missing
            else f"glob_contains {assertion['glob']}: found {summarized_values(needles)}",
        )
    if kind == "file_contains":
        content = path.read_text(encoding="utf-8") if path.is_file() else ""
        needles = assertion.get("values", [assertion.get("value", "")])
        missing = [needle for needle in needles if needle not in content]
        return CheckResult(
            not missing,
            f"file_contains {assertion['path']} missing: {summarized_values(missing)}"
            if missing
            else f"file_contains {assertion['path']}: found {summarized_values(needles)}",
        )
    if kind == "file_contains_any":
        content = path.read_text(encoding="utf-8") if path.is_file() else ""
        needles = assertion["values"]
        found = [needle for needle in needles if needle in content]
        return CheckResult(
            bool(found),
            f"file_contains_any {assertion['path']}: found {summarized_values(found)}"
            if found
            else f"file_contains_any {assertion['path']} missing alternatives: {summarized_values(needles)}",
        )
    if kind == "file_not_contains":
        content = path.read_text(encoding="utf-8") if path.is_file() else ""
        needles = assertion.get("values", [assertion.get("value", "")])
        found = [needle for needle in needles if needle in content]
        return CheckResult(
            not found,
            f"file_not_contains {assertion['path']} found forbidden: {summarized_values(found)}"
            if found
            else f"file_not_contains {assertion['path']}: absent {summarized_values(needles)}",
        )
    if kind == "response_contains":
        needles = assertion.get("values", [assertion.get("value", "")])
        missing = [needle for needle in needles if needle.lower() not in response.lower()]
        return CheckResult(not missing, f"response missing: {missing}" if missing else "response contains required text")
    if kind == "response_contains_any":
        needles = assertion["values"]
        found = [needle for needle in needles if needle.lower() in response.lower()]
        return CheckResult(
            bool(found),
            f"response missing every alternative: {needles}"
            if not found
            else f"response contains alternative: {found[0]!r}",
        )
    if kind == "response_not_contains":
        needles = assertion.get("values", [assertion.get("value", "")])
        found = [needle for needle in needles if needle.lower() in response.lower()]
        return CheckResult(not found, f"response contains forbidden text: {found}" if found else "forbidden response text absent")
    if kind == "response_section_contains":
        section = assertion["section"]
        content = markdown_h2_sections(response).get(section.casefold())
        if content is None:
            return CheckResult(False, f"response section missing: {section}")
        needles = assertion.get("values", [assertion.get("value", "")])
        missing = [needle for needle in needles if needle.casefold() not in content.casefold()]
        return CheckResult(
            not missing,
            f"response section {section} missing: {missing}"
            if missing
            else f"response section {section} contains required values",
        )
    if kind == "response_sections_only":
        headings = set(markdown_h2_sections(response))
        allowed = {heading.casefold() for heading in assertion["sections"]}
        unexpected = sorted(headings - allowed)
        return CheckResult(
            not unexpected,
            f"unexpected response sections: {unexpected}"
            if unexpected
            else "response sections stay within the contract",
        )
    if kind == "response_word_budget":
        count = len(response.split())
        maximum = assertion["max"]
        return CheckResult(count <= maximum, f"response words: {count}, maximum: {maximum}")
    if kind == "trace_equals":
        if trace is None:
            return CheckResult(False, "agent did not produce a trace")
        field = assertion["field"]
        expected = assertion["value"]
        actual = trace.get(field)
        return CheckResult(actual == expected, f"trace {field}: {actual!r}, expected: {expected!r}")
    if kind == "unchanged":
        patterns = assertion["paths"]
        violations = sorted(item for item in changed if matches_any(item, patterns))
        return CheckResult(not violations, f"unexpected changes: {violations}" if violations else "protected paths unchanged")
    if kind == "changed_only":
        patterns = assertion["paths"]
        violations = sorted(item for item in changed if not matches_any(item, patterns))
        return CheckResult(not violations, f"changes outside allowed paths: {violations}" if violations else "changes stay in allowed paths")
    if kind == "max_changed_files":
        maximum = assertion["max"]
        return CheckResult(len(changed) <= maximum, f"changed files: {len(changed)}, maximum: {maximum}")
    if kind == "command_succeeds":
        command = assertion["command"]
        completed = subprocess.run(
            command,
            cwd=workspace,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=assertion.get("timeout_seconds", 60),
            check=False,
        )
        output = completed.stdout.strip()
        message = f"command exit {completed.returncode}: {' '.join(command)}"
        if output and completed.returncode:
            message += f"\n{output}"
        return CheckResult(completed.returncode == 0, message)
    if kind in {"read_only", "read_includes", "max_files_read"}:
        if trace is None or not isinstance(trace.get("files_read"), list):
            return CheckResult(False, "agent did not produce .eval/trace.json with files_read")
        files_read = [str(item) for item in trace["files_read"]]
        if kind == "read_only":
            violations = sorted(item for item in files_read if not matches_any(item, assertion["paths"]))
            return CheckResult(not violations, f"reads outside allowed paths: {violations}" if violations else "reads stay in allowed paths")
        if kind == "read_includes":
            missing = sorted(pattern for pattern in assertion["paths"] if not any(fnmatch.fnmatch(item, pattern) for item in files_read))
            return CheckResult(not missing, f"required reads missing: {missing}" if missing else "required files were read")
        maximum = assertion["max"]
        return CheckResult(len(set(files_read)) <= maximum, f"files read: {len(set(files_read))}, maximum: {maximum}")
    if kind == "command_includes":
        if trace is None or not isinstance(trace.get("commands"), list):
            return CheckResult(False, "agent did not produce .eval/trace.json with commands")
        commands = [str(item) for item in trace["commands"]]
        needles = assertion.get("values", [assertion.get("value", "")])
        missing = [needle for needle in needles if not any(needle in command for command in commands)]
        return CheckResult(not missing, f"command text missing: {missing}" if missing else "required command text found")
    if kind == "command_excludes":
        if trace is None or not isinstance(trace.get("commands"), list):
            return CheckResult(False, "agent did not produce .eval/trace.json with commands")
        commands = [str(item) for item in trace["commands"]]
        needles = assertion.get("values", [assertion.get("value", "")])
        found = [needle for needle in needles if any(needle in command for command in commands)]
        return CheckResult(not found, f"forbidden command text found: {found}" if found else "forbidden command text absent")
    if kind in {
        "collab_spawn_count",
        "collab_initial_spawn_count",
        "collab_spawn_prompts",
        "collab_refill_before_staging_consume",
        "collab_targets_spawned_agents",
    }:
        if trace is None or not isinstance(trace.get("collab_calls"), list):
            return CheckResult(
                False, "agent did not produce a trace with collab_calls"
            )
        all_calls = [
            item for item in trace["collab_calls"] if isinstance(item, dict)
        ]
        calls = [
            item
            for item in all_calls
            if item.get("status") == "completed"
        ]
        spawns = [item for item in calls if item.get("tool") == "spawn_agent"]
        if kind == "collab_spawn_count":
            minimum = assertion.get("min", 0)
            maximum = assertion.get("max", sys.maxsize)
            count = len(spawns)
            return CheckResult(
                minimum <= count <= maximum,
                f"completed spawn calls: {count}, expected {minimum}..{maximum}",
            )
        if kind == "collab_initial_spawn_count":
            first_wait = next(
                (index for index, item in enumerate(calls) if item.get("tool") == "wait"),
                len(calls),
            )
            count = sum(
                item.get("tool") == "spawn_agent" for item in calls[:first_wait]
            )
            minimum = assertion.get("min", 0)
            maximum = assertion.get("max", sys.maxsize)
            return CheckResult(
                minimum <= count <= maximum,
                f"spawn calls before first wait: {count}, expected {minimum}..{maximum}",
            )
        if kind == "collab_spawn_prompts":
            prompts = [str(item.get("prompt") or "") for item in spawns]
            every = assertion.get("each_contains", [])
            forbidden = assertion.get("none_contains", [])
            collective = assertion.get("collectively_contain", [])
            partition = assertion.get("partition_values", [])
            partition_after = assertion.get("partition_after")
            maximum_per_partition = assertion.get("max_per_partition", 1)
            missing_each = [
                value
                for value in every
                if any(value not in prompt for prompt in prompts)
            ]
            present_forbidden = [
                value
                for value in forbidden
                if any(value in prompt for prompt in prompts)
            ]
            combined = "\n".join(prompts)
            missing_collective = [
                value for value in collective if value not in combined
            ]
            partition_prompts = [
                (
                    prompt.split(partition_after, 1)[1]
                    if partition_after and partition_after in prompt
                    else prompt
                )
                for prompt in prompts
            ]
            partition_counts = {
                value: sum(value in prompt for prompt in partition_prompts)
                for value in partition
            }
            prompt_partition_counts = [
                sum(value in prompt for value in partition)
                for prompt in partition_prompts
            ]
            partition_valid = (
                not partition
                or (
                    all(
                        1 <= count <= maximum_per_partition
                        for count in partition_counts.values()
                    )
                    and all(count == 1 for count in prompt_partition_counts)
                )
            )
            passed = (
                bool(prompts)
                and not missing_each
                and not present_forbidden
                and not missing_collective
                and partition_valid
            )
            return CheckResult(
                passed,
                (
                    f"spawn prompts missing per-prompt {missing_each}; "
                    f"contain forbidden {present_forbidden}; "
                    f"missing collectively {missing_collective}; "
                    f"partition counts {partition_counts}, "
                    f"per-prompt partition counts {prompt_partition_counts}"
                )
                if not passed
                else "spawn prompts contain required mapper handoff context",
            )
        if kind == "collab_targets_spawned_agents":
            spawned_ids = {
                str(receiver)
                for item in spawns
                for receiver in item.get("receiver_thread_ids", [])
            }
            targeted = [
                (str(item.get("tool")), str(receiver))
                for item in all_calls
                if item.get("tool") in {"wait", "send_input", "close_agent"}
                for receiver in item.get("receiver_thread_ids", [])
            ]
            unknown = [
                f"{tool}:{receiver}"
                for tool, receiver in targeted
                if receiver not in spawned_ids
            ]
            return CheckResult(
                bool(targeted) and not unknown,
                (
                    f"collaboration calls target unknown agent IDs: {unknown}"
                    if unknown
                    else (
                        f"all {len(targeted)} targeted collaboration calls use "
                        "successful spawn IDs"
                        if targeted
                        else "no targeted collaboration calls found"
                    )
                ),
            )
        activity = trace.get("activity")
        if not isinstance(activity, list):
            return CheckResult(False, "agent trace has no ordered activity")
        staging_path = assertion["path"]
        refill_observed = False
        violations: list[str] = []
        for index, item in enumerate(activity):
            if not isinstance(item, dict) or item.get("kind") != "collab":
                continue
            states = item.get("agents_states", {})
            completed_wait = (
                item.get("tool") == "wait"
                and isinstance(states, dict)
                and any(
                    isinstance(state, dict) and state.get("status") == "completed"
                    for state in states.values()
                )
            )
            if not completed_wait:
                continue
            next_spawn = next(
                (
                    later
                    for later in range(index + 1, len(activity))
                    if isinstance(activity[later], dict)
                    and activity[later].get("kind") == "collab"
                    and activity[later].get("tool") == "spawn_agent"
                    and activity[later].get("status") == "completed"
                ),
                None,
            )
            if next_spawn is None:
                continue
            refill_observed = True
            for between in activity[index + 1 : next_spawn]:
                if (
                    not isinstance(between, dict)
                    or between.get("kind") not in {"command_started", "command"}
                ):
                    continue
                command = str(between.get("command") or "")
                if staging_path not in command:
                    continue
                consumes = bool(
                    re.search(r"(?:^|[;&|]\s*|\s)(?:cat|sed|head|tail|awk|mv|cp|install)\b", command)
                    or (
                        re.search(r"(?:^|\s)rg\b", command)
                        and not re.search(r"\brg\b[^;&|]*\s--files(?:\s|$)", command)
                    )
                )
                if consumes:
                    violations.append(command[:300])
        return CheckResult(
            refill_observed and not violations,
            (
                f"staging consumed before refill: {violations}"
                if violations
                else "replacement spawn precedes staging consumption"
                if refill_observed
                else "no completed-worker refill transition was observed"
            ),
        )
    if kind == "balanced_markers":
        content = path.read_text(encoding="utf-8") if path.is_file() else ""
        begin, end = assertion["begin"], assertion["end"]
        passed = content.count(begin) == content.count(end) == assertion.get("count", 1)
        return CheckResult(passed, f"marker counts: {content.count(begin)}/{content.count(end)}")
    if kind == "no_template_placeholders":
        failures = []
        for item in project_files(workspace, assertion["glob"]):
            if re.search(r"\{\{[^{}]+\}\}", item.read_text(encoding="utf-8")):
                failures.append(str(item.relative_to(workspace)))
        target = assertion["glob"]
        return CheckResult(
            not failures,
            f"{target} unresolved placeholders: {failures}"
            if failures
            else f"{target}: no unresolved placeholders",
        )
    if kind == "markdown_links_valid":
        return check_doctor_findings(
            workspace,
            assertion,
            selected_codes=PREFLIGHT_ERROR_CODES | {"BROKEN_LINK"},
            check_name="markdown_links_valid",
            success_message="markdown_links_valid: no broken links or preflight errors",
        )
    if kind == "semantic_ids_valid":
        return check_doctor_findings(
            workspace,
            assertion,
            selected_codes=PREFLIGHT_ERROR_CODES | SEMANTIC_ID_ERROR_CODES,
            check_name="semantic_ids_valid",
            success_message="semantic_ids_valid: no semantic ID or preflight errors",
        )
    if kind == "spine_mechanical_valid":
        return check_doctor_findings(workspace, assertion)
    raise ValueError(f"unknown assertion type: {kind}")


def build_prompt(case: dict[str, Any], stage: dict[str, Any] | None = None) -> str:
    scenario = stage["prompt"] if stage is not None else (
        case["prompt"] if "prompt" in case else scenario_user_request(case)
    )
    config = stage or case
    eval_language = config.get("eval_language", case.get("eval_language", "English"))
    if execution_profile(case) == "no-extract":
        return (
            "You are running a repeatable documentation-retrieval evaluation.\n"
            + NO_SKILL_BOUNDARY_INSTRUCTIONS
            + "No retrieval skill is installed for this profile. Work directly from "
            "the project documentation without inspecting `.eval`.\n"
            "Treat the current directory as the project root.\n"
            f"For reproducibility, write the final response in {eval_language}. "
            "Preserve existing user-authored language, identifiers, and quoted text.\n"
            "Perform the user request described by the scenario.\n\n"
            f"{scenario}\n"
        )
    return (
        "You are running a repeatable SpecSpine evaluation.\n"
        + WORKSPACE_BOUNDARY_INSTRUCTIONS
        + f"Before any project discovery, read .eval/skill/{config.get('entrypoint', 'SKILL.md')}. "
        "Then read only the references it requires. Do not list `.eval` or combine "
        "skill loading with project inspection.\n"
        "For this evaluation, the loaded skill root is exactly `.eval/skill`; use "
        "that literal path for bundled scripts and references.\n"
        "Installed companion skills, when configured, are under .eval/companions/.\n"
        "Evaluator tools, when explicitly named by the staged skill, are under .eval/tools/.\n"
        "Treat the current directory as the project root.\n"
        f"For reproducibility, write the final response and newly created project documents in {eval_language}. "
        "Preserve existing user-authored language, identifiers, and quoted text.\n"
        "Perform the user request described by the scenario.\n\n"
        f"{scenario}\n"
    )


def secure_workspace_parent() -> Path:
    configured = os.environ.get("SPECSPINE_EVAL_WORKSPACES_DIR")
    root = Path(configured).expanduser() if configured else (
        Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        / "specspine-eval"
        / "workspaces"
    )
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    return root.resolve()


def create_workspace(prefix: str) -> Path:
    return Path(tempfile.mkdtemp(prefix=prefix, dir=secure_workspace_parent()))


def initialize_git_workspace(workspace: Path) -> None:
    commands = (
        ["git", "init", "-q"],
        ["git", "add", "-A"],
        [
            "git", "-c", "user.name=SpecSpine Eval",
            "-c", "user.email=eval@invalid.local",
            "commit", "-qm", "fixture baseline",
        ],
    )
    for command in commands:
        subprocess.run(command, cwd=workspace, check=True, capture_output=True, text=True)


def scenario_user_request(case: dict[str, Any]) -> str:
    text = (ROOT / case["scenario"]).read_text(encoding="utf-8")
    match = re.search(r"^## User request\s*$\n(.*?)(?=^##\s|\Z)", text, re.MULTILINE | re.DOTALL)
    if not match:
        raise ValueError(f"scenario has no User request section: {case['scenario']}")
    request = match.group(1).strip()
    fenced = re.fullmatch(r"```(?:text)?\s*\n(.*?)\n```", request, re.DOTALL)
    return fenced.group(1).strip() if fenced else request


def read_trace(workspace: Path) -> dict[str, Any] | None:
    trace_path = workspace / ".eval" / "trace.json"
    return json.loads(trace_path.read_text(encoding="utf-8")) if trace_path.is_file() else None


def archive_stage(
    workspace: Path,
    stage_number: int,
    stage_id: str,
    response: str,
    stderr: str,
    trace: dict[str, Any] | None,
) -> None:
    target = workspace / ".eval" / "stages" / f"{stage_number:02d}-{stage_id}"
    target.mkdir(parents=True, exist_ok=True)
    (target / "response.md").write_text(response, encoding="utf-8")
    if stderr:
        (target / "stderr.txt").write_text(stderr, encoding="utf-8")
    if trace is not None:
        (target / "trace.json").write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def print_results(
    results: list[CheckResult], indent: str = "  ", output: TextIO | None = None
) -> None:
    for result in results:
        print(
            f"{indent}{'ok' if result.passed else 'not ok'} - {result.message}",
            file=output,
        )


def workspace_boundary_check(trace: dict[str, Any] | None) -> CheckResult:
    violations = [] if trace is None else trace.get("scope_violations", [])
    return CheckResult(
        not violations,
        "workspace boundary respected"
        if not violations
        else f"workspace boundary violations: {violations}",
    )


def run_staged_case(
    case: dict[str, Any],
    command: list[str],
    workspace: Path,
    env: dict[str, str],
    token_usage: dict[str, int] | None = None,
    agent_runs: list[dict[str, Any]] | None = None,
    output: TextIO | None = None,
) -> bool:
    token_usage = {} if token_usage is None else token_usage
    agent_runs = [] if agent_runs is None else agent_runs
    initial = snapshot(workspace)
    all_responses: list[str] = []
    last_trace: dict[str, Any] | None = None
    passed = True
    for stage_number, stage in enumerate(case["stages"], 1):
        stage_id = stage["id"]
        before = snapshot(workspace)
        response = ""
        stderr = ""
        returncode = 0
        trace: dict[str, Any] | None = None
        if "fixture" in stage:
            apply_fixture_mutation(stage["fixture"], workspace)
        else:
            install_stage_skill(stage, workspace)
            trace_path = workspace / ".eval" / "trace.json"
            if trace_path.exists():
                trace_path.unlink()
            completed = subprocess.run(
                command,
                cwd=workspace,
                input=build_prompt(case, stage),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={
                    **env,
                    "SPECSPINE_EVAL_RUN": str(stage_number),
                    "SPECSPINE_EVAL_STAGE": stage_id,
                },
                timeout=stage.get("timeout_seconds", case.get("timeout_seconds", 600)),
                check=False,
            )
            response = completed.stdout
            stderr = completed.stderr
            returncode = completed.returncode
            trace = read_trace(workspace)
            add_token_usage(token_usage, trace)
            if trace is not None:
                agent_runs.append(compact_agent_trace(trace))
            last_trace = trace
            all_responses.append(response)
        after = snapshot(workspace)
        results = [
            evaluate_assertion(item, workspace, before, after, response, trace)
            for item in stage.get("assertions", [])
        ]
        if "fixture" not in stage:
            results.append(workspace_boundary_check(trace))
        stage_passed = returncode == 0 and all(result.passed for result in results)
        stage_execution = "fixture" if "fixture" in stage else f"agent exit {returncode}"
        print(
            f"  {'PASS' if stage_passed else 'FAIL'} stage {stage_number}: {stage_id} ({stage_execution})",
            file=output,
        )
        if trace is not None:
            print(f"    metrics: {format_stage_metrics(trace)}", file=output)
        print_results(results, "    ", output)
        if stderr:
            print("    agent stderr:", file=output)
            print("      " + stderr.strip().replace("\n", "\n      "), file=output)
        archive_stage(workspace, stage_number, stage_id, response, stderr, trace)
        if not stage_passed:
            passed = False
            break
    final = snapshot(workspace)
    final_results = [
        evaluate_assertion(item, workspace, initial, final, "\n".join(all_responses), last_trace)
        for item in case.get("final_assertions", [])
    ]
    if final_results:
        print("  final assertions:", file=output)
        print_results(final_results, "    ", output)
    return passed and all(result.passed for result in final_results)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def run_case(
    case: dict[str, Any],
    command: list[str],
    keep_workspace: bool,
    output: TextIO | None = None,
    metrics: dict[str, Any] | None = None,
    sample_number: int = 1,
) -> bool:
    started = time.monotonic()
    token_usage: dict[str, int] = {}
    agent_runs: list[dict[str, Any]] = []
    temp = create_workspace(prefix=f"specspine-eval-{case['id']}-")
    try:
        write_fixture(case, temp)
        initialize_git_workspace(temp)
        before = snapshot(temp)
        env = os.environ.copy()
        env["SPECSPINE_EVAL_CASE"] = case["id"]
        env["SPECSPINE_EVAL_SAMPLE"] = str(sample_number)
        env["SPECSPINE_EVAL_WORKSPACE"] = str(temp)
        env["SPECSPINE_EVAL_PROFILE"] = execution_profile(case)
        if "stages" in case:
            stage_count = len(case["stages"])
            stage_label = "stage" if stage_count == 1 else "stages"
            print(f"CASE {case['id']} ({stage_count} {stage_label})", file=output)
            passed = run_staged_case(
                case, command, temp, env, token_usage, agent_runs, output
            )
            duration_seconds = time.monotonic() - started
            if metrics is not None:
                metrics.update(
                    agent_runs=list(agent_runs),
                    duration_seconds=duration_seconds,
                    token_usage=dict(token_usage),
                    response="",
                    stderr="",
                )
            print(f"{'PASS' if passed else 'FAIL'} {case['id']}", file=output)
            print(
                f"  metrics: {format_metrics(duration_seconds, token_usage)}",
                file=output,
            )
            if not passed and keep_workspace:
                print(f"  workspace: {temp}", file=output)
                temp = None  # type: ignore[assignment]
            return passed
        responses: list[str] = []
        errors: list[str] = []
        scope_checks: list[CheckResult] = []
        returncode = 0
        completed_runs = 0
        for run_number in range(1, case.get("runs", 1) + 1):
            trace_path = temp / ".eval" / "trace.json"
            if trace_path.exists():
                trace_path.unlink()
            completed = subprocess.run(
                command,
                cwd=temp,
                input=build_prompt(case),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**env, "SPECSPINE_EVAL_RUN": str(run_number)},
                timeout=case.get("timeout_seconds", 600),
                check=False,
            )
            completed_runs += 1
            responses.append(completed.stdout)
            errors.append(completed.stderr)
            run_trace = read_trace(temp)
            add_token_usage(token_usage, run_trace)
            if run_trace is not None:
                agent_runs.append(compact_agent_trace(run_trace))
            scope_checks.append(workspace_boundary_check(run_trace))
            if completed.returncode:
                returncode = completed.returncode
                break
        response = "\n".join(responses)
        stderr = "\n".join(item for item in errors if item)
        after = snapshot(temp)
        trace = read_trace(temp)
        assertions = active_assertions(case["assertions"], case)
        results = [
            evaluate_assertion(item, temp, before, after, response, trace)
            for item in assertions
        ]
        results.extend(scope_checks)
        passed = returncode == 0 and all(result.passed for result in results)
        failed_checks = [
            {"type": assertion["type"], "message": result.message}
            for assertion, result in zip(assertions, results)
            if not result.passed
        ]
        failed_checks.extend(
            {"type": "workspace_boundary", "message": result.message}
            for result in results[len(assertions):]
            if not result.passed
        )
        if returncode:
            failed_checks.append({"type": "agent_exit", "message": str(returncode)})
        duration_seconds = time.monotonic() - started
        if metrics is not None:
            metrics.update(
                agent_runs=list(agent_runs),
                duration_seconds=duration_seconds,
                failed_checks=failed_checks,
                token_usage=dict(token_usage),
                response=response,
                stderr=stderr,
            )
        print(
            f"{'PASS' if passed else 'FAIL'} {case['id']} "
            f"({completed_runs} {'run' if completed_runs == 1 else 'runs'}, agent exit {returncode})",
            file=output,
        )
        print(
            f"  metrics: {format_metrics(duration_seconds, token_usage)}",
            file=output,
        )
        print_results(results, output=output)
        if stderr:
            print("  agent stderr:", file=output)
            print("    " + stderr.strip().replace("\n", "\n    "), file=output)
        if not passed and keep_workspace:
            print(f"  workspace: {temp}", file=output)
            temp = None  # type: ignore[assignment]
        return passed
    finally:
        if temp is not None:
            shutil.rmtree(temp)


def run_case_captured(
    case: dict[str, Any],
    command: list[str],
    keep_workspace: bool,
    sample_number: int = 1,
    queued_monotonic: float | None = None,
) -> CaseReport:
    queue_seconds = max(0.0, time.monotonic() - queued_monotonic) if queued_monotonic else 0.0
    started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    output = io.StringIO()
    metrics: dict[str, Any] = {}
    passed = run_case(case, command, keep_workspace, output, metrics, sample_number)
    finished_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return CaseReport(
        case_id=case["id"],
        passed=passed,
        output=output.getvalue(),
        duration_seconds=float(metrics.get("duration_seconds", 0.0)),
        token_usage=dict(metrics.get("token_usage", {})),
        sample_number=sample_number,
        agent_runs=tuple(metrics.get("agent_runs", ())),
        failed_checks=tuple(metrics.get("failed_checks", ())),
        started_at=started_at,
        finished_at=finished_at,
        queue_seconds=queue_seconds,
        response=str(metrics.get("response", "")),
        stderr=str(metrics.get("stderr", "")),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="list registered cases")
    parser.add_argument("--audit", action="store_true", help="report scenario registration and executable coverage")
    parser.add_argument("--validate", action="store_true", help="validate manifests without running an agent")
    parser.add_argument("--case", action="append", default=[], help="case ID to run; repeatable")
    parser.add_argument(
        "--category",
        action="append",
        default=[],
        choices=sorted(CASE_CATEGORIES - {"planned"}),
        help="run an executable category; repeatable",
    )
    parser.add_argument("--agent-command", help="command that accepts the prompt on stdin and edits its cwd")
    parser.add_argument("--report-json", type=Path, help="write per-sample metrics as JSON")
    parser.add_argument("--report-label", default="", help="label stored in the JSON report")
    parser.add_argument("--run-id", help="stable identifier to correlate related report runs")
    parser.add_argument(
        "--execution-profile",
        choices=sorted(EXECUTION_PROFILES),
        default="extract",
        help="run accelerated Extract, Extract fallback, or a direct-documentation baseline",
    )
    parser.add_argument(
        "--jobs",
        type=positive_int,
        default=8,
        help="maximum concurrent cases; use 1 for sequential execution (default: 8)",
    )
    parser.add_argument(
        "--samples",
        type=positive_int,
        default=1,
        help="independent fresh-workspace samples per selected case (default: 1)",
    )
    parser.add_argument("--keep-workspace", action="store_true", help="keep failed workspaces")
    args = parser.parse_args()
    cases = load_cases()
    if not any((args.list, args.audit, args.validate, args.agent_command)):
        parser.error("specify --case NAME or --category CATEGORY with --agent-command; use --list to inspect choices")
    if args.agent_command and not (args.case or args.category):
        parser.error("agent eval execution requires at least one --case NAME or --category CATEGORY")
    if args.report_json and not args.agent_command:
        parser.error("--report-json requires --agent-command")
    known_ids = {case["id"] for case in cases}
    unknown_ids = sorted(set(args.case) - known_ids)
    if unknown_ids:
        parser.error(f"unknown case(s): {', '.join(unknown_ids)}; use --list to inspect choices")
    selected = [
        {**case, "_execution_profile": args.execution_profile}
        for case in cases
        if case["id"] in args.case or case["category"] in args.category
    ]
    if args.execution_profile == "no-extract" and any("stages" in case for case in selected):
        parser.error("the no-extract profile supports only non-staged cases")

    if args.list:
        for case in cases:
            owner = case.get("skill", f"{len(case.get('stages', []))} stages")
            print(f"{case['id']}: {case['status']}/{case['category']} ({owner})")

    failed_validation = False
    if args.validate or args.audit or args.agent_command:
        for error in validate_collection(cases):
            failed_validation = True
            print(f"INVALID collection: {error}")
        for case in cases:
            errors = validate_case(case)
            if errors:
                failed_validation = True
                for error in errors:
                    print(f"INVALID {case.get('id', case['_manifest'].name)}: {error}")

    if args.audit:
        documented, registered, executable = scenario_coverage(cases)
        print(f"documented scenarios: {len(documented)}")
        print(f"registered scenarios: {len(registered)}")
        print(f"executable scenarios: {len(executable)}")
        for category in sorted(CASE_CATEGORIES):
            category_cases = [case for case in cases if case["category"] == category]
            agent_calls = sum(
                len([stage for stage in case.get("stages", []) if "skill" in stage])
                if "stages" in case
                else case.get("runs", 1)
                for case in category_cases
                if case["status"] == "executable"
            )
            print(
                f"category {category}: {len(category_cases)} cases, "
                f"{agent_calls} top-level agent calls"
            )
        for scenario in sorted(documented - registered):
            print(f"UNREGISTERED {scenario}")
        for scenario in sorted(registered - documented):
            print(f"ORPHAN {scenario}")
        for scenario in sorted(registered - executable):
            print(f"PLANNED {scenario}")

    if args.agent_command:
        if failed_validation:
            return 2
        executable = [case for case in selected if case["status"] == "executable"]
        if args.case and not executable:
            print("No selected executable cases", file=sys.stderr)
            return 2
        command = shlex.split(args.agent_command)
        reports: list[CaseReport] = []
        work_items = [
            (case, sample_number)
            for case in executable
            for sample_number in range(1, args.samples + 1)
        ]
        execution_started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        execution_started = time.monotonic()

        def publish(report: CaseReport) -> None:
            reports.append(report)
            sample_label = (
                f" [{report.case_id} sample {report.sample_number}/{args.samples}]"
                if args.samples > 1
                else ""
            )
            print(
                f"[{len(reports)}/{len(work_items)} completed]{sample_label}\n{report.output}",
                end="",
                flush=True,
            )

        if args.jobs > 1 and len(work_items) > 1:
            queued = time.monotonic()
            with ThreadPoolExecutor(max_workers=min(args.jobs, len(work_items))) as executor:
                futures = [
                    executor.submit(
                        run_case_captured,
                        case,
                        command,
                        args.keep_workspace,
                        sample_number,
                        queued,
                    )
                    for case, sample_number in work_items
                ]
                for future in as_completed(futures):
                    publish(future.result())
        else:
            for case, sample_number in work_items:
                publish(
                    run_case_captured(
                        case, command, args.keep_workspace, sample_number
                    )
                )
        wall_seconds = time.monotonic() - execution_started
        execution_finished_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        passed_count = sum(report.passed for report in reports)
        failed_ids = [
            f"{report.case_id}#{report.sample_number}"
            if args.samples > 1
            else report.case_id
            for report in reports
            if not report.passed
        ]
        summed_case_seconds = sum(report.duration_seconds for report in reports)
        token_summary = format_token_usage(aggregate_token_usage(reports))
        result_unit = "samples" if args.samples > 1 else "tests"
        summary = (
            f"SUMMARY: {passed_count}/{len(reports)} {result_unit} passed; "
            f"wall time: {wall_seconds:.3f}s; summed case time: {summed_case_seconds:.3f}s; "
            f"{token_summary}"
        )
        if failed_ids:
            summary += f"; failed: {', '.join(failed_ids)}"
        print(summary)
        if args.samples > 1:
            print("SUCCESS RATE:")
            for case in executable:
                case_reports = [report for report in reports if report.case_id == case["id"]]
                case_passed = sum(report.passed for report in case_reports)
                rate = 100.0 * case_passed / len(case_reports)
                print(f"  {case['id']}: {case_passed}/{len(case_reports)} ({rate:.1f}%)")
        if args.report_json:
            write_json_report(
                args.report_json,
                args.report_label,
                args.agent_command,
                reports,
                executable,
                args.samples,
                args.jobs,
                run_id=args.run_id,
                started_at=execution_started_at,
                finished_at=execution_finished_at,
            )
            print(f"JSON report: {args.report_json}")
        return 0 if not failed_ids else 1

    if not any((args.list, args.audit, args.validate)):
        parser.print_help()
    return 2 if failed_validation else 0


if __name__ == "__main__":
    raise SystemExit(main())
