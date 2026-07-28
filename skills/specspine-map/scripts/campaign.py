#!/usr/bin/env python3
"""Run a reliable exhaustive SpecSpine Map campaign.

The campaign deliberately separates four authorities:

* deterministic repository inventory defines the lower bound of discovery;
* one-shot producers verify one bounded task and stage missing observations;
* the root orchestrator publishes and integrates accepted results;
* the ledger derives completion from inventory, ToDo, and integration state.

Producer prose is never treated as proof of coverage or saturation.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


SCHEMA_VERSION = 10
PRODUCER_CONTRACT_VERSION = 5
MAX_UNIT_FILES = 80
MAX_CANDIDATE_DOCUMENTS = 12
TASK_STATES = {"todo", "assigned", "review", "published", "complete", "blocked"}
CHECKPOINT_STATUSES = {
    "draft",
    "covered",
    "answered",
    "unresolved",
    "supporting",
    "retry",
    "blocked",
}
SOURCE_CLASSIFICATIONS = {
    "queued",
    "dependency-lock",
    "generated",
    "opaque-asset",
    "vendored",
    "test-only",
    "repository-support",
}
REVIEW_DISPOSITIONS = {
    "integrated",
    "already_canonical",
    "answered_canonical",
    "still_open",
    "confirmed_supporting",
    "retry",
}
ANCHOR_DISPOSITIONS = {"resolved", "refined", "still-open", "blocking"}
OQ_ID_RE = re.compile(r"OQ-[a-z0-9]+(?:-[a-z0-9]+)*")
COVERAGE_CLAIM_ID_RE = re.compile(
    r"(?:DEC|CON|REQ|GUA|INV|QLT|VER|OBS)-"
    r"[a-z0-9]+(?:-[a-z0-9]+)*"
)
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
DOCUMENT_IDENTITY_RE = re.compile(
    r"^\*\*ID:\*\*\s+`([a-z0-9]+(?:-[a-z0-9]+)*)`\s+·\s+"
    r"\*\*Kind:\*\*\s+`(?!index`)[^`]+`\s*$",
    re.MULTILINE,
)
RELATION_ROW_RE = re.compile(
    r"^\|\s*`(?:[a-z][a-z0-9-]*|x-[a-z0-9-]+)`\s*\|\s*"
    r"\[[^\]]+\]\(([^)#?]+\.md)\)\s*\|",
    re.MULTILINE,
)
SUGGESTION_DISPOSITIONS = {"queued", "covered", "preserved", "rejected"}
DEFERRED_CHECKER_CODES = {"UNREACHABLE_SPEC"}
V3_ENVELOPE_BLOCKER_CODES = {
    "INDEX_MISSING",
    "MANIFEST_IMPLEMENTATION_FREEDOM",
    "MANIFEST_INVALID",
    "MANIFEST_MISSING",
    "MANIFEST_MISSING_KEY",
    "MANIFEST_PROJECT",
    "MANIFEST_UNKNOWN_KEY",
    "MANIFEST_VERSION",
}
DEFAULT_RECENT_HOURS = 24.0
COLLAPSED_DIRECTORIES = {
    ".git",
    ".next",
    ".venv",
    ".yarn",
    "build",
    "dist",
    "node_modules",
    "target",
    "vendor",
    "venv",
    ".specspine-map",
}
VENDORED_DIRECTORIES = {"node_modules", "vendor"}
GENERATED_DIRECTORIES = {
    ".next",
    ".venv",
    ".yarn",
    "build",
    "dist",
    "target",
    "venv",
    ".specspine-map",
    "__generated__",
    "generated",
    "gen",
}
TEST_ROOTS = {
    "__tests__",
    "e2e",
    "e2e-playwright",
    "integration-tests",
    "test",
    "tests",
}
TEST_COMPONENTS = TEST_ROOTS | {
    "__fixtures__",
    "__mocks__",
    "__snapshots__",
    "fixture",
    "fixtures",
    "mock",
    "mocks",
    "snapshot",
    "snapshots",
    "test-data",
    "test_data",
    "testdata",
}
DOCUMENTATION_ROOTS = {
    ".changelog-archive",
    "devenv",
    "docs",
    "local",
}
ROOT_MANIFESTS = {
    "Cargo.toml",
    "Gemfile",
    "Makefile",
    "build.gradle",
    "build.gradle.kts",
    "go.mod",
    "go.work",
    "package.json",
    "pom.xml",
    "pyproject.toml",
    "settings.gradle",
    "settings.gradle.kts",
}
ROOT_GOVERNANCE = {
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "GOVERNANCE.md",
    "LICENSE",
    "LICENSING.md",
    "MAINTAINERS.md",
    "NOTICE.md",
    "README.md",
    "ROADMAP.md",
    "SECURITY.md",
    "SUPPORT.md",
}
REPOSITORY_SUPPORT_UNITS = {
    ".claude",
    ".citools",
    ".github",
    ".idea",
    ".vim",
    ".vscode",
    "contribute",
}
DEPENDENCY_LOCK_FILES = {
    "cargo.lock",
    "composer.lock",
    "go.sum",
    "go.work.sum",
    "package-lock.json",
    "packages.lock.json",
    "pnpm-lock.yaml",
    "poetry.lock",
    "yarn.lock",
}
OPAQUE_ASSET_EXTENSIONS = {
    ".avif",
    ".bmp",
    ".csv",
    ".eot",
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".map",
    ".mp3",
    ".mp4",
    ".otf",
    ".pdf",
    ".png",
    ".svg",
    ".ttf",
    ".webm",
    ".webp",
    ".woff",
    ".woff2",
}
ROOT_SUPPORT_FILES = {
    "crowdin.yml",
    "eslint-suppressions.json",
    "eslint.config.js",
    "i18next.config.ts",
    "jest.config.codeowner.js",
    "jest.config.js",
    "knip.config.ts",
    "lefthook.rc",
    "lefthook.yml",
    "lerna.json",
    "nx.json",
    "playwright.config.ts",
    "playwright.storybook.config.ts",
    "project.json",
    "relyance.yaml",
    "stylelint.config.js",
    "yarn.config.cjs",
}
REPOSITORY_SUPPORT_FILENAMES = {
    ".dockerignore",
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    ".ignore",
    ".npmignore",
    ".prettierignore",
    "license",
    "notice",
}
REPOSITORY_SUPPORT_NAME_PREFIXES = (
    "babel.config.",
    "eslint.config.",
    "jest.config.",
    "playwright.config.",
    "prettier.config.",
    "stylelint.config.",
    "tsconfig.",
    "vite.config.",
    "vitest.config.",
    "webpack.config.",
)


class CampaignError(ValueError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_timestamp() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def digest_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def producer_contract() -> dict[str, Any]:
    path = Path(__file__).resolve().parents[1] / "references/producer-task.md"
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise CampaignError(f"cannot read producer contract {path}: {error}") from error
    return {
        "version": PRODUCER_CONTRACT_VERSION,
        "digest": digest,
    }


def ledger_producer_contract(ledger: dict[str, Any]) -> dict[str, Any]:
    version = ledger.get("producer_contract_version")
    digest = ledger.get("producer_contract_digest")
    if (
        version != PRODUCER_CONTRACT_VERSION
        or isinstance(version, bool)
        or not isinstance(digest, str)
        or not re.fullmatch(r"[0-9a-f]{64}", digest)
    ):
        raise CampaignError(
            "campaign does not use the current producer contract; "
            "start a new campaign"
        )
    return {"version": version, "digest": digest}


def require_current_producer_contract(ledger: dict[str, Any]) -> dict[str, Any]:
    recorded = ledger_producer_contract(ledger)
    current = producer_contract()
    if recorded != current:
        raise CampaignError("producer contract changed; start a new campaign")
    return current


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a positive integer") from error
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CampaignError(f"cannot read JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise CampaignError(f"JSON root must be an object: {path}")
    return value


def validate_id(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not value
        or any(
            not (
                character.isascii()
                and (character.islower() or character.isdigit() or character == "-")
            )
            for character in value
        )
        or value.startswith("-")
        or value.endswith("-")
        or "--" in value
    ):
        raise CampaignError(f"invalid stable ID: {value!r}")
    return value


def validate_relative_path(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CampaignError(f"invalid relative path: {value!r}")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or value.startswith("./"):
        raise CampaignError(f"path must be repository-relative: {value!r}")
    return path.as_posix()


def string_list(
    value: Any,
    field: str,
    *,
    nonempty: bool = False,
) -> list[str]:
    if (
        not isinstance(value, list)
        or (nonempty and not value)
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        qualifier = "nonempty " if nonempty else ""
        raise CampaignError(f"{field} must be a {qualifier}list of strings")
    return list(value)


def document_hashes(spine_root: Path) -> dict[str, str]:
    files = {
        path.relative_to(spine_root).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(spine_root.rglob("*.md"))
        if path.is_file()
    }
    manifest = spine_root / "specspine.json"
    if manifest.is_file():
        files["specspine.json"] = hashlib.sha256(
            manifest.read_bytes()
        ).hexdigest()
    return files


def spine_changes(
    before: dict[str, str],
    after: dict[str, str],
) -> list[dict[str, str]]:
    return [
        {
            "path": path,
            "operation": (
                "created"
                if path not in before
                else "deleted"
                if path not in after
                else "changed"
            ),
        }
        for path in sorted(before.keys() | after.keys())
        if before.get(path) != after.get(path)
    ]


def ledger_spine_snapshot(ledger: dict[str, Any]) -> dict[str, str]:
    raw = ledger.get("spine_snapshot")
    if (
        not isinstance(raw, dict)
        or any(
            not isinstance(path, str)
            or not isinstance(digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
            for path, digest in raw.items()
        )
    ):
        raise CampaignError("campaign Spine snapshot is invalid")
    return dict(raw)


def validate_reported_spine_changes(
    raw: Any,
    actual: list[dict[str, str]],
) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        raise CampaignError("integration changed_documents must be a list")
    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for value in raw:
        if (
            not isinstance(value, dict)
            or set(value) != {"path", "operation"}
            or value.get("operation") not in {"created", "changed", "deleted"}
        ):
            raise CampaignError(
                "each changed document needs path and created/changed/deleted operation"
            )
        path = validate_relative_path(value["path"])
        if Path(path).suffix.lower() != ".md" and path != "specspine.json":
            raise CampaignError(
                f"changed document must be Markdown or specspine.json: {path}"
            )
        if path in seen:
            raise CampaignError(f"duplicate changed document: {path}")
        seen.add(path)
        normalized.append({"path": path, "operation": value["operation"]})
    normalized.sort(key=lambda value: value["path"])
    if normalized != actual:
        raise CampaignError(
            "integration changed_documents does not match workspace changes: "
            + json.dumps(
                {"reported": normalized, "actual": actual},
                ensure_ascii=False,
            )
        )
    return normalized


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(canonical_json(value) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def load(path: Path) -> dict[str, Any]:
    ledger = read_json(path)
    if ledger.get("schema_version") != SCHEMA_VERSION:
        raise CampaignError(
            f"unsupported campaign schema: {ledger.get('schema_version')!r}; "
            f"expected {SCHEMA_VERSION}"
        )
    if not isinstance(ledger.get("tasks"), dict):
        raise CampaignError("campaign tasks are missing")
    if parse_timestamp(ledger.get("created_at")) is None:
        raise CampaignError("campaign created_at timestamp is invalid")
    if parse_timestamp(ledger.get("updated_at")) is None:
        raise CampaignError("campaign updated_at timestamp is invalid")
    ledger_producer_contract(ledger)
    return ledger


@contextlib.contextmanager
def locked_ledger(path: Path) -> Iterator[dict[str, Any]]:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + ".lock")
    with lock_path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        ledger = load(path)
        yield ledger


def save_locked(path: Path, ledger: dict[str, Any]) -> None:
    ledger["revision"] += 1
    ledger["updated_at"] = utc_timestamp()
    atomic_write(path, ledger)


def new_task(raw: dict[str, Any], *, source: str) -> dict[str, Any]:
    task_id = validate_id(raw.get("id"))
    question = raw.get("question")
    reason = raw.get("reason")
    if not isinstance(question, str) or not question.strip():
        raise CampaignError(f"ToDo {task_id} needs a question")
    if not isinstance(reason, str) or not reason.strip():
        raise CampaignError(f"ToDo {task_id} needs a reason")
    evidence = string_list(raw.get("evidence", []), f"ToDo {task_id} evidence")
    documents = [
        validate_relative_path(value)
        for value in string_list(
            raw.get("documents", []),
            f"ToDo {task_id} documents",
        )
    ]
    excludes = string_list(raw.get("excludes", []), f"ToDo {task_id} excludes")
    basis = raw.get("basis", "repository-observation")
    if basis != "repository-observation":
        raise CampaignError(
            f"ToDo {task_id} basis must be repository-observation"
        )
    units = [
        validate_relative_path(value)
        for value in string_list(raw.get("units", []), f"ToDo {task_id} units")
    ]
    architecture_unit = raw.get("architecture_unit")
    if architecture_unit is not None:
        architecture_unit = validate_relative_path(architecture_unit)
    evidence_baseline = raw.get("evidence_baseline")
    if (
        evidence_baseline is not None
        and (
            not isinstance(evidence_baseline, str)
            or EVIDENCE_BASELINE_RE.fullmatch(evidence_baseline) is None
        )
    ):
        raise CampaignError(f"ToDo {task_id} evidence_baseline is invalid")
    evidence_strata = raw.get("evidence_strata", [])
    if not isinstance(evidence_strata, list):
        raise CampaignError(f"ToDo {task_id} evidence_strata must be a list")
    normalized_strata: list[dict[str, str]] = []
    for value in evidence_strata:
        if not isinstance(value, dict) or set(value) != {"id", "sample"}:
            raise CampaignError(
                f"ToDo {task_id} evidence stratum needs id and sample"
            )
        normalized_strata.append(
            {
                "id": validate_id(value["id"]),
                "sample": validate_relative_path(value["sample"]),
            }
        )
    anchor = raw.get("anchor")
    if anchor is not None:
        if not isinstance(anchor, dict):
            raise CampaignError(f"ToDo {task_id} anchor must be an object")
        document = validate_relative_path(anchor.get("document"))
        location = anchor.get("location")
        known = anchor.get("known")
        anchor_question = anchor.get("question")
        if (
            not isinstance(location, str)
            or not location.strip()
            or not isinstance(known, str)
            or not known.strip()
            or not isinstance(anchor_question, str)
            or not anchor_question.strip()
        ):
            raise CampaignError(
                f"ToDo {task_id} anchor needs nonempty location, known, and question"
            )
        if " ".join(anchor_question.split()) != " ".join(question.split()):
            raise CampaignError(
                f"ToDo {task_id} question must exactly match anchor question"
            )
        anchor = {
            "document": document,
            "location": location,
            "known": known,
            "question": anchor_question.strip(),
        }
    return {
        "id": task_id,
        "question": question.strip(),
        "reason": reason.strip(),
        "origin": source,
        "evidence": evidence,
        "documents": documents,
        "excludes": excludes,
        "basis": basis,
        "units": units,
        "architecture_unit": architecture_unit,
        "evidence_baseline": evidence_baseline,
        "evidence_strata": normalized_strata,
        "anchor": anchor,
        "state": "todo",
        "owner": None,
        "attempts": 0,
        "published": [],
        "checkpoint_digest": None,
        "producer_suggestions": [],
        "suggestion_reviews": {},
        "coverage_result": None,
        "answer_result": None,
        "uncertainty_result": None,
        "accepted_staging_root": None,
        "accepted_staging_digest": None,
        "terminal_reason": None,
    }


def task_definition(task: dict[str, Any]) -> dict[str, Any]:
    return {
        key: task.get(key)
        for key in (
            "id",
            "question",
            "reason",
            "origin",
            "evidence",
            "documents",
            "excludes",
            "basis",
            "units",
            "architecture_unit",
            "evidence_baseline",
            "evidence_strata",
            "anchor",
        )
    }


def task_semantics(task: dict[str, Any]) -> dict[str, Any]:
    definition = task_definition(task)
    definition.pop("origin", None)
    return definition


def add_tasks(
    ledger: dict[str, Any],
    raw_tasks: list[Any],
    *,
    source: str,
) -> list[str]:
    added: list[str] = []
    for raw in raw_tasks:
        if not isinstance(raw, dict):
            raise CampaignError("each ToDo entry must be an object")
        task = new_task(raw, source=source)
        existing = ledger["tasks"].get(task["id"])
        if existing is not None:
            if task_semantics(existing) != task_semantics(task):
                raise CampaignError(f"conflicting ToDo ID: {task['id']}")
            continue
        ledger["tasks"][task["id"]] = task
        added.append(task["id"])
    return added


def require_task(ledger: dict[str, Any], task_id: str) -> dict[str, Any]:
    task_id = validate_id(task_id)
    try:
        task = ledger["tasks"][task_id]
    except KeyError as error:
        raise CampaignError(f"unknown ToDo: {task_id}") from error
    if task.get("state") not in TASK_STATES:
        raise CampaignError(f"invalid ToDo state: {task_id}")
    return task


def repository_unit(relative_path: Path) -> str:
    parts = relative_path.parts
    if len(parts) == 1:
        name = parts[0]
        if name in ROOT_GOVERNANCE or name.lower().endswith((".md", ".txt")):
            return "repository-root/governance"
        if name in ROOT_MANIFESTS:
            return "repository-root/manifests"
        if name.lower().startswith(("dockerfile", "compose.")):
            return "repository-root/deployment"
        if name.startswith(".") or name.lower().endswith(
            (".json", ".toml", ".yaml", ".yml")
        ):
            return "repository-root/tooling"
        return "repository-root/runtime"
    first = parts[0]
    if first in COLLAPSED_DIRECTORIES:
        return first
    if first == "public":
        if len(parts) >= 4 and parts[:3] == ("public", "app", "features"):
            if Path(parts[3]).suffix:
                return "public/app/features"
            return Path(*parts[:4]).as_posix()
        if len(parts) >= 3 and parts[1] == "app":
            if Path(parts[2]).suffix:
                return "public/app"
            return Path(*parts[:3]).as_posix()
        if len(parts) >= 2:
            return Path(*parts[:2]).as_posix()
        return first
    if (
        len(parts) >= 3
        and first == "pkg"
        and parts[1]
        in {
            "api",
            "cmd",
            "infra",
            "plugins",
            "registry",
            "services",
            "storage",
            "tsdb",
        }
    ):
        if Path(parts[2]).suffix:
            return Path(*parts[:2]).as_posix()
        return Path(*parts[:3]).as_posix()
    if first in {
        "apps",
        "cmd",
        "internal",
        "kinds",
        "lib",
        "modules",
        "packages",
        "plugins",
        "services",
        "src",
    }:
        if Path(parts[1]).suffix:
            return first
        return Path(*parts[:2]).as_posix()
    return first


def file_classification(path: Path) -> tuple[str, str]:
    """Classify a concrete repository file before it enters the flat inventory."""
    parts = tuple(value.lower() for value in path.parts)
    first = parts[0]
    name = parts[-1]
    if any(value in VENDORED_DIRECTORIES for value in parts):
        return "vendored", "Mechanically identified vendored dependency file"
    if name in DEPENDENCY_LOCK_FILES:
        return "dependency-lock", "Mechanically identified dependency lock/checksum"
    if any(value in GENERATED_DIRECTORIES for value in parts) or (
        name.startswith("zz_generated")
        or name.endswith(
            (
                "_generated.go",
                "_mock.go",
                ".pb.go",
                ".pb.gw.go",
                ".generated.ts",
                ".generated.js",
                ".mock.ts",
                ".mock.tsx",
            )
        )
        or any(marker in name for marker in (".gen.", "_gen.", ".generated."))
    ):
        return "generated", "Mechanically identified generated file"
    if (
        any(value in TEST_COMPONENTS for value in parts[:-1])
        or first.startswith(("e2e-", "test-"))
        or name.endswith(
            ("_test.go", "_test.ts", "_test.tsx", "_spec.ts", "_spec.tsx")
        )
        or any(marker in name for marker in (".test.", ".spec."))
    ):
        return "test-only", "Mechanically identified test or fixture file"
    if path.suffix.lower() in OPAQUE_ASSET_EXTENSIONS or (
        len(parts) >= 2 and parts[:2] == ("public", "locales")
    ):
        return "opaque-asset", "Mechanically identified opaque/static runtime asset"
    if (
        first in REPOSITORY_SUPPORT_UNITS
        or name in REPOSITORY_SUPPORT_FILENAMES
        or name.startswith(("license_", "license.", "notice_", "notice."))
        or name.startswith(REPOSITORY_SUPPORT_NAME_PREFIXES)
        or (len(parts) > 1 and name == "makefile")
        or (
            len(parts) == 1
            and (
                name in ROOT_SUPPORT_FILES
                or (name.startswith(".") and name not in ROOT_MANIFESTS)
            )
        )
    ):
        return (
            "repository-support",
            "Mechanically identified repository governance or collaboration file",
        )
    area = repository_unit(path)
    if (
        area == "repository-root/governance"
        or first in REPOSITORY_SUPPORT_UNITS
        or first in DOCUMENTATION_ROOTS
        or path.suffix.lower() in {".md", ".mdx", ".txt"}
    ):
        return "repository-support", "Mechanically identified documentation or repository support"
    return "queued", "Production-capable file requires producer verification"


def repository_evidence_baseline(
    repository_root: Path,
    inventory_digest: str,
) -> dict[str, str]:
    root = repository_root.resolve()
    commit: str | None = None
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    value = result.stdout.strip()
    if result.returncode == 0 and re.fullmatch(r"[0-9a-fA-F]{40,64}", value):
        commit = value.lower()
    snapshot = inventory_digest[:16]
    source = (
        f"commit-{commit[:16]}-snapshot-{snapshot}"
        if commit is not None
        else f"workspace-snapshot-{snapshot}"
    )
    inspected = utc_now().date().isoformat()
    return {
        "source": source,
        "inspected": inspected,
        "marker": (
            f"<!-- specspine:evidence-baseline source={source}; "
            f"inspected={inspected} -->"
        ),
    }


def verification_task_id(area: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", area.lower()).strip("-") or "root"
    suffix = hashlib.sha256(area.encode()).hexdigest()[:10]
    return f"verify-{slug[:48].rstrip('-')}-{suffix}"


def candidate_owner_documents(
    spine_root: Path,
    area: str,
    members: list[str],
) -> list[str]:
    base_area = area.split("/@", 1)[0]
    parent_counts: dict[str, int] = {}
    for member in members:
        for parent in Path(member).parents:
            value = parent.as_posix()
            if value == ".":
                continue
            parent_counts[value] = parent_counts.get(value, 0) + 1
    threshold = max(2, math.ceil(len(members) / 4))
    focused_parents = sorted(
        (
            value
            for value, count in parent_counts.items()
            if count >= threshold and len(Path(value).parts) >= 2
        ),
        key=lambda value: (-len(Path(value).parts), value),
    )[:6]
    broad = [base_area] if len(Path(base_area).parts) >= 2 else []
    candidates: list[tuple[int, str]] = []
    for path in sorted(spine_root.rglob("*.md")):
        if not path.is_file():
            continue
        body = path.read_text(encoding="utf-8")
        score = (
            100 * sum(value in body for value in members)
            + 10 * sum(value in body for value in focused_parents)
            + sum(value in body for value in broad)
        )
        if score:
            candidates.append((score, path.relative_to(spine_root).as_posix()))
    return [
        path
        for _, path in sorted(candidates, key=lambda value: (-value[0], value[1]))[
            :MAX_CANDIDATE_DOCUMENTS
        ]
    ]


def is_probably_text(path: Path) -> bool:
    with path.open("rb") as stream:
        sample = stream.read(8192)
    if b"\0" in sample:
        return False
    try:
        sample.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def repository_inventory(
    repository_root: Path,
    *,
    spine_root: Path | None = None,
) -> dict[str, Any]:
    root = repository_root.resolve()
    if not root.is_dir():
        raise CampaignError(f"repository root is not a directory: {root}")
    excluded_spine: Path | None = None
    if spine_root is not None:
        resolved_spine = spine_root.resolve()
        try:
            resolved_spine.relative_to(root)
        except ValueError:
            pass
        else:
            excluded_spine = resolved_spine

    production_files: list[str] = []
    excluded: dict[str, list[str]] = {
        classification: []
        for classification in SOURCE_CLASSIFICATIONS
        if classification != "queued"
    }
    excluded_directories: list[dict[str, str]] = []
    snapshot = hashlib.sha256()
    for directory, names, files in os.walk(root):
        current = Path(directory)
        names.sort()
        files.sort()
        if excluded_spine is not None and (
            current == excluded_spine or excluded_spine in current.parents
        ):
            names[:] = []
            continue
        relative_directory = current.relative_to(root)
        if relative_directory.parts and relative_directory.parts[0] == ".git":
            names[:] = []
            continue
        collapsed = [
            name for name in names if name in COLLAPSED_DIRECTORIES and name != ".git"
        ]
        for name in collapsed:
            area_path = (relative_directory / name).as_posix()
            stat = (current / name).stat()
            snapshot.update(
                f"D\0{area_path}\0{stat.st_size}\0{stat.st_mtime_ns}\n".encode()
            )
            classification = (
                "vendored" if name in VENDORED_DIRECTORIES else "generated"
            )
            excluded_directories.append(
                {"path": area_path + "/", "classification": classification}
            )
            names.remove(name)
        for filename in files:
            path = relative_directory / filename
            source = current / filename
            snapshot.update(f"F\0{path.as_posix()}\0".encode())
            with source.open("rb") as stream:
                while chunk := stream.read(1024 * 1024):
                    snapshot.update(chunk)
            snapshot.update(b"\n")
            classification, _ = file_classification(path)
            if classification == "queued" and not is_probably_text(source):
                classification = "opaque-asset"
            if classification == "queued":
                production_files.append(path.as_posix())
            else:
                excluded[classification].append(path.as_posix())
    return {
        "repository_root": str(root),
        "production_files": sorted(production_files),
        "excluded": {
            classification: sorted(paths)
            for classification, paths in sorted(excluded.items())
        },
        "excluded_directories": sorted(
            excluded_directories,
            key=lambda value: (value["path"], value["classification"]),
        ),
        "digest": snapshot.hexdigest(),
    }


def validate_integration_evidence(
    spine_root: Path,
    inspected: Any,
    *,
    field: str,
) -> dict[str, str]:
    documents = document_hashes(spine_root)
    paths = {
        validate_relative_path(value)
        for value in string_list(inspected, field, nonempty=True)
    }
    unknown = paths - set(documents)
    if unknown:
        raise CampaignError(
            f"{field} must name only workspace Markdown documents; "
            f"unknown={sorted(unknown)}"
        )
    return documents


def validate_empty_reason(
    todo: list[Any],
    terminal_reason: Any,
    *,
    prefix: str,
) -> None:
    if todo:
        if terminal_reason is not None:
            raise CampaignError("terminal_reason must be null when ToDo is nonempty")
    elif (
        not isinstance(terminal_reason, str)
        or not terminal_reason.startswith(prefix)
    ):
        raise CampaignError(f"empty ToDo requires '{prefix}<reason>'")


def command_init(args: argparse.Namespace) -> dict[str, Any]:
    if args.ledger.exists():
        raise CampaignError(f"campaign already exists: {args.ledger}")
    timestamp = utc_timestamp()
    contract = producer_contract()
    ledger = {
        "schema_version": SCHEMA_VERSION,
        "campaign_id": str(uuid.uuid4()),
        "revision": 0,
        "created_at": timestamp,
        "updated_at": timestamp,
        "repository_root": (
            str(args.repository_root.resolve())
            if args.repository_root is not None
            else None
        ),
        "scope": args.scope,
        "root_question": args.root_question,
        "spine_state": args.spine_state,
        "producer_contract_version": contract["version"],
        "producer_contract_digest": contract["digest"],
        "tasks": {},
        "used_producers": {},
        "publication_epoch": 0,
        "publication_history": [],
        "document_change_history": [],
        "documentation_seed": None,
        "spine_snapshot": None,
        "source_pass": None,
        "integration_pass": None,
        "resume_history": [],
    }
    atomic_write(args.ledger, ledger)
    return ledger


def command_seed_from_spine(args: argparse.Namespace) -> dict[str, Any]:
    spine_root = args.spine_root.resolve()
    current = load(args.ledger)
    if current["spine_state"] != "existing":
        raise CampaignError("seed-from-spine requires --spine-state existing")
    findings = run_checker(
        args.checker,
        spine_root,
        repository_root=repository_root_from_ledger(current),
        allow_material=True,
    )
    envelope_blockers = [
        value
        for value in findings
        if isinstance(value, dict)
        and value.get("code") in V3_ENVELOPE_BLOCKER_CODES
    ]
    if envelope_blockers:
        raise CampaignError(
            "seed-from-spine accepts only the current SpecSpine v3 format: "
            + json.dumps(envelope_blockers, ensure_ascii=False)
        )
    documents = document_hashes(spine_root)
    if not documents:
        raise CampaignError("seed-from-spine requires live Markdown documents")
    baseline = sorted(
        {
            canonical_json(normalize_checker_finding(value)).decode("utf-8")
            for value in findings
            if isinstance(value, dict)
            and value.get("code") not in DEFERRED_CHECKER_CODES
        }
    )
    with locked_ledger(args.ledger) as ledger:
        if ledger["documentation_seed"] is not None:
            raise CampaignError("documentation seed already exists")
        ledger["documentation_seed"] = {
            "documents": documents,
            "checker_baseline": [
                json.loads(value)
                for value in baseline
            ],
            "todo": [],
            "terminal_reason": (
                "mechanical documentation index only; source verification and "
                "integration derive bounded ToDo"
            ),
        }
        save_locked(args.ledger, ledger)
        return {
            "status": "seeded",
            "campaign_id": ledger["campaign_id"],
            "documents": len(documents),
            "checker_baseline_findings": len(baseline),
            "added_todo": [],
            "revision": ledger["revision"],
        }


def command_inventory(args: argparse.Namespace) -> dict[str, Any]:
    inventory = repository_inventory(
        args.repository_root,
        spine_root=args.spine_root,
    )
    if args.output is None:
        return inventory
    if args.output.exists():
        raise CampaignError(f"inventory output already exists: {args.output}")
    atomic_write(args.output, inventory)
    return {
        "status": "written",
        "inventory": str(args.output.resolve()),
        "production_files": len(inventory["production_files"]),
        "excluded_files": sum(len(value) for value in inventory["excluded"].values()),
        "digest": inventory["digest"],
    }


def command_planning_packets(args: argparse.Namespace) -> dict[str, Any]:
    inventory = read_json(args.inventory)
    files = string_list(
        inventory.get("production_files"),
        "inventory production_files",
    )
    repository_root = inventory.get("repository_root")
    digest = inventory.get("digest")
    if not isinstance(repository_root, str) or not isinstance(digest, str):
        raise CampaignError("planning inventory metadata is invalid")
    if args.output_dir.exists():
        raise CampaignError(f"planning packet directory already exists: {args.output_dir}")
    args.output_dir.mkdir(parents=True)
    packets: list[str] = []
    for offset in range(0, len(files), args.page_size):
        index = offset // args.page_size + 1
        packet = {
            "planning_contract_version": 1,
            "repository_root": repository_root,
            "inventory_digest": digest,
            "page": index,
            "production_files": files[offset : offset + args.page_size],
        }
        path = args.output_dir / f"page-{index:04d}.json"
        atomic_write(path, packet)
        packets.append(str(path.resolve()))
    return {
        "status": "written",
        "packets": packets,
        "packet_count": len(packets),
        "production_files": len(files),
    }


def validate_planning_result(
    packet: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    if set(result) != {"page", "topics", "supporting"}:
        raise CampaignError("planning result needs exactly page, topics, and supporting")
    if result["page"] != packet.get("page"):
        raise CampaignError("planning result page does not match its packet")
    assigned = set(
        string_list(
            packet.get("production_files"),
            "planning packet production_files",
        )
    )
    if not isinstance(result["topics"], list) or not isinstance(
        result["supporting"], list
    ):
        raise CampaignError("planning result topics and supporting must be lists")
    topics: list[dict[str, Any]] = []
    topic_ids: set[str] = set()
    topic_files: set[str] = set()
    for value in result["topics"]:
        if not isinstance(value, dict) or set(value) != {
            "id",
            "title",
            "responsibility",
            "reason",
            "files",
        }:
            raise CampaignError(
                "planning topic needs id, title, responsibility, reason, and files"
            )
        topic_id = validate_id(value["id"])
        if topic_id in topic_ids:
            raise CampaignError(f"duplicate planning topic id: {topic_id}")
        topic_ids.add(topic_id)
        texts = [value["title"], value["responsibility"], value["reason"]]
        if any(not isinstance(text, str) or not text.strip() for text in texts):
            raise CampaignError(f"planning topic {topic_id} has empty text")
        files = [
            validate_relative_path(item)
            for item in string_list(
                value["files"],
                f"planning topic {topic_id} files",
                nonempty=True,
            )
        ]
        unknown = sorted(set(files) - assigned)
        if unknown:
            raise CampaignError(
                f"planning topic {topic_id} uses files outside its page: {unknown}"
            )
        topic_files.update(files)
        topics.append(
            {
                "id": topic_id,
                "title": value["title"].strip(),
                "responsibility": value["responsibility"].strip(),
                "reason": value["reason"].strip(),
                "files": sorted(set(files)),
            }
        )
    supporting: list[dict[str, Any]] = []
    supporting_files: set[str] = set()
    for index, value in enumerate(result["supporting"], start=1):
        if not isinstance(value, dict) or set(value) != {"reason", "files"}:
            raise CampaignError("planning supporting entry needs reason and files")
        reason = value["reason"]
        if not isinstance(reason, str) or not reason.strip():
            raise CampaignError(f"planning supporting entry {index} needs a reason")
        files = [
            validate_relative_path(item)
            for item in string_list(
                value["files"],
                f"planning supporting entry {index} files",
                nonempty=True,
            )
        ]
        unknown = sorted(set(files) - assigned)
        if unknown:
            raise CampaignError(
                f"planning supporting entry {index} uses files outside its page: {unknown}"
            )
        overlap = sorted(set(files) & supporting_files)
        if overlap:
            raise CampaignError(f"planning supporting files are repeated: {overlap}")
        supporting_files.update(files)
        supporting.append({"reason": reason.strip(), "files": sorted(set(files))})
    conflict = sorted(topic_files & supporting_files)
    if conflict:
        raise CampaignError(
            f"planning files cannot be both topic and supporting: {conflict}"
        )
    missing = sorted(assigned - topic_files - supporting_files)
    if missing:
        raise CampaignError(f"planning result leaves page files uncovered: {missing}")
    return {
        "page": packet["page"],
        "topics": topics,
        "supporting": supporting,
    }


def command_planning_collect(args: argparse.Namespace) -> dict[str, Any]:
    if args.output.exists():
        raise CampaignError(f"planning corpus output already exists: {args.output}")
    packet_paths = sorted(args.packets_dir.glob("page-*.json"))
    if not packet_paths:
        raise CampaignError("planning packet directory is empty")
    pages: list[dict[str, Any]] = []
    repository_root: str | None = None
    inventory_digest: str | None = None
    for packet_path in packet_paths:
        result_path = args.results_dir / packet_path.name
        if not result_path.is_file():
            raise CampaignError(f"missing planning result: {result_path}")
        packet = read_json(packet_path)
        if repository_root is None:
            repository_root = packet.get("repository_root")
            inventory_digest = packet.get("inventory_digest")
        elif (
            packet.get("repository_root") != repository_root
            or packet.get("inventory_digest") != inventory_digest
        ):
            raise CampaignError("planning packets do not share one inventory snapshot")
        pages.append(validate_planning_result(packet, read_json(result_path)))
    extra = sorted(
        path.name
        for path in args.results_dir.glob("page-*.json")
        if not (args.packets_dir / path.name).is_file()
    )
    if extra:
        raise CampaignError(f"planning results have unknown pages: {extra}")
    corpus = {
        "planning_contract_version": 1,
        "repository_root": repository_root,
        "inventory_digest": inventory_digest,
        "pages": pages,
    }
    atomic_write(args.output, corpus)
    return {
        "status": "written",
        "corpus": str(args.output.resolve()),
        "pages": len(pages),
        "candidate_topics": sum(len(value["topics"]) for value in pages),
    }


def validate_topic_plan(
    path: Path,
    production_files: list[str],
    spine_root: Path,
) -> dict[str, Any]:
    raw = read_json(path)
    if set(raw) != {"topics", "covered", "supporting"}:
        raise CampaignError(
            "topic plan needs exactly topics, covered, and supporting"
        )
    if any(
        not isinstance(raw[field], list)
        for field in ("topics", "covered", "supporting")
    ):
        raise CampaignError(
            "topic plan topics, covered, and supporting must be lists"
        )
    production = set(production_files)
    topics: list[dict[str, Any]] = []
    topic_ids: set[str] = set()
    topic_files: set[str] = set()

    def normalize_topic(value: Any, *, field: str) -> dict[str, Any]:
        if not isinstance(value, dict) or set(value) != {
            "id",
            "title",
            "responsibility",
            "reason",
            "files",
        }:
            raise CampaignError(
                f"each {field} topic needs id, title, responsibility, reason, and files"
            )
        topic_id = validate_id(value["id"])
        if topic_id in topic_ids:
            raise CampaignError(f"duplicate topic id: {topic_id}")
        topic_ids.add(topic_id)
        title = value["title"]
        responsibility = value["responsibility"]
        reason = value["reason"]
        if any(
            not isinstance(text, str) or not text.strip()
            for text in (title, responsibility, reason)
        ):
            raise CampaignError(f"topic {topic_id} text fields must be nonempty")
        files = [
            validate_relative_path(item)
            for item in string_list(
                value["files"],
                f"{field} topic {topic_id} files",
                nonempty=True,
            )
        ]
        if len(files) != len(set(files)):
            raise CampaignError(
                f"{field} topic {topic_id} contains duplicate files"
            )
        if len(files) > MAX_UNIT_FILES:
            raise CampaignError(
                f"{field} topic {topic_id} exceeds "
                f"{MAX_UNIT_FILES} production files"
            )
        unknown = sorted(set(files) - production)
        if unknown:
            raise CampaignError(
                f"{field} topic {topic_id} has unknown files: {unknown}"
            )
        return {
            "id": topic_id,
            "title": title.strip(),
            "responsibility": responsibility.strip(),
            "reason": reason.strip(),
            "files": sorted(files),
        }

    for value in raw["topics"]:
        topic = normalize_topic(value, field="uncovered")
        topic_files.update(topic["files"])
        topics.append(topic)

    covered_topics: list[dict[str, Any]] = []
    covered_files: set[str] = set()
    for value in raw["covered"]:
        if not isinstance(value, dict) or set(value) != {
            "id",
            "title",
            "responsibility",
            "reason",
            "files",
            "coverage_reason",
            "coverage",
        }:
            raise CampaignError(
                "each covered topic needs id, title, responsibility, reason, "
                "files, coverage_reason, and coverage"
            )
        topic = normalize_topic(
            {
                key: value[key]
                for key in ("id", "title", "responsibility", "reason", "files")
            },
            field="covered",
        )
        coverage_reason = value["coverage_reason"]
        if not isinstance(coverage_reason, str) or not coverage_reason.strip():
            raise CampaignError(
                f"covered topic {topic['id']} needs a coverage_reason"
            )
        if not isinstance(value["coverage"], list) or not value["coverage"]:
            raise CampaignError(
                f"covered topic {topic['id']} needs nonempty coverage"
            )
        citations: list[dict[str, Any]] = []
        seen_documents: set[str] = set()
        for citation in value["coverage"]:
            if not isinstance(citation, dict) or set(citation) != {
                "document",
                "claims",
            }:
                raise CampaignError(
                    f"covered topic {topic['id']} coverage needs document and claims"
                )
            document = validate_relative_path(citation["document"])
            if not document.endswith(".md"):
                raise CampaignError(
                    f"covered topic {topic['id']} document must be Markdown: "
                    f"{document}"
                )
            if document in seen_documents:
                raise CampaignError(
                    f"covered topic {topic['id']} repeats document: {document}"
                )
            seen_documents.add(document)
            document_path = spine_root.resolve() / document
            try:
                document_path.resolve().relative_to(spine_root.resolve())
            except ValueError as error:
                raise CampaignError(
                    f"covered topic {topic['id']} document escapes Spine: {document}"
                ) from error
            if not document_path.is_file():
                raise CampaignError(
                    f"covered topic {topic['id']} document does not exist: {document}"
                )
            claims = string_list(
                citation["claims"],
                f"covered topic {topic['id']} claims",
                nonempty=True,
            )
            if len(claims) != len(set(claims)):
                raise CampaignError(
                    f"covered topic {topic['id']} repeats semantic claims"
                )
            body = document_path.read_text(encoding="utf-8")
            for claim in claims:
                if COVERAGE_CLAIM_ID_RE.fullmatch(claim) is None:
                    raise CampaignError(
                        f"covered topic {topic['id']} has invalid semantic claim: "
                        f"{claim}"
                    )
                definition = re.compile(
                    rf"^ {{0,3}}[-+*]\s+\*\*{re.escape(claim)}\*\*"
                    rf"\s+—\s+\S",
                    re.MULTILINE,
                )
                if definition.search(body) is None:
                    raise CampaignError(
                        f"covered topic {topic['id']} claim is not defined in "
                        f"{document}: {claim}"
                    )
            citations.append({"document": document, "claims": sorted(claims)})
        covered_files.update(topic["files"])
        covered_topics.append(
            topic
            | {
                "coverage_reason": coverage_reason.strip(),
                "coverage": sorted(
                    citations,
                    key=lambda citation: citation["document"],
                ),
            }
        )

    supporting: list[dict[str, Any]] = []
    supporting_files: set[str] = set()
    for index, value in enumerate(raw["supporting"], start=1):
        if not isinstance(value, dict) or set(value) != {"reason", "files"}:
            raise CampaignError("each supporting entry needs reason and files")
        reason = value["reason"]
        if not isinstance(reason, str) or not reason.strip():
            raise CampaignError(f"supporting entry {index} needs a reason")
        files = [
            validate_relative_path(item)
            for item in string_list(
                value["files"],
                f"supporting entry {index} files",
                nonempty=True,
            )
        ]
        if len(files) != len(set(files)):
            raise CampaignError(f"supporting entry {index} contains duplicate files")
        unknown = sorted(set(files) - production)
        if unknown:
            raise CampaignError(f"supporting entry {index} has unknown files: {unknown}")
        overlap = sorted(set(files) & supporting_files)
        if overlap:
            raise CampaignError(f"supporting files are repeated: {overlap}")
        supporting_files.update(files)
        supporting.append({"reason": reason.strip(), "files": sorted(files)})
    conflict = sorted((topic_files | covered_files) & supporting_files)
    if conflict:
        raise CampaignError(
            f"files cannot be both topic-covered and supporting: {conflict}"
        )
    accounted = topic_files | covered_files | supporting_files
    missing = sorted(production - accounted)
    if missing:
        raise CampaignError(f"topic plan leaves production files uncovered: {missing}")
    normalized_topics = sorted(topics, key=lambda value: value["id"])
    normalized_covered = sorted(
        covered_topics,
        key=lambda value: value["id"],
    )
    normalized_supporting = sorted(
        supporting,
        key=lambda value: (value["files"], value["reason"]),
    )
    return {
        "topics": normalized_topics,
        "covered": normalized_covered,
        "supporting": normalized_supporting,
        "production_files": sorted(production),
        "digest": digest_json(
            {
                "topics": normalized_topics,
                "covered": normalized_covered,
                "supporting": normalized_supporting,
            }
        ),
    }


def command_source_pass(args: argparse.Namespace) -> dict[str, Any]:
    current = load(args.ledger)
    if current["spine_state"] == "existing" and current["documentation_seed"] is None:
        raise CampaignError("seed-from-spine is required before source-pass")
    run_checker(
        args.checker,
        args.spine_root.resolve(),
        repository_root=args.repository_root.resolve(),
        allowed_findings=checker_baseline_fingerprints(current),
    )
    inventory = repository_inventory(
        args.repository_root,
        spine_root=args.spine_root,
    )
    evidence_baseline = repository_evidence_baseline(
        args.repository_root,
        inventory["digest"],
    )
    if args.topic_plan is None:
        raise CampaignError("source-pass requires a synthesized --topic-plan")
    plan = validate_topic_plan(
        args.topic_plan,
        inventory["production_files"],
        args.spine_root,
    )
    raw_todo: list[dict[str, Any]] = []
    topic_tasks: dict[str, str] = {}
    for topic in plan["topics"]:
        task_id = verification_task_id(f"topic/{topic['id']}")
        topic_tasks[topic["id"]] = task_id
        candidates = candidate_owner_documents(
            args.spine_root.resolve(),
            topic["id"],
            topic["files"],
        )
        raw_todo.append(
            {
                "id": task_id,
                "question": (
                    f"Verify observed architecture topic {topic['title']}: "
                    f"{topic['responsibility']}"
                ),
                "reason": topic["reason"],
                "evidence": topic["files"],
                "documents": candidates,
                "excludes": [],
                "units": [f"topics/{topic['id']}"],
                "architecture_unit": f"topics/{topic['id']}",
                "evidence_baseline": evidence_baseline["marker"],
                "evidence_strata": [
                    {"id": f"file-{index:03d}", "sample": path}
                    for index, path in enumerate(topic["files"], start=1)
                ],
                "anchor": None,
            }
        )
    with locked_ledger(args.ledger) as ledger:
        if ledger["source_pass"] is not None:
            raise CampaignError("source-pass is immutable once recorded")
        added = add_tasks(ledger, raw_todo, source="source-pass")
        ledger["source_pass"] = {
            "repository_root": str(args.repository_root.resolve()),
            "spine_root": str(args.spine_root.resolve()),
            "inventory_digest": inventory["digest"],
            "evidence_baseline": evidence_baseline,
            "production_files": inventory["production_files"],
            "excluded": inventory["excluded"],
            "excluded_directories": inventory["excluded_directories"],
            "topic_plan": plan,
            "topic_tasks": topic_tasks,
            "todo": sorted(value["id"] for value in raw_todo),
            "terminal_reason": None,
            "publication_epoch": ledger["publication_epoch"],
        }
        ledger["spine_snapshot"] = document_hashes(args.spine_root.resolve())
        ledger.setdefault("document_change_history", [])
        save_locked(args.ledger, ledger)
        return {
            "status": "recorded",
            "production_files": len(inventory["production_files"]),
            "topics": len(plan["topics"]),
            "covered_topics": len(plan["covered"]),
            "supporting_groups": len(plan["supporting"]),
            "verification_todo": len(raw_todo),
            "added_todo_count": len(added),
            "revision": ledger["revision"],
        }


def command_todo_add(args: argparse.Namespace) -> dict[str, Any]:
    raw = {
        "id": args.id,
        "question": args.question,
        "reason": args.reason,
        "evidence": args.evidence,
        "documents": args.document,
        "excludes": args.exclude,
    }
    with locked_ledger(args.ledger) as ledger:
        added = add_tasks(ledger, [raw], source=args.origin)
        if added:
            ledger["integration_pass"] = None
        save_locked(args.ledger, ledger)
        return {
            "status": "added" if added else "already-present",
            "added_todo": added,
            "revision": ledger["revision"],
        }


def command_todo(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    tasks = [
        task_definition(task)
        | {
            "state": task["state"],
            "attempts": task["attempts"],
            "terminal_reason": task["terminal_reason"],
        }
        for task in sorted(ledger["tasks"].values(), key=lambda value: value["id"])
        if args.all or task["state"] in {"todo", "assigned", "published", "blocked"}
    ]
    selected = tasks[: args.limit] if args.limit is not None else tasks
    return {
        "campaign_id": ledger["campaign_id"],
        "todo": selected,
        "returned": len(selected),
        "total": len(tasks),
    }


def source_task_priority(task: dict[str, Any]) -> tuple[int, int, str]:
    ranked: list[tuple[int, int]] = []
    for value in task.get("evidence", []):
        path = Path(value)
        parts = path.parts
        area = repository_unit(path)
        if area in {"repository-root/runtime", "repository-root/deployment"}:
            tier = 0
        elif area == "repository-root/manifests":
            tier = 1
        elif parts[:1] == ("cmd",) or parts[:2] == ("pkg", "cmd"):
            tier = 2
        elif parts[:1] in {("apps",), ("kinds",), ("pkg",)}:
            tier = 3
        elif parts[:1] in {("public",), ("packages",), ("plugins",)}:
            tier = 4
        elif area == "repository-root/tooling" or parts[:1] in {
            (".github",),
            (".citools",),
            ("scripts",),
            ("tools",),
        }:
            tier = 6
        else:
            tier = 5
        ranked.append((tier, len(parts)))
    priority = min(ranked) if ranked else (5, 0)
    return priority[0], priority[1], task["id"]


def breadth_order(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source = [task for task in tasks if task.get("origin") == "source-pass"]
    derived = [task for task in tasks if task.get("origin") != "source-pass"]
    bootstrap_open = any(source_task_priority(task)[0] <= 2 for task in source)
    ranked: list[tuple[tuple[int, int, str], str, dict[str, Any]]] = []
    for task in source:
        priority = source_task_priority(task)
        unit = task.get("architecture_unit") or task.get("units", [""])[0]
        family = Path(unit).parts[0] if unit else task["id"]
        ranked.append((priority, family, task))
    derived_tier = 5 if bootstrap_open else 2
    for task in derived:
        ranked.append(((derived_tier, 0, task["id"]), "integration", task))

    ordered: list[dict[str, Any]] = []
    remaining = sorted(ranked, key=lambda value: (value[0], value[1]))
    while remaining:
        tier = remaining[0][0][0]
        tier_rows = [value for value in remaining if value[0][0] == tier]
        other_rows = [value for value in remaining if value[0][0] != tier]
        families: dict[str, list[tuple[tuple[int, int, str], str, dict[str, Any]]]] = {}
        for row in tier_rows:
            families.setdefault(row[1], []).append(row)
        while families:
            for family in sorted(list(families)):
                rows = families[family]
                ordered.append(rows.pop(0)[2])
                if not rows:
                    del families[family]
        remaining = other_rows
    return ordered


def command_ready(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    ordered = breadth_order(
        [
            task
            for task in ledger["tasks"].values()
            if task["state"] == "todo"
        ]
    )
    ready = [task["id"] for task in ordered]
    limit = args.limit if args.limit is not None else len(ready)
    selected: list[str] = []
    selected_units: set[str] = set()
    for task in ordered:
        architecture_unit = task.get("architecture_unit") or task["id"]
        if architecture_unit in selected_units:
            continue
        selected.append(task["id"])
        selected_units.add(architecture_unit)
        if len(selected) == limit:
            break
    return {
        "campaign_id": ledger["campaign_id"],
        "ready": selected,
        "returned": len(selected),
        "total": len(ready),
    }


def ledger_repository_root(ledger: dict[str, Any]) -> Path | None:
    source_pass = ledger.get("source_pass")
    raw = (
        source_pass.get("repository_root")
        if isinstance(source_pass, dict)
        else ledger.get("repository_root")
    )
    if not isinstance(raw, str) or not raw:
        return None
    return Path(raw).resolve()


def incomplete_reason(ledger: dict[str, Any]) -> str | None:
    states = {
        state: sum(
            task.get("state") == state for task in ledger["tasks"].values()
        )
        for state in TASK_STATES
    }
    if any(states[state] for state in ("todo", "assigned", "review", "published")):
        return "actionable_tasks"
    if ledger.get("source_pass") is None:
        return "source_pass_missing"
    if states["blocked"]:
        return None
    integration = ledger.get("integration_pass")
    if (
        not isinstance(integration, dict)
        or integration.get("publication_epoch") != ledger.get("publication_epoch")
        or integration.get("todo")
    ):
        return "integration_incomplete"
    return None


def campaign_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    result: list[Path] = []
    for directory, names, files in os.walk(root, followlinks=False):
        names[:] = sorted(
            name
            for name in names
            if not (Path(directory) / name).is_symlink()
        )
        if "campaign.json" in files:
            path = Path(directory) / "campaign.json"
            if path.is_file() and not path.is_symlink():
                result.append(path)
    return sorted(result)


def command_discover(args: argparse.Namespace) -> dict[str, Any]:
    if not math.isfinite(args.recent_hours) or args.recent_hours <= 0:
        raise CampaignError("recent-hours must be positive")
    repository_root = args.repository_root.resolve()
    now = utc_now()
    recent_seconds = args.recent_hours * 3600
    campaigns: list[dict[str, Any]] = []
    invalid: list[dict[str, str]] = []
    for path in campaign_files(args.campaign_home.resolve()):
        try:
            ledger = load(path)
        except (CampaignError, OSError, UnicodeError) as error:
            invalid.append({"ledger": str(path), "error": str(error)})
            continue
        if ledger_repository_root(ledger) != repository_root:
            continue
        reason = incomplete_reason(ledger)
        if reason is None:
            continue
        activity = parse_timestamp(ledger["updated_at"])
        assert activity is not None
        age_seconds = max(0, int((now - activity).total_seconds()))
        source_current: bool | None = (
            current_inventory(ledger)
            if isinstance(ledger.get("source_pass"), dict)
            else None
        )
        recent = age_seconds <= recent_seconds
        resume_allowed = source_current is not False
        recommendation = (
            "resume"
            if recent and resume_allowed
            else "new"
        )
        states = {
            state: sum(
                task.get("state") == state
                for task in ledger["tasks"].values()
            )
            for state in sorted(TASK_STATES)
        }
        campaigns.append(
            {
                "ledger": str(path.resolve()),
                "campaign_id": ledger["campaign_id"],
                "scope": ledger["scope"],
                "last_activity": activity.isoformat().replace("+00:00", "Z"),
                "age_seconds": age_seconds,
                "recency": "recent" if recent else "stale",
                "recent_hours": args.recent_hours,
                "source_current": source_current,
                "resume_allowed": resume_allowed,
                "recommendation": recommendation,
                "requires_operator_choice": True,
                "incomplete_reason": reason,
                "states": states,
            }
        )
    campaigns.sort(key=lambda value: (value["age_seconds"], value["ledger"]))
    return {
        "repository_root": str(repository_root),
        "campaign_home": str(args.campaign_home.resolve()),
        "campaigns": campaigns,
        "invalid_ledgers": invalid,
        "requires_operator_choice": bool(campaigns),
    }


def command_resume_session(args: argparse.Namespace) -> dict[str, Any]:
    with locked_ledger(args.ledger) as ledger:
        if incomplete_reason(ledger) is None:
            raise CampaignError("campaign is not resumable")
        if isinstance(ledger.get("source_pass"), dict) and not current_inventory(ledger):
            raise CampaignError(
                "campaign source snapshot changed; start a new campaign"
            )
        current_contract = require_current_producer_contract(ledger)
        released = sorted(
            task["id"]
            for task in ledger["tasks"].values()
            if task["state"] == "assigned"
        )
        for task_id in released:
            task = ledger["tasks"][task_id]
            task["state"] = "todo"
            task["owner"] = None
        resumed_at = utc_timestamp()
        ledger.setdefault("resume_history", []).append(
            {
                "resumed_at": resumed_at,
                "released_orphaned_tasks": released,
            }
        )
        save_locked(args.ledger, ledger)
        return {
            "status": "resumed",
            "campaign_id": ledger["campaign_id"],
            "resumed_at": resumed_at,
            "released_orphaned_tasks": released,
            "producer_contract": current_contract,
            "revision": ledger["revision"],
        }


def command_packet(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    contract = require_current_producer_contract(ledger)
    task = require_task(ledger, args.id)
    if task["state"] != "todo":
        raise CampaignError(f"packet requires todo state: {args.id}")
    packet = {
        "campaign_id": ledger["campaign_id"],
        "producer_contract": contract,
        "task": task_definition(task),
    }
    if args.output is None:
        return packet
    if args.output.exists():
        raise CampaignError(f"packet output already exists: {args.output}")
    atomic_write(args.output, packet)
    return {
        "status": "written",
        "task": task["id"],
        "packet": str(args.output.resolve()),
    }


def command_assign(args: argparse.Namespace) -> dict[str, Any]:
    with locked_ledger(args.ledger) as ledger:
        task = require_task(ledger, args.id)
        if task["state"] != "todo":
            raise CampaignError(f"assign requires todo state: {args.id}")
        if args.owner in ledger["used_producers"]:
            previous = ledger["used_producers"][args.owner]
            raise CampaignError(
                f"one producer may run only one task: {args.owner} already ran {previous}"
            )
        task["state"] = "assigned"
        task["owner"] = args.owner
        task["attempts"] += 1
        ledger["used_producers"][args.owner] = task["id"]
        save_locked(args.ledger, ledger)
        return {
            "status": "assigned",
            "task": task_definition(task),
            "owner": args.owner,
            "revision": ledger["revision"],
        }


def command_release(args: argparse.Namespace) -> dict[str, Any]:
    with locked_ledger(args.ledger) as ledger:
        task = require_task(ledger, args.id)
        if task["state"] != "assigned":
            raise CampaignError(f"release requires assigned state: {args.id}")
        task["state"] = "todo"
        task["owner"] = None
        save_locked(args.ledger, ledger)
        return {
            "status": "released",
            "task": args.id,
            "revision": ledger["revision"],
        }


def candidate_files(root: Path) -> dict[str, Path]:
    if not root.is_dir():
        raise CampaignError(f"staging root is not a directory: {root}")
    result: dict[str, Path] = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise CampaignError(f"staging contains symbolic link: {path}")
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            if path.suffix.lower() != ".md":
                raise CampaignError(f"staging may contain only Markdown files: {relative}")
            if relative == "README.md":
                raise CampaignError("producer must not publish README.md")
            result[relative] = path
    return result


def normalize_directions(task_id: str, raw: Any) -> list[dict[str, str]]:
    directions = string_list(raw, "checkpoint directions")
    suggestions: list[dict[str, str]] = []
    seen: set[str] = set()
    for question in directions:
        question = question.strip()
        suggestion_id = (
            "direction-"
            + hashlib.sha256(f"{task_id}\0{question}".encode()).hexdigest()[:16]
        )
        if suggestion_id in seen:
            continue
        seen.add(suggestion_id)
        suggestions.append({"id": suggestion_id, "question": question})
    return suggestions


def infer_candidates(
    staging: dict[str, Path],
    spine_root: Path,
) -> list[dict[str, str]]:
    return [
        {
            "path": path,
            "operation": "replace" if (spine_root / path).exists() else "create",
        }
        for path in sorted(staging)
    ]


def staging_digest(staging: dict[str, Path]) -> str:
    return digest_json(
        {
            relative: hashlib.sha256(path.read_bytes()).hexdigest()
            for relative, path in sorted(staging.items())
        }
    )


def validate_checkpoint(
    raw: dict[str, Any],
    staging: dict[str, Path],
) -> tuple[
    str,
    list[str],
    dict[str, Any] | None,
]:
    allowed = {"outcome", "evidence", "summary", "owner", "directions", "need", "reason"}
    unknown = set(raw) - allowed
    if unknown:
        raise CampaignError(f"unknown checkpoint fields: {sorted(unknown)}")
    status = raw.get("outcome")
    if status not in CHECKPOINT_STATUSES:
        raise CampaignError(f"invalid checkpoint outcome: {status!r}")
    string_list(
        raw.get("evidence"),
        "checkpoint evidence",
        nonempty=True,
    )
    summary = raw.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise CampaignError("checkpoint summary must be nonempty")
    directions = string_list(raw.get("directions", []), "checkpoint directions")
    if status not in {"draft", "covered", "answered"} and directions:
        raise CampaignError(
            f"{status} cannot emit directions without an integrable result"
        )
    coverage: dict[str, Any] | None = None
    if status in {"covered", "answered"}:
        raw_owner = raw.get("owner")
        if not isinstance(raw_owner, dict) or set(raw_owner) != {
            "document",
            "claims",
        }:
            raise CampaignError(
                f"{status} requires owner with document and claims"
            )
        owner_document = validate_relative_path(raw_owner["document"])
        claim_ids = string_list(
            raw_owner["claims"],
            "owner claims",
            nonempty=True,
        )
        coverage = {
            "owner_document": owner_document,
            "owner_claim_ids": claim_ids,
            "boundary_summary": summary.strip(),
        }
    elif raw.get("owner") is not None:
        raise CampaignError(f"{status} checkpoint must not include owner")
    if status == "retry":
        string_list(raw.get("need"), "checkpoint need", nonempty=True)
    elif raw.get("need") is not None:
        raise CampaignError(f"{status} checkpoint must not include need")
    if status == "draft" and not staging:
        raise CampaignError("draft requires at least one staged Markdown file")
    if status != "draft" and staging:
        raise CampaignError(f"{status} must not publish staged files")
    elif status in {"blocked", "supporting", "unresolved"}:
        reason = raw.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise CampaignError(f"{status} checkpoint needs reason")
    elif raw.get("reason") is not None:
        raise CampaignError(f"{status} checkpoint must not include reason")
    return status, directions, coverage


def normalize_checker_finding(value: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value.get(key)
        for key in ("severity", "code", "path", "message")
    }


def checker_fingerprint(value: dict[str, Any]) -> str:
    return digest_json(normalize_checker_finding(value))


def checker_baseline_fingerprints(ledger: dict[str, Any]) -> set[str]:
    seed = ledger.get("documentation_seed")
    raw = seed.get("checker_baseline", []) if isinstance(seed, dict) else []
    if not isinstance(raw, list):
        raise CampaignError("documentation checker baseline must be a list")
    fingerprints: set[str] = set()
    for value in raw:
        if not isinstance(value, dict):
            raise CampaignError("documentation checker baseline is invalid")
        fingerprints.add(checker_fingerprint(value))
    return fingerprints


def run_checker(
    checker: Path,
    root: Path,
    *,
    candidates_root: Path | None = None,
    repository_root: Path | None = None,
    allowed_findings: set[str] | None = None,
    allow_material: bool = False,
) -> list[Any]:
    command = [sys.executable, str(checker), str(root), "--json"]
    if repository_root is not None:
        command.extend(["--repository-root", str(repository_root)])
    if candidates_root is not None:
        command.extend(["--candidates", str(candidates_root)])
        for relative in sorted(candidate_files(candidates_root)):
            if (root / relative).exists():
                command.extend(["--replace-existing", relative])
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    try:
        findings = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        detail = result.stderr.strip() or result.stdout.strip() or "no output"
        raise CampaignError(f"checker returned invalid JSON: {detail}") from error
    if not isinstance(findings, list):
        raise CampaignError("checker output must be a JSON list")
    material = [
        value
        for value in findings
        if not (
            candidates_root is None
            and isinstance(value, dict)
            and value.get("code") in DEFERRED_CHECKER_CODES
        )
        and not (
            candidates_root is None
            and isinstance(value, dict)
            and checker_fingerprint(value) in (allowed_findings or set())
        )
    ]
    if result.returncode != 0 and not findings:
        raise CampaignError(result.stderr.strip() or "checker failed")
    if material and not allow_material:
        raise CampaignError(
            "SpecSpine checker rejected publication: "
            + json.dumps(material, ensure_ascii=False)
        )
    return findings


def repository_root_from_ledger(ledger: dict[str, Any]) -> Path | None:
    value = ledger.get("repository_root")
    return Path(value).resolve() if isinstance(value, str) and value else None


def validate_task_evidence(
    ledger: dict[str, Any],
    task: dict[str, Any],
    inspected: Any,
    *,
    outcome: str,
) -> list[str]:
    paths = [
        validate_relative_path(value)
        for value in string_list(
            inspected,
            "checkpoint evidence",
            nonempty=True,
        )
    ]
    units = task.get("units", [])
    if not units:
        return paths
    source_pass = ledger.get("source_pass")
    if not isinstance(source_pass, dict):
        raise CampaignError("verification task requires a recorded source-pass")
    repository_root = Path(source_pass["repository_root"])
    for value in paths:
        path = repository_root / value
        if not path.is_file():
            raise CampaignError(f"checkpoint evidence is not a repository file: {value}")
    if outcome in {"draft", "covered", "answered", "unresolved", "supporting"}:
        expected = {
            value["sample"]
            for value in task.get("evidence_strata", [])
            if isinstance(value, dict) and isinstance(value.get("sample"), str)
        }
        missing = sorted(expected - set(paths))
        if missing:
            raise CampaignError(
                "checkpoint must inspect every evidence stratum for an integrable "
                f"result: {missing}"
            )
    return paths


def validate_coverage_result(
    task: dict[str, Any],
    coverage: dict[str, Any] | None,
    spine_root: Path,
    inspected: list[str],
    *,
    outcome: str,
) -> dict[str, Any]:
    if coverage is None:
        raise CampaignError(f"{outcome} checkpoint is missing owner evidence")
    owner_document = coverage["owner_document"]
    if Path(owner_document).parts[:1] == (spine_root.name,):
        owner_document = Path(*Path(owner_document).parts[1:]).as_posix()
    coverage = coverage | {"owner_document": owner_document}
    owner_path = spine_root / owner_document
    if not owner_path.is_file():
        raise CampaignError(
            f"coverage owner document does not exist: {coverage['owner_document']}"
        )
    body = owner_path.read_text(encoding="utf-8")
    missing = [
        claim_id
        for claim_id in coverage["owner_claim_ids"]
        if f"**{claim_id}**" not in body
    ]
    if missing:
        raise CampaignError(
            f"coverage owner claim IDs do not exist in owner document: {missing}"
        )
    if outcome == "answered" and any(
        not claim_id.startswith("OBS-")
        for claim_id in coverage["owner_claim_ids"]
    ):
        raise CampaignError(
            "answered owner claims must all be repository observations (OBS-*)"
        )
    evidence_refs = [*task.get("units", []), *inspected]
    if not any(value in body for value in evidence_refs):
        raise CampaignError(
            "coverage owner document does not reference the verified unit or "
            "inspected evidence"
        )
    return coverage


def validate_task_outcome(task: dict[str, Any], outcome: str) -> None:
    inventory_task = bool(task.get("units"))
    if outcome in {"covered", "supporting"} and not inventory_task:
        raise CampaignError(
            f"{outcome} is valid only for inventory verification tasks"
        )
    if outcome in {"answered", "unresolved"} and inventory_task:
        raise CampaignError(
            f"{outcome} is valid only for integration-derived tasks"
        )
    if outcome in {"answered", "unresolved"} and task.get("anchor") is None:
        raise CampaignError(
            f"{outcome} requires an integration-derived task with an anchor"
        )


def validate_draft_semantics(
    staging: dict[str, Path],
    task: dict[str, Any],
) -> None:
    expected_baseline = task.get("evidence_baseline")
    for relative, path in staging.items():
        body = path.read_text(encoding="utf-8")
        if LEGACY_SEMANTIC_RE.search(body):
            raise CampaignError(
                f"candidate uses legacy semantic definition syntax: {relative}"
            )
        if EVIDENCE_BASELINE_RE.search(body) is None:
            raise CampaignError(
                f"candidate needs an evidence baseline: {relative}"
            )
        if expected_baseline is not None and expected_baseline not in body:
            raise CampaignError(
                f"candidate must use the campaign evidence baseline: {relative}"
            )
        if OBS_DEFINITION_RE.search(body) is None:
            raise CampaignError(
                f"candidate needs a semantic OBS definition: {relative}"
            )


def harvest_receipt(
    ledger: dict[str, Any],
    task_id: str,
    owner: str,
    raw: dict[str, Any],
    staging: dict[str, Path],
    staging_root: Path,
    spine_root: Path,
    checker: Path,
) -> dict[str, Any]:
    task = require_task(ledger, task_id)
    status, directions, coverage = validate_checkpoint(raw, staging)
    if status == "draft":
        validate_draft_semantics(staging, task)
    candidates = infer_candidates(staging, spine_root)
    if candidates:
        run_checker(
            checker,
            spine_root,
            candidates_root=staging_root,
            repository_root=repository_root_from_ledger(ledger),
        )
    if task["state"] != "assigned":
        raise CampaignError(f"harvest requires assigned task: {task_id}")
    if task["owner"] != owner:
        raise CampaignError(
            f"checkpoint owner mismatch: expected {task['owner']}, got {owner}"
        )
    validate_task_outcome(task, status)
    inspected = validate_task_evidence(
        ledger,
        task,
        raw.get("evidence"),
        outcome=status,
    )
    if status in {"covered", "answered"}:
        validate_coverage_result(
            task,
            coverage,
            spine_root,
            inspected,
            outcome=status,
        )
    return {
        "status": "harvested",
        "campaign_id": ledger["campaign_id"],
        "task": task["id"],
        "owner": owner,
        "outcome": status,
        "checkpoint_digest": digest_json(raw),
        "staging_digest": staging_digest(staging),
        "candidates": candidates,
        "directions": len(directions),
    }


def command_harvest(args: argparse.Namespace) -> dict[str, Any]:
    raw = read_json(args.checkpoint)
    staging = candidate_files(args.staging_root)
    receipt = harvest_receipt(
        load(args.ledger),
        args.id,
        args.owner,
        raw,
        staging,
        args.staging_root.resolve(),
        args.spine_root.resolve(),
        args.checker,
    )
    if args.output is None:
        return receipt
    if args.output.exists():
        existing = read_json(args.output)
        if existing != receipt:
            raise CampaignError(
                f"harvest receipt conflicts with current handoff: {args.output}"
            )
        return {
            "status": "already_harvested",
            "task": receipt["task"],
            "outcome": receipt["outcome"],
            "receipt": str(args.output.resolve()),
            "checkpoint_digest": receipt["checkpoint_digest"],
            "staging_digest": receipt["staging_digest"],
        }
    atomic_write(args.output, receipt)
    return {
        "status": "harvested",
        "task": receipt["task"],
        "outcome": receipt["outcome"],
        "receipt": str(args.output.resolve()),
        "checkpoint_digest": receipt["checkpoint_digest"],
        "staging_digest": receipt["staging_digest"],
    }


def wave_result_paths(
    task: dict[str, Any],
    handoffs_root: Path,
    harvest_root: Path,
) -> tuple[Path, Path, Path]:
    attempt = task.get("attempts")
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 1:
        raise CampaignError(f"assigned task has invalid attempt: {task['id']}")
    name = f"{task['id']}-{attempt}"
    package = handoffs_root / name
    return package / "checkpoint.json", package / "staging", harvest_root / f"{name}.json"


def command_harvest_wave(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    tasks = sorted(
        (
            task
            for task in ledger["tasks"].values()
            if task["state"] == "assigned"
        ),
        key=lambda value: value["id"],
    )
    harvested: list[str] = []
    pending: list[str] = []
    rejected: list[dict[str, str]] = []
    cached = 0
    for task in tasks:
        checkpoint, staging_root, receipt = wave_result_paths(
            task,
            args.handoffs_root,
            args.harvest_root,
        )
        package = checkpoint.parent
        if not package.exists():
            pending.append(task["id"])
            continue
        if not checkpoint.is_file() or not staging_root.is_dir():
            raise CampaignError(
                f"atomic handoff is incomplete for assigned task: {task['id']}"
            )
        try:
            result = command_harvest(
                argparse.Namespace(
                    ledger=args.ledger,
                    id=task["id"],
                    checkpoint=checkpoint,
                    staging_root=staging_root,
                    spine_root=args.spine_root,
                    owner=task["owner"],
                    output=receipt,
                    checker=args.checker,
                )
            )
        except CampaignError as error:
            rejected.append({"task": task["id"], "error": str(error)})
            continue
        harvested.append(task["id"])
        cached += result["status"] == "already_harvested"
    return {
        "status": "harvested_wave",
        "assigned": len(tasks),
        "harvested": len(harvested),
        "already_harvested": cached,
        "pending": len(pending),
        "rejected": len(rejected),
        "harvested_tasks": harvested,
        "pending_tasks": pending,
        "rejected_tasks": rejected,
    }


def require_harvest_receipt(
    path: Path,
    ledger: dict[str, Any],
    task_id: str,
    owner: str,
    status: str,
    checkpoint_digest: str,
    current_staging_digest: str,
) -> None:
    receipt = read_json(path)
    expected = {
        "campaign_id": ledger["campaign_id"],
        "task": task_id,
        "owner": owner,
        "outcome": status,
        "checkpoint_digest": checkpoint_digest,
        "staging_digest": current_staging_digest,
    }
    mismatches = {
        key: {"expected": value, "actual": receipt.get(key)}
        for key, value in expected.items()
        if receipt.get(key) != value
    }
    if receipt.get("status") != "harvested":
        mismatches["status"] = {
            "expected": "harvested",
            "actual": receipt.get("status"),
        }
    if mismatches:
        raise CampaignError(
            "handoff changed after harvest or receipt does not match: "
            + json.dumps(mismatches, ensure_ascii=False)
        )


def apply_accepted_result(
    ledger: dict[str, Any],
    task: dict[str, Any],
    raw: dict[str, Any],
    staging: dict[str, Path],
    staging_root: Path,
    spine_root: Path,
    *,
    status: str,
    directions: list[str],
    coverage: dict[str, Any] | None,
    checkpoint_digest: str,
) -> dict[str, Any]:
    validate_task_outcome(task, status)
    inspected = validate_task_evidence(
        ledger,
        task,
        raw.get("evidence"),
        outcome=status,
    )
    suggestions = normalize_directions(task["id"], directions)
    published: list[str] = []
    if status == "draft":
        candidates = infer_candidates(staging, spine_root)
        published = [candidate["path"] for candidate in candidates]
        task["state"] = "published"
        task["published"] = published
        task["accepted_staging_root"] = str(staging_root.resolve())
        task["accepted_staging_digest"] = staging_digest(staging)
        task["producer_suggestions"] = suggestions
    elif status in {"covered", "answered"}:
        result = validate_coverage_result(
            task,
            coverage,
            spine_root,
            inspected,
            outcome=status,
        )
        task["state"] = "review"
        if status == "covered":
            task["coverage_result"] = result
        else:
            task["answer_result"] = result
        task["producer_suggestions"] = suggestions
    elif status == "unresolved":
        task["state"] = "review"
        task["uncertainty_result"] = {
            "boundary_summary": raw["summary"].strip(),
            "reason": raw["reason"].strip(),
            "evidence": inspected,
        }
        task["producer_suggestions"] = []
    elif status == "supporting":
        task["state"] = "review"
        task["support_result"] = {
            "boundary_summary": raw["summary"].strip(),
            "reason": raw["reason"].strip(),
            "evidence": inspected,
        }
        task["producer_suggestions"] = []
    elif status == "retry":
        task["state"] = "todo"
        task["evidence"] = sorted(
            set(task["evidence"])
            | set(
                string_list(
                    raw["need"],
                    "checkpoint need",
                    nonempty=True,
                )
            )
        )
    else:
        task["state"] = "blocked"
        task["terminal_reason"] = raw["reason"]
        task["producer_suggestions"] = suggestions

    if status in {"draft", "covered", "answered", "unresolved", "supporting"}:
        ledger["publication_epoch"] += 1
        ledger["integration_pass"] = None
    task["owner"] = None
    task["checkpoint_outcome"] = status
    task["checkpoint_digest"] = checkpoint_digest
    return {
        "task": task["id"],
        "task_state": task["state"],
        "published": published,
        "suggestions_pending_review": [value["id"] for value in suggestions],
    }


def command_accept(args: argparse.Namespace) -> dict[str, Any]:
    raw = read_json(args.checkpoint)
    staging = candidate_files(args.staging_root)
    status, directions, coverage = validate_checkpoint(raw, staging)
    candidates = infer_candidates(staging, args.spine_root.resolve())
    checkpoint_digest = digest_json(raw)
    repository_root = repository_root_from_ledger(load(args.ledger))
    if candidates:
        run_checker(
            args.checker,
            args.spine_root.resolve(),
            candidates_root=args.staging_root.resolve(),
            repository_root=repository_root,
        )

    with locked_ledger(args.ledger) as ledger:
        task = require_task(ledger, args.id)
        if task["state"] != "assigned":
            raise CampaignError(f"accept requires assigned task: {args.id}")
        if task["owner"] != args.owner:
            raise CampaignError(
                f"checkpoint owner mismatch: expected {task['owner']}, got {args.owner}"
            )
        require_harvest_receipt(
            args.harvest_receipt,
            ledger,
            task["id"],
            args.owner,
            status,
            checkpoint_digest,
            staging_digest(staging),
        )
        result = apply_accepted_result(
            ledger,
            task,
            raw,
            staging,
            args.staging_root,
            args.spine_root.resolve(),
            status=status,
            directions=directions,
            coverage=coverage,
            checkpoint_digest=checkpoint_digest,
        )
        save_locked(args.ledger, ledger)
        return {
            "status": "accepted",
            **result,
            "revision": ledger["revision"],
        }


def command_accept_wave(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    tasks = sorted(
        (
            task
            for task in ledger["tasks"].values()
            if task["state"] == "assigned"
        ),
        key=lambda value: value["id"],
    )
    prepared: list[
        tuple[
            str,
            str,
            dict[str, Any],
            dict[str, Path],
            Path,
            Path,
            str,
            list[str],
            dict[str, Any] | None,
        ]
    ] = []
    candidate_owners: dict[str, str] = {}
    for task in tasks:
        checkpoint, staging_root, receipt = wave_result_paths(
            task,
            args.handoffs_root,
            args.harvest_root,
        )
        if not checkpoint.is_file() or not staging_root.is_dir() or not receipt.is_file():
            raise CampaignError(
                f"wave is not fully harvested for assigned task: {task['id']}"
            )
        raw = read_json(checkpoint)
        staging = candidate_files(staging_root)
        fresh_receipt = harvest_receipt(
            ledger,
            task["id"],
            task["owner"],
            raw,
            staging,
            staging_root.resolve(),
            args.spine_root.resolve(),
            args.checker,
        )
        recorded_receipt = read_json(receipt)
        if recorded_receipt != fresh_receipt:
            raise CampaignError(
                f"handoff changed after wave harvest: {task['id']}"
            )
        for candidate in fresh_receipt["candidates"]:
            relative = candidate["path"]
            previous = candidate_owners.get(relative)
            if previous is not None:
                raise CampaignError(
                    "wave candidates conflict on live Spine path: "
                    f"{relative} from {previous} and {task['id']}"
                )
            candidate_owners[relative] = task["id"]
        status, directions, coverage = validate_checkpoint(raw, staging)
        prepared.append(
            (
                task["id"],
                task["owner"],
                raw,
                staging,
                staging_root,
                receipt,
                status,
                directions,
                coverage,
            )
        )

    results: list[dict[str, Any]] = []
    with locked_ledger(args.ledger) as current:
        for (
            task_id,
            owner,
            raw,
            staging,
            staging_root,
            receipt,
            status,
            directions,
            coverage,
        ) in prepared:
            task = require_task(current, task_id)
            if task["state"] != "assigned" or task["owner"] != owner:
                raise CampaignError(f"wave task changed before acceptance: {task_id}")
            checkpoint_digest = digest_json(raw)
            require_harvest_receipt(
                receipt,
                current,
                task_id,
                owner,
                status,
                checkpoint_digest,
                staging_digest(staging),
            )
            results.append(
                apply_accepted_result(
                    current,
                    task,
                    raw,
                    staging,
                    staging_root,
                    args.spine_root.resolve(),
                    status=status,
                    directions=directions,
                    coverage=coverage,
                    checkpoint_digest=checkpoint_digest,
                )
            )
        save_locked(args.ledger, current)
    publications = [
        {"task": result["task"], "paths": result["published"]}
        for result in results
        if result["published"]
    ]
    return {
        "status": "accepted_wave",
        "accepted": len(results),
        "task_states": {
            result["task"]: result["task_state"]
            for result in results
        },
        "publications": publications,
        "suggestions_pending_review": sum(
            len(result["suggestions_pending_review"])
            for result in results
        ),
    }


def accepted_candidates(task: dict[str, Any]) -> dict[str, Path]:
    root_value = task.get("accepted_staging_root")
    expected_digest = task.get("accepted_staging_digest")
    if not isinstance(root_value, str) or not isinstance(expected_digest, str):
        raise CampaignError(
            f"accepted draft is missing its private staging reference: {task['id']}"
        )
    root = Path(root_value)
    candidates = candidate_files(root)
    if staging_digest(candidates) != expected_digest:
        raise CampaignError(
            f"accepted draft changed after acceptance: {task['id']}"
        )
    if sorted(candidates) != sorted(task.get("published", [])):
        raise CampaignError(
            f"accepted draft paths do not match task publication: {task['id']}"
        )
    return candidates


def command_prepare_integration(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    spine_root = args.spine_root.resolve()
    workspace = args.workspace.resolve()
    if workspace.exists():
        raise CampaignError(f"integration workspace already exists: {workspace}")
    if workspace == spine_root or workspace in spine_root.parents or spine_root in workspace.parents:
        raise CampaignError("integration workspace and live Spine must be separate")
    current_hashes = document_hashes(spine_root)
    if current_hashes != ledger_spine_snapshot(ledger):
        raise CampaignError(
            "live Spine changed since the last successful campaign boundary"
        )
    settled = [
        task
        for task in ledger["tasks"].values()
        if task["state"] in {"published", "review"}
    ]
    shutil.copytree(spine_root, workspace)
    copied: list[str] = []
    try:
        owners: dict[str, str] = {}
        for task in settled:
            if task["state"] != "published":
                continue
            for relative, source in accepted_candidates(task).items():
                previous = owners.get(relative)
                if previous is not None:
                    raise CampaignError(
                        f"integration candidates conflict: {relative} from "
                        f"{previous} and {task['id']}"
                    )
                owners[relative] = task["id"]
                destination = workspace / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                copied.append(relative)
    except Exception:
        shutil.rmtree(workspace, ignore_errors=True)
        raise
    return {
        "status": "prepared",
        "workspace": str(workspace),
        "settled_tasks": sorted(task["id"] for task in settled),
        "candidate_files": sorted(copied),
    }


def publish_integration_workspace(
    spine_root: Path,
    workspace: Path,
) -> tuple[Path, Path]:
    parent = spine_root.parent
    candidate = Path(
        tempfile.mkdtemp(prefix=f".{spine_root.name}.map-next.", dir=parent)
    )
    candidate.rmdir()
    shutil.copytree(workspace, candidate)
    backup = parent / f".{spine_root.name}.map-backup.{uuid.uuid4().hex}"
    try:
        os.replace(spine_root, backup)
        os.replace(candidate, spine_root)
    except Exception:
        if backup.exists() and not spine_root.exists():
            os.replace(backup, spine_root)
        shutil.rmtree(candidate, ignore_errors=True)
        raise
    return backup, candidate


def rollback_integration_publication(spine_root: Path, backup: Path) -> None:
    failed = spine_root.parent / f".{spine_root.name}.map-failed.{uuid.uuid4().hex}"
    if spine_root.exists():
        os.replace(spine_root, failed)
    os.replace(backup, spine_root)
    shutil.rmtree(failed, ignore_errors=True)


def command_block(args: argparse.Namespace) -> dict[str, Any]:
    with locked_ledger(args.ledger) as ledger:
        task = require_task(ledger, args.id)
        if task["state"] not in {"todo", "assigned"}:
            raise CampaignError(f"block requires todo or assigned state: {args.id}")
        task["state"] = "blocked"
        task["owner"] = None
        task["terminal_reason"] = args.reason
        save_locked(args.ledger, ledger)
        return {
            "status": "blocked",
            "task": args.id,
            "revision": ledger["revision"],
        }


def validate_integrated_source_publication(
    task: dict[str, Any],
    spine_root: Path,
) -> None:
    published = task.get("published", [])
    if not published:
        raise CampaignError(
            f"integrated source task has no published owner: {task['id']}"
        )
    bodies: list[str] = []
    missing: list[str] = []
    for relative in published:
        path = spine_root / relative
        if not path.is_file():
            missing.append(relative)
        else:
            bodies.append(path.read_text(encoding="utf-8"))
    if missing:
        raise CampaignError(
            f"integrated source task cannot discard producer publications: {missing}"
        )
    if task.get("origin") != "source-pass":
        return
    combined = "\n".join(bodies)
    if "**OBS-" not in combined:
        raise CampaignError(
            f"integrated source publication needs a semantic OBS claim: {task['id']}"
        )
    expected_baseline = task.get("evidence_baseline")
    if expected_baseline is not None and expected_baseline not in combined:
        raise CampaignError(
            f"integrated source publication must retain the campaign evidence "
            f"baseline: {task['id']}"
        )
    evidence = [*task.get("units", []), *task.get("evidence", [])]
    if not any(value in combined for value in evidence):
        raise CampaignError(
            f"integrated source publication must reference its unit or evidence: {task['id']}"
        )


def validate_published_graph(
    settled: dict[str, dict[str, Any]],
    workspace: Path,
) -> None:
    documents = {
        path.relative_to(workspace).as_posix(): path.read_text(encoding="utf-8")
        for path in workspace.rglob("*.md")
        if path.is_file() and path.name != "README.md"
    }
    owners = {
        relative
        for relative, body in documents.items()
        if DOCUMENT_IDENTITY_RE.search(body)
    }
    if len(owners) <= 1:
        return
    connected: set[str] = set()
    for relative, body in documents.items():
        source = Path(relative)
        for target in RELATION_ROW_RE.findall(body):
            resolved = (source.parent / target).as_posix()
            if resolved in owners:
                connected.update((relative, resolved))
    missing = sorted(
        relative
        for task in settled.values()
        if task["state"] == "published"
        for relative in task.get("published", [])
        if relative in owners and relative not in connected
    )
    if missing:
        raise CampaignError(
            "integrated source owners need an incoming or outgoing typed "
            f"relationship: {missing}"
        )


def validate_blocking_anchor(
    workspace: Path,
    anchor: dict[str, str],
    blocker: str,
) -> None:
    document = workspace / anchor["document"]
    if not document.is_file():
        raise CampaignError(
            f"blocking anchor document does not exist: {anchor['document']}"
        )
    body = document.read_text(encoding="utf-8")
    identity = re.search(
        r"^\*\*ID:\*\*\s+`([a-z0-9]+(?:-[a-z0-9]+)*)`\s+·\s+"
        r"\*\*Kind:\*\*\s+`[^`]+`\s*$",
        body,
        re.MULTILINE,
    )
    if identity is None:
        raise CampaignError(
            f"blocking anchor document has no valid identity: {anchor['document']}"
        )
    definition = re.search(
        rf"^ {{0,3}}[-+*]\s+\*\*{re.escape(blocker)}\*\*\s+—\s+\S",
        body,
        re.MULTILINE,
    )
    if definition is None:
        raise CampaignError(
            f"blocking anchor must define {blocker} in {anchor['document']}"
        )
    manifest = read_json(workspace / "specspine.json")
    areas = manifest.get("areas")
    if not isinstance(areas, list) or not any(
        isinstance(area, dict)
        and area.get("owner") == identity.group(1)
        and isinstance(area.get("blockers"), list)
        and blocker in area["blockers"]
        for area in areas
    ):
        raise CampaignError(
            f"blocking anchor must register {blocker} on owner {identity.group(1)}"
        )


def validate_new_task_anchors(
    workspace: Path,
    raw_tasks: list[Any],
) -> None:
    """Bind every integration-derived task to the exact visible question."""
    for raw in raw_tasks:
        if not isinstance(raw, dict) or raw.get("anchor") is None:
            continue
        task = new_task(raw, source="integration-validation")
        anchor = task["anchor"]
        document = workspace / anchor["document"]
        if not document.is_file():
            raise CampaignError(
                f"ToDo {task['id']} anchor document does not exist: "
                f"{anchor['document']}"
            )
        body = " ".join(document.read_text(encoding="utf-8").split())
        question = " ".join(anchor["question"].split())
        if question not in body:
            raise CampaignError(
                f"ToDo {task['id']} anchor question is absent from "
                f"{anchor['document']}"
            )


def command_integration_pass(args: argparse.Namespace) -> dict[str, Any]:
    report = read_json(args.report)
    spine_root = args.spine_root.resolve()
    workspace = args.workspace.resolve()
    if not workspace.is_dir():
        raise CampaignError(f"integration workspace is not a directory: {workspace}")
    current = load(args.ledger)
    repository_root = repository_root_from_ledger(current)
    documents = validate_integration_evidence(
        workspace,
        report.get("evidence_inspected"),
        field="integration evidence_inspected",
    )
    reviews = report.get("task_reviews")
    if not isinstance(reviews, list):
        raise CampaignError("integration task_reviews must be a list")
    suggestion_reviews = report.get("suggestion_reviews")
    if not isinstance(suggestion_reviews, list):
        raise CampaignError("integration suggestion_reviews must be a list")
    raw_todo = report.get("todo")
    if not isinstance(raw_todo, list):
        raise CampaignError("integration todo must be a list")
    validate_empty_reason(
        raw_todo,
        report.get("terminal_reason"),
        prefix="no integration-derived ToDo: ",
    )
    organization = report.get("organization")
    if (
        not isinstance(organization, dict)
        or organization.get("status")
        not in {"flat_sufficient", "directories_sufficient", "reorganized"}
        or not isinstance(organization.get("reason"), str)
        or not organization["reason"].strip()
    ):
        raise CampaignError("integration needs a reasoned organization assessment")
    checker_findings = run_checker(
        args.checker,
        workspace,
        repository_root=repository_root,
        allowed_findings=checker_baseline_fingerprints(current),
    )

    normalized_reviews: dict[str, dict[str, Any]] = {}
    for value in reviews:
        if not isinstance(value, dict):
            raise CampaignError("task review must be an object")
        task_id = validate_id(value.get("task"))
        disposition = value.get("disposition")
        reason = value.get("reason")
        anchor_disposition = value.get("anchor_disposition")
        if disposition not in REVIEW_DISPOSITIONS:
            raise CampaignError(
                f"invalid integration disposition for {task_id}: {disposition!r}"
            )
        if not isinstance(reason, str) or not reason.strip():
            raise CampaignError(f"task review needs a reason: {task_id}")
        if task_id in normalized_reviews:
            raise CampaignError(f"duplicate task review: {task_id}")
        normalized_anchor: dict[str, str] | None = None
        if anchor_disposition is not None:
            anchor_status = (
                anchor_disposition.get("status")
                if isinstance(anchor_disposition, dict)
                else None
            )
            expected_fields = {"status", "reason"}
            if anchor_status == "refined":
                expected_fields.add("todo")
            elif anchor_status == "blocking":
                expected_fields.add("blocker")
            if (
                not isinstance(anchor_disposition, dict)
                or set(anchor_disposition) != expected_fields
                or anchor_status not in ANCHOR_DISPOSITIONS
                or not isinstance(anchor_disposition.get("reason"), str)
                or not anchor_disposition["reason"].strip()
            ):
                raise CampaignError(
                    f"task review has invalid anchor_disposition: {task_id}"
                )
            normalized_anchor = {
                "status": anchor_status,
                "reason": anchor_disposition["reason"].strip(),
            }
            if anchor_status == "refined":
                normalized_anchor["todo"] = validate_id(anchor_disposition["todo"])
            elif anchor_status == "blocking":
                blocker = anchor_disposition["blocker"]
                if not isinstance(blocker, str) or OQ_ID_RE.fullmatch(blocker) is None:
                    raise CampaignError(
                        f"blocking anchor needs a valid OQ-* ID: {task_id}"
                    )
                normalized_anchor["blocker"] = blocker
        normalized_reviews[task_id] = {
            "disposition": disposition,
            "reason": reason.strip(),
            "anchor_disposition": normalized_anchor,
        }

    normalized_suggestions: dict[tuple[str, str], dict[str, str]] = {}
    for value in suggestion_reviews:
        if not isinstance(value, dict):
            raise CampaignError("suggestion review must be an object")
        task_id = validate_id(value.get("task"))
        suggestion_id = validate_id(value.get("suggestion"))
        disposition = value.get("disposition")
        reason = value.get("reason")
        queued_task = value.get("todo")
        preserved_document = value.get("document")
        if disposition not in SUGGESTION_DISPOSITIONS:
            raise CampaignError(
                f"invalid suggestion disposition for {suggestion_id}: {disposition!r}"
            )
        if not isinstance(reason, str) or not reason.strip():
            raise CampaignError(
                f"suggestion review needs a reason: {suggestion_id}"
            )
        if disposition == "queued":
            queued_task = validate_id(queued_task)
        elif queued_task is not None:
            raise CampaignError(
                f"non-queued suggestion must not name ToDo: {suggestion_id}"
            )
        if disposition == "preserved":
            preserved_document = validate_relative_path(preserved_document)
        elif preserved_document is not None:
            raise CampaignError(
                f"only preserved suggestion may name a document: {suggestion_id}"
            )
        key = (task_id, suggestion_id)
        if key in normalized_suggestions:
            raise CampaignError(f"duplicate suggestion review: {key}")
        normalized_suggestions[key] = {
            "disposition": disposition,
            "reason": reason.strip(),
            "todo": queued_task,
            "document": preserved_document,
        }

    with locked_ledger(args.ledger) as ledger:
        baseline = ledger_spine_snapshot(ledger)
        if document_hashes(spine_root) != baseline:
            raise CampaignError(
                "live Spine changed after integration workspace preparation"
            )
        actual_changes = spine_changes(
            baseline,
            documents,
        )
        reported_changes = validate_reported_spine_changes(
            report.get("changed_documents"),
            actual_changes,
        )
        settled = {
            task["id"]: task
            for task in ledger["tasks"].values()
            if task["state"] in {"published", "review"}
        }
        if set(normalized_reviews) != set(settled):
            raise CampaignError(
                "integration must review every settled producer task; "
                f"missing={sorted(set(settled) - set(normalized_reviews))}, "
                f"unknown={sorted(set(normalized_reviews) - set(settled))}"
            )
        invalid_coverage_reviews = [
            task_id
            for task_id, task in settled.items()
            if task["state"] == "review"
            and task.get("checkpoint_outcome") == "covered"
            and normalized_reviews[task_id]["disposition"] != "already_canonical"
        ]
        if invalid_coverage_reviews:
            raise CampaignError(
                "covered tasks require already_canonical integration "
                f"disposition: {invalid_coverage_reviews}"
            )
        invalid_answer_reviews = [
            task_id
            for task_id, task in settled.items()
            if task.get("checkpoint_outcome") == "answered"
            and normalized_reviews[task_id]["disposition"] != "answered_canonical"
        ]
        if invalid_answer_reviews:
            raise CampaignError(
                "answered tasks require answered_canonical integration "
                f"disposition: {invalid_answer_reviews}"
            )
        invalid_uncertainty_reviews = [
            task_id
            for task_id, task in settled.items()
            if task.get("checkpoint_outcome") == "unresolved"
            and normalized_reviews[task_id]["disposition"] != "still_open"
        ]
        if invalid_uncertainty_reviews:
            raise CampaignError(
                "unresolved tasks require still_open integration "
                f"disposition: {invalid_uncertainty_reviews}"
            )
        invalid_support_reviews = [
            task_id
            for task_id, task in settled.items()
            if task["state"] == "review"
            and task.get("checkpoint_outcome") == "supporting"
            and normalized_reviews[task_id]["disposition"]
            not in {"confirmed_supporting", "retry"}
        ]
        if invalid_support_reviews:
            raise CampaignError(
                "supporting tasks require confirmed_supporting or retry "
                f"integration disposition: {invalid_support_reviews}"
            )
        invalid_publication_reviews = [
            task_id
            for task_id, task in settled.items()
            if task["state"] == "published"
            and normalized_reviews[task_id]["disposition"] != "integrated"
        ]
        if invalid_publication_reviews:
            raise CampaignError(
                "published tasks require integrated disposition: "
                f"{invalid_publication_reviews}"
            )
        for task_id, task in settled.items():
            anchor = task.get("anchor")
            anchor_review = normalized_reviews[task_id]["anchor_disposition"]
            if anchor is None and anchor_review is not None:
                raise CampaignError(
                    f"inventory task must not have anchor_disposition: {task_id}"
                )
            if anchor is not None and normalized_reviews[task_id]["disposition"] != "retry":
                if anchor_review is None:
                    raise CampaignError(
                        f"integration-derived task needs anchor_disposition: {task_id}"
                    )
                if (
                    task.get("checkpoint_outcome") == "unresolved"
                    and anchor_review["status"]
                    not in {"refined", "still-open", "blocking"}
                ):
                    raise CampaignError(
                        f"unresolved task must preserve uncertainty: {task_id}"
                    )
                if anchor_review["status"] == "resolved":
                    anchor_path = workspace / anchor["document"]
                    if anchor_path.is_file():
                        normalized_body = " ".join(
                            anchor_path.read_text(encoding="utf-8").split()
                        )
                        normalized_question = " ".join(
                            anchor["question"].split()
                        )
                        if normalized_question in normalized_body:
                            raise CampaignError(
                                f"resolved anchor question remains in document: {task_id}"
                            )
                elif anchor_review["status"] == "blocking":
                    validate_blocking_anchor(
                        workspace,
                        anchor,
                        anchor_review["blocker"],
                    )
        for task_id, task in settled.items():
            if task["state"] == "published":
                validate_integrated_source_publication(task, workspace)
        validate_published_graph(settled, workspace)
        expected_suggestions = {
            (task_id, suggestion["id"])
            for task_id, task in settled.items()
            for suggestion in task["producer_suggestions"]
        }
        if set(normalized_suggestions) != expected_suggestions:
            raise CampaignError(
                "integration must disposition every producer suggestion; "
                f"missing={sorted(expected_suggestions - set(normalized_suggestions))}, "
                f"unknown={sorted(set(normalized_suggestions) - expected_suggestions)}"
            )
        for (task_id, suggestion_id), review in normalized_suggestions.items():
            if review["disposition"] != "preserved":
                continue
            document = workspace / review["document"]
            if not document.is_file():
                raise CampaignError(
                    f"preserved suggestion document does not exist: "
                    f"{review['document']}"
                )
            suggestion = next(
                value
                for value in settled[task_id]["producer_suggestions"]
                if value["id"] == suggestion_id
            )
            body = " ".join(document.read_text(encoding="utf-8").split())
            question = " ".join(suggestion["question"].split())
            if question not in body:
                raise CampaignError(
                    f"preserved suggestion question is absent from "
                    f"{review['document']}: {suggestion_id}"
                )
        validate_new_task_anchors(workspace, raw_todo)
        source_baseline = ledger.get("source_pass", {}).get("evidence_baseline", {})
        baseline_marker = (
            source_baseline.get("marker")
            if isinstance(source_baseline, dict)
            else None
        )
        for value in raw_todo:
            if isinstance(value, dict):
                value["evidence_baseline"] = baseline_marker
        added = add_tasks(
            ledger,
            raw_todo,
            source=f"integration-{ledger['publication_epoch']}",
        )
        added_set = set(added) | {
            validate_id(value.get("id"))
            for value in raw_todo
            if isinstance(value, dict)
        }
        for task_id, task in settled.items():
            anchor_review = normalized_reviews[task_id]["anchor_disposition"]
            if (
                anchor_review is None
                or anchor_review["status"] != "refined"
            ):
                continue
            successor_id = anchor_review["todo"]
            if successor_id not in added_set:
                raise CampaignError(
                    f"refined anchor needs matching integration ToDo: {task_id}"
                )
            successor = ledger["tasks"][successor_id]
            if (
                successor.get("anchor", {}).get("document")
                != task["anchor"]["document"]
                or " ".join(successor["question"].split())
                == " ".join(task["question"].split())
            ):
                raise CampaignError(
                    f"refined anchor ToDo must be narrower and keep its document: {task_id}"
                )
        for key, review in normalized_suggestions.items():
            if review["disposition"] == "queued" and review["todo"] not in added_set:
                raise CampaignError(
                    f"queued suggestion {key} has no matching integration ToDo"
                )
        retried: set[str] = set()
        for task_id, task in settled.items():
            disposition = normalized_reviews[task_id]["disposition"]
            if disposition == "retry":
                task["state"] = "todo"
                task["checkpoint_outcome"] = None
                task["support_result"] = None
                task["answer_result"] = None
                task["uncertainty_result"] = None
                task["accepted_staging_root"] = None
                task["accepted_staging_digest"] = None
                retried.add(task_id)
            else:
                task["state"] = "complete"
                task["terminal_reason"] = normalized_reviews[task_id]["reason"]
            task["suggestion_reviews"] = {
                suggestion_id: normalized_suggestions[(task_id, suggestion_id)]
                for candidate_task, suggestion_id in expected_suggestions
                if candidate_task == task_id
            }
        ledger["integration_pass"] = {
            "publication_epoch": ledger["publication_epoch"],
            "documents": documents,
            "changed_documents": reported_changes,
            "task_reviews": normalized_reviews,
            "suggestion_reviews": {
                f"{task}:{suggestion}": value
                for (task, suggestion), value in normalized_suggestions.items()
            },
            "todo": sorted(added_set | retried),
            "terminal_reason": report.get("terminal_reason"),
            "organization": organization,
            "checker_clean": not checker_findings,
        }
        history = ledger.setdefault("document_change_history", [])
        history.extend(
            {
                "publication_epoch": ledger["publication_epoch"],
                "path": value["path"],
                "operation": value["operation"],
            }
            for value in reported_changes
        )
        operations = {
            value["path"]: value["operation"] for value in reported_changes
        }
        for task in settled.values():
            if task.get("checkpoint_outcome") != "draft":
                continue
            for relative in task.get("published", []):
                ledger["publication_history"].append(
                    {
                        "task": task["id"],
                        "path": relative,
                        "operation": operations.get(relative, "changed"),
                        "publication_epoch": ledger["publication_epoch"],
                    }
                )
        ledger["spine_snapshot"] = documents
        backup, candidate = publish_integration_workspace(spine_root, workspace)
        try:
            save_locked(args.ledger, ledger)
        except Exception:
            rollback_integration_publication(spine_root, backup)
            raise
        else:
            shutil.rmtree(backup, ignore_errors=True)
            shutil.rmtree(candidate, ignore_errors=True)
        return {
            "status": "integrated",
            "reviewed_tasks": sorted(settled),
            "added_todo": added,
            "changed_documents": reported_changes,
            "checker_findings": len(checker_findings),
            "revision": ledger["revision"],
        }


def current_inventory(ledger: dict[str, Any]) -> bool:
    source = ledger.get("source_pass")
    if not isinstance(source, dict):
        return False
    try:
        current = repository_inventory(
            Path(source["repository_root"]),
            spine_root=Path(source["spine_root"]),
        )
    except (CampaignError, KeyError, OSError):
        return False
    return current["digest"] == source.get("inventory_digest")


def current_integration(ledger: dict[str, Any]) -> bool:
    integration = ledger.get("integration_pass")
    source = ledger.get("source_pass")
    if (
        not isinstance(integration, dict)
        or not isinstance(source, dict)
        or integration.get("publication_epoch") != ledger["publication_epoch"]
        or integration.get("todo")
    ):
        return False
    try:
        current_documents = document_hashes(Path(source["spine_root"]))
    except (KeyError, OSError):
        return False
    return current_documents == integration.get("documents")


def terminal_gates(ledger: dict[str, Any]) -> dict[str, bool]:
    tasks = list(ledger["tasks"].values())
    source_pass = ledger.get("source_pass")
    source_tasks = (
        source_pass.get("todo", []) if isinstance(source_pass, dict) else []
    )
    units_verified = bool(isinstance(source_pass, dict)) and all(
        task_id in ledger["tasks"]
        and ledger["tasks"][task_id]["state"] == "complete"
        for task_id in source_tasks
    )
    return {
        "todo_empty": not any(task["state"] == "todo" for task in tasks),
        "producers_finished": not any(
            task["state"] == "assigned" for task in tasks
        ),
        "publications_integrated": not any(
            task["state"] in {"published", "review"} for task in tasks
        ),
        "no_blocked_tasks": not any(
            task["state"] == "blocked" for task in tasks
        ),
        "source_inventory_current": current_inventory(ledger),
        "inventory_units_verified": (
            isinstance(source_pass, dict) and units_verified
        ),
        "integration_current": current_integration(ledger),
        "spine_v3_clean": (
            isinstance(ledger.get("integration_pass"), dict)
            and ledger["integration_pass"].get("checker_clean") is True
        ),
    }


def command_summary(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    gates = terminal_gates(ledger)
    states = {
        state: sorted(
            task["id"]
            for task in ledger["tasks"].values()
            if task["state"] == state
        )
        for state in sorted(TASK_STATES)
    }
    terminal: str | None = None
    if all(gates.values()):
        terminal = "inventory_verified"
    elif (
        gates["todo_empty"]
        and gates["producers_finished"]
        and gates["publications_integrated"]
        and not gates["no_blocked_tasks"]
    ):
        terminal = "blocked"
    return {
        "campaign_id": ledger["campaign_id"],
        "revision": ledger["revision"],
        "states": states,
        "ready": states["todo"],
        "document_change_history": ledger.get("document_change_history", []),
        "terminal_gates": gates,
        "terminal": terminal,
    }


def command_next_action(args: argparse.Namespace) -> dict[str, Any]:
    summary = command_summary(args)
    states = summary["states"]
    gates = summary["terminal_gates"]
    if summary["terminal"] == "inventory_verified":
        action = "finalize"
        may_finish = True
        reason = "inventory_verified"
    elif summary["terminal"] == "blocked":
        action = "report_blocked"
        may_finish = True
        reason = "campaign has only terminal blockers"
    elif states["published"] or states["review"]:
        action = "integrate"
        may_finish = False
        reason = "settled producer results require root integration"
    elif states["assigned"]:
        action = "wait"
        may_finish = False
        reason = "assigned producers have not settled"
    elif states["todo"]:
        action = "dispatch"
        may_finish = False
        reason = "ready verification work remains"
    else:
        action = "repair"
        may_finish = False
        reason = "terminal gates are stale or incomplete"
    may_pause = bool(
        action == "dispatch"
        and gates["producers_finished"]
        and gates["publications_integrated"]
        and gates["source_inventory_current"]
        and gates["integration_current"]
        and gates["spine_v3_clean"]
    )
    return {
        "campaign_id": summary["campaign_id"],
        "revision": summary["revision"],
        "action": action,
        "may_finish": may_finish,
        "may_pause": may_pause,
        "response_policy": (
            "final_response_allowed"
            if may_finish
            else (
                "unavoidable_platform_turn_boundary_only"
                if may_pause
                else "continue_in_same_turn_no_final_response"
            )
        ),
        "reason": reason,
        "counts": {
            state: len(task_ids) for state, task_ids in states.items()
        },
        "terminal": summary["terminal"],
        "terminal_gates": summary["terminal_gates"],
    }


def command_coverage_report(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    summary = command_summary(args)
    source = ledger.get("source_pass", {})
    excluded = source.get("excluded", {}) if isinstance(source, dict) else {}
    counts = {
        classification: (
            len(source.get("production_files", []))
            if classification == "queued"
            else len(excluded.get(classification, []))
        )
        for classification in sorted(SOURCE_CLASSIFICATIONS)
    }
    verified_units = sum(
        ledger["tasks"].get(task_id, {}).get("state") == "complete"
        for task_id in source.get("todo", [])
    )
    return {
        "campaign_id": ledger["campaign_id"],
        "scope": ledger["scope"],
        "terminal": summary["terminal"],
        "terminal_gates": summary["terminal_gates"],
        "task_states": {
            state: len(values) for state, values in summary["states"].items()
        },
        "inventory_classifications": counts,
        "verified_topics": verified_units,
        "existing_spine_covered_topics": len(
            source.get("topic_plan", {}).get("covered", [])
        ),
        "coverage_claim": (
            "inventory_verified"
            if summary["terminal"] == "inventory_verified"
            else "blocked"
            if summary["terminal"] == "blocked"
            else "partial"
        ),
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("ledger", type=Path)
    init.add_argument("--scope", required=True)
    init.add_argument("--root-question", required=True)
    init.add_argument(
        "--spine-state",
        choices=("empty", "existing"),
        default="empty",
    )
    init.add_argument("--repository-root", type=Path)

    discover = sub.add_parser("discover")
    discover.add_argument("campaign_home", type=Path)
    discover.add_argument("repository_root", type=Path)
    discover.add_argument(
        "--recent-hours",
        type=float,
        default=DEFAULT_RECENT_HOURS,
    )

    resume = sub.add_parser("resume-session")
    resume.add_argument("ledger", type=Path)

    seed = sub.add_parser("seed-from-spine")
    seed.add_argument("ledger", type=Path)
    seed.add_argument("spine_root", type=Path)
    seed.add_argument(
        "--checker",
        type=Path,
        default=Path(__file__).with_name("check_spine.py"),
    )

    inventory = sub.add_parser("inventory")
    inventory.add_argument("repository_root", type=Path)
    inventory.add_argument("--spine-root", type=Path)
    inventory.add_argument("--output", type=Path)

    planning_packets = sub.add_parser("planning-packets")
    planning_packets.add_argument("inventory", type=Path)
    planning_packets.add_argument("output_dir", type=Path)
    planning_packets.add_argument(
        "--page-size",
        type=positive_int,
        default=MAX_UNIT_FILES,
    )

    planning_collect = sub.add_parser("planning-collect")
    planning_collect.add_argument("packets_dir", type=Path)
    planning_collect.add_argument("results_dir", type=Path)
    planning_collect.add_argument("output", type=Path)

    source = sub.add_parser("source-pass")
    source.add_argument("ledger", type=Path)
    source.add_argument("repository_root", type=Path)
    source.add_argument("spine_root", type=Path)
    source.add_argument("--topic-plan", type=Path)
    source.add_argument(
        "--checker",
        type=Path,
        default=Path(__file__).with_name("check_spine.py"),
    )

    add = sub.add_parser("todo-add")
    add.add_argument("ledger", type=Path)
    add.add_argument("id")
    add.add_argument("--question", required=True)
    add.add_argument("--reason", required=True)
    add.add_argument("--origin", required=True)
    add.add_argument("--evidence", action="append", default=[])
    add.add_argument("--document", action="append", default=[])
    add.add_argument("--exclude", action="append", default=[])

    todo = sub.add_parser("todo")
    todo.add_argument("ledger", type=Path)
    todo.add_argument("--all", action="store_true")
    todo.add_argument("--limit", type=positive_int)

    ready = sub.add_parser("ready")
    ready.add_argument("ledger", type=Path)
    ready.add_argument("--limit", type=positive_int)

    packet = sub.add_parser("packet")
    packet.add_argument("ledger", type=Path)
    packet.add_argument("id")
    packet.add_argument("--output", type=Path)

    assign = sub.add_parser("assign")
    assign.add_argument("ledger", type=Path)
    assign.add_argument("id")
    assign.add_argument("--owner", required=True)

    release = sub.add_parser("release")
    release.add_argument("ledger", type=Path)
    release.add_argument("id")

    harvest = sub.add_parser("harvest")
    harvest.add_argument("ledger", type=Path)
    harvest.add_argument("id")
    harvest.add_argument("checkpoint", type=Path)
    harvest.add_argument("staging_root", type=Path)
    harvest.add_argument("spine_root", type=Path)
    harvest.add_argument("--owner", required=True)
    harvest.add_argument("--output", type=Path)
    harvest.add_argument(
        "--checker",
        type=Path,
        default=Path(__file__).with_name("check_spine.py"),
    )

    harvest_wave = sub.add_parser("harvest-wave")
    harvest_wave.add_argument("ledger", type=Path)
    harvest_wave.add_argument("handoffs_root", type=Path)
    harvest_wave.add_argument("spine_root", type=Path)
    harvest_wave.add_argument("harvest_root", type=Path)
    harvest_wave.add_argument(
        "--checker",
        type=Path,
        default=Path(__file__).with_name("check_spine.py"),
    )

    accept = sub.add_parser("accept")
    accept.add_argument("ledger", type=Path)
    accept.add_argument("id")
    accept.add_argument("checkpoint", type=Path)
    accept.add_argument("staging_root", type=Path)
    accept.add_argument("spine_root", type=Path)
    accept.add_argument("--owner", required=True)
    accept.add_argument("--harvest-receipt", required=True, type=Path)
    accept.add_argument(
        "--checker",
        type=Path,
        default=Path(__file__).with_name("check_spine.py"),
    )

    accept_wave = sub.add_parser("accept-wave")
    accept_wave.add_argument("ledger", type=Path)
    accept_wave.add_argument("handoffs_root", type=Path)
    accept_wave.add_argument("spine_root", type=Path)
    accept_wave.add_argument("harvest_root", type=Path)
    accept_wave.add_argument(
        "--checker",
        type=Path,
        default=Path(__file__).with_name("check_spine.py"),
    )

    prepare_integration = sub.add_parser("prepare-integration")
    prepare_integration.add_argument("ledger", type=Path)
    prepare_integration.add_argument("spine_root", type=Path)
    prepare_integration.add_argument("workspace", type=Path)

    block = sub.add_parser("block")
    block.add_argument("ledger", type=Path)
    block.add_argument("id")
    block.add_argument("--reason", required=True)

    integration = sub.add_parser("integration-pass")
    integration.add_argument("ledger", type=Path)
    integration.add_argument("spine_root", type=Path)
    integration.add_argument("workspace", type=Path)
    integration.add_argument("report", type=Path)
    integration.add_argument(
        "--checker",
        type=Path,
        default=Path(__file__).with_name("check_spine.py"),
    )

    summary = sub.add_parser("summary")
    summary.add_argument("ledger", type=Path)

    next_action = sub.add_parser("next-action")
    next_action.add_argument("ledger", type=Path)

    coverage = sub.add_parser("coverage-report")
    coverage.add_argument("ledger", type=Path)

    return result


def main() -> int:
    args = parser().parse_args()
    commands = {
        "init": command_init,
        "discover": command_discover,
        "resume-session": command_resume_session,
        "seed-from-spine": command_seed_from_spine,
        "inventory": command_inventory,
        "planning-packets": command_planning_packets,
        "planning-collect": command_planning_collect,
        "source-pass": command_source_pass,
        "todo-add": command_todo_add,
        "todo": command_todo,
        "ready": command_ready,
        "packet": command_packet,
        "assign": command_assign,
        "release": command_release,
        "harvest": command_harvest,
        "harvest-wave": command_harvest_wave,
        "accept": command_accept,
        "accept-wave": command_accept_wave,
        "prepare-integration": command_prepare_integration,
        "block": command_block,
        "integration-pass": command_integration_pass,
        "summary": command_summary,
        "next-action": command_next_action,
        "coverage-report": command_coverage_report,
    }
    try:
        value = commands[args.command](args)
    except (CampaignError, OSError, UnicodeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(value, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
