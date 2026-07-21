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
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CASES_DIR = Path(__file__).resolve().parent / "cases"
SCENARIOS_DIR = ROOT / "tests" / "scenarios"
ID_RE = re.compile(r"^(DEC|CON|OBS|INF|OQ)-[a-z0-9]+(?:-[a-z0-9]+)*$")
REFERENCE_RE = re.compile(r"\[((?:DEC|CON|OBS|INF|OQ)-[^\]]+)\]\(([^)]+)\)")
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
SECTION_PREFIXES = {
    "Decisions": "DEC",
    "Constraints": "CON",
    "Observed": "OBS",
    "Inferred": "INF",
    "Open questions": "OQ",
}


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
    required = {"id", "scenario", "skill", "status", "initial_files", "assertions"}
    missing = sorted(required - case.keys())
    if missing:
        errors.append(f"missing fields: {', '.join(missing)}")
        return errors
    if case["status"] not in {"executable", "planned"}:
        errors.append("status must be executable or planned")
    scenario = ROOT / case["scenario"]
    skill = ROOT / case["skill"]
    if not scenario.is_file():
        errors.append(f"scenario does not exist: {case['scenario']}")
    entrypoint = case.get("entrypoint", "SKILL.md")
    if not (skill / entrypoint).is_file():
        errors.append(f"evaluation entrypoint does not exist: {case['skill']}/{entrypoint}")
    if case["status"] == "executable" and not case["assertions"]:
        errors.append("executable case has no assertions")
    for companion in case.get("companion_skills", []):
        if not (ROOT / companion / "SKILL.md").is_file():
            errors.append(f"companion skill does not exist: {companion}")
    for rel in case["initial_files"]:
        path = Path(rel)
        if path.is_absolute() or ".." in path.parts:
            errors.append(f"unsafe initial file path: {rel}")
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
    skill_source = ROOT / case["skill"]
    shutil.copytree(skill_source, workspace / ".eval" / "skill")
    for companion in case.get("companion_skills", []):
        companion_source = ROOT / companion
        shutil.copytree(companion_source, workspace / ".eval" / "companions" / companion_source.name)
    scenario_source = ROOT / case["scenario"]
    (workspace / ".eval").mkdir(exist_ok=True)
    shutil.copy2(scenario_source, workspace / ".eval" / "scenario.md")


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


def check_markdown_links(workspace: Path, glob: str) -> CheckResult:
    failures: list[str] = []
    for source in markdown_files(workspace, glob):
        text = source.read_text(encoding="utf-8")
        for target in MARKDOWN_LINK_RE.findall(text):
            target = target.split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            resolved = (source.parent / target).resolve()
            if not resolved.exists():
                failures.append(f"{source.relative_to(workspace)} -> {target}")
    return CheckResult(not failures, "broken links: " + ", ".join(failures) if failures else "all Markdown links resolve")


def check_semantic_ids(workspace: Path, glob: str) -> CheckResult:
    definitions: dict[tuple[Path, str], int] = {}
    failures: list[str] = []
    references: list[tuple[Path, str, str]] = []
    for source in markdown_files(workspace, glob):
        text = source.read_text(encoding="utf-8")
        section = ""
        for line in text.splitlines():
            heading = re.match(r"^##\s+(.+?)\s*$", line)
            if heading:
                section = heading.group(1)
            definition = re.match(r"^- \*\*((?:DEC|CON|OBS|INF|OQ)-[^*]+)\*\* — ", line)
            if not definition:
                continue
            identifier = definition.group(1)
            if not ID_RE.fullmatch(identifier):
                failures.append(f"invalid ID {identifier} in {source.relative_to(workspace)}")
            expected_prefix = SECTION_PREFIXES.get(section)
            actual_prefix = identifier.split("-", 1)[0]
            if expected_prefix != actual_prefix:
                failures.append(
                    f"{identifier} is under '{section or 'no section'}' in {source.relative_to(workspace)}"
                )
            key = (source.resolve(), identifier)
            definitions[key] = definitions.get(key, 0) + 1
        for identifier, target in REFERENCE_RE.findall(text):
            references.append((source, identifier, target))
            if not ID_RE.fullmatch(identifier):
                failures.append(f"invalid reference ID {identifier} in {source.relative_to(workspace)}")
            if "#" in target:
                failures.append(f"ID reference uses a fragment in {source.relative_to(workspace)}: {target}")
    for (source, identifier), count in definitions.items():
        if count > 1:
            failures.append(f"duplicate {identifier} in {source.relative_to(workspace)}")
    for source, identifier, target in references:
        resolved = (source.parent / target).resolve()
        if resolved.exists() and definitions.get((resolved, identifier), 0) != 1:
            failures.append(f"unresolved {identifier}: {source.relative_to(workspace)} -> {target}")
    return CheckResult(not failures, "; ".join(failures) if failures else "semantic IDs are valid and resolvable")


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
    if kind == "path_absent":
        return CheckResult(not path.exists(), f"absent: {assertion['path']}")
    if kind == "glob_count":
        count = len([item for item in workspace.glob(assertion["glob"]) if item.is_file()])
        minimum = assertion.get("min", 0)
        maximum = assertion.get("max", sys.maxsize)
        return CheckResult(minimum <= count <= maximum, f"{assertion['glob']}: {count}, expected {minimum}..{maximum}")
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
    if kind == "balanced_markers":
        content = path.read_text(encoding="utf-8") if path.is_file() else ""
        begin, end = assertion["begin"], assertion["end"]
        passed = content.count(begin) == content.count(end) == assertion.get("count", 1)
        return CheckResult(passed, f"marker counts: {content.count(begin)}/{content.count(end)}")
    if kind == "no_template_placeholders":
        failures = []
        for item in workspace.glob(assertion["glob"]):
            if item.is_file() and re.search(r"\{\{[^{}]+\}\}", item.read_text(encoding="utf-8")):
                failures.append(str(item.relative_to(workspace)))
        return CheckResult(not failures, f"unresolved placeholders: {failures}" if failures else "no unresolved placeholders")
    if kind == "markdown_links_valid":
        return check_markdown_links(workspace, assertion.get("glob", "**/*.md"))
    if kind == "semantic_ids_valid":
        return check_semantic_ids(workspace, assertion.get("glob", "**/*.md"))
    raise ValueError(f"unknown assertion type: {kind}")


def build_prompt(case: dict[str, Any]) -> str:
    scenario = (ROOT / case["scenario"]).read_text(encoding="utf-8")
    return (
        "You are running a repeatable SpecSpine evaluation.\n"
        f"Read .eval/skill/{case.get('entrypoint', 'SKILL.md')} and all references it requires.\n"
        "Installed companion skills, when configured, are under .eval/companions/.\n"
        "Treat the current directory as the project root.\n"
        "Perform the user request described by the scenario.\n\n"
        f"{scenario}\n"
    )


def run_case(case: dict[str, Any], command: list[str], keep_workspace: bool) -> bool:
    temp = Path(tempfile.mkdtemp(prefix=f"specspine-eval-{case['id']}-"))
    try:
        write_fixture(case, temp)
        before = snapshot(temp)
        env = os.environ.copy()
        env["SPECSPINE_EVAL_CASE"] = case["id"]
        env["SPECSPINE_EVAL_WORKSPACE"] = str(temp)
        completed = subprocess.run(
            command,
            cwd=temp,
            input=build_prompt(case),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            timeout=case.get("timeout_seconds", 600),
            check=False,
        )
        after = snapshot(temp)
        trace_path = temp / ".eval" / "trace.json"
        trace = json.loads(trace_path.read_text(encoding="utf-8")) if trace_path.is_file() else None
        results = [evaluate_assertion(item, temp, before, after, completed.stdout, trace) for item in case["assertions"]]
        passed = completed.returncode == 0 and all(result.passed for result in results)
        print(f"{'PASS' if passed else 'FAIL'} {case['id']} (agent exit {completed.returncode})")
        for result in results:
            print(f"  {'ok' if result.passed else 'not ok'} - {result.message}")
        if completed.stderr:
            print("  agent stderr:")
            print("    " + completed.stderr.strip().replace("\n", "\n    "))
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
    parser.add_argument("--agent-command", help="command that accepts the prompt on stdin and edits its cwd")
    parser.add_argument("--keep-workspace", action="store_true", help="keep failed workspaces")
    args = parser.parse_args()
    cases = load_cases()
    selected = [case for case in cases if not args.case or case["id"] in args.case]

    if args.list:
        for case in cases:
            print(f"{case['id']}: {case['status']} ({case['skill']})")

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
        results = [run_case(case, command, args.keep_workspace) for case in executable]
        return 0 if all(results) else 1

    if not any((args.list, args.audit, args.validate)):
        parser.print_help()
    return 2 if failed_validation else 0


if __name__ == "__main__":
    raise SystemExit(main())
