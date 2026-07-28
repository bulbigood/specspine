#!/usr/bin/env python3
"""Validate one producer result and atomically expose its handoff package."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


CHECKPOINT_STATUSES = {
    "draft",
    "covered",
    "answered",
    "unresolved",
    "supporting",
    "retry",
    "blocked",
}
ALLOWED_FIELDS = {
    "outcome",
    "evidence",
    "summary",
    "owner",
    "directions",
    "need",
    "reason",
}
EVIDENCE_BASELINE_RE = re.compile(
    r"<!--\s*specspine:evidence-baseline\s+"
    r"source=[^;\s>]+;\s*inspected=\d{4}-\d{2}-\d{2}\s*-->"
)
OBS_DEFINITION_RE = re.compile(
    r"^ {0,3}[-+*]\s+\*\*OBS-[a-z0-9]+(?:-[a-z0-9]+)*\*\*\s+—\s+\S",
    re.MULTILINE,
)
LEGACY_SEMANTIC_RE = re.compile(
    r"^\*\*ID:\*\*\s+`(?:DEC|CON|REQ|GUA|INV|QLT|VER|OBS|INF|OQ)-[^`]+`"
    r"\s+·\s+\*\*Status:\*\*",
    re.MULTILINE,
)


class PreflightError(ValueError):
    pass


def read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise PreflightError(f"cannot read JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise PreflightError(f"JSON root must be an object: {path}")
    return value


def strings(value: Any, field: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise PreflightError(f"{field} must be a list of nonempty strings")
    if nonempty and not value:
        raise PreflightError(f"{field} must not be empty")
    return [item.strip() for item in value]


def relative_markdown_files(root: Path) -> dict[str, Path]:
    if not root.is_dir():
        raise PreflightError(f"work package needs a staging directory: {root}")
    files: dict[str, Path] = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise PreflightError(f"staging contains symbolic link: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if path.suffix.lower() != ".md":
            raise PreflightError(
                f"staging may contain only Markdown files: {relative.as_posix()}"
            )
        if relative == Path("README.md"):
            raise PreflightError("producer must not publish README.md")
        files[relative.as_posix()] = path
    return files


def relative_path(value: str, field: str) -> str:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise PreflightError(f"{field} must be a safe relative path: {value!r}")
    return path.as_posix()


def task_definition(raw: dict[str, Any]) -> dict[str, Any]:
    nested = raw.get("task")
    task = nested if isinstance(nested, dict) else raw
    if not isinstance(task.get("id"), str) or not task["id"].strip():
        raise PreflightError("task packet needs a task id")
    strata = task.get("evidence_strata", [])
    if not isinstance(strata, list):
        raise PreflightError("task evidence_strata must be a list")
    for value in strata:
        if (
            not isinstance(value, dict)
            or set(value) != {"id", "sample"}
            or not isinstance(value["id"], str)
            or not value["id"].strip()
            or not isinstance(value["sample"], str)
            or not value["sample"].strip()
        ):
            raise PreflightError("each evidence stratum needs id and sample")
    return task


def validate_checkpoint(
    checkpoint: dict[str, Any],
    task: dict[str, Any],
    staged: dict[str, Path],
) -> list[str]:
    unknown = set(checkpoint) - ALLOWED_FIELDS
    if unknown:
        raise PreflightError(f"unknown checkpoint fields: {sorted(unknown)}")
    outcome = checkpoint.get("outcome")
    if outcome not in CHECKPOINT_STATUSES:
        raise PreflightError(f"invalid checkpoint outcome: {outcome!r}")
    evidence = strings(
        checkpoint.get("evidence"),
        "checkpoint evidence",
        nonempty=True,
    )
    evidence = [
        relative_path(value, "checkpoint evidence") for value in evidence
    ]
    summary = checkpoint.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise PreflightError("checkpoint summary must be nonempty")
    directions = strings(
        checkpoint.get("directions", []),
        "checkpoint directions",
    )
    if outcome not in {"draft", "covered", "answered"} and directions:
        raise PreflightError(f"{outcome} cannot emit directions")

    if outcome in {"covered", "answered"}:
        owner = checkpoint.get("owner")
        if not isinstance(owner, dict) or set(owner) != {"document", "claims"}:
            raise PreflightError(
                f"{outcome} requires owner with document and claims"
            )
        if not isinstance(owner["document"], str) or not owner["document"].strip():
            raise PreflightError(f"{outcome} owner document must be nonempty")
        strings(owner["claims"], f"{outcome} owner claims", nonempty=True)
    elif checkpoint.get("owner") is not None:
        raise PreflightError(f"{outcome} checkpoint must not include owner")

    if outcome == "retry":
        strings(checkpoint.get("need"), "checkpoint need", nonempty=True)
    elif checkpoint.get("need") is not None:
        raise PreflightError(f"{outcome} checkpoint must not include need")

    if outcome in {"blocked", "supporting", "unresolved"}:
        reason = checkpoint.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise PreflightError(f"{outcome} checkpoint needs reason")
    elif checkpoint.get("reason") is not None:
        raise PreflightError(f"{outcome} checkpoint must not include reason")

    if outcome == "draft" and not staged:
        raise PreflightError("draft requires at least one staged Markdown file")
    if outcome != "draft" and staged:
        raise PreflightError(f"{outcome} must not publish staged files")

    if outcome in {"draft", "covered", "answered", "unresolved", "supporting"}:
        samples = {
            value["sample"] for value in task.get("evidence_strata", [])
        }
        missing = sorted(samples - set(evidence))
        if missing:
            raise PreflightError(
                "integrable checkpoint must inspect every packet evidence sample: "
                f"{missing}"
            )
    return evidence


def validate_repository_evidence(
    repository_root: Path,
    evidence: list[str],
) -> None:
    missing = [
        value for value in evidence if not (repository_root / value).is_file()
    ]
    if missing:
        raise PreflightError(
            f"checkpoint evidence is not a repository file: {missing}"
        )


def validate_covered_owner(
    checkpoint: dict[str, Any],
    task: dict[str, Any],
    spine_root: Path,
    evidence: list[str],
) -> None:
    if checkpoint["outcome"] not in {"covered", "answered"}:
        return
    owner = checkpoint["owner"]
    document = relative_path(owner["document"], "covered owner document")
    if Path(document).parts[:1] == (spine_root.name,):
        document = Path(*Path(document).parts[1:]).as_posix()
    owner_path = spine_root / document
    if not owner_path.is_file():
        raise PreflightError(f"covered owner document does not exist: {document}")
    body = owner_path.read_text(encoding="utf-8")
    missing_claims = [
        claim for claim in owner["claims"] if f"**{claim}**" not in body
    ]
    if missing_claims:
        raise PreflightError(
            f"covered owner claim IDs do not exist: {missing_claims}"
        )
    if checkpoint["outcome"] == "answered" and any(
        not claim.startswith("OBS-") for claim in owner["claims"]
    ):
        raise PreflightError(
            "answered owner claims must all be repository observations (OBS-*)"
        )
    references = [*task.get("units", []), *evidence]
    if references and not any(value in body for value in references):
        raise PreflightError(
            "covered owner does not reference the task unit or inspected evidence"
        )


def validate_task_outcome(checkpoint: dict[str, Any], task: dict[str, Any]) -> None:
    outcome = checkpoint["outcome"]
    scope_task = bool(task.get("units"))
    if outcome in {"covered", "supporting"} and not scope_task:
        raise PreflightError(
            f"{outcome} is valid only for scope verification tasks"
        )
    if outcome in {"answered", "unresolved"} and scope_task:
        raise PreflightError(
            f"{outcome} is valid only for integration-derived tasks"
        )
    if outcome in {"answered", "unresolved"} and task.get("anchor") is None:
        raise PreflightError(
            f"{outcome} requires an integration-derived task with an anchor"
        )


def run_candidate_checker(
    checker: Path,
    spine_root: Path,
    staging_root: Path,
    staged: dict[str, Path],
    repository_root: Path,
) -> None:
    command = [
        sys.executable,
        str(checker),
        str(spine_root),
        "--candidates",
        str(staging_root),
        "--repository-root",
        str(repository_root),
        "--json",
    ]
    for relative in sorted(staged):
        if (spine_root / relative).exists():
            command.extend(["--replace-existing", relative])
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    try:
        findings = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        detail = result.stderr.strip() or result.stdout.strip() or "no output"
        raise PreflightError(f"checker returned invalid JSON: {detail}") from error
    if not isinstance(findings, list):
        raise PreflightError("checker output must be a JSON list")
    if result.returncode != 0 or findings:
        raise PreflightError(
            "producer candidate preflight failed: "
            + json.dumps(findings, ensure_ascii=False)
        )


def validate_draft_semantics(
    staged: dict[str, Path],
    task: dict[str, Any],
) -> None:
    expected_baseline = task.get("evidence_baseline")
    for relative, path in staged.items():
        body = path.read_text(encoding="utf-8")
        if LEGACY_SEMANTIC_RE.search(body):
            raise PreflightError(
                f"candidate uses legacy semantic definition syntax: {relative}"
            )
        if EVIDENCE_BASELINE_RE.search(body) is None:
            raise PreflightError(
                f"candidate needs an evidence baseline: {relative}"
            )
        if expected_baseline is not None and expected_baseline not in body:
            raise PreflightError(
                f"candidate must use the task packet evidence baseline: {relative}"
            )
        if OBS_DEFINITION_RE.search(body) is None:
            raise PreflightError(
                f"candidate needs a semantic OBS definition: {relative}"
            )


def finalize(args: argparse.Namespace) -> dict[str, Any]:
    work = args.work_package.resolve()
    handoff = args.handoff_package.resolve()
    if not work.is_dir():
        raise PreflightError(f"work package is not a directory: {work}")
    if handoff.exists():
        raise PreflightError(f"handoff package already exists: {handoff}")
    if handoff == work or work in handoff.parents or handoff in work.parents:
        raise PreflightError("work and handoff packages must be separate siblings")

    staging = work / "staging"
    checkpoint_path = work / "checkpoint.json"
    staged = relative_markdown_files(staging)
    task = task_definition(read_object(args.task_packet))
    checkpoint = read_object(checkpoint_path)
    evidence = validate_checkpoint(checkpoint, task, staged)
    validate_task_outcome(checkpoint, task)
    repository_root = args.repository_root.resolve()
    spine_root = args.spine_root.resolve()
    validate_repository_evidence(repository_root, evidence)
    validate_covered_owner(checkpoint, task, spine_root, evidence)
    if checkpoint["outcome"] == "draft":
        validate_draft_semantics(staged, task)
        run_candidate_checker(
            args.checker.resolve(),
            spine_root,
            staging,
            staged,
            repository_root,
        )

    handoff.parent.mkdir(parents=True, exist_ok=True)
    os.replace(work, handoff)
    return {
        "status": "ready",
        "task": task["id"],
        "outcome": checkpoint["outcome"],
        "handoff_package": str(handoff),
        "checkpoint": str(handoff / "checkpoint.json"),
        "staging_root": str(handoff / "staging"),
        "candidate_files": sorted(staged),
        "mechanical_preflight": (
            "clean" if checkpoint["outcome"] == "draft" else "not_applicable"
        ),
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("task_packet", type=Path)
    result.add_argument("work_package", type=Path)
    result.add_argument("handoff_package", type=Path)
    result.add_argument("repository_root", type=Path)
    result.add_argument("spine_root", type=Path)
    result.add_argument(
        "--checker",
        type=Path,
        default=Path(__file__).with_name("check_spine.py"),
    )
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        value = finalize(args)
    except (PreflightError, OSError, UnicodeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(value, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
