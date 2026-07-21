#!/usr/bin/env python3
"""Dependency-free runner for repeatable SpecSpine agent evaluations."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CASES_DIR = Path(__file__).resolve().parent / "cases"
SCENARIOS_DIR = ROOT / "tests" / "scenarios"
CASE_CATEGORIES = {"core", "extended", "planned"}
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


def load_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for path in sorted(CASES_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        data["_manifest"] = path
        cases.append(data)
    return cases


def validate_case(case: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {"id", "scenario", "status", "category", "initial_files"}
    missing = sorted(required - case.keys())
    if missing:
        errors.append(f"missing fields: {', '.join(missing)}")
        return errors
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
    for rel in case["initial_files"]:
        if not safe_relative_path(rel):
            errors.append(f"unsafe initial file path: {rel}")
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


def write_fixture(case: dict[str, Any], workspace: Path) -> None:
    for rel, content in case["initial_files"].items():
        path = workspace / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    scenario_source = ROOT / case["scenario"]
    (workspace / ".eval").mkdir(exist_ok=True)
    shutil.copy2(scenario_source, workspace / ".eval" / "scenario.md")
    if "stages" not in case:
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
        if path.is_file() and ".eval" not in path.relative_to(workspace).parts:
            result[str(path.relative_to(workspace))] = path.read_bytes()
    return result


def changed_paths(before: dict[str, bytes], after: dict[str, bytes]) -> set[str]:
    return {path for path in before.keys() | after.keys() if before.get(path) != after.get(path)}


def matches_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


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
        f"unexpected Doctor findings: {unexpected}" if unexpected else "Doctor mechanical errors are absent",
    )


def evaluate_assertion(
    assertion: dict[str, Any],
    workspace: Path,
    before: dict[str, bytes],
    after: dict[str, bytes],
    response: str,
    trace: dict[str, Any] | None,
) -> CheckResult:
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
    if kind == "glob_contains":
        files = project_files(workspace, assertion["glob"])
        content = "\n".join(path.read_text(encoding="utf-8") for path in files)
        needles = assertion.get("values", [assertion.get("value", "")])
        missing = [needle for needle in needles if needle not in content]
        return CheckResult(
            not missing,
            f"{assertion['glob']} missing: {missing}" if missing else f"content found in {assertion['glob']}",
        )
    if kind == "file_contains":
        content = path.read_text(encoding="utf-8") if path.is_file() else ""
        needles = assertion.get("values", [assertion.get("value", "")])
        missing = [needle for needle in needles if needle not in content]
        return CheckResult(not missing, f"{assertion['path']} missing: {missing}" if missing else f"content found in {assertion['path']}")
    if kind == "file_not_contains":
        content = path.read_text(encoding="utf-8") if path.is_file() else ""
        needles = assertion.get("values", [assertion.get("value", "")])
        found = [needle for needle in needles if needle in content]
        return CheckResult(not found, f"{assertion['path']} contains forbidden: {found}" if found else f"forbidden content absent in {assertion['path']}")
    if kind == "response_contains":
        needles = assertion.get("values", [assertion.get("value", "")])
        missing = [needle for needle in needles if needle.lower() not in response.lower()]
        return CheckResult(not missing, f"response missing: {missing}" if missing else "response contains required text")
    if kind == "response_not_contains":
        needles = assertion.get("values", [assertion.get("value", "")])
        found = [needle for needle in needles if needle.lower() in response.lower()]
        return CheckResult(not found, f"response contains forbidden text: {found}" if found else "forbidden response text absent")
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
        return CheckResult(not failures, f"unresolved placeholders: {failures}" if failures else "no unresolved placeholders")
    if kind == "markdown_links_valid":
        return check_doctor_findings(
            workspace, assertion, selected_codes=PREFLIGHT_ERROR_CODES | {"BROKEN_LINK"}
        )
    if kind == "semantic_ids_valid":
        return check_doctor_findings(
            workspace, assertion, selected_codes=PREFLIGHT_ERROR_CODES | SEMANTIC_ID_ERROR_CODES
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
    return (
        "You are running a repeatable SpecSpine evaluation.\n"
        f"Read .eval/skill/{config.get('entrypoint', 'SKILL.md')} and all references it requires.\n"
        "Installed companion skills, when configured, are under .eval/companions/.\n"
        "Treat the current directory as the project root.\n"
        f"For reproducibility, write the final response and newly created project documents in {eval_language}. "
        "Preserve existing user-authored language, identifiers, and quoted text.\n"
        "Perform the user request described by the scenario.\n\n"
        f"{scenario}\n"
    )


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


def print_results(results: list[CheckResult], indent: str = "  ") -> None:
    for result in results:
        print(f"{indent}{'ok' if result.passed else 'not ok'} - {result.message}")


def run_staged_case(case: dict[str, Any], command: list[str], workspace: Path, env: dict[str, str]) -> bool:
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
            last_trace = trace
            all_responses.append(response)
        after = snapshot(workspace)
        results = [
            evaluate_assertion(item, workspace, before, after, response, trace)
            for item in stage.get("assertions", [])
        ]
        stage_passed = returncode == 0 and all(result.passed for result in results)
        print(f"  {'PASS' if stage_passed else 'FAIL'} stage {stage_number}: {stage_id} (agent exit {returncode})")
        print_results(results, "    ")
        if stderr:
            print("    agent stderr:")
            print("      " + stderr.strip().replace("\n", "\n      "))
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
        print("  final assertions:")
        print_results(final_results, "    ")
    return passed and all(result.passed for result in final_results)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def run_case(case: dict[str, Any], command: list[str], keep_workspace: bool) -> bool:
    temp = Path(tempfile.mkdtemp(prefix=f"specspine-eval-{case['id']}-"))
    try:
        write_fixture(case, temp)
        before = snapshot(temp)
        env = os.environ.copy()
        env["SPECSPINE_EVAL_CASE"] = case["id"]
        env["SPECSPINE_EVAL_WORKSPACE"] = str(temp)
        if "stages" in case:
            print(f"CASE {case['id']} ({len(case['stages'])} stages)")
            passed = run_staged_case(case, command, temp, env)
            print(f"{'PASS' if passed else 'FAIL'} {case['id']}")
            if not passed and keep_workspace:
                print(f"  workspace: {temp}")
                temp = None  # type: ignore[assignment]
            return passed
        responses: list[str] = []
        errors: list[str] = []
        returncode = 0
        for run_number in range(1, case.get("runs", 1) + 1):
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
            responses.append(completed.stdout)
            errors.append(completed.stderr)
            if completed.returncode:
                returncode = completed.returncode
                break
        response = "\n".join(responses)
        stderr = "\n".join(item for item in errors if item)
        after = snapshot(temp)
        trace = read_trace(temp)
        results = [evaluate_assertion(item, temp, before, after, response, trace) for item in case["assertions"]]
        passed = returncode == 0 and all(result.passed for result in results)
        print(f"{'PASS' if passed else 'FAIL'} {case['id']} ({case.get('runs', 1)} run(s), agent exit {returncode})")
        print_results(results)
        if stderr:
            print("  agent stderr:")
            print("    " + stderr.strip().replace("\n", "\n    "))
        if not passed and keep_workspace:
            print(f"  workspace: {temp}")
            temp = None  # type: ignore[assignment]
        return passed
    finally:
        if temp is not None:
            shutil.rmtree(temp)


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
    parser.add_argument(
        "--jobs",
        type=positive_int,
        default=8,
        help="maximum concurrent cases; use 1 for sequential execution (default: 8)",
    )
    parser.add_argument("--keep-workspace", action="store_true", help="keep failed workspaces")
    args = parser.parse_args()
    cases = load_cases()
    if not any((args.list, args.audit, args.validate, args.agent_command)):
        parser.error("specify --case NAME or --category CATEGORY with --agent-command; use --list to inspect choices")
    if args.agent_command and not (args.case or args.category):
        parser.error("agent eval execution requires at least one --case NAME or --category CATEGORY")
    known_ids = {case["id"] for case in cases}
    unknown_ids = sorted(set(args.case) - known_ids)
    if unknown_ids:
        parser.error(f"unknown case(s): {', '.join(unknown_ids)}; use --list to inspect choices")
    selected = [
        case
        for case in cases
        if case["id"] in args.case or case["category"] in args.category
    ]

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
            print(f"category {category}: {len(category_cases)} cases, {agent_calls} agent calls")
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
        if args.jobs > 1 and len(executable) > 1:
            with ThreadPoolExecutor(max_workers=min(args.jobs, len(executable))) as executor:
                results = list(
                    executor.map(
                        lambda case: run_case(case, command, args.keep_workspace),
                        executable,
                    )
                )
        else:
            results = [run_case(case, command, args.keep_workspace) for case in executable]
        passed_count = sum(results)
        print(f"SUMMARY: {passed_count}/{len(results)} tests passed")
        return 0 if all(results) else 1

    if not any((args.list, args.audit, args.validate)):
        parser.print_help()
    return 2 if failed_validation else 0


if __name__ == "__main__":
    raise SystemExit(main())
