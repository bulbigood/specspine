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


SCHEMA_VERSION = 5
PRODUCER_CONTRACT_VERSION = 1
MAX_UNIT_FILES = 80
MAX_EVIDENCE_STRATA = 4
MAX_CANDIDATE_DOCUMENTS = 12
TASK_STATES = {"todo", "assigned", "review", "published", "complete", "blocked"}
CHECKPOINT_STATUSES = {
    "draft",
    "covered",
    "supporting",
    "retry",
    "blocked",
}
SOURCE_CLASSIFICATIONS = {
    "queued",
    "generated",
    "vendored",
    "test-only",
    "repository-support",
}
TERMINAL_CLASSIFICATIONS = {
    "generated",
    "vendored",
    "test-only",
    "repository-support",
}
REVIEW_DISPOSITIONS = {
    "integrated",
    "already_canonical",
    "confirmed_supporting",
    "retry",
}
SUGGESTION_DISPOSITIONS = {"queued", "covered", "rejected"}
DEFERRED_CHECKER_CODES = {"UNREACHABLE_SPEC"}
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
    ".idea",
    ".vim",
    ".vscode",
    "contribute",
}


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


def ledger_producer_contract(ledger: dict[str, Any]) -> dict[str, Any] | None:
    version = ledger.get("producer_contract_version")
    digest = ledger.get("producer_contract_digest")
    if version is None and digest is None:
        return None
    if (
        not isinstance(version, int)
        or isinstance(version, bool)
        or version < 1
        or not isinstance(digest, str)
        or not re.fullmatch(r"[0-9a-f]{64}", digest)
    ):
        raise CampaignError("campaign producer contract metadata is invalid")
    return {"version": version, "digest": digest}


def require_current_producer_contract(ledger: dict[str, Any]) -> dict[str, Any]:
    recorded = ledger_producer_contract(ledger)
    current = producer_contract()
    if recorded is None:
        raise CampaignError(
            "campaign has no producer contract metadata; run resume-session first"
        )
    if recorded != current:
        raise CampaignError(
            "producer contract changed; run resume-session "
            "--adopt-producer-contract after operator approval"
        )
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
    return {
        path.relative_to(spine_root).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(spine_root.rglob("*.md"))
        if path.is_file()
    }


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
    if raw is None:
        integration = ledger.get("integration_pass")
        raw = (
            integration.get("documents")
            if isinstance(integration, dict)
            else None
        )
    if raw is None:
        seed = ledger.get("documentation_seed")
        raw = seed.get("documents", {}) if isinstance(seed, dict) else {}
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
        if Path(path).suffix.lower() != ".md":
            raise CampaignError(f"changed document must be Markdown: {path}")
        if path in seen:
            raise CampaignError(f"duplicate changed document: {path}")
        seen.add(path)
        normalized.append({"path": path, "operation": value["operation"]})
    normalized.sort(key=lambda value: value["path"])
    if normalized != actual:
        raise CampaignError(
            "integration changed_documents does not match live Spine changes: "
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
    units = [
        validate_relative_path(value)
        for value in string_list(raw.get("units", []), f"ToDo {task_id} units")
    ]
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
        if (
            not isinstance(location, str)
            or not location.strip()
            or not isinstance(known, str)
            or not known.strip()
        ):
            raise CampaignError(
                f"ToDo {task_id} anchor needs nonempty location and known"
            )
        anchor = {
            "document": document,
            "location": location,
            "known": known,
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
            "units",
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
        if name.startswith(".") or name.lower().endswith(
            (".json", ".toml", ".yaml", ".yml")
        ):
            return "repository-root/tooling"
        return "repository-root/runtime"
    first = parts[0]
    if first in COLLAPSED_DIRECTORIES:
        return first
    if len(parts) >= 4 and parts[:3] == ("public", "app", "features"):
        if Path(parts[3]).suffix:
            return "public/app/features"
        return Path(*parts[:4]).as_posix()
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
    """Classify a concrete repository file before it enters a work unit."""
    parts = tuple(value.lower() for value in path.parts)
    first = parts[0]
    name = parts[-1]
    if any(value in VENDORED_DIRECTORIES for value in parts):
        return "vendored", "Mechanically identified vendored dependency file"
    if any(value in GENERATED_DIRECTORIES for value in parts) or (
        name.startswith("zz_generated")
        or name.endswith(("_generated.go", ".generated.ts", ".generated.js"))
        or any(marker in name for marker in (".gen.", "_gen.", ".generated."))
    ):
        return "generated", "Mechanically identified generated file"
    if (
        any(value in TEST_COMPONENTS for value in parts[:-1])
        or first.startswith(("e2e-", "test-"))
        or name.endswith("_test.go")
        or any(marker in name for marker in (".test.", ".spec."))
    ):
        return "test-only", "Mechanically identified test or fixture file"
    area = repository_unit(path)
    if (
        area == "repository-root/governance"
        or first in REPOSITORY_SUPPORT_UNITS
        or first in DOCUMENTATION_ROOTS
        or path.suffix.lower() in {".md", ".txt"}
    ):
        return "repository-support", "Mechanically identified documentation or repository support"
    return "queued", "Production-capable file requires producer verification"


def classification_reason(classification: str) -> str:
    return {
        "queued": "Production-capable unit requires producer verification",
        "generated": "Mechanically identified generated/build output",
        "vendored": "Mechanically identified vendored dependency tree",
        "test-only": "Mechanically identified tests or fixtures",
        "repository-support": "Mechanically identified documentation or repository support",
    }[classification]


def evidence_strata(members: list[str]) -> list[dict[str, Any]]:
    """Create a small deterministic evidence obligation spanning the whole unit."""
    if not members:
        return []
    count = min(MAX_EVIDENCE_STRATA, max(1, math.ceil(len(members) / 20)))
    strata: list[dict[str, Any]] = []
    for index in range(count):
        start = index * len(members) // count
        end = (index + 1) * len(members) // count
        partition = members[start:end]
        strata.append(
            {
                "id": f"stratum-{index + 1:02d}",
                "members": partition,
                "sample": partition[0],
            }
        )
    return strata


def common_directory_depth(members: list[str]) -> int:
    directories = [Path(value).parts[:-1] for value in members]
    if not directories:
        return 0
    depth = 0
    for values in zip(*directories):
        if len(set(values)) != 1:
            break
        depth += 1
    return depth


def split_production_unit(area: str, members: list[str]) -> list[dict[str, Any]]:
    """Split by whole directory subtrees, then pack bounded sibling groups."""
    members = sorted(members)
    partitions = partition_members(members)
    groups = [
        (
            area if len(partitions) == 1 else f"{area}/@unit-{index:03d}",
            values,
        )
        for index, values in enumerate(partitions, start=1)
    ]
    return [
        {
            "area": unit_area,
            "classification": "queued",
            "files": len(values),
            "members": values,
            "strata": evidence_strata(values),
            "samples": [value["sample"] for value in evidence_strata(values)],
        }
        for unit_area, values in groups
    ]


def partition_members(members: list[str]) -> list[list[str]]:
    if len(members) <= MAX_UNIT_FILES:
        return [members]
    depth = common_directory_depth(members)
    grouped: dict[str, list[str]] = {}
    direct: list[str] = []
    for value in members:
        parts = Path(value).parts
        if len(parts) - 1 <= depth:
            direct.append(value)
        else:
            grouped.setdefault(parts[depth], []).append(value)
    atomic: list[list[str]] = [
        direct[index : index + MAX_UNIT_FILES]
        for index in range(0, len(direct), MAX_UNIT_FILES)
    ]
    for _, values in sorted(grouped.items()):
        if len(values) <= MAX_UNIT_FILES:
            atomic.append(values)
        elif common_directory_depth(values) > depth:
            atomic.extend(partition_members(values))
        else:
            atomic.extend(
                values[index : index + MAX_UNIT_FILES]
                for index in range(0, len(values), MAX_UNIT_FILES)
            )
    packed: list[list[str]] = []
    current: list[str] = []
    for values in atomic:
        if current and len(current) + len(values) > MAX_UNIT_FILES:
            packed.append(sorted(current))
            current = []
        current.extend(values)
    if current:
        packed.append(sorted(current))
    return packed


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
            if count >= threshold and len(Path(value).parts) >= 3
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

    units: dict[tuple[str, str], dict[str, Any]] = {}
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
            area = repository_unit(Path(area_path))
            classification = (
                "vendored" if name in VENDORED_DIRECTORIES else "generated"
            )
            record = units.setdefault(
                (area, classification),
                {
                    "area": area,
                    "classification": classification,
                    "members": [],
                    "collapsed_samples": [],
                },
            )
            record["collapsed_samples"].append(area_path + "/")
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
            area = repository_unit(path)
            record = units.setdefault(
                (area, classification),
                {
                    "area": area,
                    "classification": classification,
                    "members": [],
                    "collapsed_samples": [],
                },
            )
            record["members"].append(path.as_posix())
    bounded: list[dict[str, Any]] = []
    used_areas: set[str] = set()
    for (_, classification), record in sorted(units.items()):
        area = record["area"]
        if classification == "queued":
            production = split_production_unit(area, record["members"])
            for value in production:
                if value["area"] in used_areas:
                    raise CampaignError(f"duplicate inventory area: {value['area']}")
                used_areas.add(value["area"])
                bounded.append(value)
            continue
        terminal_area = f"{area}/@{classification}"
        suffix = 2
        while terminal_area in used_areas:
            terminal_area = f"{area}/@{classification}-{suffix}"
            suffix += 1
        used_areas.add(terminal_area)
        members = sorted(record["members"])
        bounded.append(
            {
                "area": terminal_area,
                "classification": classification,
                "files": len(members),
                "members": members,
                "strata": [],
                "samples": [
                    *members[:5],
                    *record["collapsed_samples"][: max(0, 5 - len(members))],
                ],
            }
        )
    inventory = sorted(bounded, key=lambda value: value["area"])
    oversized = [
        value["area"]
        for value in inventory
        if value["classification"] == "queued"
        and value["files"] > MAX_UNIT_FILES
    ]
    if oversized:
        raise CampaignError(f"inventory contains oversized units: {oversized}")
    return {
        "repository_root": str(root),
        "areas": inventory,
        "digest": snapshot.hexdigest(),
        "shape_digest": digest_json(inventory),
        "max_unit_files": MAX_UNIT_FILES,
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
            f"{field} must name only live Markdown documents; "
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
        "producer_contract_history": [
            {
                "version": contract["version"],
                "digest": contract["digest"],
                "activated_at": timestamp,
                "activated_revision": 0,
                "reason": "init",
            }
        ],
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
    documents = document_hashes(args.spine_root.resolve())
    if not documents:
        raise CampaignError("seed-from-spine requires live Markdown documents")
    with locked_ledger(args.ledger) as ledger:
        if ledger["spine_state"] != "existing":
            raise CampaignError("seed-from-spine requires --spine-state existing")
        if ledger["documentation_seed"] is not None:
            raise CampaignError("documentation seed already exists")
        ledger["documentation_seed"] = {
            "documents": documents,
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
            "added_todo": [],
            "revision": ledger["revision"],
        }


def command_inventory(args: argparse.Namespace) -> dict[str, Any]:
    return repository_inventory(
        args.repository_root,
        spine_root=args.spine_root,
    )


def command_source_pass(args: argparse.Namespace) -> dict[str, Any]:
    inventory = repository_inventory(
        args.repository_root,
        spine_root=args.spine_root,
    )
    normalized: dict[str, dict[str, Any]] = {}
    raw_todo: list[dict[str, Any]] = []
    for record in inventory["areas"]:
        area = record["area"]
        classification = record["classification"]
        reason = classification_reason(classification)
        task_id: str | None = None
        candidates: list[str] = []
        if classification == "queued":
            task_id = verification_task_id(area)
            candidates = candidate_owner_documents(
                args.spine_root.resolve(),
                area,
                record["members"],
            )
            raw_todo.append(
                {
                    "id": task_id,
                    "question": (
                        f"Verify whether repository unit {area} is architecturally "
                        "covered; publish the missing observation if it is not"
                    ),
                    "reason": (
                        "Every production-capable inventory unit requires an "
                        "independent producer checkpoint"
                    ),
                    "evidence": record["samples"],
                    "documents": candidates,
                    "excludes": [],
                    "units": [area],
                    "evidence_strata": [
                        {"id": value["id"], "sample": value["sample"]}
                        for value in record["strata"]
                    ],
                    "anchor": None,
                }
            )
        normalized[area] = {
            "classification": classification,
            "reason": reason,
            "task": task_id,
            "candidate_documents": candidates,
            "files": record["files"],
            "members": record["members"],
            "strata": record["strata"],
            "samples": record["samples"],
        }
    with locked_ledger(args.ledger) as ledger:
        if ledger["spine_state"] == "existing" and ledger["documentation_seed"] is None:
            raise CampaignError("seed-from-spine is required before source-pass")
        if ledger["source_pass"] is not None:
            raise CampaignError("source-pass is immutable once recorded")
        added = add_tasks(ledger, raw_todo, source="source-pass")
        ledger["source_pass"] = {
            "repository_root": str(args.repository_root.resolve()),
            "spine_root": str(args.spine_root.resolve()),
            "inventory_digest": inventory["digest"],
            "max_unit_files": inventory["max_unit_files"],
            "inventory": normalized,
            "todo": sorted(value["id"] for value in raw_todo),
            "terminal_reason": None,
            "publication_epoch": ledger["publication_epoch"],
        }
        ledger["spine_snapshot"] = document_hashes(args.spine_root.resolve())
        ledger.setdefault("document_change_history", [])
        save_locked(args.ledger, ledger)
        return {
            "status": "recorded",
            "areas": len(normalized),
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


def command_ready(args: argparse.Namespace) -> dict[str, Any]:
    ledger = load(args.ledger)
    ready = [
        task["id"]
        for task in sorted(ledger["tasks"].values(), key=lambda value: value["id"])
        if task["state"] == "todo"
    ]
    selected = ready[: args.limit] if args.limit is not None else ready
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
        activity = (
            parse_timestamp(ledger.get("updated_at"))
            or parse_timestamp(ledger.get("created_at"))
            or datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        )
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
        recorded_contract = ledger_producer_contract(ledger)
        current_contract = producer_contract()
        contract_change = None
        if recorded_contract is None:
            contract_change = {
                "from": None,
                "to": current_contract,
                "reason": "legacy-migration",
            }
        elif recorded_contract != current_contract:
            if not args.adopt_producer_contract:
                raise CampaignError(
                    "producer contract changed; resume requires operator-approved "
                    "--adopt-producer-contract"
                )
            contract_change = {
                "from": recorded_contract,
                "to": current_contract,
                "reason": "operator-adopted",
            }
        if contract_change is not None:
            ledger["producer_contract_version"] = current_contract["version"]
            ledger["producer_contract_digest"] = current_contract["digest"]
            ledger.setdefault("producer_contract_history", []).append(
                {
                    "version": current_contract["version"],
                    "digest": current_contract["digest"],
                    "activated_at": utc_timestamp(),
                    "activated_revision": ledger["revision"] + 1,
                    "reason": contract_change["reason"],
                }
            )
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
                "producer_contract_change": contract_change,
            }
        )
        save_locked(args.ledger, ledger)
        return {
            "status": "resumed",
            "campaign_id": ledger["campaign_id"],
            "resumed_at": resumed_at,
            "released_orphaned_tasks": released,
            "producer_contract": current_contract,
            "producer_contract_change": contract_change,
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
    if status not in {"draft", "covered"} and directions:
        raise CampaignError(
            f"{status} cannot emit directions without an integrable result"
        )
    coverage: dict[str, Any] | None = None
    if status == "covered":
        raw_owner = raw.get("owner")
        if not isinstance(raw_owner, dict) or set(raw_owner) != {
            "document",
            "claims",
        }:
            raise CampaignError(
                "covered requires owner with document and claims"
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
    elif status in {"blocked", "supporting"}:
        reason = raw.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise CampaignError(f"{status} checkpoint needs reason")
    elif raw.get("reason") is not None:
        raise CampaignError(f"{status} checkpoint must not include reason")
    return status, directions, coverage


def run_checker(
    checker: Path,
    root: Path,
    *,
    candidates_root: Path | None = None,
) -> None:
    command = [sys.executable, str(checker), str(root), "--json"]
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
    ]
    if result.returncode != 0 and not findings:
        raise CampaignError(result.stderr.strip() or "checker failed")
    if material:
        raise CampaignError(
            "SpecSpine checker rejected publication: "
            + json.dumps(material, ensure_ascii=False)
        )


def rollback_publication(
    destinations: list[Path],
    backups: dict[Path, Path],
    sources: dict[Path, Path],
) -> None:
    for destination in reversed(destinations):
        source = sources[destination]
        source.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            os.replace(destination, source)
        backup = backups.get(destination)
        if backup is not None and backup.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(backup, destination)


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
    inventory = source_pass.get("inventory", {})
    covered: set[str] = set()
    covered_strata: dict[str, set[str]] = {unit: set() for unit in units}
    for value in paths:
        path = repository_root / value
        if not path.is_file():
            raise CampaignError(f"checkpoint evidence is not a repository file: {value}")
        for unit in units:
            record = inventory.get(unit)
            if isinstance(record, dict) and value in record.get("members", []):
                covered.add(unit)
                for stratum in record.get("strata", []):
                    if value in stratum.get("members", []):
                        covered_strata[unit].add(stratum["id"])
    if covered != set(units):
        raise CampaignError(
            "checkpoint must inspect at least one concrete file from every task unit; "
            f"missing={sorted(set(units) - covered)}"
        )
    if outcome in {"draft", "covered", "supporting"}:
        missing_strata: dict[str, list[str]] = {}
        for unit in units:
            record = inventory.get(unit, {})
            expected = {
                value["id"]
                for value in record.get("strata", [])
                if isinstance(value, dict) and isinstance(value.get("id"), str)
            }
            missing = sorted(expected - covered_strata[unit])
            if missing:
                missing_strata[unit] = missing
        if missing_strata:
            raise CampaignError(
                "checkpoint must inspect every evidence stratum for an integrable "
                f"result: {missing_strata}"
            )
    return paths


def validate_coverage_result(
    task: dict[str, Any],
    coverage: dict[str, Any] | None,
    spine_root: Path,
    inspected: list[str],
) -> dict[str, Any]:
    if not task.get("units"):
        raise CampaignError("covered is valid only for inventory verification tasks")
    if coverage is None:
        raise CampaignError("covered checkpoint is missing owner evidence")
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
    evidence_refs = [*task["units"], *inspected]
    if not any(value in body for value in evidence_refs):
        raise CampaignError(
            "coverage owner document does not reference the verified unit or "
            "inspected evidence"
        )
    return coverage


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
    status, directions, coverage = validate_checkpoint(raw, staging)
    candidates = infer_candidates(staging, spine_root)
    if candidates:
        run_checker(checker, spine_root, candidates_root=staging_root)
    task = require_task(ledger, task_id)
    if task["state"] != "assigned":
        raise CampaignError(f"harvest requires assigned task: {task_id}")
    if task["owner"] != owner:
        raise CampaignError(
            f"checkpoint owner mismatch: expected {task['owner']}, got {owner}"
        )
    inspected = validate_task_evidence(
        ledger,
        task,
        raw.get("evidence"),
        outcome=status,
    )
    if status == "covered":
        validate_coverage_result(task, coverage, spine_root, inspected)
    if status == "supporting" and not task.get("units"):
        raise CampaignError(
            "supporting is valid only for inventory verification tasks"
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
        harvested.append(task["id"])
        cached += result["status"] == "already_harvested"
    return {
        "status": "harvested_wave",
        "assigned": len(tasks),
        "harvested": len(harvested),
        "already_harvested": cached,
        "pending": len(pending),
        "harvested_tasks": harvested,
        "pending_tasks": pending,
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


def command_accept(args: argparse.Namespace) -> dict[str, Any]:
    raw = read_json(args.checkpoint)
    staging = candidate_files(args.staging_root)
    status, directions, coverage = validate_checkpoint(raw, staging)
    candidates = infer_candidates(staging, args.spine_root.resolve())
    checkpoint_digest = digest_json(raw)
    if candidates:
        run_checker(
            args.checker,
            args.spine_root.resolve(),
            candidates_root=args.staging_root.resolve(),
        )

    backups_root = Path(tempfile.mkdtemp(prefix="specspine-map-backup."))
    destinations: list[Path] = []
    backups: dict[Path, Path] = {}
    sources: dict[Path, Path] = {}
    published: list[str] = []
    try:
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
            inspected = validate_task_evidence(
                ledger,
                task,
                raw.get("evidence"),
                outcome=status,
            )
            suggestions = normalize_directions(task["id"], directions)
            if status == "draft":
                spine_root = args.spine_root.resolve()
                plans: list[tuple[dict[str, str], Path, Path, bool]] = []
                for candidate in candidates:
                    source = staging[candidate["path"]]
                    destination = spine_root / candidate["path"]
                    exists = destination.exists()
                    if candidate["operation"] == "create" and exists:
                        raise CampaignError(f"create destination exists: {candidate['path']}")
                    if candidate["operation"] == "replace" and not exists:
                        raise CampaignError(
                            f"replace destination is missing: {candidate['path']}"
                        )
                    plans.append((candidate, source, destination, exists))
                try:
                    for candidate, source, destination, exists in plans:
                        sources[destination] = source
                        if exists:
                            backup = backups_root / candidate["path"]
                            backup.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(destination, backup)
                            backups[destination] = backup
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        os.replace(source, destination)
                        destinations.append(destination)
                        published.append(candidate["path"])
                    run_checker(args.checker, spine_root)
                except Exception:
                    rollback_publication(destinations, backups, sources)
                    raise
                task["state"] = "published"
                task["published"] = published
                task["producer_suggestions"] = suggestions
                ledger["publication_epoch"] += 1
                ledger["integration_pass"] = None
                for candidate in candidates:
                    ledger["publication_history"].append(
                        {
                            "task": task["id"],
                            "path": candidate["path"],
                            "operation": candidate["operation"],
                            "publication_epoch": ledger["publication_epoch"],
                        }
                    )
            elif status == "covered":
                task["state"] = "review"
                task["checkpoint_outcome"] = status
                task["coverage_result"] = validate_coverage_result(
                    task,
                    coverage,
                    args.spine_root.resolve(),
                    inspected,
                )
                task["producer_suggestions"] = suggestions
                ledger["publication_epoch"] += 1
                ledger["integration_pass"] = None
            elif status == "supporting":
                if not task.get("units"):
                    raise CampaignError(
                        "supporting is valid only for inventory verification tasks"
                    )
                task["state"] = "review"
                task["checkpoint_outcome"] = status
                task["support_result"] = {
                    "boundary_summary": raw["summary"].strip(),
                    "reason": raw["reason"].strip(),
                    "evidence": inspected,
                }
                task["producer_suggestions"] = []
                ledger["publication_epoch"] += 1
                ledger["integration_pass"] = None
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
            task["owner"] = None
            if status == "draft":
                task["checkpoint_outcome"] = status
            task["checkpoint_digest"] = checkpoint_digest
            save_locked(args.ledger, ledger)
            return {
                "status": "accepted",
                "task": task["id"],
                "task_state": task["state"],
                "published": published,
                "suggestions_pending_review": [
                    value["id"] for value in suggestions
                ],
                "revision": ledger["revision"],
            }
    finally:
        shutil.rmtree(backups_root, ignore_errors=True)


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
    prepared: list[tuple[dict[str, Any], Path, Path, Path]] = []
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
        prepared.append((task, checkpoint, staging_root, receipt))

    results = [
        command_accept(
            argparse.Namespace(
                ledger=args.ledger,
                id=task["id"],
                checkpoint=checkpoint,
                staging_root=staging_root,
                spine_root=args.spine_root,
                owner=task["owner"],
                harvest_receipt=receipt,
                checker=args.checker,
            )
        )
        for task, checkpoint, staging_root, receipt in prepared
    ]
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
    if task.get("origin") != "source-pass":
        return
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
    combined = "\n".join(bodies)
    if "**OBS-" not in combined:
        raise CampaignError(
            f"integrated source publication needs a semantic OBS claim: {task['id']}"
        )
    evidence = [*task.get("units", []), *task.get("evidence", [])]
    if not any(value in combined for value in evidence):
        raise CampaignError(
            f"integrated source publication must reference its unit or evidence: {task['id']}"
        )


def command_integration_pass(args: argparse.Namespace) -> dict[str, Any]:
    report = read_json(args.report)
    spine_root = args.spine_root.resolve()
    documents = validate_integration_evidence(
        spine_root,
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
    run_checker(args.checker, spine_root)

    normalized_reviews: dict[str, dict[str, str]] = {}
    for value in reviews:
        if not isinstance(value, dict):
            raise CampaignError("task review must be an object")
        task_id = validate_id(value.get("task"))
        disposition = value.get("disposition")
        reason = value.get("reason")
        if disposition not in REVIEW_DISPOSITIONS:
            raise CampaignError(
                f"invalid integration disposition for {task_id}: {disposition!r}"
            )
        if not isinstance(reason, str) or not reason.strip():
            raise CampaignError(f"task review needs a reason: {task_id}")
        if task_id in normalized_reviews:
            raise CampaignError(f"duplicate task review: {task_id}")
        normalized_reviews[task_id] = {
            "disposition": disposition,
            "reason": reason.strip(),
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
        key = (task_id, suggestion_id)
        if key in normalized_suggestions:
            raise CampaignError(f"duplicate suggestion review: {key}")
        normalized_suggestions[key] = {
            "disposition": disposition,
            "reason": reason.strip(),
            "todo": queued_task,
        }

    with locked_ledger(args.ledger) as ledger:
        actual_changes = spine_changes(
            ledger_spine_snapshot(ledger),
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
            if task["state"] == "published":
                validate_integrated_source_publication(task, spine_root)
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
        ledger["spine_snapshot"] = documents
        save_locked(args.ledger, ledger)
        return {
            "status": "integrated",
            "reviewed_tasks": sorted(settled),
            "added_todo": added,
            "changed_documents": reported_changes,
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
    inventory = (
        source_pass.get("inventory", {}) if isinstance(source_pass, dict) else {}
    )
    units_verified = all(
        value.get("classification") != "queued"
        or (
            value.get("task") in ledger["tasks"]
            and ledger["tasks"][value["task"]]["state"] == "complete"
        )
        for value in inventory.values()
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
    return {
        "campaign_id": summary["campaign_id"],
        "revision": summary["revision"],
        "action": action,
        "may_finish": may_finish,
        "response_policy": (
            "final_response_allowed"
            if may_finish
            else "continue_in_same_turn_no_final_response"
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
    inventory = ledger.get("source_pass", {}).get("inventory", {})
    counts = {
        classification: sum(
            1
            for value in inventory.values()
            if value.get("classification") == classification
        )
        for classification in sorted(SOURCE_CLASSIFICATIONS)
    }
    verified_units = sum(
        value.get("classification") == "queued"
        and value.get("task") in ledger["tasks"]
        and ledger["tasks"][value["task"]]["state"] == "complete"
        for value in inventory.values()
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
        "verified_production_units": verified_units,
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
    resume.add_argument("--adopt-producer-contract", action="store_true")

    seed = sub.add_parser("seed-from-spine")
    seed.add_argument("ledger", type=Path)
    seed.add_argument("spine_root", type=Path)

    inventory = sub.add_parser("inventory")
    inventory.add_argument("repository_root", type=Path)
    inventory.add_argument("--spine-root", type=Path)

    source = sub.add_parser("source-pass")
    source.add_argument("ledger", type=Path)
    source.add_argument("repository_root", type=Path)
    source.add_argument("spine_root", type=Path)

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

    block = sub.add_parser("block")
    block.add_argument("ledger", type=Path)
    block.add_argument("id")
    block.add_argument("--reason", required=True)

    integration = sub.add_parser("integration-pass")
    integration.add_argument("ledger", type=Path)
    integration.add_argument("spine_root", type=Path)
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
