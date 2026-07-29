#!/usr/bin/env python3
"""Run a reliable SpecSpine Map operation.

The campaign deliberately separates four authorities:

* scoped discovery builds the semantic evidence frontier;
* one-shot producers verify one bounded task and stage missing observations;
* the root orchestrator publishes and integrates accepted results;
* the ledger derives the selected completion claim from evidence and integration.

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

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from spec_contract import CORE_RELATIONS, canonical_heading, presentation


SCHEMA_VERSION = 15
PRODUCER_CONTRACT_VERSION = 9
DISCOVERY_CONTRACT_VERSION = 5
MAX_UNIT_FILES = 80
MAX_SCOUT_SEED_FILES = 40
MAX_INITIAL_SCOUTS = 10
MAX_PRODUCER_WAVE = 10
MAX_CANDIDATE_DOCUMENTS = 12
DISCOVERY_TERMINAL_STATUSES = {
    "unresolved",
    "closed",
    "duplicate",
    "out_of_scope",
}
UNRESOLVED_FALLBACK_KINDS = {
    "independent_investigation",
    "context_limit",
    "separate_owner",
    "increment_continuation",
}
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
SEMANTIC_DEFINITION_RE = re.compile(
    r"^ {0,3}[-+*]\s+\*\*((?:DEC|CON|REQ|GUA|INV|QLT|VER|OBS|INF|OQ)-"
    r"[a-z0-9]+(?:-[a-z0-9]+)*)\*\*\s+—\s+\S",
    re.MULTILINE,
)
NORMATIVE_PREFIXES = ("DEC-", "CON-", "REQ-", "GUA-", "INV-", "QLT-", "VER-")
DOCUMENT_IDENTITY_RE = re.compile(
    r"^\*\*ID:\*\*\s+`([a-z0-9]+(?:-[a-z0-9]+)*)`\s+·\s+"
    r"\*\*Kind:\*\*\s+`((?!index`)[^`]+)`\s*$",
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
    "MANIFEST_PRESENTATION",
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
    ".specspine",
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
    ".specspine",
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
    "_INDEX.md",
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


def path_digest(path: Path) -> str:
    """Digest a file or directory without depending on mtimes or permissions."""
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    if not path.is_dir():
        raise CampaignError(f"artifact does not exist: {path}")
    entries = [
        {
            "path": item.relative_to(path).as_posix(),
            "digest": hashlib.sha256(item.read_bytes()).hexdigest(),
        }
        for item in sorted(path.rglob("*"))
        if item.is_file()
    ]
    return digest_json(entries)


def artifact_ref(path: Path, *, input_digest: str) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "input_digest": input_digest,
        "artifact_digest": path_digest(resolved),
    }


def same_artifact(
    recorded: Any,
    path: Path,
    *,
    input_digest: str,
) -> bool:
    if not isinstance(recorded, dict):
        return False
    resolved = path.resolve()
    return (
        recorded.get("path") == str(resolved)
        and recorded.get("input_digest") == input_digest
        and recorded.get("artifact_digest") == path_digest(resolved)
    )


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


def map_runtime_root(repository_root: Path) -> Path:
    return repository_root.resolve() / ".specspine" / "map"


def ensure_map_runtime_root(repository_root: Path) -> Path:
    root = map_runtime_root(repository_root)
    root.mkdir(parents=True, exist_ok=True)
    ignore = root.parent / ".gitignore"
    if not ignore.exists():
        ignore.write_text("*\n", encoding="utf-8")
    elif not ignore.is_file():
        raise CampaignError(f"workspace state ignore path is not a file: {ignore}")
    return root


def require_map_runtime_path(
    path: Path,
    repository_root: Path | None,
    *,
    field: str,
) -> Path:
    """Keep every Map runtime artifact under the workspace-local state root."""
    resolved = path.resolve()
    if repository_root is None:
        return resolved
    runtime_root = map_runtime_root(repository_root)
    if resolved != runtime_root and runtime_root not in resolved.parents:
        raise CampaignError(
            f"{field} must be under the workspace Map runtime root "
            f"{runtime_root}: {resolved}"
        )
    return resolved


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


def spine_owner_registry(spine_root: Path) -> dict[str, dict[str, str]]:
    owners: dict[str, dict[str, str]] = {}
    for path in sorted(spine_root.rglob("*.md")):
        if not path.is_file():
            continue
        body = path.read_text(encoding="utf-8")
        identity = DOCUMENT_IDENTITY_RE.search(body)
        if identity is None:
            continue
        owner = identity.group(1)
        title = re.search(r"^#\s+(.+?)\s*$", body, re.MULTILINE)
        if owner in owners:
            raise CampaignError(f"duplicate Spine owner ID: {owner}")
        owners[owner] = {
            "document": path.relative_to(spine_root).as_posix(),
            "title": title.group(1).strip() if title else owner,
        }
    return owners


def planned_owner_profile(
    ledger: dict[str, Any],
    task: dict[str, Any],
) -> dict[str, Any]:
    document = task.get("planned_document")
    source_pass = ledger.get("source_pass")
    if not isinstance(document, str) or not isinstance(source_pass, dict):
        return {"document": document, "exists": False}
    spine_root = Path(source_pass["spine_root"])
    path = spine_root / document
    if not path.is_file():
        return {"document": document, "exists": False}

    identity = DOCUMENT_IDENTITY_RE.search(path.read_text(encoding="utf-8"))
    if identity is None:
        raise CampaignError(f"planned owner has no valid identity: {document}")
    owner = identity.group(1)
    manifest = read_json(spine_root / "specspine.json")
    area = next(
        (
            value
            for value in manifest.get("areas", [])
            if isinstance(value, dict) and value.get("owner") == owner
        ),
        None,
    )
    if area is None:
        raise CampaignError(f"planned owner has no manifest area: {owner}")
    return {
        "document": document,
        "exists": True,
        "owner": owner,
        "kind": identity.group(2),
        "facets": area["facets"],
        "blockers": area["blockers"],
    }


def related_existing_owners(
    ledger: dict[str, Any],
    task: dict[str, Any],
) -> list[dict[str, str]]:
    source_pass = ledger.get("source_pass")
    if not isinstance(source_pass, dict):
        return []
    registry = spine_owner_registry(Path(source_pass["spine_root"]))
    owner_ids = {
        relationship["target"]
        for relationship in task.get("planned_relationships", [])
        if relationship.get("target") in registry
    }
    return [
        {"id": owner, **registry[owner]}
        for owner in sorted(owner_ids)
    ]


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
    atomic_write_bytes(path, canonical_json(value) + b"\n")


def atomic_write_pretty(path: Path, value: dict[str, Any]) -> None:
    payload = (
        json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
    atomic_write_bytes(path, payload)


def atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
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
    validate_operation_spec(ledger.get("operation"))
    ledger_producer_contract(ledger)
    repository_value = ledger.get("repository_root")
    if isinstance(repository_value, str):
        require_map_runtime_path(
            path,
            Path(repository_value),
            field="campaign ledger",
        )
    artifacts = ledger.get("artifacts")
    if (
        not isinstance(artifacts, dict)
        or set(artifacts) != {"discovery", "synthesis", "integration"}
        or any(not isinstance(artifacts[name], dict) for name in artifacts)
    ):
        raise CampaignError("campaign artifact manifest is invalid")
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


def record_artifact(
    ledger: dict[str, Any],
    phase: str,
    name: str,
    path: Path,
    *,
    input_digest: str,
) -> dict[str, Any]:
    reference = artifact_ref(path, input_digest=input_digest)
    ledger["artifacts"][phase][name] = reference
    return reference


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
    units = [
        validate_relative_path(value)
        for value in string_list(raw.get("units", []), f"ToDo {task_id} units")
    ]
    architecture_unit = raw.get("architecture_unit")
    if architecture_unit is not None:
        architecture_unit = validate_relative_path(architecture_unit)
    planned_document = raw.get("planned_document")
    if planned_document is not None:
        planned_document = validate_relative_path(planned_document)
        if not planned_document.endswith(".md") or planned_document == "_INDEX.md":
            raise CampaignError(
                f"ToDo {task_id} planned_document must be non-index Markdown"
            )
    planned_relationships = raw.get("planned_relationships", [])
    if not isinstance(planned_relationships, list):
        raise CampaignError(f"ToDo {task_id} planned_relationships must be a list")
    normalized_relationships: list[dict[str, str]] = []
    relationship_keys: set[tuple[str, str]] = set()
    for index, value in enumerate(planned_relationships, start=1):
        if not isinstance(value, dict) or set(value) != {"type", "target", "reason"}:
            raise CampaignError(
                f"ToDo {task_id} relationship {index} needs type, target, and reason"
            )
        relation = value["type"]
        if relation not in CORE_RELATIONS and (
            not isinstance(relation, str)
            or re.fullmatch(r"x-[a-z0-9]+(?:-[a-z0-9]+)*", relation) is None
        ):
            raise CampaignError(
                f"ToDo {task_id} relationship {index} has invalid type"
            )
        target = validate_id(value["target"])
        reason_text = value["reason"]
        if not isinstance(reason_text, str) or not reason_text.strip():
            raise CampaignError(
                f"ToDo {task_id} relationship {index} needs a reason"
            )
        key = (relation, target)
        if key in relationship_keys:
            raise CampaignError(f"ToDo {task_id} repeats relationship {key}")
        relationship_keys.add(key)
        normalized_relationships.append(
            {"type": relation, "target": target, "reason": reason_text.strip()}
        )
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
        "units": units,
        "architecture_unit": architecture_unit,
        "planned_document": planned_document,
        "planned_relationships": sorted(
            normalized_relationships,
            key=lambda row: (row["type"], row["target"], row["reason"]),
        ),
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
        "accepted_staging_root": None,
        "accepted_staging_digest": None,
        "terminal_reason": None,
        "retry_history": [],
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
            "units",
            "architecture_unit",
            "planned_document",
            "planned_relationships",
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


def file_classification(path: Path) -> tuple[str, str]:
    """Classify a concrete repository file for snapshot and verification."""
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
    if (
        (len(parts) == 1 and (
            name in ROOT_GOVERNANCE
            or path.suffix.lower() in {".md", ".txt"}
        ))
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
            classification, _ = file_classification(path)
            if classification == "queued" and not is_probably_text(source):
                classification = "opaque-asset"
            if classification == "queued":
                snapshot.update(f"F\0{path.as_posix()}\0".encode())
                with source.open("rb") as stream:
                    while chunk := stream.read(1024 * 1024):
                        snapshot.update(chunk)
                snapshot.update(b"\n")
                production_files.append(path.as_posix())
            else:
                snapshot.update(
                    f"X\0{path.as_posix()}\0{classification}\n".encode()
                )
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


def validate_scope_spec(value: Any) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {
        "kind",
        "title",
        "question",
        "inclusion_rule",
        "exclusion_rule",
    }:
        raise CampaignError(
            "scope spec needs exactly kind, title, question, inclusion_rule, "
            "and exclusion_rule"
        )
    if value["kind"] not in {"repository", "semantic"}:
        raise CampaignError("scope kind must be repository or semantic")
    for field in ("title", "question", "inclusion_rule", "exclusion_rule"):
        if not isinstance(value[field], str) or not value[field].strip():
            raise CampaignError(f"scope {field} must be nonempty")
    return {
        "kind": value["kind"],
        "title": value["title"].strip(),
        "question": value["question"].strip(),
        "inclusion_rule": value["inclusion_rule"].strip(),
        "exclusion_rule": value["exclusion_rule"].strip(),
    }


def validate_operation_spec(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"scope", "completion"}:
        raise CampaignError("operation spec needs exactly scope and completion")
    scope = validate_scope_spec(value["scope"])
    completion = value["completion"]
    if not isinstance(completion, dict) or "kind" not in completion:
        raise CampaignError("operation completion must be an object with kind")
    if completion["kind"] == "exhaustive":
        if set(completion) != {"kind"}:
            raise CampaignError("exhaustive completion needs exactly kind")
        normalized_completion = {"kind": "exhaustive"}
    elif completion["kind"] == "increment":
        if set(completion) != {"kind", "intent"}:
            raise CampaignError("increment completion needs exactly kind and intent")
        if completion["intent"] not in {"survey", "deepen", "refresh", "drift"}:
            raise CampaignError(
                "increment intent must be survey, deepen, refresh, or drift"
            )
        normalized_completion = {
            "kind": "increment",
            "intent": completion["intent"],
        }
    else:
        raise CampaignError("completion kind must be increment or exhaustive")
    if (
        scope["kind"] == "repository"
        and normalized_completion["kind"] == "increment"
        and normalized_completion["intent"] != "survey"
    ):
        raise CampaignError(
            "repository increment supports only survey intent; use semantic "
            "scope for deepen, refresh, or drift"
        )
    return {"scope": scope, "completion": normalized_completion}


def normalize_discovery_lead(value: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "id",
        "title",
        "question",
        "reason",
        "parent_ids",
        "seed_files",
    }:
        raise CampaignError(
            f"{field} needs id, title, question, reason, parent_ids, and seed_files"
        )
    lead_id = validate_id(value["id"])
    texts = (value["title"], value["question"], value["reason"])
    if any(not isinstance(text, str) or not text.strip() for text in texts):
        raise CampaignError(f"{field} {lead_id} has empty text")
    parent_ids = [
        validate_id(item)
        for item in string_list(value["parent_ids"], f"{field} parent_ids")
    ]
    seed_files = [
        validate_relative_path(item)
        for item in string_list(value["seed_files"], f"{field} seed_files")
    ]
    if len(parent_ids) != len(set(parent_ids)):
        raise CampaignError(f"{field} {lead_id} repeats parent_ids")
    if len(seed_files) != len(set(seed_files)):
        raise CampaignError(f"{field} {lead_id} repeats seed_files")
    if len(seed_files) > MAX_SCOUT_SEED_FILES:
        raise CampaignError(
            f"{field} {lead_id} exceeds {MAX_SCOUT_SEED_FILES} seed files"
        )
    return {
        "id": lead_id,
        "title": value["title"].strip(),
        "question": value["question"].strip(),
        "reason": value["reason"].strip(),
        "parent_ids": sorted(parent_ids),
        "seed_files": sorted(seed_files),
    }


def validate_initial_discovery_plan(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "discovery_plan_version",
        "rationale",
        "leads",
    }:
        raise CampaignError(
            "initial discovery plan needs exactly discovery_plan_version, "
            "rationale, and leads"
        )
    if value["discovery_plan_version"] != 1:
        raise CampaignError("initial discovery plan version must be 1")
    if not isinstance(value["rationale"], str) or not value["rationale"].strip():
        raise CampaignError("initial discovery plan rationale must be nonempty")
    if (
        not isinstance(value["leads"], list)
        or not value["leads"]
        or len(value["leads"]) > MAX_INITIAL_SCOUTS
    ):
        raise CampaignError(
            f"initial discovery plan needs 1..{MAX_INITIAL_SCOUTS} leads"
        )
    leads: list[dict[str, Any]] = []
    for index, raw in enumerate(value["leads"], start=1):
        if not isinstance(raw, dict) or set(raw) != {
            "id",
            "title",
            "question",
            "reason",
        }:
            raise CampaignError(
                f"initial discovery plan lead {index} needs exactly "
                "id, title, question, and reason"
            )
        leads.append(
            normalize_discovery_lead(
                raw | {"parent_ids": [], "seed_files": []},
                field=f"initial discovery plan lead {index}",
            )
        )
    ids = [lead["id"] for lead in leads]
    if len(ids) != len(set(ids)):
        raise CampaignError("initial discovery plan repeats lead ids")
    boundaries = [
        (lead["title"].casefold(), lead["question"].casefold()) for lead in leads
    ]
    if len(boundaries) != len(set(boundaries)):
        raise CampaignError(
            "initial discovery plan repeats a semantic search boundary"
        )
    return {
        "discovery_plan_version": 1,
        "rationale": value["rationale"].strip(),
        "leads": leads,
    }


def discovery_packet(
    seed: dict[str, Any],
    lead: dict[str, Any],
    *,
    source_refs: list[str],
) -> dict[str, Any]:
    return {
        "discovery_contract_version": DISCOVERY_CONTRACT_VERSION,
        "repository_root": seed["repository_root"],
        "spine_root": seed["spine_root"],
        "operation": seed["operation"],
        "lead": lead,
        "source_refs": sorted(source_refs),
    }


def command_discovery_start(args: argparse.Namespace) -> dict[str, Any]:
    repository_root = args.repository_root.resolve()
    spine_root = args.spine_root.resolve()
    if not repository_root.is_dir():
        raise CampaignError(
            f"repository root is not a directory: {repository_root}"
        )
    if not spine_root.is_dir():
        raise CampaignError(f"Spine root is not a directory: {spine_root}")
    require_map_runtime_path(
        args.output_dir,
        repository_root,
        field="discovery output",
    )
    current = load(args.ledger)
    operation = validate_operation_spec(current["operation"])
    scope = operation["scope"]
    recorded_repository = repository_root_from_ledger(current)
    if (
        recorded_repository is not None
        and recorded_repository != repository_root
    ):
        raise CampaignError("discovery repository root differs from operation")
    existing_discovery = current.get("discovery")
    if existing_discovery is not None and (
        existing_discovery.get("root") != str(args.output_dir.resolve())
    ):
        raise CampaignError("operation discovery already started elsewhere")
    require_map_runtime_path(
        args.initial_plan,
        repository_root,
        field="initial discovery plan",
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    packets_dir = args.output_dir / "wave-0001"
    packets_dir.mkdir(exist_ok=True)
    initial_plan = validate_initial_discovery_plan(read_json(args.initial_plan))
    leads = initial_plan["leads"]
    seed = {
        "discovery_contract_version": DISCOVERY_CONTRACT_VERSION,
        "repository_root": str(repository_root),
        "spine_root": str(spine_root),
        "operation": operation,
        "initial_plan": initial_plan,
        "initial_leads": [lead["id"] for lead in leads],
    }
    seed_path = args.output_dir / "discovery-seed.json"
    input_digest = digest_json(
        {
            "contract": DISCOVERY_CONTRACT_VERSION,
            "operation": operation,
            "initial_plan": initial_plan,
            "repository_root": str(repository_root),
            "spine_root": str(spine_root),
        }
    )
    if seed_path.exists() and read_json(seed_path) != seed:
        raise CampaignError("existing discovery seed differs from current inputs")
    atomic_write(seed_path, seed)
    packets: list[str] = []
    expected_packet_names: set[str] = set()
    for lead in leads:
        path = packets_dir / f"lead-{lead['id']}.json"
        expected = discovery_packet(seed, lead, source_refs=[])
        expected_packet_names.add(path.name)
        if path.exists() and read_json(path) != expected:
            raise CampaignError(f"existing discovery packet conflicts: {path}")
        atomic_write(path, expected)
        packets.append(str(path.resolve()))
    unexpected = sorted(
        path.name
        for path in packets_dir.glob("lead-*.json")
        if path.name not in expected_packet_names
    )
    if unexpected:
        raise CampaignError(f"discovery packet directory has stale packets: {unexpected}")
    with locked_ledger(args.ledger) as ledger:
        state = {
            "status": "discovering",
            "root": str(args.output_dir.resolve()),
            "seed": str(seed_path.resolve()),
            "corpus": None,
        }
        already_ready = ledger.get("discovery") == state and same_artifact(
            ledger["artifacts"]["discovery"].get("seed"),
            seed_path,
            input_digest=input_digest,
        )
        if ledger.get("discovery") is not None and ledger.get("discovery") != state:
            raise CampaignError("recorded discovery differs from current inputs")
        ledger["discovery"] = state
        record_artifact(
            ledger,
            "discovery",
            "seed",
            seed_path,
            input_digest=input_digest,
        )
        if not already_ready:
            save_locked(args.ledger, ledger)
    return {
        "status": "already_ready" if already_ready else "written",
        "seed": str((args.output_dir / "discovery-seed.json").resolve()),
        "packets": packets,
        "scope_kind": scope["kind"],
        "completion_kind": operation["completion"]["kind"],
        "initial_leads": len(leads),
    }


def normalize_frontier_decision(
    value: Any,
    *,
    index: int,
) -> dict[str, Any]:
    if not isinstance(value, dict) or "disposition" not in value:
        raise CampaignError(f"frontier decision {index} is invalid")
    disposition = value["disposition"]
    if disposition == "queue":
        expected = {"disposition", "sources", "lead"}
    elif disposition == "defer":
        expected = {"disposition", "sources", "lead", "reason"}
    elif disposition == "duplicate":
        expected = {"disposition", "sources", "target", "reason"}
    elif disposition == "out_of_scope":
        expected = {"disposition", "sources", "reason"}
    else:
        raise CampaignError(
            f"frontier decision {index} has invalid disposition: {disposition}"
        )
    if set(value) != expected:
        raise CampaignError(
            f"frontier decision {index} needs exactly {sorted(expected)}"
        )
    sources = string_list(
        value["sources"],
        f"frontier decision {index} sources",
        nonempty=True,
    )
    if len(sources) != len(set(sources)):
        raise CampaignError(f"frontier decision {index} repeats sources")
    if any(
        re.fullmatch(
            r"[a-z0-9]+(?:-[a-z0-9]+)*/[a-z0-9]+(?:-[a-z0-9]+)*",
            source,
        )
        is None
        for source in sources
    ):
        raise CampaignError(
            f"frontier decision {index} has invalid proposal references"
        )
    normalized: dict[str, Any] = {
        "disposition": disposition,
        "sources": sorted(sources),
    }
    if disposition in {"queue", "defer"}:
        normalized["lead"] = normalize_discovery_lead(
            value["lead"],
            field=f"frontier decision {index} lead",
        )
        if disposition == "defer":
            reason = value["reason"]
            if not isinstance(reason, str) or not reason.strip():
                raise CampaignError(f"frontier decision {index} needs a reason")
            normalized["reason"] = reason.strip()
    else:
        reason = value["reason"]
        if not isinstance(reason, str) or not reason.strip():
            raise CampaignError(f"frontier decision {index} needs a reason")
        normalized["reason"] = reason.strip()
        if disposition == "duplicate":
            normalized["target"] = validate_id(value["target"])
    return normalized


def command_discovery_packets(args: argparse.Namespace) -> dict[str, Any]:
    seed = read_json(args.seed)
    if (
        not isinstance(seed, dict)
        or seed.get("discovery_contract_version") != DISCOVERY_CONTRACT_VERSION
    ):
        raise CampaignError("discovery seed contract is invalid")
    require_map_runtime_path(
        args.output_dir,
        Path(seed["repository_root"]),
        field="discovery packet output",
    )
    raw = read_json(args.frontier)
    if not isinstance(raw, dict) or set(raw) != {"decisions"} or not isinstance(
        raw["decisions"], list
    ):
        raise CampaignError("frontier needs exactly a decisions list")
    decisions = [
        normalize_frontier_decision(value, index=index)
        for index, value in enumerate(raw["decisions"], start=1)
    ]
    completion_kind = validate_operation_spec(seed["operation"])["completion"]["kind"]
    if completion_kind == "exhaustive" and any(
        value["disposition"] == "defer" for value in decisions
    ):
        raise CampaignError("exhaustive discovery cannot defer frontier leads")
    if completion_kind == "increment" and any(
        value["disposition"] == "queue" for value in decisions
    ):
        raise CampaignError("increment discovery cannot expand unresolved leads")
    seen_sources: set[str] = set()
    queued_ids: set[str] = set()
    for decision in decisions:
        overlap = seen_sources & set(decision["sources"])
        if overlap:
            raise CampaignError(
                f"frontier proposal references are repeated: {sorted(overlap)}"
            )
        seen_sources.update(decision["sources"])
        if decision["disposition"] == "queue":
            lead_id = decision["lead"]["id"]
            if lead_id in queued_ids:
                raise CampaignError(f"frontier repeats queued lead: {lead_id}")
            queued_ids.add(lead_id)
    input_digest = digest_json(
        {
            "contract": DISCOVERY_CONTRACT_VERSION,
            "seed": digest_json(seed),
            "decisions": decisions,
        }
    )
    manifest = {
        "kind": "discovery-packets",
        "input_digest": input_digest,
    }
    manifest_path = args.output_dir / "_artifact.json"
    already_ready = manifest_path.is_file()
    if args.output_dir.exists():
        if not manifest_path.is_file() or read_json(manifest_path) != manifest:
            raise CampaignError(
                f"existing discovery packet directory has different inputs: "
                f"{args.output_dir}"
            )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    frontier_value = {"decisions": decisions}
    frontier_path = args.output_dir / "_frontier.json"
    if frontier_path.exists() and read_json(frontier_path) != frontier_value:
        raise CampaignError("existing frontier artifact conflicts")
    atomic_write(frontier_path, frontier_value)
    atomic_write(manifest_path, manifest)
    packets: list[str] = []
    for decision in decisions:
        if decision["disposition"] != "queue":
            continue
        lead = decision["lead"]
        path = args.output_dir / f"lead-{lead['id']}.json"
        expected = discovery_packet(seed, lead, source_refs=decision["sources"])
        if path.exists() and read_json(path) != expected:
            raise CampaignError(f"existing discovery packet conflicts: {path}")
        atomic_write(path, expected)
        packets.append(str(path.resolve()))
    return {
        "status": "already_ready" if already_ready else "written",
        "packets": packets,
        "queued": len(packets),
        "duplicate": sum(
            value["disposition"] == "duplicate" for value in decisions
        ),
        "out_of_scope": sum(
            value["disposition"] == "out_of_scope" for value in decisions
        ),
        "deferred": sum(
            value["disposition"] == "defer" for value in decisions
        ),
    }


def command_discovery_defer(args: argparse.Namespace) -> dict[str, Any]:
    seed = read_json(args.seed)
    operation = validate_operation_spec(seed["operation"])
    if operation["completion"]["kind"] != "increment":
        raise CampaignError("discovery-defer is only for increment completion")
    repository_root = Path(seed["repository_root"]).resolve()
    require_map_runtime_path(
        args.output_dir,
        repository_root,
        field="deferred frontier output",
    )
    decisions: list[dict[str, Any]] = []
    for packet_path in sorted(args.packets_root.rglob("lead-*.json")):
        relative = packet_path.relative_to(args.packets_root)
        result = validate_discovery_packet_result(
            seed,
            packet_path,
            args.results_root / relative,
        )
        parent = result["lead"]["id"]
        for unresolved in result["unresolved_leads"]:
            deferred_id = validate_id(f"{parent}-{unresolved['id']}")
            decisions.append(
                {
                    "disposition": "defer",
                    "sources": [f"{parent}/{unresolved['id']}"],
                    "lead": {
                        key: unresolved[key]
                        for key in ("title", "question", "reason", "seed_files")
                    }
                    | {"id": deferred_id, "parent_ids": [parent]},
                    "reason": "Increment stops after the initial semantic layer.",
                }
            )
    value = {"decisions": decisions}
    manifest = {
        "kind": "discovery-defer",
        "input_digest": digest_json(
            {
                "seed": digest_json(seed),
                "decisions": decisions,
            }
        ),
    }
    manifest_path = args.output_dir / "_artifact.json"
    already_ready = manifest_path.is_file()
    if args.output_dir.exists() and (
        not already_ready or read_json(manifest_path) != manifest
    ):
        raise CampaignError("existing deferred frontier has different inputs")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    frontier_path = args.output_dir / "_frontier.json"
    if frontier_path.exists() and read_json(frontier_path) != value:
        raise CampaignError("existing deferred frontier has different inputs")
    atomic_write(frontier_path, value)
    atomic_write(manifest_path, manifest)
    return {
        "status": "already_ready" if already_ready else "written",
        "deferred": len(decisions),
        "frontier": str(frontier_path.resolve()),
    }


def validate_coverage_review(value: Any) -> dict[str, Any]:
    expected = {
        "coverage_contract_version",
        "status",
        "reason",
        "inspected_roots",
        "open_leads",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise CampaignError("coverage review has invalid shape")
    if value["coverage_contract_version"] != 1:
        raise CampaignError("coverage review contract is invalid")
    if value["status"] not in {"clear", "gaps"}:
        raise CampaignError("coverage review status is invalid")
    if not isinstance(value["reason"], str) or not value["reason"].strip():
        raise CampaignError("coverage review reason must be nonempty")
    string_list(
        value["inspected_roots"],
        "coverage inspected_roots",
        nonempty=True,
    )
    if not isinstance(value["open_leads"], list):
        raise CampaignError("coverage open_leads must be a list")
    if value["status"] == "clear" and value["open_leads"]:
        raise CampaignError("clear coverage review cannot contain open leads")
    if value["status"] == "gaps" and not value["open_leads"]:
        raise CampaignError("gaps coverage review needs open leads")
    return value


def command_coverage_record(args: argparse.Namespace) -> dict[str, Any]:
    current = load(args.ledger)
    operation = validate_operation_spec(current["operation"])
    if (
        operation["scope"]["kind"] != "repository"
        or operation["completion"]["kind"] != "exhaustive"
    ):
        raise CampaignError(
            "coverage-record is only for repository exhaustive operations"
        )
    repository_root = repository_root_from_ledger(current)
    for path, field in (
        (args.topic_plan, "coverage topic plan"),
        (args.review, "coverage review"),
    ):
        require_map_runtime_path(path, repository_root, field=field)
    review = validate_coverage_review(read_json(args.review))
    plan_digest = hashlib.sha256(args.topic_plan.read_bytes()).hexdigest()
    value = {
        "status": review["status"],
        "plan_digest": plan_digest,
        "review": str(args.review.resolve()),
        "review_digest": hashlib.sha256(args.review.read_bytes()).hexdigest(),
        "open_leads": len(review["open_leads"]),
    }
    with locked_ledger(args.ledger) as ledger:
        already_ready = ledger.get("coverage_audit") == value
        if not already_ready:
            ledger["coverage_audit"] = value
            save_locked(args.ledger, ledger)
        return {
            "status": "already_ready" if already_ready else "recorded",
            "result": review["status"],
            "open_leads": len(review["open_leads"]),
            "revision": ledger["revision"],
        }


def command_coverage_reopen(args: argparse.Namespace) -> dict[str, Any]:
    seed = read_json(args.seed)
    current = load(args.ledger)
    review = validate_coverage_review(read_json(args.review))
    if review["status"] != "gaps":
        raise CampaignError("coverage-reopen requires a gaps review")
    audit = current.get("coverage_audit")
    if (
        not isinstance(audit, dict)
        or audit.get("status") != "gaps"
        or audit.get("review") != str(args.review.resolve())
    ):
        raise CampaignError("coverage gaps are not recorded in the campaign")
    repository_root = Path(seed["repository_root"]).resolve()
    require_map_runtime_path(
        args.output_dir,
        repository_root,
        field="coverage discovery output",
    )
    decisions: list[dict[str, Any]] = []
    proposals: list[str] = []
    for index, raw in enumerate(review["open_leads"], start=1):
        if not isinstance(raw, dict) or set(raw) != {
            "id", "title", "question", "reason", "seed_files"
        }:
            raise CampaignError(f"coverage lead {index} has invalid shape")
        lead = normalize_discovery_lead(
            raw | {"parent_ids": []},
            field=f"coverage lead {index}",
        )
        validate_repository_files(
            repository_root,
            lead["seed_files"],
            field=f"coverage lead {lead['id']} seed file",
        )
        source = f"coverage-audit/{lead['id']}"
        proposals.append(source)
        decisions.append(
            {
                "disposition": "queue",
                "sources": [source],
                "lead": lead,
            }
        )
    manifest = {
        "kind": "coverage-reopen",
        "input_digest": digest_json(
            {
                "seed": digest_json(seed),
                "review": review,
            }
        ),
    }
    manifest_path = args.output_dir / "_artifact.json"
    already_ready = manifest_path.is_file()
    if args.output_dir.exists() and (
        not already_ready or read_json(manifest_path) != manifest
    ):
        raise CampaignError("existing coverage discovery has different inputs")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    gaps = {"proposals": proposals}
    frontier = {"decisions": decisions}
    for path, value in (
        (args.output_dir / "_coverage-gaps.json", gaps),
        (args.output_dir / "_frontier.json", frontier),
    ):
        if path.exists() and read_json(path) != value:
            raise CampaignError(f"existing coverage artifact conflicts: {path}")
        atomic_write(path, value)
    atomic_write(manifest_path, manifest)
    packets: list[str] = []
    for decision in decisions:
        lead = decision["lead"]
        path = args.output_dir / f"lead-{lead['id']}.json"
        expected = discovery_packet(seed, lead, source_refs=decision["sources"])
        if path.exists() and read_json(path) != expected:
            raise CampaignError(f"existing coverage packet conflicts: {path}")
        atomic_write(path, expected)
        packets.append(str(path.resolve()))
    return {
        "status": "already_ready" if already_ready else "written",
        "packets": packets,
        "queued": len(packets),
    }


def command_discovery_reopen(args: argparse.Namespace) -> dict[str, Any]:
    seed = read_json(args.seed)
    if (
        not isinstance(seed, dict)
        or seed.get("discovery_contract_version") != DISCOVERY_CONTRACT_VERSION
    ):
        raise CampaignError("discovery seed contract is invalid")
    require_map_runtime_path(
        args.output_dir,
        Path(seed["repository_root"]),
        field="reopened discovery output",
    )
    plan = read_json(args.topic_plan)
    operation = validate_operation_spec(seed["operation"])
    if operation["completion"]["kind"] != "exhaustive":
        raise CampaignError("only exhaustive discovery may reopen synthesis gaps")
    current = load(args.ledger)
    if current["operation"] != operation:
        raise CampaignError("discovery operation differs from ledger")
    if current.get("discovery", {}).get("status") not in {"synthesis", "discovering"}:
        raise CampaignError("ledger is not awaiting synthesis")
    if not isinstance(plan, dict) or set(plan) != {
        "topics",
        "covered",
        "supporting",
        "open_leads",
        "deferred_leads",
        "peer_family_review",
    }:
        raise CampaignError("synthesis topic plan shape is invalid")
    if not isinstance(plan["open_leads"], list) or not plan["open_leads"]:
        raise CampaignError("discovery-reopen requires nonempty open_leads")
    if plan["deferred_leads"]:
        raise CampaignError("exhaustive synthesis cannot defer discovery leads")
    decisions: list[dict[str, Any]] = []
    proposals: list[str] = []
    seen_ids: set[str] = set()
    for index, value in enumerate(plan["open_leads"], start=1):
        if not isinstance(value, dict) or set(value) != {
            "id",
            "title",
            "question",
            "reason",
            "seed_files",
        }:
            raise CampaignError(
                f"open discovery lead {index} has invalid shape"
            )
        lead_id = validate_id(value["id"])
        if lead_id in seen_ids:
            raise CampaignError(f"open discovery lead repeats id: {lead_id}")
        seen_ids.add(lead_id)
        texts = (value["title"], value["question"], value["reason"])
        if any(not isinstance(text, str) or not text.strip() for text in texts):
            raise CampaignError(f"open discovery lead {lead_id} has empty text")
        seed_files = [
            validate_relative_path(item)
            for item in string_list(
                value["seed_files"],
                f"open discovery lead {lead_id} seed_files",
            )
        ]
        if len(seed_files) != len(set(seed_files)):
            raise CampaignError(
                f"open discovery lead {lead_id} repeats seed_files"
            )
        if len(seed_files) > MAX_SCOUT_SEED_FILES:
            raise CampaignError(
                f"open discovery lead {lead_id} exceeds "
                f"{MAX_SCOUT_SEED_FILES} seed files"
            )
        validate_repository_files(
            Path(seed["repository_root"]),
            seed_files,
            field=f"open discovery lead {lead_id} seed file",
        )
        source = f"synthesis/{lead_id}"
        proposals.append(source)
        decisions.append(
            {
                "disposition": "queue",
                "sources": [source],
                "lead": {
                    "id": lead_id,
                    "title": value["title"].strip(),
                    "question": value["question"].strip(),
                    "reason": value["reason"].strip(),
                    "parent_ids": [],
                    "seed_files": sorted(set(seed_files)),
                },
            }
        )
    input_digest = digest_json(
        {
            "contract": DISCOVERY_CONTRACT_VERSION,
            "seed": digest_json(seed),
            "topic_plan": digest_json(plan),
        }
    )
    manifest = {"kind": "discovery-reopen", "input_digest": input_digest}
    manifest_path = args.output_dir / "_artifact.json"
    already_ready = manifest_path.is_file()
    if current.get("discovery", {}).get("status") == "discovering" and not same_artifact(
        current["artifacts"]["discovery"].get(f"reopen-{args.output_dir.name}"),
        args.output_dir,
        input_digest=input_digest,
    ):
        raise CampaignError(
            "discovery is already open for a different or incomplete wave"
        )
    if args.output_dir.exists() and (
        not already_ready or read_json(manifest_path) != manifest
    ):
        raise CampaignError(
            f"existing reopened discovery wave has different inputs: {args.output_dir}"
        )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    gaps = {"proposals": sorted(proposals)}
    frontier = {"decisions": decisions}
    for path, expected in (
        (args.output_dir / "_synthesis-gaps.json", gaps),
        (args.output_dir / "_frontier.json", frontier),
    ):
        if path.exists() and read_json(path) != expected:
            raise CampaignError(f"existing discovery artifact conflicts: {path}")
        atomic_write(path, expected)
    atomic_write(manifest_path, manifest)
    packets: list[str] = []
    for decision in decisions:
        lead = decision["lead"]
        path = args.output_dir / f"lead-{lead['id']}.json"
        expected = discovery_packet(seed, lead, source_refs=decision["sources"])
        if path.exists() and read_json(path) != expected:
            raise CampaignError(f"existing discovery packet conflicts: {path}")
        atomic_write(path, expected)
        packets.append(str(path.resolve()))
    with locked_ledger(args.ledger) as ledger:
        artifact_current = same_artifact(
            ledger["artifacts"]["discovery"].get(
                f"reopen-{args.output_dir.name}"
            ),
            args.output_dir,
            input_digest=input_digest,
        )
        ledger["discovery"] = {
            **ledger["discovery"],
            "status": "discovering",
            "corpus": None,
        }
        record_artifact(
            ledger,
            "discovery",
            f"reopen-{args.output_dir.name}",
            args.output_dir,
            input_digest=input_digest,
        )
        if (
            not already_ready
            or not artifact_current
            or current.get("discovery", {}).get("status") != "discovering"
        ):
            save_locked(args.ledger, ledger)
    return {
        "status": "already_ready" if already_ready else "written",
        "packets": packets,
        "reopened": len(packets),
    }


def normalize_candidate_topic(value: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "id",
        "title",
        "responsibility",
        "reason",
        "files",
    }:
        raise CampaignError(
            f"{field} needs id, title, responsibility, reason, and files"
        )
    topic_id = validate_id(value["id"])
    texts = (value["title"], value["responsibility"], value["reason"])
    if any(not isinstance(text, str) or not text.strip() for text in texts):
        raise CampaignError(f"{field} {topic_id} has empty text")
    files = [
        validate_relative_path(item)
        for item in string_list(
            value["files"],
            f"{field} {topic_id} files",
            nonempty=True,
        )
    ]
    if len(files) != len(set(files)):
        raise CampaignError(f"{field} {topic_id} repeats files")
    if len(files) > MAX_UNIT_FILES:
        raise CampaignError(
            f"{field} {topic_id} exceeds {MAX_UNIT_FILES} files"
        )
    return {
        "id": topic_id,
        "title": value["title"].strip(),
        "responsibility": value["responsibility"].strip(),
        "reason": value["reason"].strip(),
        "files": sorted(files),
    }


def validate_repository_files(
    repository_root: Path,
    values: list[str],
    *,
    field: str,
) -> None:
    root = repository_root.resolve()
    for relative in values:
        path = root / validate_relative_path(relative)
        try:
            path.resolve().relative_to(root)
        except ValueError as error:
            raise CampaignError(f"{field} escapes repository: {relative}") from error
        if not path.is_file():
            raise CampaignError(f"{field} does not exist: {relative}")
        if not is_probably_text(path):
            raise CampaignError(f"{field} is not UTF-8 text: {relative}")


def validate_discovery_result(
    packet: dict[str, Any],
    raw: Any,
    repository_root: Path,
) -> dict[str, Any]:
    expected = {
        "lead_id",
        "status",
        "reason",
        "inspected",
        "topics",
        "supporting",
        "unresolved_leads",
    }
    if not isinstance(raw, dict) or set(raw) != expected:
        raise CampaignError(
            "discovery result needs exactly lead_id, status, reason, inspected, "
            "topics, supporting, and unresolved_leads"
        )
    lead = normalize_discovery_lead(packet.get("lead"), field="discovery packet lead")
    if raw["lead_id"] != lead["id"]:
        raise CampaignError("discovery result lead_id does not match packet")
    if raw["status"] not in DISCOVERY_TERMINAL_STATUSES:
        raise CampaignError(
            f"discovery result {lead['id']} has nonterminal status"
        )
    if not isinstance(raw["reason"], str) or not raw["reason"].strip():
        raise CampaignError(f"discovery result {lead['id']} needs a reason")
    inspected = raw["inspected"]
    if not isinstance(inspected, dict) or set(inspected) != {"files", "queries"}:
        raise CampaignError(
            f"discovery result {lead['id']} inspected needs files and queries"
        )
    inspected_files = [
        validate_relative_path(item)
        for item in string_list(
            inspected["files"],
            f"discovery result {lead['id']} inspected files",
        )
    ]
    queries = string_list(
        inspected["queries"],
        f"discovery result {lead['id']} queries",
    )
    if len(inspected_files) != len(set(inspected_files)):
        raise CampaignError(
            f"discovery result {lead['id']} repeats inspected files"
        )
    validate_repository_files(
        repository_root,
        inspected_files,
        field=f"discovery result {lead['id']} inspected file",
    )
    if not isinstance(raw["topics"], list):
        raise CampaignError(
            f"discovery result {lead['id']} topics must be a list"
        )
    topics = [
        normalize_candidate_topic(
            value,
            field=f"discovery result {lead['id']} topic",
        )
        for value in raw["topics"]
    ]
    supporting: list[dict[str, Any]] = []
    supporting_files: set[str] = set()
    if not isinstance(raw["supporting"], list):
        raise CampaignError(
            f"discovery result {lead['id']} supporting must be a list"
        )
    for index, value in enumerate(raw["supporting"], start=1):
        if not isinstance(value, dict) or set(value) != {"reason", "files"}:
            raise CampaignError(
                f"discovery result {lead['id']} supporting {index} is invalid"
            )
        reason = value["reason"]
        if not isinstance(reason, str) or not reason.strip():
            raise CampaignError(
                f"discovery result {lead['id']} supporting {index} needs a reason"
            )
        files = [
            validate_relative_path(item)
            for item in string_list(
                value["files"],
                f"discovery result {lead['id']} supporting {index} files",
                nonempty=True,
            )
        ]
        if len(files) != len(set(files)):
            raise CampaignError(
                f"discovery result {lead['id']} supporting {index} repeats files"
            )
        overlap = supporting_files & set(files)
        if overlap:
            raise CampaignError(
                f"discovery result {lead['id']} repeats supporting files: "
                f"{sorted(overlap)}"
            )
        supporting_files.update(files)
        supporting.append({"reason": reason.strip(), "files": sorted(files)})
    topic_files = {
        path
        for topic in topics
        for path in topic["files"]
    }
    conflict = topic_files & supporting_files
    if conflict:
        raise CampaignError(
            f"discovery result {lead['id']} classifies files as both topic "
            f"and supporting: {sorted(conflict)}"
        )
    classified = topic_files | supporting_files
    if not classified <= set(inspected_files):
        raise CampaignError(
            f"discovery result {lead['id']} classifies uninspected files: "
            f"{sorted(classified - set(inspected_files))}"
        )
    missing_seed = set(lead["seed_files"]) - classified
    if missing_seed:
        raise CampaignError(
            f"discovery result {lead['id']} leaves seed files unclassified: "
            f"{sorted(missing_seed)}"
        )
    unresolved_leads: list[dict[str, Any]] = []
    if not isinstance(raw["unresolved_leads"], list):
        raise CampaignError(
            f"discovery result {lead['id']} unresolved_leads must be a list"
        )
    unresolved_ids: set[str] = set()
    for value in raw["unresolved_leads"]:
        if not isinstance(value, dict) or set(value) != {
            "id",
            "title",
            "question",
            "reason",
            "seed_files",
            "fallback_kind",
        }:
            raise CampaignError(
                f"discovery result {lead['id']} unresolved lead is invalid"
            )
        unresolved_id = validate_id(value["id"])
        if unresolved_id in unresolved_ids:
            raise CampaignError(
                f"discovery result {lead['id']} repeats unresolved lead {unresolved_id}"
            )
        unresolved_ids.add(unresolved_id)
        texts = (value["title"], value["question"], value["reason"])
        if any(not isinstance(text, str) or not text.strip() for text in texts):
            raise CampaignError(
                f"discovery result {lead['id']} unresolved lead {unresolved_id} has empty text"
            )
        seed_files = [
            validate_relative_path(item)
            for item in string_list(
                value["seed_files"],
                f"discovery result {lead['id']} unresolved lead {unresolved_id} seed_files",
            )
        ]
        validate_repository_files(
            repository_root,
            seed_files,
            field=(
                f"discovery result {lead['id']} unresolved lead {unresolved_id} seed file"
            ),
        )
        unknown_seed = set(seed_files) - set(inspected_files)
        if unknown_seed:
            raise CampaignError(
                f"discovery result {lead['id']} unresolved lead {unresolved_id} uses "
                f"uninspected seed files: {sorted(unknown_seed)}"
            )
        if len(seed_files) != len(set(seed_files)):
            raise CampaignError(
                f"discovery result {lead['id']} unresolved lead {unresolved_id} "
                "repeats seed files"
            )
        if len(seed_files) > MAX_SCOUT_SEED_FILES:
            raise CampaignError(
                f"discovery result {lead['id']} unresolved lead {unresolved_id} "
                f"exceeds {MAX_SCOUT_SEED_FILES} seed files"
            )
        fallback_kind = value["fallback_kind"]
        if fallback_kind not in UNRESOLVED_FALLBACK_KINDS:
            raise CampaignError(
                f"discovery result {lead['id']} unresolved lead {unresolved_id} "
                f"has invalid fallback_kind: {fallback_kind!r}"
            )
        completion_kind = packet["operation"]["completion"]["kind"]
        if (
            completion_kind == "increment"
            and fallback_kind != "increment_continuation"
        ):
            raise CampaignError(
                f"increment unresolved lead {unresolved_id} must use "
                "fallback_kind increment_continuation"
            )
        if (
            completion_kind == "exhaustive"
            and fallback_kind == "increment_continuation"
        ):
            raise CampaignError(
                f"exhaustive unresolved lead {unresolved_id} cannot use "
                "fallback_kind increment_continuation"
            )
        unresolved_leads.append(
            {
                "id": unresolved_id,
                "title": value["title"].strip(),
                "question": value["question"].strip(),
                "reason": value["reason"].strip(),
                "seed_files": sorted(set(seed_files)),
                "fallback_kind": fallback_kind,
            }
        )
    if raw["status"] in {"duplicate", "out_of_scope"} and (
        topics or supporting or unresolved_leads
    ):
        raise CampaignError(
            f"discovery result {lead['id']} status {raw['status']} "
            "cannot publish topics, supporting files, or unresolved leads"
        )
    if raw["status"] == "unresolved" and not unresolved_leads:
        raise CampaignError(
            f"discovery result {lead['id']} unresolved without unresolved leads"
        )
    if raw["status"] == "closed" and unresolved_leads:
        raise CampaignError(
            f"discovery result {lead['id']} closed cannot have unresolved leads"
        )
    return {
        "lead": lead,
        "source_refs": packet.get("source_refs", []),
        "status": raw["status"],
        "reason": raw["reason"].strip(),
        "inspected": {
            "files": sorted(inspected_files),
            "queries": queries,
        },
        "topics": topics,
        "supporting": supporting,
        "unresolved_leads": unresolved_leads,
    }


def evidence_files_digest(repository_root: Path, files: list[str]) -> str:
    root = repository_root.resolve()
    digest = hashlib.sha256()
    for relative in sorted(files):
        path = root / relative
        digest.update(f"F\0{relative}\0".encode())
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
        digest.update(b"\n")
    return digest.hexdigest()


def validate_discovery_packet_result(
    seed: dict[str, Any],
    packet_path: Path,
    result_path: Path,
) -> dict[str, Any]:
    packet = read_json(packet_path)
    if (
        packet.get("discovery_contract_version")
        != DISCOVERY_CONTRACT_VERSION
        or packet.get("repository_root") != seed["repository_root"]
        or packet.get("spine_root") != seed["spine_root"]
        or packet.get("operation") != seed["operation"]
    ):
        raise CampaignError(
            f"discovery packet metadata is invalid: {packet_path}"
        )
    if not result_path.is_file():
        raise CampaignError(f"missing discovery result: {result_path}")
    return validate_discovery_result(
        packet,
        read_json(result_path),
        Path(seed["repository_root"]).resolve(),
    )


def command_discovery_validate(args: argparse.Namespace) -> dict[str, Any]:
    seed = read_json(args.seed)
    if (
        not isinstance(seed, dict)
        or seed.get("discovery_contract_version")
        != DISCOVERY_CONTRACT_VERSION
    ):
        raise CampaignError("discovery seed contract is invalid")
    packets_root = args.packets_root.resolve()
    results_root = args.results_root.resolve()
    validated: list[dict[str, Any]] = []
    relative_paths: set[str] = set()
    for raw_path in args.packets:
        packet_path = raw_path.resolve()
        try:
            relative = packet_path.relative_to(packets_root)
        except ValueError as error:
            raise CampaignError(
                f"discovery packet is outside packets root: {raw_path}"
            ) from error
        relative_name = relative.as_posix()
        if relative_name in relative_paths:
            raise CampaignError(
                f"discovery validation repeats packet: {relative_name}"
            )
        relative_paths.add(relative_name)
        result_path = results_root / relative
        result = validate_discovery_packet_result(
            seed,
            packet_path,
            result_path,
        )
        validated.append(
            {
                "lead_id": result["lead"]["id"],
                "packet": str(packet_path),
                "result": str(result_path),
                "unresolved_leads": len(result["unresolved_leads"]),
            }
        )
    return {
        "status": "valid",
        "validated": validated,
        "count": len(validated),
        "unresolved_leads": sum(
            value["unresolved_leads"] for value in validated
        ),
    }


def command_discovery_collect(args: argparse.Namespace) -> dict[str, Any]:
    output_existed = args.output.exists()
    seed = read_json(args.seed)
    if (
        not isinstance(seed, dict)
        or seed.get("discovery_contract_version") != DISCOVERY_CONTRACT_VERSION
    ):
        raise CampaignError("discovery seed contract is invalid")
    repository_root = Path(seed["repository_root"]).resolve()
    for path, field in (
        (args.packets_root, "discovery packet root"),
        (args.results_root, "discovery result root"),
        (args.output, "discovery corpus"),
    ):
        require_map_runtime_path(path, repository_root, field=field)
    operation = validate_operation_spec(seed["operation"])
    current = load(args.ledger)
    if current["operation"] != operation:
        raise CampaignError("discovery operation differs from ledger")
    discovery_state = current.get("discovery")
    if (
        not isinstance(discovery_state, dict)
        or discovery_state.get("status") not in {"discovering", "synthesis"}
        or discovery_state.get("seed") != str(args.seed.resolve())
    ):
        raise CampaignError("ledger does not track this active discovery")
    packet_paths = sorted(args.packets_root.rglob("lead-*.json"))
    if not packet_paths:
        raise CampaignError("discovery packet tree is empty")
    packets: dict[str, dict[str, Any]] = {}
    results: dict[str, dict[str, Any]] = {}
    for packet_path in packet_paths:
        relative = packet_path.relative_to(args.packets_root)
        result = validate_discovery_packet_result(
            seed,
            packet_path,
            args.results_root / relative,
        )
        lead_id = result["lead"]["id"]
        if lead_id in packets:
            raise CampaignError(f"discovery repeats packet lead: {lead_id}")
        packets[lead_id] = read_json(packet_path)
        results[lead_id] = result
    extra = sorted(
        path.relative_to(args.results_root).as_posix()
        for path in args.results_root.rglob("lead-*.json")
        if not (args.packets_root / path.relative_to(args.results_root)).is_file()
    )
    if extra:
        raise CampaignError(f"discovery results have unknown packets: {extra}")

    proposals = {
        f"{lead_id}/{unresolved['id']}"
        for lead_id, result in results.items()
        for unresolved in result["unresolved_leads"]
    }
    for gaps_path in sorted(
        [
            *args.packets_root.rglob("_synthesis-gaps.json"),
            *args.packets_root.rglob("_coverage-gaps.json"),
        ]
    ):
        raw = read_json(gaps_path)
        if not isinstance(raw, dict) or set(raw) != {"proposals"}:
            raise CampaignError(f"invalid synthesis-gap artifact: {gaps_path}")
        proposals.update(
            string_list(
                raw["proposals"],
                f"synthesis-gap proposals in {gaps_path}",
                nonempty=True,
            )
        )
    decisions: list[dict[str, Any]] = []
    decision_sources: set[str] = set()
    for frontier_path in sorted(args.packets_root.rglob("_frontier.json")):
        raw = read_json(frontier_path)
        if not isinstance(raw, dict) or set(raw) != {"decisions"}:
            raise CampaignError(f"invalid frontier artifact: {frontier_path}")
        for index, value in enumerate(raw["decisions"], start=1):
            decision = normalize_frontier_decision(value, index=index)
            overlap = decision_sources & set(decision["sources"])
            if overlap:
                raise CampaignError(
                    f"frontier decisions repeat proposals: {sorted(overlap)}"
                )
            decision_sources.update(decision["sources"])
            decisions.append(decision)
    if proposals != decision_sources:
        raise CampaignError(
            "discovery frontier is not closed: "
            f"undispositioned={sorted(proposals - decision_sources)}, "
            f"unknown={sorted(decision_sources - proposals)}"
        )
    deferred_decisions = [
        value for value in decisions if value["disposition"] == "defer"
    ]
    if operation["completion"]["kind"] == "exhaustive" and deferred_decisions:
        raise CampaignError("exhaustive discovery cannot contain deferred leads")
    if operation["completion"]["kind"] == "increment" and any(
        value["disposition"] == "queue" for value in decisions
    ):
        raise CampaignError("increment discovery cannot contain queued unresolved leads")
    queued: dict[str, set[str]] = {}
    for decision in decisions:
        if decision["disposition"] == "queue":
            lead_id = decision["lead"]["id"]
            queued.setdefault(lead_id, set()).update(decision["sources"])
            if lead_id not in packets:
                raise CampaignError(
                    f"queued discovery lead has no packet: {lead_id}"
                )
            if set(packets[lead_id].get("source_refs", [])) != set(
                decision["sources"]
            ):
                raise CampaignError(
                    f"queued discovery lead source refs differ: {lead_id}"
                )
        elif decision["disposition"] == "duplicate":
            if decision["target"] not in packets:
                raise CampaignError(
                    "duplicate discovery decision targets unknown lead: "
                    f"{decision['target']}"
                )
    initial = set(seed.get("initial_leads", []))
    unknown_initial = initial - set(packets)
    if unknown_initial:
        raise CampaignError(
            f"discovery initial leads have no packets: {sorted(unknown_initial)}"
        )
    for lead_id, packet in packets.items():
        if lead_id not in initial and lead_id not in queued:
            raise CampaignError(
                f"discovery packet is neither initial nor queued: {lead_id}"
            )
        parents = set(packet["lead"]["parent_ids"])
        if not parents <= set(packets):
            raise CampaignError(
                f"discovery lead {lead_id} has unknown parents: "
                f"{sorted(parents - set(packets))}"
            )
        if lead_id in initial and parents:
            raise CampaignError(
                f"initial discovery lead must not have parents: {lead_id}"
            )
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(lead_id: str) -> None:
        if lead_id in visiting:
            raise CampaignError(f"discovery lead graph has a cycle at {lead_id}")
        if lead_id in visited:
            return
        visiting.add(lead_id)
        for parent_id in packets[lead_id]["lead"]["parent_ids"]:
            visit(parent_id)
        visiting.remove(lead_id)
        visited.add(lead_id)

    for lead_id in packets:
        visit(lead_id)

    topics = [
        topic
        for result in results.values()
        for topic in result["topics"]
    ]
    supporting = [
        value
        for result in results.values()
        for value in result["supporting"]
    ]
    evidence_files = sorted(
        {
            path
            for topic in topics
            for path in topic["files"]
        }
        | {
            path
            for value in supporting
            for path in value["files"]
        }
    )
    snapshot: dict[str, Any]
    if operation["scope"]["kind"] == "repository":
        inventory = repository_inventory(
            repository_root,
            spine_root=Path(seed["spine_root"]),
        )
        snapshot = {
            "kind": "repository",
            "digest": inventory["digest"],
        }
    else:
        snapshot = {
            "kind": "evidence-files",
            "digest": evidence_files_digest(repository_root, evidence_files),
        }
    corpus = {
        "discovery_contract_version": DISCOVERY_CONTRACT_VERSION,
        "repository_root": seed["repository_root"],
        "spine_root": seed["spine_root"],
        "operation": operation,
        "snapshot": snapshot,
        "leads": sorted(results.values(), key=lambda value: value["lead"]["id"]),
        "frontier_decisions": decisions,
        "topics": topics,
        "supporting": supporting,
        "deferred_leads": [
            value["lead"] | {"deferral_reason": value["reason"]}
            for value in deferred_decisions
        ],
        "evidence_files": evidence_files,
    }
    corpus["digest"] = digest_json(corpus)
    input_digest = digest_json(
        {
            "contract": DISCOVERY_CONTRACT_VERSION,
            "seed": digest_json(seed),
            "packets": path_digest(args.packets_root),
            "results": path_digest(args.results_root),
        }
    )
    if output_existed and read_json(args.output) != corpus:
        raise CampaignError(
            "existing discovery corpus conflicts with current packets/results"
        )
    atomic_write(args.output, corpus)
    with locked_ledger(args.ledger) as ledger:
        if ledger["operation"] != operation:
            raise CampaignError("discovery operation differs from ledger")
        state = {
            **ledger["discovery"],
            "status": "synthesis",
            "corpus": str(args.output.resolve()),
        }
        already_ready = output_existed and ledger["discovery"] == state and same_artifact(
            ledger["artifacts"]["discovery"].get("corpus"),
            args.output,
            input_digest=input_digest,
        )
        ledger["discovery"] = state
        record_artifact(
            ledger,
            "discovery",
            "corpus",
            args.output,
            input_digest=input_digest,
        )
        if not already_ready:
            save_locked(args.ledger, ledger)
    return {
        "status": "already_ready" if already_ready else "written",
        "corpus": str(args.output.resolve()),
        "scope_kind": operation["scope"]["kind"],
        "completion_kind": operation["completion"]["kind"],
        "leads": len(results),
        "candidate_topics": len(topics),
        "evidence_files": len(evidence_files),
        "deferred_leads": len(deferred_decisions),
    }


def load_discovery_corpus(
    path: Path,
    repository_root: Path,
    spine_root: Path,
) -> dict[str, Any]:
    corpus = read_json(path)
    expected = {
        "discovery_contract_version",
        "repository_root",
        "spine_root",
        "operation",
        "snapshot",
        "leads",
        "frontier_decisions",
        "topics",
        "supporting",
        "deferred_leads",
        "evidence_files",
        "digest",
    }
    if not isinstance(corpus, dict) or set(corpus) != expected:
        raise CampaignError("discovery corpus shape is invalid")
    if corpus["discovery_contract_version"] != DISCOVERY_CONTRACT_VERSION:
        raise CampaignError("discovery corpus contract version is invalid")
    if corpus["repository_root"] != str(repository_root.resolve()):
        raise CampaignError("discovery corpus repository root differs")
    if corpus["spine_root"] != str(spine_root.resolve()):
        raise CampaignError("discovery corpus Spine root differs")
    operation = validate_operation_spec(corpus["operation"])
    files = [
        validate_relative_path(value)
        for value in string_list(
            corpus["evidence_files"],
            "discovery corpus evidence_files",
        )
    ]
    if files != sorted(set(files)):
        raise CampaignError("discovery corpus evidence_files are not canonical")
    validate_repository_files(
        repository_root,
        files,
        field="discovery corpus evidence file",
    )
    digest = corpus["digest"]
    unsigned = dict(corpus)
    unsigned.pop("digest")
    if digest != digest_json(unsigned):
        raise CampaignError("discovery corpus digest is invalid")
    snapshot = corpus["snapshot"]
    if not isinstance(snapshot, dict) or set(snapshot) != {"kind", "digest"}:
        raise CampaignError("discovery corpus snapshot is invalid")
    if snapshot["kind"] == "repository":
        current_digest = repository_inventory(
            repository_root,
            spine_root=spine_root,
        )["digest"]
    elif snapshot["kind"] == "evidence-files":
        current_digest = evidence_files_digest(repository_root, files)
    else:
        raise CampaignError("discovery corpus snapshot kind is invalid")
    if current_digest != snapshot["digest"]:
        raise CampaignError(
            "discovery corpus source snapshot changed; restart discovery"
        )
    if not isinstance(corpus["topics"], list) or not isinstance(
        corpus["supporting"], list
    ):
        raise CampaignError("discovery corpus candidate lists are invalid")
    if not isinstance(corpus["deferred_leads"], list):
        raise CampaignError("discovery corpus deferred_leads must be a list")
    deferred_leads: list[dict[str, Any]] = []
    for index, value in enumerate(corpus["deferred_leads"], start=1):
        if not isinstance(value, dict) or "deferral_reason" not in value:
            raise CampaignError(f"deferred lead {index} is invalid")
        reason = value["deferral_reason"]
        if not isinstance(reason, str) or not reason.strip():
            raise CampaignError(f"deferred lead {index} needs a deferral_reason")
        lead = dict(value)
        lead.pop("deferral_reason")
        deferred_leads.append(
            normalize_discovery_lead(
                lead,
                field=f"deferred lead {index}",
            )
            | {"deferral_reason": reason.strip()}
        )
    if operation["completion"]["kind"] == "exhaustive" and deferred_leads:
        raise CampaignError("exhaustive discovery corpus cannot defer leads")
    if deferred_leads != corpus["deferred_leads"]:
        raise CampaignError("discovery corpus deferred_leads are not canonical")
    candidate_files = {
        path
        for index, value in enumerate(corpus["topics"], start=1)
        for path in normalize_candidate_topic(
            value,
            field=f"discovery corpus topic {index}",
        )["files"]
    }
    supporting_files: set[str] = set()
    for index, value in enumerate(corpus["supporting"], start=1):
        if not isinstance(value, dict) or set(value) != {"reason", "files"}:
            raise CampaignError(
                f"discovery corpus supporting {index} is invalid"
            )
        if not isinstance(value["reason"], str) or not value["reason"].strip():
            raise CampaignError(
                f"discovery corpus supporting {index} needs a reason"
            )
        supporting_files.update(
            validate_relative_path(item)
            for item in string_list(
                value["files"],
                f"discovery corpus supporting {index} files",
                nonempty=True,
            )
        )
    if candidate_files | supporting_files != set(files):
        raise CampaignError(
            "discovery corpus evidence_files differ from candidate disposition"
        )
    if not isinstance(corpus["leads"], list) or not corpus["leads"]:
        raise CampaignError("discovery corpus needs terminal discovery leads")
    for value in corpus["leads"]:
        if (
            not isinstance(value, dict)
            or value.get("status") not in DISCOVERY_TERMINAL_STATUSES
        ):
            raise CampaignError("discovery corpus contains nonterminal leads")
    return corpus


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


def incomplete_duplicate_campaign(
    ledger_path: Path,
    repository_root: Path,
    operation: dict[str, Any],
) -> Path | None:
    campaign_home = ledger_path.resolve().parent.parent
    if campaign_home.name != "map":
        return None
    for candidate in sorted(campaign_home.glob("*/campaign.json")):
        if candidate.resolve() == ledger_path.resolve():
            continue
        try:
            existing = load(candidate)
            existing_repository = repository_root_from_ledger(existing)
            summary = campaign_summary(candidate)
        except (CampaignError, OSError):
            continue
        if (
            existing_repository == repository_root.resolve()
            and existing["operation"] == operation
            and summary["terminal"] not in {
                "increment_verified",
                "scope_verified",
            }
        ):
            return candidate.resolve()
    return None


def command_init(args: argparse.Namespace) -> dict[str, Any]:
    if args.ledger.exists():
        raise CampaignError(f"campaign already exists: {args.ledger}")
    if args.repository_root is not None:
        ensure_map_runtime_root(args.repository_root)
        require_map_runtime_path(
            args.ledger,
            args.repository_root,
            field="campaign ledger",
        )
        require_map_runtime_path(
            args.operation_spec,
            args.repository_root,
            field="operation specification",
        )
    timestamp = utc_timestamp()
    contract = producer_contract()
    operation = validate_operation_spec(read_json(args.operation_spec))
    duplicate = incomplete_duplicate_campaign(
        args.ledger,
        args.repository_root,
        operation,
    )
    if duplicate is not None and not args.allow_duplicate_incomplete:
        raise CampaignError(
            "an incomplete campaign already owns this operation; resume it "
            f"instead of repeating discovery or synthesis: {duplicate}"
        )
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
        "operation": operation,
        "spine_state": args.spine_state,
        "producer_contract_version": contract["version"],
        "producer_contract_digest": contract["digest"],
        "tasks": {},
        "used_producers": {},
        "publication_epoch": 0,
        "publication_history": [],
        "document_change_history": [],
        "documentation_seed": None,
        "discovery": None,
        "artifacts": {
            "discovery": {},
            "synthesis": {},
            "integration": {},
        },
        "spine_snapshot": None,
        "source_pass": None,
        "coverage_audit": None,
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


def command_bootstrap_spine(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    if ledger["spine_state"] != "empty":
        raise CampaignError("bootstrap-spine requires --spine-state empty")
    if ledger.get("source_pass") is not None:
        raise CampaignError("bootstrap-spine must run before source-pass")
    project = args.project.strip()
    if not project:
        raise CampaignError("bootstrap project must be nonempty")
    spine_root = args.spine_root.resolve()
    process = subprocess.run(
        [
            sys.executable,
            str(args.bootstrapper),
            str(spine_root),
            "--project",
            project,
            "--index-file",
            str(args.index_template),
            "--require-exact",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        try:
            detail = json.loads(process.stderr).get("error")
        except (json.JSONDecodeError, AttributeError):
            detail = process.stderr.strip() or process.stdout.strip()
        raise CampaignError(f"Spine bootstrap failed: {detail}")
    try:
        receipt = json.loads(process.stdout)
    except json.JSONDecodeError as error:
        raise CampaignError("Spine bootstrap returned invalid JSON") from error

    findings = run_checker(
        args.checker,
        spine_root,
        repository_root=repository_root_from_ledger(ledger),
    )
    return {
        "status": receipt["status"],
        "spine_root": str(spine_root),
        "created": receipt["created"],
        "checker_findings": len(findings),
    }


def validate_topic_plan(
    path: Path,
    evidence_files: list[str],
    spine_root: Path,
    operation: dict[str, Any],
    expected_deferred_leads: list[dict[str, Any]],
) -> dict[str, Any]:
    raw = read_json(path)
    if set(raw) != {
        "topics",
        "covered",
        "supporting",
        "open_leads",
        "deferred_leads",
        "peer_family_review",
    }:
        raise CampaignError(
            "topic plan needs exactly topics, covered, supporting, open_leads, "
            "deferred_leads, and peer_family_review"
        )
    if any(
        not isinstance(raw[field], list)
        for field in (
            "topics",
            "covered",
            "supporting",
            "open_leads",
            "deferred_leads",
        )
    ):
        raise CampaignError(
            "topic plan collections must be lists"
        )
    if raw["open_leads"]:
        raise CampaignError(
            "topic plan has open discovery leads; return them to discovery "
            "before source-pass"
        )
    completion_kind = operation["completion"]["kind"]
    peer_family_review = raw["peer_family_review"]
    peer_keys = {"status", "reason", "source_topic_ids", "open_lead_ids"}
    if (
        not isinstance(peer_family_review, dict)
        or set(peer_family_review) != peer_keys
        or peer_family_review.get("status") not in {
            "accounted", "none-found", "not-required"
        }
        or not isinstance(peer_family_review.get("reason"), str)
        or not peer_family_review["reason"].strip()
        or not isinstance(peer_family_review.get("source_topic_ids"), list)
        or not isinstance(peer_family_review.get("open_lead_ids"), list)
    ):
        raise CampaignError("topic plan peer_family_review is invalid")
    if completion_kind == "exhaustive" and peer_family_review["status"] == "not-required":
        raise CampaignError("exhaustive topic plan requires peer-family review")
    if peer_family_review["open_lead_ids"]:
        raise CampaignError("published peer-family review cannot retain open leads")
    if completion_kind == "exhaustive" and raw["deferred_leads"]:
        raise CampaignError("exhaustive topic plan cannot defer discovery leads")
    if raw["deferred_leads"] != expected_deferred_leads:
        raise CampaignError(
            "topic plan deferred_leads differ from the discovery corpus"
        )
    evidence = set(evidence_files)
    topics: list[dict[str, Any]] = []
    topic_ids: set[str] = set()
    topic_files: set[str] = set()

    def normalize_topic(value: Any, *, field: str) -> dict[str, Any]:
        required = {
            "id",
            "document",
            "title",
            "responsibility",
            "reason",
            "relationships",
            "files",
        }
        allowed = required | {"evidence_strata"}
        if not isinstance(value, dict) or set(value) not in (required, allowed):
            raise CampaignError(
                f"each {field} topic needs id, document, title, responsibility, "
                "reason, relationships, and files"
            )
        topic_id = validate_id(value["id"])
        if topic_id in topic_ids:
            raise CampaignError(f"duplicate topic id: {topic_id}")
        topic_ids.add(topic_id)
        document = validate_relative_path(value["document"])
        if not document.endswith(".md") or (
            field == "uncovered" and document == "_INDEX.md"
        ):
            raise CampaignError(
                f"{field} topic {topic_id} document must be non-index Markdown"
            )
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
                f"{MAX_UNIT_FILES} evidence files"
            )
        unknown = sorted(set(files) - evidence)
        if unknown:
            raise CampaignError(
                f"{field} topic {topic_id} has unknown files: {unknown}"
            )
        relationships: list[dict[str, str]] = []
        relation_keys: set[tuple[str, str]] = set()
        if not isinstance(value["relationships"], list):
            raise CampaignError(
                f"{field} topic {topic_id} relationships must be a list"
            )
        for index, row in enumerate(value["relationships"], start=1):
            if not isinstance(row, dict) or set(row) != {
                "type", "target", "reason"
            }:
                raise CampaignError(
                    f"{field} topic {topic_id} relationship {index} is invalid"
                )
            relation = row["type"]
            if relation not in CORE_RELATIONS and (
                not isinstance(relation, str)
                or re.fullmatch(r"x-[a-z0-9]+(?:-[a-z0-9]+)*", relation) is None
            ):
                raise CampaignError(
                    f"{field} topic {topic_id} relationship type is invalid"
                )
            target = validate_id(row["target"])
            meaning = row["reason"]
            if not isinstance(meaning, str) or not meaning.strip():
                raise CampaignError(
                    f"{field} topic {topic_id} relationship reason is empty"
                )
            key = (relation, target)
            if key in relation_keys:
                raise CampaignError(
                    f"{field} topic {topic_id} repeats relationship {key}"
                )
            relation_keys.add(key)
            relationships.append(
                {"type": relation, "target": target, "reason": meaning.strip()}
            )
        evidence_strata = value.get("evidence_strata", [])
        if not isinstance(evidence_strata, list):
            raise CampaignError(
                f"{field} topic {topic_id} evidence_strata must be a list"
            )
        normalized_strata: list[dict[str, str]] = []
        stratum_ids: set[str] = set()
        for row in evidence_strata:
            if not isinstance(row, dict) or set(row) != {"id", "sample"}:
                raise CampaignError(
                    f"{field} topic {topic_id} evidence stratum is invalid"
                )
            stratum_id = validate_id(row["id"])
            sample = validate_relative_path(row["sample"])
            if stratum_id in stratum_ids:
                raise CampaignError(
                    f"{field} topic {topic_id} repeats evidence stratum "
                    f"{stratum_id}"
                )
            if sample not in files:
                raise CampaignError(
                    f"{field} topic {topic_id} evidence stratum sample is "
                    f"outside topic files: {sample}"
                )
            stratum_ids.add(stratum_id)
            normalized_strata.append({"id": stratum_id, "sample": sample})
        return {
            "id": topic_id,
            "document": document,
            "title": title.strip(),
            "responsibility": responsibility.strip(),
            "reason": reason.strip(),
            "relationships": sorted(
                relationships,
                key=lambda row: (row["type"], row["target"], row["reason"]),
            ),
            "files": sorted(files),
            "evidence_strata": normalized_strata,
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
            "document",
            "title",
            "responsibility",
            "reason",
            "relationships",
            "files",
            "coverage_reason",
            "coverage",
        }:
            raise CampaignError(
                "each covered topic needs id, document, title, responsibility, "
                "reason, relationships, files, coverage_reason, and coverage"
            )
        topic = normalize_topic(
            {
                key: value[key]
                for key in (
                    "id", "document", "title", "responsibility", "reason",
                    "relationships", "files",
                )
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
        unknown = sorted(set(files) - evidence)
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
    missing = sorted(evidence - accounted)
    if missing:
        raise CampaignError(f"topic plan leaves evidence files uncovered: {missing}")
    normalized_topics = sorted(topics, key=lambda value: value["id"])
    normalized_covered = sorted(
        covered_topics,
        key=lambda value: value["id"],
    )
    normalized_supporting = sorted(
        supporting,
        key=lambda value: (value["files"], value["reason"]),
    )
    semantic_topics = normalized_topics + normalized_covered
    semantic_ids = {topic["id"] for topic in semantic_topics}
    existing_owners = spine_owner_registry(spine_root)
    existing_ids = set(existing_owners)
    existing_documents = {
        profile["document"]: owner
        for owner, profile in existing_owners.items()
    }
    documents = [topic["document"] for topic in semantic_topics]
    if len(documents) != len(set(documents)):
        raise CampaignError("topic plan repeats canonical documents")
    connected: set[str] = set()
    for topic in semantic_topics:
        existing_document = existing_owners.get(topic["id"], {}).get("document")
        if existing_document is not None and topic["document"] != existing_document:
            raise CampaignError(
                f"existing owner {topic['id']} must keep canonical document "
                f"{existing_document}"
            )
        document_owner = existing_documents.get(topic["document"])
        if document_owner is not None and topic["id"] != document_owner:
            raise CampaignError(
                f"existing document {topic['document']} must keep owner "
                f"{document_owner}"
            )
        for relationship in topic["relationships"]:
            target = relationship["target"]
            if target not in semantic_ids | existing_ids:
                raise CampaignError(
                    f"topic {topic['id']} targets unknown owner: {target}"
                )
            if target == topic["id"]:
                raise CampaignError(f"topic {topic['id']} cannot relate to itself")
            connected.update((topic["id"], target))
    if len(semantic_topics) > 1:
        isolated = sorted(semantic_ids - connected)
        if isolated:
            raise CampaignError(f"topic plan has isolated topics: {isolated}")
    return {
        "topics": normalized_topics,
        "covered": normalized_covered,
        "supporting": normalized_supporting,
        "evidence_files": sorted(evidence),
        "open_leads": [],
        "deferred_leads": raw["deferred_leads"],
        "peer_family_review": peer_family_review,
        "digest": digest_json(
            {
                "topics": normalized_topics,
                "covered": normalized_covered,
                "supporting": normalized_supporting,
                "open_leads": [],
                "deferred_leads": raw["deferred_leads"],
                "peer_family_review": peer_family_review,
            }
        ),
    }


def command_source_pass(args: argparse.Namespace) -> dict[str, Any]:
    current = load(args.ledger)
    if current["source_pass"] is not None:
        raise CampaignError("source-pass is immutable once recorded")
    if current["spine_state"] == "existing" and current["documentation_seed"] is None:
        raise CampaignError("seed-from-spine is required before source-pass")
    if args.discovery_corpus is None:
        raise CampaignError("source-pass requires --discovery-corpus")
    if args.topic_plan is None:
        raise CampaignError("source-pass requires a synthesized --topic-plan")
    run_checker(
        args.checker,
        args.spine_root.resolve(),
        repository_root=args.repository_root.resolve(),
        allowed_findings=checker_baseline_fingerprints(current),
    )
    corpus = load_discovery_corpus(
        args.discovery_corpus,
        args.repository_root,
        args.spine_root,
    )
    if corpus["operation"] != current["operation"]:
        raise CampaignError("discovery corpus operation differs from ledger")
    discovery_state = current.get("discovery")
    if (
        not isinstance(discovery_state, dict)
        or discovery_state.get("status") != "synthesis"
        or discovery_state.get("corpus") != str(args.discovery_corpus.resolve())
    ):
        raise CampaignError("ledger is not ready to record this synthesis")
    evidence_baseline = repository_evidence_baseline(
        args.repository_root,
        corpus["snapshot"]["digest"],
    )
    plan = validate_topic_plan(
        args.topic_plan,
        corpus["evidence_files"],
        args.spine_root,
        corpus["operation"],
        corpus["deferred_leads"],
    )
    if (
        corpus["operation"]["scope"]["kind"] == "repository"
        and corpus["operation"]["completion"]["kind"] == "exhaustive"
    ):
        audit = current.get("coverage_audit")
        plan_digest = hashlib.sha256(args.topic_plan.read_bytes()).hexdigest()
        if (
            not isinstance(audit, dict)
            or audit.get("status") != "clear"
            or audit.get("plan_digest") != plan_digest
        ):
            raise CampaignError(
                "repository exhaustive source-pass requires a clear coverage "
                "audit for the current topic plan"
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
                "planned_document": topic["document"],
                "planned_relationships": topic["relationships"],
                "evidence_baseline": evidence_baseline["marker"],
                "evidence_strata": (
                    topic["evidence_strata"]
                    or [
                        {"id": "semantic-source-01", "sample": topic["files"][0]}
                    ]
                ),
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
            "operation": corpus["operation"],
            "scope": corpus["operation"]["scope"],
            "completion": corpus["operation"]["completion"],
            "scope_snapshot": corpus["snapshot"],
            "discovery_digest": corpus["digest"],
            "discovery_corpus": corpus,
            "evidence_baseline": evidence_baseline,
            "evidence_files": corpus["evidence_files"],
            "topic_plan": plan,
            "topic_tasks": topic_tasks,
            "todo": sorted(value["id"] for value in raw_todo),
            "terminal_reason": None,
            "publication_epoch": ledger["publication_epoch"],
        }
        ledger["spine_snapshot"] = document_hashes(args.spine_root.resolve())
        ledger["discovery"] = {
            **ledger["discovery"],
            "status": "production",
        }
        save_locked(args.ledger, ledger)
        return {
            "status": "recorded",
            "scope_kind": corpus["operation"]["scope"]["kind"],
            "completion_kind": corpus["operation"]["completion"]["kind"],
            "evidence_files": len(corpus["evidence_files"]),
            "discovery_leads": len(corpus["leads"]),
            "topics": len(plan["topics"]),
            "covered_topics": len(plan["covered"]),
            "supporting_groups": len(plan["supporting"]),
            "deferred_leads": len(plan["deferred_leads"]),
            "verification_todo": len(raw_todo),
            "added_todo_count": len(added),
            "revision": ledger["revision"],
        }


def source_task_priority(task: dict[str, Any]) -> tuple[int, int, str]:
    ranked: list[tuple[int, int]] = []
    for value in task.get("evidence", []):
        path = Path(value)
        parts = path.parts
        name = parts[0].lower() if len(parts) == 1 else ""
        if len(parts) == 1 and (
            parts[0] in ROOT_MANIFESTS
            or name.startswith(("dockerfile", "compose."))
        ):
            tier = 1
        elif len(parts) == 1:
            tier = 0
        elif len(parts) == 2:
            tier = 2
        else:
            tier = 3
        ranked.append((tier, len(parts)))
    priority = min(ranked) if ranked else (4, 0)
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
    limit = args.limit if args.limit is not None else MAX_PRODUCER_WAVE
    if limit > MAX_PRODUCER_WAVE:
        raise CampaignError(
            f"producer wave limit exceeds {MAX_PRODUCER_WAVE}"
        )
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
    expected_home = ensure_map_runtime_root(repository_root)
    if args.campaign_home.resolve() != expected_home:
        raise CampaignError(
            f"campaign home must be the workspace Map runtime root: {expected_home}"
        )
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
            current_operation_snapshot(ledger)
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
                "scope": ledger["operation"]["scope"],
                "completion": ledger["operation"]["completion"],
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
        if (
            isinstance(ledger.get("source_pass"), dict)
            and not current_operation_snapshot(ledger)
        ):
            raise CampaignError(
                "campaign source snapshot changed; start a new campaign"
            )
        current_contract = require_current_producer_contract(ledger)
        retained = sorted(
            task["id"]
            for task in ledger["tasks"].values()
            if task["state"] == "assigned"
        )
        resumed_at = utc_timestamp()
        ledger["resume_history"].append(
            {
                "resumed_at": resumed_at,
                "retained_assigned_tasks": retained,
            }
        )
        save_locked(args.ledger, ledger)
        return {
            "status": "resumed",
            "campaign_id": ledger["campaign_id"],
            "resumed_at": resumed_at,
            "retained_assigned_tasks": retained,
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
        "operation": ledger["operation"],
        "current_owner": planned_owner_profile(ledger, task),
        "related_existing_owners": related_existing_owners(ledger, task),
        "task": task_definition(task),
    }
    if args.output is None:
        return packet
    require_map_runtime_path(
        args.output,
        repository_root_from_ledger(ledger),
        field="producer packet",
    )
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
        require_map_runtime_path(
            args.handoffs_root,
            repository_root_from_ledger(ledger),
            field="producer handoff root",
        )
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
        task["handoff_package"] = str(
            args.handoffs_root.resolve()
            / f"{task['id']}-{task['attempts']}"
        )
        ledger["used_producers"][args.owner] = task["id"]
        save_locked(args.ledger, ledger)
        return {
            "status": "assigned",
            "task": task_definition(task),
            "owner": args.owner,
            "attempt": task["attempts"],
            "handoff_package": task["handoff_package"],
            "revision": ledger["revision"],
        }


def command_release(args: argparse.Namespace) -> dict[str, Any]:
    with locked_ledger(args.ledger) as ledger:
        task = require_task(ledger, args.id)
        if task["state"] != "assigned":
            raise CampaignError(f"release requires assigned state: {args.id}")
        task["state"] = "todo"
        task["owner"] = None
        task["handoff_package"] = None
        save_locked(args.ledger, ledger)
        return {
            "status": "released",
            "task": args.id,
            "revision": ledger["revision"],
        }


def command_retry_blocked(args: argparse.Namespace) -> dict[str, Any]:
    reason = args.reason.strip()
    if not reason:
        raise CampaignError("retry-blocked requires a nonempty mechanical reason")
    with locked_ledger(args.ledger) as ledger:
        task = require_task(ledger, args.id)
        history = task["retry_history"]
        if task["state"] == "todo" and history:
            return {
                "status": "already_retryable",
                "task": args.id,
                "revision": ledger["revision"],
            }
        if task["state"] != "blocked":
            raise CampaignError(
                f"retry-blocked requires blocked state: {args.id}"
            )
        history.append(
            {
                "at": utc_timestamp(),
                "reason": reason,
                "previous_terminal_reason": task.get("terminal_reason"),
                "previous_checkpoint_outcome": task.get("checkpoint_outcome"),
                "previous_checkpoint_digest": task.get("checkpoint_digest"),
                "previous_handoff_package": task.get("handoff_package"),
            }
        )
        task["state"] = "todo"
        task["owner"] = None
        task["handoff_package"] = None
        task["checkpoint_outcome"] = None
        task["checkpoint_digest"] = None
        task["terminal_reason"] = None
        task["producer_suggestions"] = []
        task["accepted_staging_root"] = None
        task["accepted_staging_digest"] = None
        ledger["integration_pass"] = None
        save_locked(args.ledger, ledger)
        return {
            "status": "retryable",
            "task": args.id,
            "attempts": task["attempts"],
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
            if relative == "_INDEX.md":
                raise CampaignError("producer must not publish _INDEX.md")
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
    if outcome == "answered" and not any(value in body for value in evidence_refs):
        raise CampaignError(
            "coverage owner document does not reference the verified unit or "
            "inspected evidence"
        )
    return coverage


def validate_task_outcome(task: dict[str, Any], outcome: str) -> None:
    scope_task = bool(task.get("units"))
    if outcome in {"covered", "supporting"} and not scope_task:
        raise CampaignError(
            f"{outcome} is valid only for scope verification tasks"
        )
    if outcome in {"answered", "unresolved"} and scope_task:
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


def semantic_definition_blocks(body: str) -> dict[str, str]:
    lines = body.splitlines()
    starts = [
        (index, match.group(1))
        for index, line in enumerate(lines)
        if (match := SEMANTIC_DEFINITION_RE.match(line))
    ]
    result: dict[str, str] = {}
    for position, (start, identifier) in enumerate(starts):
        next_definition = (
            starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        )
        end = next_definition
        for index in range(start + 1, next_definition):
            if lines[index].startswith("## ") or lines[index].strip().startswith(
                "<!-- specspine:semantic-ids:end"
            ):
                end = index
                break
        result[identifier] = "\n".join(
            line.rstrip() for line in lines[start:end]
        ).rstrip()
    return result


def test_evidence_path(value: str) -> bool:
    path = Path(value)
    components = {part.casefold() for part in path.parts}
    name = path.name.casefold()
    return bool(
        components & TEST_COMPONENTS
        or name.startswith("test_")
        or re.search(r"(?:^|[._-])(?:test|spec)(?:[._-]|$)", name)
    )


def validate_map_candidate_policy(
    staging: dict[str, Path],
    spine_root: Path,
) -> None:
    for relative, candidate in staging.items():
        candidate_blocks = semantic_definition_blocks(
            candidate.read_text(encoding="utf-8")
        )
        candidate_normative = {
            identifier: block
            for identifier, block in candidate_blocks.items()
            if identifier.startswith(NORMATIVE_PREFIXES)
        }
        live = spine_root / relative
        live_normative = (
            {
                identifier: block
                for identifier, block in semantic_definition_blocks(
                    live.read_text(encoding="utf-8")
                ).items()
                if identifier.startswith(NORMATIVE_PREFIXES)
            }
            if live.is_file()
            else {}
        )
        if candidate_normative != live_normative:
            raise CampaignError(
                "Map cannot add, remove, or change accepted normative claims; "
                f"use Evolve: {relative}"
            )
        for identifier, block in candidate_blocks.items():
            if not identifier.startswith("OBS-"):
                continue
            marker = block.find("Evidence:")
            evidence = (
                re.findall(r"`([^`\n]+)`", block[marker + len("Evidence:") :])
                if marker >= 0
                else []
            )
            if evidence and all(test_evidence_path(value) for value in evidence):
                raise CampaignError(
                    f"{identifier} uses only test evidence; tests establish "
                    "repository expectations, not actual behavior"
                )


def harvest_receipt(
    ledger: dict[str, Any],
    task_id: str,
    owner: str,
    raw: dict[str, Any],
    staging: dict[str, Path],
    staging_root: Path,
    spine_root: Path,
) -> dict[str, Any]:
    task = require_task(ledger, task_id)
    status, directions, coverage = validate_checkpoint(raw, staging)
    if status == "draft":
        validate_draft_semantics(staging, task)
        validate_map_candidate_policy(staging, spine_root)
    candidates = infer_candidates(staging, spine_root)
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


def harvest_handoff(
    *,
    ledger_path: Path,
    task_id: str,
    owner: str,
    checkpoint: Path,
    staging_root: Path,
    spine_root: Path,
    receipt_path: Path,
) -> dict[str, Any]:
    raw = read_json(checkpoint)
    staging = candidate_files(staging_root)
    receipt = harvest_receipt(
        load(ledger_path),
        task_id,
        owner,
        raw,
        staging,
        staging_root.resolve(),
        spine_root.resolve(),
    )
    if receipt_path.exists():
        existing = read_json(receipt_path)
        if existing != receipt:
            raise CampaignError(
                f"harvest receipt conflicts with current handoff: {receipt_path}"
            )
        return {
            "status": "already_harvested",
            "task": receipt["task"],
            "outcome": receipt["outcome"],
            "receipt": str(receipt_path.resolve()),
            "checkpoint_digest": receipt["checkpoint_digest"],
            "staging_digest": receipt["staging_digest"],
        }
    atomic_write(receipt_path, receipt)
    return {
        "status": "harvested",
        "task": receipt["task"],
        "outcome": receipt["outcome"],
        "receipt": str(receipt_path.resolve()),
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
    if task.get("handoff_package") != str(package.resolve()):
        raise CampaignError(
            f"handoff root differs from assigned package for task: {task['id']}"
        )
    return package / "checkpoint.json", package / "staging", harvest_root / f"{name}.json"


def harvest_wave(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    for path, field in (
        (args.handoffs_root, "producer handoff root"),
        (args.harvest_root, "harvest receipt root"),
    ):
        require_map_runtime_path(
            path,
            repository_root_from_ledger(ledger),
            field=field,
        )
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
            result = harvest_handoff(
                ledger_path=args.ledger,
                task_id=task["id"],
                owner=task["owner"],
                checkpoint=checkpoint,
                staging_root=staging_root,
                spine_root=args.spine_root,
                receipt_path=receipt,
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
        validate_coverage_result(
            task,
            coverage,
            spine_root,
            inspected,
            outcome=status,
        )
        task["state"] = "review"
        task["producer_suggestions"] = suggestions
    elif status == "unresolved":
        task["state"] = "review"
        task["producer_suggestions"] = []
    elif status == "supporting":
        task["state"] = "review"
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


def accept_wave(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    for path, field in (
        (args.handoffs_root, "producer handoff root"),
        (args.harvest_root, "harvest receipt root"),
    ):
        require_map_runtime_path(
            path,
            repository_root_from_ledger(ledger),
            field=field,
        )
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


def command_settle_wave(args: argparse.Namespace) -> dict[str, Any]:
    harvested = harvest_wave(args)
    if harvested["rejected"]:
        return {
            **harvested,
            "status": "needs_mechanical_repair",
        }
    if harvested["pending"]:
        return {
            **harvested,
            "status": "waiting_for_handoffs",
        }
    accepted = accept_wave(args)
    return {
        "status": "settled_wave",
        "harvest": harvested,
        **{
            key: value
            for key, value in accepted.items()
            if key != "status"
        },
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
    require_map_runtime_path(
        workspace,
        repository_root_from_ledger(ledger),
        field="integration workspace",
    )
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
    input_digest = digest_json(
        {
            "spine_snapshot": current_hashes,
            "settled_tasks": [
                {
                    "id": task["id"],
                    "state": task["state"],
                    "checkpoint_digest": task.get("checkpoint_digest"),
                    "staging_digest": task.get("accepted_staging_digest"),
                }
                for task in sorted(settled, key=lambda value: value["id"])
            ],
        }
    )
    manifest_path = workspace.parent / f".{workspace.name}.map-integration.json"
    manifest = {
        "kind": "integration-workspace",
        "workspace": str(workspace),
        "spine_root": str(spine_root),
        "input_digest": input_digest,
        "spine_snapshot": current_hashes,
        "settled_tasks": sorted(task["id"] for task in settled),
    }
    if workspace.exists():
        if not workspace.is_dir():
            raise CampaignError(f"integration workspace is not a directory: {workspace}")
        if not manifest_path.is_file() or read_json(manifest_path) != manifest:
            raise CampaignError(
                "existing integration workspace is stale or has no matching manifest"
            )
        with locked_ledger(args.ledger) as mutable:
            ready = same_artifact(
                mutable["artifacts"]["integration"].get("workspace"),
                manifest_path,
                input_digest=input_digest,
            )
            record_artifact(
                mutable,
                "integration",
                "workspace",
                manifest_path,
                input_digest=input_digest,
            )
            if not ready:
                save_locked(args.ledger, mutable)
        return {
            "status": "already_ready",
            "workspace": str(workspace),
            "manifest": str(manifest_path),
            "settled_tasks": manifest["settled_tasks"],
            "candidate_files": [],
        }
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
    atomic_write(manifest_path, manifest)
    with locked_ledger(args.ledger) as mutable:
        record_artifact(
            mutable,
            "integration",
            "workspace",
            manifest_path,
            input_digest=input_digest,
        )
        save_locked(args.ledger, mutable)
    return {
        "status": "prepared",
        "workspace": str(workspace),
        "manifest": str(manifest_path),
        "settled_tasks": sorted(task["id"] for task in settled),
        "candidate_files": sorted(copied),
    }


FACET_SECTION_KEYS = {
    "behavior": {"behavior", "lifecycle-and-invariants"},
    "interfaces": {"interfaces"},
    "data": {"information-model", "data-ownership"},
    "failure": {"failure-behavior"},
    "quality": {"quality-constraints"},
    "verification": {"verification"},
}


def replace_markdown_section(body: str, heading: str, replacement: str) -> str:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\s*$.*?(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    replacement = replacement.rstrip() + "\n\n"
    if pattern.search(body):
        return pattern.sub(replacement, body, count=1).rstrip() + "\n"
    return body.rstrip() + "\n\n" + replacement


def conservative_facets(body: str, manifest: dict[str, Any]) -> dict[str, str]:
    headings = {
        key
        for value in re.findall(r"^##\s+(.+?)\s*$", body, re.MULTILINE)
        if (key := canonical_heading(value, manifest)) is not None
    }
    facets = {
        "architecture": "partial",
        "behavior": "missing",
        "interfaces": "missing",
        "data": "missing",
        "failure": "missing",
        "quality": "missing",
        "verification": "missing",
    }
    for facet, section_keys in FACET_SECTION_KEYS.items():
        if headings & section_keys:
            facets[facet] = "partial"
    return facets


def command_assemble_integration(args: argparse.Namespace) -> dict[str, Any]:
    current = load(args.ledger)
    source_pass = current.get("source_pass")
    if not isinstance(source_pass, dict):
        raise CampaignError("assemble-integration requires source-pass")
    settled = {
        task["id"]: task
        for task in current["tasks"].values()
        if task["state"] in {"published", "review"}
    }
    if not settled:
        unfinished = [
            task["id"]
            for task in current["tasks"].values()
            if task["state"] != "complete"
        ]
        if unfinished:
            raise CampaignError(
                f"assemble-integration needs settled producers: {unfinished}"
            )
        if not source_pass["topic_plan"].get("covered"):
            return {"status": "already_integrated", "reviewed_tasks": 0}
    unfinished = [
        task["id"]
        for task in current["tasks"].values()
        if task["state"] in {"todo", "assigned"}
    ]
    if unfinished:
        raise CampaignError(
            "assemble-integration waits for every producer; unfinished="
            f"{sorted(unfinished)}"
        )
    exceptions: list[dict[str, Any]] = []
    for task in settled.values():
        if task["state"] != "published":
            outcome = task.get("checkpoint_outcome")
            code = {
                "covered": "synthesis-coverage-conflict",
                "supporting": "synthesis-granularity-conflict",
                "answered": "derived-answer-needs-anchor-update",
                "unresolved": "derived-uncertainty-needs-preservation",
            }.get(outcome, "producer-outcome-conflict")
            exceptions.append(
                {
                    "task": task["id"],
                    "code": code,
                    "outcome": outcome,
                    "state": task["state"],
                }
            )
    if exceptions:
        return {"status": "needs_semantic_review", "exceptions": exceptions}

    plan = source_pass["topic_plan"]
    topics = {topic["id"]: topic for topic in plan["topics"] + plan["covered"]}
    topic_tasks = source_pass["topic_tasks"]
    runtime = args.ledger.resolve().parent
    workspace = runtime / "integration-workspace"
    report_path = runtime / "integration-report.json"
    repository_root = repository_root_from_ledger(current)
    require_map_runtime_path(
        workspace, repository_root, field="integration workspace"
    )
    require_map_runtime_path(
        report_path, repository_root, field="integration report"
    )
    input_digest = digest_json(
        {
            "spine_snapshot": ledger_spine_snapshot(current),
            "topic_plan": plan["digest"],
            "settled": [
                {
                    "id": task["id"],
                    "checkpoint": task["checkpoint_digest"],
                    "staging": task["accepted_staging_digest"],
                }
                for task in sorted(settled.values(), key=lambda row: row["id"])
            ],
        }
    )
    assembly_manifest = workspace.parent / f".{workspace.name}.map-assembly.json"
    if workspace.exists():
        recorded = (
            read_json(assembly_manifest) if assembly_manifest.is_file() else {}
        )
        if (
            recorded.get("input_digest") != input_digest
            or recorded.get("workspace") != str(workspace)
            or not report_path.is_file()
            or recorded.get("workspace_digest") != path_digest(workspace)
            or recorded.get("report_digest")
            != hashlib.sha256(report_path.read_bytes()).hexdigest()
        ):
            raise CampaignError("existing assembly workspace is stale")
    else:
        shutil.copytree(args.spine_root.resolve(), workspace)
        try:
            for topic_id, task_id in topic_tasks.items():
                task = settled.get(task_id)
                if task is None:
                    continue
                topic = topics[topic_id]
                candidates = accepted_candidates(task)
                if set(candidates) != {topic["document"]}:
                    raise CampaignError(
                        f"producer {task_id} must publish canonical document "
                        f"{topic['document']}; actual={sorted(candidates)}"
                    )
                destination = workspace / topic["document"]
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(candidates[topic["document"]], destination)

            manifest = read_json(workspace / "specspine.json")
            relationship_heading = presentation(manifest)["headings"]["relationships"]
            owner_registry = spine_owner_registry(workspace)
            owner_registry.update(
                {
                    topic["id"]: {
                        "document": topic["document"],
                        "title": topic["title"],
                    }
                    for topic in topics.values()
                }
            )
            for topic in topics.values():
                document = workspace / topic["document"]
                if not document.is_file():
                    raise CampaignError(
                        f"canonical graph document is absent: {topic['document']}"
                    )
                body = document.read_text(encoding="utf-8")
                identity = DOCUMENT_IDENTITY_RE.search(body)
                if identity is None or identity.group(1) != topic["id"]:
                    raise CampaignError(
                        f"canonical document {topic['document']} must define "
                        f"owner ID {topic['id']}"
                    )
                rows: list[str] = []
                for relationship in topic["relationships"]:
                    target = owner_registry[relationship["target"]]
                    relative = os.path.relpath(
                        workspace / target["document"], start=document.parent
                    )
                    title = target["title"].replace("|", "\\|")
                    meaning = relationship["reason"].replace("|", "\\|")
                    rows.append(
                        f"| `{relationship['type']}` | "
                        f"[{title}]({Path(relative).as_posix()}) | {meaning} |"
                    )
                if rows:
                    section = (
                        f"## {relationship_heading}\n\n"
                        "| Relation | Target | Meaning |\n"
                        "|---|---|---|\n"
                        + "\n".join(rows)
                    )
                    body = replace_markdown_section(body, relationship_heading, section)
                else:
                    body = re.sub(
                        rf"^## {re.escape(relationship_heading)}\s*$.*?(?=^## |\Z)",
                        "",
                        body,
                        count=1,
                        flags=re.MULTILINE | re.DOTALL,
                    ).rstrip() + "\n"
                document.write_text(body, encoding="utf-8")

            baseline = source_pass["evidence_baseline"]
            completion = source_pass["completion"]
            inspection_mode = (
                completion["intent"]
                if completion["kind"] == "increment"
                else "exhaustive"
            )
            areas = {
                area["owner"]: area
                for area in manifest.get("areas", [])
                if isinstance(area, dict) and isinstance(area.get("owner"), str)
            }
            for topic in topics.values():
                body = (workspace / topic["document"]).read_text(encoding="utf-8")
                previous = areas.get(topic["id"], {})
                blockers = previous.get("blockers", [])
                derived = conservative_facets(body, manifest)
                previous_facets = previous.get("facets", {})
                facets = {
                    name: (
                        previous_facets[name]
                        if previous_facets.get(name) in {
                            "partial", "complete", "blocked", "not-applicable"
                        }
                        else derived[name]
                    )
                    for name in derived
                }
                producer_checked = topic["id"] in topic_tasks
                inspection = {
                    "source": baseline["source"],
                    "inspected": baseline["inspected"],
                    "mode": inspection_mode,
                    "facets": {
                        name: (
                            "checked"
                            if name == "architecture"
                            or producer_checked
                            and name in {
                                "behavior", "interfaces", "data", "failure"
                            }
                            else "not-checked"
                        )
                        for name in derived
                    },
                }
                areas[topic["id"]] = {
                    "owner": topic["id"],
                    "facets": facets,
                    "blockers": blockers if isinstance(blockers, list) else [],
                    "inspection": inspection,
                }
            manifest["areas"] = [areas[key] for key in sorted(areas)]
            atomic_write_pretty(workspace / "specspine.json", manifest)
            process = subprocess.run(
                [
                    sys.executable,
                    str(
                        getattr(
                            args,
                            "indexer",
                            Path(__file__).with_name("rebuild_indexes.py"),
                        )
                    ),
                    str(workspace),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            if process.returncode:
                raise CampaignError(
                    "deterministic index rebuild failed: "
                    f"{process.stderr.strip() or process.stdout.strip()}"
                )

            changed = spine_changes(
                ledger_spine_snapshot(current), document_hashes(workspace)
            )
            report = {
                "evidence_inspected": sorted(
                    topic["document"] for topic in topics.values()
                ),
                "changed_documents": changed,
                "task_reviews": [
                    {
                        "task": task["id"],
                        "disposition": "integrated",
                        "reason": (
                            "Canonical owner and graph edges were accepted by "
                            "the synthesized production plan."
                        ),
                    }
                    for task in sorted(settled.values(), key=lambda row: row["id"])
                ],
                "suggestion_reviews": [
                    {
                        "task": task["id"],
                        "suggestion": suggestion["id"],
                        "disposition": "rejected",
                        "reason": (
                            "Map records semantic doubt without blocking fast "
                            "publication; Doctor or Evolve may refine it later."
                        ),
                    }
                    for task in sorted(settled.values(), key=lambda row: row["id"])
                    for suggestion in task.get("producer_suggestions", [])
                ],
                "todo": [],
                "organization": {
                    "status": "flat_sufficient",
                    "reason": (
                        "Canonical paths and navigation are fixed by the synthesized "
                        "semantic graph."
                    ),
                },
                "terminal_reason": (
                    "no integration-derived ToDo: the synthesized graph and every "
                    "mechanically valid producer draft were assembled"
                ),
            }
            atomic_write(report_path, report)
            atomic_write(
                assembly_manifest,
                {
                    "kind": "integration-assembly",
                    "workspace": str(workspace),
                    "report": str(report_path),
                    "input_digest": input_digest,
                    "workspace_digest": path_digest(workspace),
                    "report_digest": hashlib.sha256(
                        report_path.read_bytes()
                    ).hexdigest(),
                },
            )
        except Exception:
            shutil.rmtree(workspace, ignore_errors=True)
            report_path.unlink(missing_ok=True)
            assembly_manifest.unlink(missing_ok=True)
            raise

    result = command_integration_pass(
        argparse.Namespace(
            ledger=args.ledger,
            spine_root=args.spine_root,
            workspace=workspace,
            report=report_path,
            checker=args.checker,
        )
    )
    return {
        **result,
        "status": "assembled_and_integrated",
        "workspace": str(workspace),
        "report": str(report_path),
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
        if path.is_file() and path.name != "_INDEX.md"
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
    completion_kind = validate_operation_spec(current["operation"])["completion"][
        "kind"
    ]
    if completion_kind == "increment" and raw_todo:
        raise CampaignError(
            "increment integration cannot derive additional ToDo; preserve "
            "adjacent work as deferred continuation"
        )
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
        if completion_kind == "increment" and disposition == "queued":
            raise CampaignError(
                "increment integration cannot queue producer suggestions"
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
                    f"scope task must not have anchor_disposition: {task_id}"
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
        history = ledger["document_change_history"]
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


def current_operation_snapshot(ledger: dict[str, Any]) -> bool:
    source = ledger.get("source_pass")
    if not isinstance(source, dict):
        return False
    try:
        snapshot = source["scope_snapshot"]
        if snapshot["kind"] == "repository":
            digest = repository_inventory(
                Path(source["repository_root"]),
                spine_root=Path(source["spine_root"]),
            )["digest"]
        elif snapshot["kind"] == "evidence-files":
            digest = evidence_files_digest(
                Path(source["repository_root"]),
                source["evidence_files"],
            )
        else:
            return False
    except (CampaignError, KeyError, OSError):
        return False
    return digest == snapshot.get("digest")


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
        "operation_snapshot_current": current_operation_snapshot(ledger),
        "operation_units_verified": (
            isinstance(source_pass, dict) and units_verified
        ),
        "integration_current": current_integration(ledger),
        "spine_v3_clean": (
            isinstance(ledger.get("integration_pass"), dict)
            and ledger["integration_pass"].get("checker_clean") is True
        ),
    }


def campaign_summary(ledger_path: Path) -> dict[str, Any]:
    ledger = load(ledger_path)
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
        terminal = (
            "increment_verified"
            if ledger["operation"]["completion"]["kind"] == "increment"
            else "scope_verified"
        )
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
        "document_change_history": ledger["document_change_history"],
        "terminal_gates": gates,
        "terminal": terminal,
    }


def command_next_action(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    if ledger.get("source_pass") is None:
        discovery = ledger.get("discovery")
        if discovery is None:
            action = "discover"
            reason = "operation discovery has not started"
        elif discovery.get("status") == "discovering":
            action = "discover"
            reason = "semantic discovery frontier is not yet synthesized"
        elif discovery.get("status") == "synthesis":
            audit = ledger.get("coverage_audit")
            if isinstance(audit, dict) and audit.get("status") == "gaps":
                action = "discover"
                reason = "repository topology coverage gaps require discovery"
            else:
                action = "synthesize"
                reason = "discovery corpus requires semantic synthesis"
        else:
            action = "repair"
            reason = "pre-production operation state is invalid"
        return {
            "campaign_id": ledger["campaign_id"],
            "revision": ledger["revision"],
            "action": action,
            "may_finish": False,
            "may_pause": action == "synthesize",
            "response_policy": (
                "unavoidable_platform_turn_boundary_only"
                if action == "synthesize"
                else "continue_in_same_turn_no_final_response"
            ),
            "reason": reason,
            "counts": {state: 0 for state in sorted(TASK_STATES)},
            "terminal": None,
            "terminal_gates": terminal_gates(ledger),
        }
    summary = campaign_summary(args.ledger)
    states = summary["states"]
    gates = summary["terminal_gates"]
    if summary["terminal"] in {"increment_verified", "scope_verified"}:
        action = "finalize"
        may_finish = True
        reason = summary["terminal"]
    elif summary["terminal"] == "blocked":
        action = "report_blocked"
        may_finish = True
        reason = "campaign has only terminal blockers"
    elif states["assigned"]:
        action = "wait"
        may_finish = False
        reason = "assigned producers have not settled"
    elif states["todo"]:
        action = "dispatch"
        may_finish = False
        reason = "ready verification work remains"
    elif states["published"] or states["review"]:
        action = "integrate"
        may_finish = False
        reason = "all producer waves settled; assemble the synthesized graph"
    else:
        action = "repair"
        may_finish = False
        reason = "terminal gates are stale or incomplete"
    may_pause = bool(
        action == "dispatch"
        and gates["producers_finished"]
        and gates["publications_integrated"]
        and gates["operation_snapshot_current"]
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


def recorded_artifact_path(ledger: dict[str, Any], phase: str, name: str) -> Path | None:
    value = ledger["artifacts"][phase].get(name)
    if not isinstance(value, dict) or not isinstance(value.get("path"), str):
        return None
    return Path(value["path"])


def command_recover(args: argparse.Namespace) -> dict[str, Any]:
    """Reconcile durable phase artifacts and return only missing atomic work."""
    current = load(args.ledger)
    repository_root = repository_root_from_ledger(current)
    for path, field in (
        (args.discovery_results, "discovery result root"),
        (args.synthesis_packet, "synthesis packet"),
        (args.mapping, "synthesis mapping"),
        (args.topic_plan, "topic plan"),
        (args.handoffs_root, "producer handoff root"),
    ):
        if path is not None:
            require_map_runtime_path(path, repository_root, field=field)
    discovery = current.get("discovery")
    packet_root = (
        Path(discovery["root"])
        if isinstance(discovery, dict) and isinstance(discovery.get("root"), str)
        else None
    )
    seed_path = (
        Path(discovery["seed"])
        if isinstance(discovery, dict) and isinstance(discovery.get("seed"), str)
        else None
    )
    seed = read_json(seed_path) if seed_path is not None and seed_path.is_file() else None

    results_root = args.discovery_results or recorded_artifact_path(
        current, "discovery", "results-root"
    )
    scout_complete: list[str] = []
    scout_missing: list[str] = []
    scout_invalid: list[dict[str, str]] = []
    if packet_root is not None and seed is not None:
        for packet in sorted(packet_root.rglob("lead-*.json")):
            relative = packet.relative_to(packet_root)
            if results_root is None:
                scout_missing.append(relative.as_posix())
                continue
            result = results_root / relative
            if not result.is_file():
                scout_missing.append(relative.as_posix())
                continue
            try:
                validate_discovery_packet_result(seed, packet, result)
            except CampaignError as error:
                scout_invalid.append(
                    {"packet": relative.as_posix(), "error": str(error)}
                )
            else:
                scout_complete.append(relative.as_posix())

    canonical: dict[str, dict[str, Any]] = {}
    for name, supplied in (
        ("packet", args.synthesis_packet),
        ("mapping", args.mapping),
        ("topic-plan", args.topic_plan),
    ):
        path = supplied or recorded_artifact_path(current, "synthesis", name)
        canonical[name] = {
            "path": None if path is None else str(path.resolve()),
            "ready": bool(path is not None and path.is_file()),
        }

    workspace_manifest = recorded_artifact_path(
        current, "integration", "workspace"
    )
    integration_ready = bool(
        workspace_manifest is not None
        and workspace_manifest.is_file()
        and isinstance(read_json(workspace_manifest).get("workspace"), str)
        and Path(read_json(workspace_manifest)["workspace"]).is_dir()
    )

    handoffs_root = args.handoffs_root
    harvestable: list[str] = []
    pending_producers: list[str] = []
    for task in sorted(current["tasks"].values(), key=lambda value: value["id"]):
        if task["state"] != "assigned":
            continue
        package_value = task.get("handoff_package")
        package = Path(package_value) if isinstance(package_value, str) else None
        if handoffs_root is not None and package is not None:
            try:
                package.relative_to(handoffs_root.resolve())
            except ValueError:
                package = None
        if (
            package is not None
            and (package / "checkpoint.json").is_file()
            and (package / "staging").is_dir()
        ):
            harvestable.append(task["id"])
        else:
            pending_producers.append(task["id"])

    with locked_ledger(args.ledger) as ledger:
        before = canonical_json(ledger["artifacts"])
        if results_root is not None and results_root.exists():
            record_artifact(
                ledger,
                "discovery",
                "results-root",
                results_root,
                input_digest=digest_json(
                    {"seed": None if seed is None else digest_json(seed)}
                ),
            )
        for name, supplied in (
            ("packet", args.synthesis_packet),
            ("mapping", args.mapping),
            ("topic-plan", args.topic_plan),
        ):
            if supplied is not None and supplied.is_file():
                record_artifact(
                    ledger,
                    "synthesis",
                    name,
                    supplied,
                    input_digest=hashlib.sha256(supplied.read_bytes()).hexdigest(),
                )
        if canonical_json(ledger["artifacts"]) != before:
            save_locked(args.ledger, ledger)

    return {
        "status": "recovered",
        "scouts": {
            "complete": scout_complete,
            "missing": scout_missing,
            "invalid": scout_invalid,
        },
        "synthesis": canonical,
        "integration_workspace_ready": integration_ready,
        "producers": {
            "harvestable": harvestable,
            "pending": pending_producers,
        },
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("ledger", type=Path)
    init.add_argument("operation_spec", type=Path)
    init.add_argument(
        "--spine-state",
        choices=("empty", "existing"),
        default="empty",
    )
    init.add_argument("--repository-root", type=Path, required=True)
    init.add_argument(
        "--allow-duplicate-incomplete",
        action="store_true",
        help="operator-only override; never use for automatic recovery",
    )

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

    bootstrap = sub.add_parser("bootstrap-spine")
    bootstrap.add_argument("ledger", type=Path)
    bootstrap.add_argument("spine_root", type=Path)
    bootstrap.add_argument("--project", required=True)
    bootstrap.add_argument(
        "--bootstrapper",
        type=Path,
        default=Path(__file__).with_name("bootstrap_spine.py"),
    )
    bootstrap.add_argument(
        "--index-template",
        type=Path,
        default=Path(__file__).parent.parent / "assets/templates/architecture-index.md",
    )
    bootstrap.add_argument(
        "--checker",
        type=Path,
        default=Path(__file__).with_name("check_spine.py"),
    )

    discovery_start = sub.add_parser("discovery-start")
    discovery_start.add_argument("ledger", type=Path)
    discovery_start.add_argument("repository_root", type=Path)
    discovery_start.add_argument("spine_root", type=Path)
    discovery_start.add_argument("output_dir", type=Path)
    discovery_start.add_argument(
        "--initial-plan",
        type=Path,
        required=True,
        help="semantic fan-out plan with 1..10 independent search boundaries",
    )

    discovery_packets = sub.add_parser("discovery-packets")
    discovery_packets.add_argument("seed", type=Path)
    discovery_packets.add_argument("frontier", type=Path)
    discovery_packets.add_argument("output_dir", type=Path)

    discovery_defer = sub.add_parser("discovery-defer")
    discovery_defer.add_argument("seed", type=Path)
    discovery_defer.add_argument("packets_root", type=Path)
    discovery_defer.add_argument("results_root", type=Path)
    discovery_defer.add_argument("output_dir", type=Path)

    coverage_record = sub.add_parser("coverage-record")
    coverage_record.add_argument("ledger", type=Path)
    coverage_record.add_argument("topic_plan", type=Path)
    coverage_record.add_argument("review", type=Path)

    coverage_reopen = sub.add_parser("coverage-reopen")
    coverage_reopen.add_argument("ledger", type=Path)
    coverage_reopen.add_argument("seed", type=Path)
    coverage_reopen.add_argument("review", type=Path)
    coverage_reopen.add_argument("output_dir", type=Path)

    discovery_reopen = sub.add_parser("discovery-reopen")
    discovery_reopen.add_argument("ledger", type=Path)
    discovery_reopen.add_argument("seed", type=Path)
    discovery_reopen.add_argument("topic_plan", type=Path)
    discovery_reopen.add_argument("output_dir", type=Path)

    discovery_validate = sub.add_parser("discovery-validate")
    discovery_validate.add_argument("seed", type=Path)
    discovery_validate.add_argument("packets_root", type=Path)
    discovery_validate.add_argument("results_root", type=Path)
    discovery_validate.add_argument("packets", nargs="+", type=Path)

    discovery_collect = sub.add_parser("discovery-collect")
    discovery_collect.add_argument("ledger", type=Path)
    discovery_collect.add_argument("seed", type=Path)
    discovery_collect.add_argument("packets_root", type=Path)
    discovery_collect.add_argument("results_root", type=Path)
    discovery_collect.add_argument("output", type=Path)

    source = sub.add_parser("source-pass")
    source.add_argument("ledger", type=Path)
    source.add_argument("repository_root", type=Path)
    source.add_argument("spine_root", type=Path)
    source.add_argument("--discovery-corpus", type=Path)
    source.add_argument("--topic-plan", type=Path)
    source.add_argument(
        "--checker",
        type=Path,
        default=Path(__file__).with_name("check_spine.py"),
    )

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
    assign.add_argument("--handoffs-root", required=True, type=Path)

    release = sub.add_parser("release")
    release.add_argument("ledger", type=Path)
    release.add_argument("id")

    retry_blocked = sub.add_parser("retry-blocked")
    retry_blocked.add_argument("ledger", type=Path)
    retry_blocked.add_argument("id")
    retry_blocked.add_argument("--reason", required=True)

    settle_wave = sub.add_parser("settle-wave")
    settle_wave.add_argument("ledger", type=Path)
    settle_wave.add_argument("handoffs_root", type=Path)
    settle_wave.add_argument("spine_root", type=Path)
    settle_wave.add_argument("harvest_root", type=Path)

    prepare_integration = sub.add_parser("prepare-integration")
    prepare_integration.add_argument("ledger", type=Path)
    prepare_integration.add_argument("spine_root", type=Path)
    prepare_integration.add_argument("workspace", type=Path)

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
    assemble = sub.add_parser("assemble-integration")
    assemble.add_argument("ledger", type=Path)
    assemble.add_argument("spine_root", type=Path)
    assemble.add_argument(
        "--checker",
        type=Path,
        default=Path(__file__).with_name("check_spine.py"),
    )
    assemble.add_argument(
        "--indexer",
        type=Path,
        default=Path(__file__).with_name("rebuild_indexes.py"),
    )

    next_action = sub.add_parser("next-action")
    next_action.add_argument("ledger", type=Path)

    recover = sub.add_parser("recover")
    recover.add_argument("ledger", type=Path)
    recover.add_argument("--discovery-results", type=Path)
    recover.add_argument("--synthesis-packet", type=Path)
    recover.add_argument("--mapping", type=Path)
    recover.add_argument("--topic-plan", type=Path)
    recover.add_argument("--handoffs-root", type=Path)

    return result


def main() -> int:
    args = parser().parse_args()
    commands = {
        "init": command_init,
        "discover": command_discover,
        "resume-session": command_resume_session,
        "seed-from-spine": command_seed_from_spine,
        "bootstrap-spine": command_bootstrap_spine,
        "discovery-start": command_discovery_start,
        "discovery-packets": command_discovery_packets,
        "discovery-defer": command_discovery_defer,
        "coverage-record": command_coverage_record,
        "coverage-reopen": command_coverage_reopen,
        "discovery-reopen": command_discovery_reopen,
        "discovery-validate": command_discovery_validate,
        "discovery-collect": command_discovery_collect,
        "source-pass": command_source_pass,
        "ready": command_ready,
        "packet": command_packet,
        "assign": command_assign,
        "release": command_release,
        "retry-blocked": command_retry_blocked,
        "settle-wave": command_settle_wave,
        "prepare-integration": command_prepare_integration,
        "integration-pass": command_integration_pass,
        "assemble-integration": command_assemble_integration,
        "next-action": command_next_action,
        "recover": command_recover,
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
