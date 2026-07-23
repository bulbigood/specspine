#!/usr/bin/env python3
"""Validate a deterministic SpecSpine retrieval benchmark corpus."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
RANKING_PATH = (
    ROOT / "skills" / "specspine-extract" / "scripts" / "ranking_v2.py"
)
SEARCH_PATH = (
    ROOT / "skills" / "specspine-extract" / "scripts" / "search_spine_v2.py"
)
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LANGUAGE_RE = re.compile(
    r"^[a-z]{2,3}(?:-[A-Z][a-z]{3})?(?:-[A-Z]{2}|-[0-9]{3})?$"
)
HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
PROJECT_TYPES = {
    "backend-service",
    "web-frontend",
    "mobile-app",
    "cli-sdk",
    "data-pipeline",
    "infrastructure-monorepo",
}
SIZE_RANGES = {
    "small": range(10, 26),
    "medium": range(40, 121),
    "large": range(500, 2001),
}
LEVELS = {"low", "medium", "high"}
OWNERSHIP = {"single", "distributed", "mixed"}
GRAPH_DENSITY = {"none", "low", "medium", "high"}
TAGS = {
    "exact-id",
    "exact-path",
    "exact-title",
    "synonym",
    "morphology",
    "spam",
    "partial-match-decoys",
    "short-owner-long-consumer",
    "graph-only",
    "multi-slice",
    "shared-document",
    "no-match",
    "wrong-must",
    "cross-language",
    "output-budget",
}


class CorpusValidationError(ValueError):
    pass


def load_ranking() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "specspine_corpus_ranking_v2", RANKING_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load ranking policy: {RANKING_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


RANKING = load_ranking()


def load_search() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "specspine_corpus_search_v2_validator", SEARCH_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load search implementation: {SEARCH_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SEARCH = load_search()


def fail(location: str, message: str) -> None:
    raise CorpusValidationError(f"{location}: {message}")


def object_fields(
    value: object,
    location: str,
    required: set[str],
    optional: set[str] = frozenset(),
) -> dict[str, object]:
    if not isinstance(value, dict):
        fail(location, "must be an object")
    missing = sorted(required - set(value))
    unknown = sorted(set(value) - required - optional)
    if missing:
        fail(location, f"missing fields: {', '.join(missing)}")
    if unknown:
        fail(location, f"unknown fields: {', '.join(unknown)}")
    return value


def nonempty_string(value: object, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(location, "must be a non-empty string")
    return value


def integer_between(value: object, location: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        fail(location, "must be an integer")
    if not minimum <= value <= maximum:
        fail(location, f"must be between {minimum} and {maximum}")
    return value


def safe_markdown_path(value: object, location: str) -> str:
    path = Path(nonempty_string(value, location))
    if (
        path.is_absolute()
        or ".." in path.parts
        or path.suffix.casefold() != ".md"
        or path.as_posix() != str(value)
    ):
        fail(location, "must be a safe relative POSIX Markdown path")
    return str(value)


def validate_bootstrap(project: Path, language: str) -> None:
    path = project / "AGENTS.md"
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        fail("project/AGENTS.md", f"cannot read UTF-8 bootstrap: {error}")
    if content.count("<!-- specspine:begin -->") != 1 or content.count(
        "<!-- specspine:end -->"
    ) != 1:
        fail("project/AGENTS.md", "managed markers must occur exactly once")
    if "specspine/README.md" not in content:
        fail("project/AGENTS.md", "must reference specspine/README.md")
    if "{{" in content or "}}" in content:
        fail("project/AGENTS.md", "contains unresolved template placeholders")
    language_line = re.compile(
        rf"^- Documentation language:\s+`?{re.escape(language)}`?\s*$",
        re.MULTILINE,
    )
    if not language_line.search(content):
        fail(
            "project/AGENTS.md",
            "must record the manifest documentation language",
        )


def validate_inventory(
    declared: object,
    spine: Path,
    size_tier: str,
) -> set[str]:
    if not isinstance(declared, dict) or not declared:
        fail("documents", "must be a non-empty object")
    inventory: dict[str, str] = {}
    for raw_path, raw_hash in declared.items():
        path = safe_markdown_path(raw_path, f"documents.{raw_path}")
        digest = nonempty_string(raw_hash, f"documents.{path}")
        if not HASH_RE.fullmatch(digest):
            fail(f"documents.{path}", "must be sha256:<64 lowercase hex>")
        inventory[path] = digest
    discovered = {
        path.relative_to(spine).as_posix()
        for path in spine.rglob("*.md")
        if path.is_file()
    }
    if set(inventory) != discovered:
        missing = sorted(discovered - set(inventory))
        stale = sorted(set(inventory) - discovered)
        detail = []
        if missing:
            detail.append(f"unlisted: {', '.join(missing)}")
        if stale:
            detail.append(f"missing files: {', '.join(stale)}")
        fail("documents", "; ".join(detail))
    if "README.md" not in inventory:
        fail("documents", "must include README.md")
    if len(inventory) not in SIZE_RANGES[size_tier]:
        allowed = SIZE_RANGES[size_tier]
        fail(
            "corpus.size_tier",
            f"{size_tier} requires {allowed.start}..{allowed.stop - 1} documents; "
            f"found {len(inventory)}",
        )
    for relative, expected in inventory.items():
        try:
            content = (spine / relative).read_bytes()
            content.decode("utf-8")
        except (OSError, UnicodeError) as error:
            fail(f"documents.{relative}", f"cannot read UTF-8 file: {error}")
        actual = "sha256:" + hashlib.sha256(content).hexdigest()
        if actual != expected:
            fail(f"documents.{relative}", f"hash mismatch: expected {expected}")
    return set(inventory)


def validate_spine_graph(spine: Path, documents: set[str]) -> None:
    edges: dict[str, set[str]] = {path: set() for path in documents}
    semantic_owners: dict[str, str] = {}
    for relative in sorted(documents):
        source = spine / relative
        try:
            document = SEARCH.parse_document(source, spine, source.stat())
        except Exception as error:
            fail(f"documents.{relative}", f"cannot parse Markdown: {error}")
        for link in document.links:
            if link.target_path not in documents:
                fail(
                    f"documents.{relative}",
                    f"links to missing document: {link.target_path}",
                )
            edges[relative].add(link.target_path)
        for semantic_id in document.semantic_ids:
            previous = semantic_owners.get(semantic_id.identifier)
            if previous is not None:
                fail(
                    f"documents.{relative}",
                    f"semantic ID {semantic_id.identifier} already belongs to {previous}",
                )
            semantic_owners[semantic_id.identifier] = relative
    reachable = {"README.md"}
    frontier = ["README.md"]
    while frontier:
        source = frontier.pop()
        for target in edges[source] - reachable:
            reachable.add(target)
            frontier.append(target)
    unreachable = sorted(documents - reachable)
    if unreachable:
        fail(
            "documents",
            "not reachable from README.md: " + ", ".join(unreachable),
        )


def validate_judgments(
    value: object,
    location: str,
    documents: set[str],
    evaluation: str,
    expected_status: str,
) -> None:
    if not isinstance(value, list):
        fail(location, "must be an array")
    paths: set[str] = set()
    owners = 0
    for index, raw in enumerate(value):
        item_location = f"{location}[{index}]"
        item = object_fields(
            raw,
            item_location,
            {"path", "grade", "origin"},
            {"hard_negative"},
        )
        path = safe_markdown_path(item["path"], f"{item_location}.path")
        if path not in documents:
            fail(f"{item_location}.path", "does not exist in documents")
        if path in paths:
            fail(f"{item_location}.path", "duplicates another judgment")
        paths.add(path)
        grade = integer_between(item["grade"], f"{item_location}.grade", 0, 3)
        origin = item["origin"]
        if origin not in {"direct", "graph", "either"}:
            fail(f"{item_location}.origin", "must be direct, graph, or either")
        hard_negative = item.get("hard_negative", False)
        if not isinstance(hard_negative, bool):
            fail(f"{item_location}.hard_negative", "must be boolean")
        if hard_negative and grade != 0:
            fail(f"{item_location}.hard_negative", "requires grade 0")
        if grade == 3:
            owners += 1
            if path == "README.md":
                fail(f"{item_location}.path", "README.md cannot be a slice owner")
            if evaluation == "ranking" and origin != "direct":
                fail(
                    f"{item_location}.origin",
                    "ranking owner must require a direct result",
                )
    if owners > 1:
        fail(location, "one slice may have at most one canonical owner")
    if evaluation == "ranking":
        if expected_status != "matched":
            fail(location, "ranking slices must expect matched")
        if owners != 1:
            fail(location, "ranking slices require exactly one grade-3 owner")


def validate_scenario(
    raw: object,
    location: str,
    documents: set[str],
) -> str:
    scenario = object_fields(
        raw,
        location,
        {"id", "tags", "request", "search", "slices"},
    )
    identifier = nonempty_string(scenario["id"], f"{location}.id")
    if not ID_RE.fullmatch(identifier):
        fail(f"{location}.id", "must be lowercase hyphen-case")
    tags = scenario["tags"]
    if (
        not isinstance(tags, list)
        or not tags
        or any(tag not in TAGS for tag in tags)
        or len(set(tags)) != len(tags)
    ):
        fail(f"{location}.tags", "must be unique supported tags")
    request = object_fields(
        scenario["request"], f"{location}.request", {"language", "text"}
    )
    request_language = nonempty_string(
        request["language"], f"{location}.request.language"
    )
    if not LANGUAGE_RE.fullmatch(request_language):
        fail(f"{location}.request.language", "must be a basic BCP-47 tag")
    nonempty_string(request["text"], f"{location}.request.text")
    search = object_fields(
        scenario["search"],
        f"{location}.search",
        {"limit", "graph_depth", "graph_limit"},
        {"max_output_bytes"},
    )
    integer_between(search["limit"], f"{location}.search.limit", 1, 50)
    integer_between(search["graph_depth"], f"{location}.search.graph_depth", 0, 2)
    integer_between(search["graph_limit"], f"{location}.search.graph_limit", 0, 50)
    if "max_output_bytes" in search:
        integer_between(
            search["max_output_bytes"],
            f"{location}.search.max_output_bytes",
            4096,
            10_000_000,
        )
    slices = scenario["slices"]
    if not isinstance(slices, list) or not 1 <= len(slices) <= 8:
        fail(f"{location}.slices", "must contain 1 to 8 slices")
    query_payload: list[dict[str, object]] = []
    slice_ids: set[str] = set()
    for index, raw_slice in enumerate(slices):
        slice_location = f"{location}.slices[{index}]"
        item = object_fields(
            raw_slice,
            slice_location,
            {"id", "must", "evaluation", "expected_status", "judgments"},
            {"should"},
        )
        slice_id = nonempty_string(item["id"], f"{slice_location}.id")
        if slice_id in slice_ids:
            fail(f"{slice_location}.id", "must be unique within the scenario")
        slice_ids.add(slice_id)
        evaluation = item["evaluation"]
        if evaluation not in {"ranking", "protocol"}:
            fail(f"{slice_location}.evaluation", "must be ranking or protocol")
        expected_status = item["expected_status"]
        if expected_status not in {"matched", "no_match"}:
            fail(
                f"{slice_location}.expected_status",
                "must be matched or no_match",
            )
        query_item = {"id": slice_id, "must": item["must"]}
        if "should" in item:
            query_item["should"] = item["should"]
        query_payload.append(query_item)
        validate_judgments(
            item["judgments"],
            f"{slice_location}.judgments",
            documents,
            str(evaluation),
            str(expected_status),
        )
    try:
        RANKING.parse_query_slices(json.dumps(query_payload, ensure_ascii=False))
    except RANKING.InvalidRankingQuery as error:
        fail(f"{location}.slices", str(error))
    return identifier


def validate_manifest(path: Path) -> dict[str, object]:
    manifest_path = path.resolve()
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        fail(str(path), f"cannot read manifest: {error}")
    manifest = object_fields(
        payload,
        "manifest",
        {"schema_version", "corpus", "documents", "scenarios"},
    )
    if manifest["schema_version"] != 1:
        fail("manifest.schema_version", "must equal 1")
    corpus = object_fields(
        manifest["corpus"],
        "corpus",
        {
            "id",
            "project_type",
            "documentation_language",
            "size_tier",
            "seed",
            "axes",
        },
    )
    corpus_id = nonempty_string(corpus["id"], "corpus.id")
    if not ID_RE.fullmatch(corpus_id):
        fail("corpus.id", "must be lowercase hyphen-case")
    if manifest_path.parent.name != corpus_id:
        fail("corpus.id", "must equal the corpus directory name")
    if corpus["project_type"] not in PROJECT_TYPES:
        fail("corpus.project_type", "unsupported project type")
    language = nonempty_string(
        corpus["documentation_language"], "corpus.documentation_language"
    )
    if not LANGUAGE_RE.fullmatch(language):
        fail("corpus.documentation_language", "must be a basic BCP-47 tag")
    size_tier = corpus["size_tier"]
    if size_tier not in SIZE_RANGES:
        fail("corpus.size_tier", "must be small, medium, or large")
    integer_between(corpus["seed"], "corpus.seed", 0, 2**63 - 1)
    axes = object_fields(
        corpus["axes"],
        "corpus.axes",
        {"boilerplate", "lexical_overlap", "ownership", "graph_density"},
    )
    if axes["boilerplate"] not in LEVELS:
        fail("corpus.axes.boilerplate", "must be low, medium, or high")
    if axes["lexical_overlap"] not in LEVELS:
        fail("corpus.axes.lexical_overlap", "must be low, medium, or high")
    if axes["ownership"] not in OWNERSHIP:
        fail("corpus.axes.ownership", "unsupported ownership mode")
    if axes["graph_density"] not in GRAPH_DENSITY:
        fail("corpus.axes.graph_density", "unsupported graph density")
    project = manifest_path.parent / "project"
    spine = project / "specspine"
    if not spine.is_dir():
        fail("project/specspine", "directory is missing")
    validate_bootstrap(project, language)
    documents = validate_inventory(manifest["documents"], spine, str(size_tier))
    validate_spine_graph(spine, documents)
    scenarios = manifest["scenarios"]
    if not isinstance(scenarios, list) or not scenarios:
        fail("scenarios", "must be a non-empty array")
    scenario_ids: set[str] = set()
    for index, scenario in enumerate(scenarios):
        identifier = validate_scenario(
            scenario, f"scenarios[{index}]", documents
        )
        if identifier in scenario_ids:
            fail(f"scenarios[{index}].id", "must be unique within the corpus")
        scenario_ids.add(identifier)
    return manifest


def manifest_path(value: str) -> Path:
    path = Path(value)
    return path / "manifest.json" if path.is_dir() else path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifests", nargs="+", type=manifest_path)
    args = parser.parse_args()
    failed = False
    for path in args.manifests:
        try:
            payload = validate_manifest(path)
        except CorpusValidationError as error:
            failed = True
            print(f"FAIL {path}: {error}", file=sys.stderr)
            continue
        corpus = payload["corpus"]
        assert isinstance(corpus, dict)
        scenarios = payload["scenarios"]
        assert isinstance(scenarios, list)
        print(f"OK {corpus['id']}: {len(scenarios)} scenarios")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
