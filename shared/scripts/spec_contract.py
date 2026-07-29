#!/usr/bin/env python3
"""Canonical machine vocabulary and presentation profile for SpecSpine v3."""

from __future__ import annotations

from typing import Any

FORMAT_MAJOR = 3
MANIFEST_NAME = "specspine.json"
INDEX_NAME = "_INDEX.md"

DOCUMENT_ID_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
SEMANTIC_ID_PATTERN = (
    r"^(DEC|CON|REQ|GUA|INV|QLT|VER|OBS|INF|OQ)-"
    r"[a-z0-9]+(?:-[a-z0-9]+)*$"
)

CORE_KINDS = frozenset({
    "index", "system", "subsystem", "component", "capability", "behavior",
    "interface", "data", "policy", "deployment", "concept",
})
CORE_RELATIONS = frozenset({
    "contains", "decomposes-into", "performs", "depends-on", "exposes",
    "consumes", "publishes", "reads-from", "writes-to", "owns-data",
    "constrained-by", "implemented-by", "has-evidence", "superseded-by",
    "related-to", "refines", "satisfies", "verified-by", "specified-by",
    "compatible-with", "migrates-from",
})
FACET_NAMES = (
    "architecture", "behavior", "interfaces", "data", "failure", "quality",
    "verification",
)
FACET_VALUES = frozenset({"complete", "partial", "missing", "not-applicable"})
INSPECTION_MODES = frozenset({"survey", "deepen", "refresh", "drift", "exhaustive"})
INSPECTION_FACET_VALUES = frozenset({"checked", "not-checked"})
ASSET_ROLES = frozenset({
    "interface-contract", "data-schema", "execution-contract", "scenario",
    "fixture", "verification",
})
KIND_REQUIRED_FACETS = {
    "system": {"architecture", "behavior", "failure", "verification"},
    "subsystem": {"architecture", "behavior", "failure", "verification"},
    "component": {"architecture", "behavior", "failure", "verification"},
    "capability": {"architecture", "behavior", "failure", "verification"},
    "behavior": {"architecture", "behavior", "failure", "verification"},
    "interface": {"architecture", "interfaces", "failure", "verification"},
    "data": {"architecture", "data", "failure", "verification"},
    "policy": {"architecture", "behavior", "verification"},
    "deployment": {"architecture", "failure", "quality", "verification"},
    "concept": {"architecture"},
}
NORMATIVE_PREFIXES = ("DEC-", "CON-", "REQ-", "GUA-", "INV-", "QLT-", "VER-")

# Stable keys are machine identity. Values are the default rendered headings.
DEFAULT_HEADINGS = {
    "responsibility": "Responsibility",
    "boundaries": "Boundaries",
    "behavior": "Behavior",
    "interfaces": "Interfaces",
    "information-model": "Information model",
    "data-ownership": "Data ownership",
    "lifecycle-and-invariants": "Lifecycle and invariants",
    "failure-behavior": "Failure behavior",
    "edge-cases": "Edge cases",
    "configuration-contract": "Configuration contract",
    "compatibility": "Compatibility",
    "relationships": "Relationships",
    "requirements": "Requirements",
    "guarantees": "Guarantees",
    "invariants": "Invariants",
    "quality-constraints": "Quality constraints",
    "verification": "Verification",
    "decisions": "Decisions",
    "constraints": "Constraints",
    "known-divergences": "Known divergences",
    "observed": "Observed",
    "inferred": "Inferred",
    "open-questions": "Open questions",
    "implementation": "Implementation",
    "risks": "Risks",
    "rationale-and-trade-offs": "Rationale and trade-offs",
    "terminology": "Terminology",
}
DEFAULT_SECTION_ORDER = tuple(DEFAULT_HEADINGS)
DEFAULT_INDEX_TEXT = {
    "root-title": "{project} architecture",
    "purpose": (
        "SpecSpine is the project's long-lived, linked specification and "
        "architectural memory used to reconstruct contract-equivalent implementations."
    ),
    "scope": (
        "This directory contains the project's long-lived architectural intent and "
        "architecture-relevant repository observations."
    ),
    "guide-heading": "How to use this Spine",
    "guide": (
        "- Start with `Contents`, then follow links to the canonical owner of the "
        "area relevant to the task. Preserve stable document IDs when files move.\n"
        "- SpecSpine owns accepted durable intent; source code owns the current "
        "implementation. Neither alone proves that implementation conforms to intent.\n"
        "- `specspine.json` records areas, completeness, inspection coverage, blockers, "
        "and registered contract or verification assets.\n"
        "- `DEC`, `CON`, `REQ`, `GUA`, `INV`, `QLT`, and `VER` identify accepted "
        "claims. `OBS` records confirmed implementation evidence, `INF` an unconfirmed "
        "inference, and `OQ` an unresolved question.\n"
        "- `Known divergences` links accepted intent to conflicting observations. Do "
        "not silently turn code, `OBS`, or `INF` into accepted intent.\n"
        "- Update the canonical owner instead of copying a claim into another document; "
        "preserve unresolved conflicts and blocking questions explicitly."
    ),
    "contents-heading": "Contents",
    "nested-heading": "Nested SpecSpines",
    "empty": "No indexed entries.",
}
SECTION_PREFIX_KEYS = {
    "decisions": "DEC",
    "constraints": "CON",
    "requirements": "REQ",
    "guarantees": "GUA",
    "invariants": "INV",
    "quality-constraints": "QLT",
    "verification": "VER",
    "observed": "OBS",
    "inferred": "INF",
    "open-questions": "OQ",
}


class PresentationError(ValueError):
    pass


def presentation(manifest: dict[str, Any] | None) -> dict[str, Any]:
    """Return a validated, complete presentation profile."""
    raw = (manifest or {}).get("presentation", {})
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise PresentationError("presentation must be an object")
    unknown = set(raw) - {
        "profile", "language", "headings", "section_order", "index",
    }
    if unknown:
        raise PresentationError(
            "unknown presentation fields: " + ", ".join(sorted(unknown))
        )
    if raw.get("profile", 1) != 1:
        raise PresentationError("presentation.profile must be 1")
    language = raw.get("language", "en")
    if not isinstance(language, str) or not language.strip():
        raise PresentationError("presentation.language must be a nonempty string")
    overrides = raw.get("headings", {})
    if not isinstance(overrides, dict):
        raise PresentationError("presentation.headings must be an object")
    unknown_headings = set(overrides) - set(DEFAULT_HEADINGS)
    if unknown_headings:
        raise PresentationError(
            "unknown presentation heading keys: "
            + ", ".join(sorted(unknown_headings))
        )
    headings = dict(DEFAULT_HEADINGS)
    for key, value in overrides.items():
        if not isinstance(value, str) or not value.strip():
            raise PresentationError(f"presentation heading {key!r} must be nonempty")
        headings[key] = value.strip()
    normalized = [value.casefold() for value in headings.values()]
    if len(normalized) != len(set(normalized)):
        raise PresentationError("presentation headings must be unique")
    order = raw.get("section_order", list(DEFAULT_SECTION_ORDER))
    if (
        not isinstance(order, list)
        or any(not isinstance(item, str) for item in order)
        or len(order) != len(set(order))
        or set(order) != set(DEFAULT_HEADINGS)
    ):
        raise PresentationError(
            "presentation.section_order must contain every canonical heading key once"
        )
    index_overrides = raw.get("index", {})
    if not isinstance(index_overrides, dict):
        raise PresentationError("presentation.index must be an object")
    unknown_index = set(index_overrides) - set(DEFAULT_INDEX_TEXT)
    if unknown_index:
        raise PresentationError(
            "unknown presentation index keys: " + ", ".join(sorted(unknown_index))
        )
    index = dict(DEFAULT_INDEX_TEXT)
    for key, value in index_overrides.items():
        if not isinstance(value, str) or not value.strip():
            raise PresentationError(f"presentation index {key!r} must be nonempty")
        index[key] = value.strip()
    if index["root-title"].count("{project}") != 1:
        raise PresentationError(
            "presentation index 'root-title' must contain {project} exactly once"
        )
    return {
        "profile": 1,
        "language": language.strip(),
        "headings": headings,
        "section_order": tuple(order),
        "index": index,
    }


def heading_key_map(manifest: dict[str, Any] | None) -> dict[str, str]:
    profile = presentation(manifest)
    return {
        rendered.casefold(): key
        for key, rendered in profile["headings"].items()
    }


def canonical_heading(title: str, manifest: dict[str, Any] | None) -> str | None:
    try:
        mapping = heading_key_map(manifest)
    except PresentationError:
        mapping = {
            rendered.casefold(): key
            for key, rendered in DEFAULT_HEADINGS.items()
        }
    return mapping.get(title.strip().casefold())
