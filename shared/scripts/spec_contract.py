#!/usr/bin/env python3
"""Canonical machine vocabulary and presentation profile for SpecSpine v3."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

VOCABULARY_PATH = Path(__file__).resolve().parent.parent / "references/vocabulary.json"
VOCABULARY = json.loads(VOCABULARY_PATH.read_text(encoding="utf-8"))

FORMAT_MAJOR = VOCABULARY["format_major"]
MANIFEST_NAME = VOCABULARY["reserved_paths"]["manifest"]
INDEX_NAME = VOCABULARY["reserved_paths"]["index"]
README_NAME = VOCABULARY["reserved_paths"]["readme"]
DOCUMENT_ID_PATTERN = VOCABULARY["identifier_patterns"]["document"]
SEMANTIC_PREFIXES = tuple(VOCABULARY["semantic_prefixes"])
SEMANTIC_PREFIX_PATTERN = "(?:" + "|".join(map(re.escape, SEMANTIC_PREFIXES)) + ")"
DOCUMENT_ID_BODY_PATTERN = DOCUMENT_ID_PATTERN.removeprefix("^").removesuffix("$")
CORE_KINDS = frozenset(VOCABULARY["document_kinds"])
CORE_RELATIONS = frozenset(VOCABULARY["relations"])
FACET_NAMES = tuple(VOCABULARY["facets"])
FACET_VALUES = frozenset(VOCABULARY["facet_values"])
INSPECTION_MODES = frozenset(VOCABULARY["inspection_modes"])
INSPECTION_FACET_VALUES = frozenset(VOCABULARY["inspection_facet_values"])
ASSET_ROLES = frozenset(VOCABULARY["asset_roles"])
KIND_REQUIRED_FACETS = {
    kind: set(facets)
    for kind, facets in VOCABULARY["kind_required_facets"].items()
}
NORMATIVE_SEMANTIC_PREFIXES = tuple(
    prefix
    for prefix, definition in VOCABULARY["semantic_prefixes"].items()
    if definition["normative"]
)
NORMATIVE_PREFIXES = tuple(f"{prefix}-" for prefix in NORMATIVE_SEMANTIC_PREFIXES)
SEMANTIC_PREFIX_SECTIONS = {
    prefix: definition["section"]
    for prefix, definition in VOCABULARY["semantic_prefixes"].items()
}
FACET_SUPPORT_PREFIXES = {
    facet: {
        f"{prefix}-"
        for prefix, definition in VOCABULARY["semantic_prefixes"].items()
        if facet in definition.get("supports_facets", ())
    }
    for facet in FACET_NAMES
}


def semantic_id_body_pattern(prefixes: tuple[str, ...]) -> str:
    """Return an unanchored semantic-ID regex for a canonical prefix subset."""
    unknown = set(prefixes) - set(SEMANTIC_PREFIXES)
    if unknown:
        raise ValueError(f"unknown semantic prefixes: {sorted(unknown)}")
    if not prefixes:
        raise ValueError("semantic prefix subset must not be empty")
    prefix_pattern = "(?:" + "|".join(map(re.escape, prefixes)) + ")"
    return f"{prefix_pattern}-{DOCUMENT_ID_BODY_PATTERN}"


def semantic_id_pattern(prefixes: tuple[str, ...]) -> str:
    """Return an anchored semantic-ID regex for a canonical prefix subset."""
    return f"^{semantic_id_body_pattern(prefixes)}$"


SEMANTIC_ID_PATTERN = semantic_id_pattern(SEMANTIC_PREFIXES)

# Stable keys are machine identity. Values are the default rendered headings.
DEFAULT_HEADINGS = dict(VOCABULARY["headings"])
DEFAULT_SECTION_ORDER = tuple(DEFAULT_HEADINGS)


def _term_lines(values: dict[str, str]) -> str:
    return "\n".join(f"- `{token}` — {meaning}" for token, meaning in values.items())


def compact_glossary() -> str:
    """Render the complete portable vocabulary for a root index."""
    semantic = {
        prefix: definition["meaning"]
        for prefix, definition in VOCABULARY["semantic_prefixes"].items()
    }
    markers = {
        token: f"Reserved marker syntax: `{marker}`."
        for token, marker in VOCABULARY["markers"].items()
    }
    groups = [
        (
            "Identifiers and extensions",
            {
                "document ID": (
                    f"Stable document identity matching "
                    f"`{VOCABULARY['identifier_patterns']['document']}`."
                ),
                "semantic ID": (
                    f"Addressable statement identity matching "
                    f"`{SEMANTIC_ID_PATTERN}`."
                ),
                "x-*": "Project-specific document kind or relation.",
            },
        ),
        ("Semantic ID prefixes", semantic),
        ("Document kinds", VOCABULARY["document_kinds"]),
        ("Canonical section keys", VOCABULARY["heading_meanings"]),
        ("Relations", VOCABULARY["relations"]),
        ("Facets", VOCABULARY["facets"]),
        ("Facet values", VOCABULARY["facet_values"]),
        ("Inspection modes", VOCABULARY["inspection_modes"]),
        ("Inspection facet values", VOCABULARY["inspection_facet_values"]),
        ("Implementation freedom", VOCABULARY["implementation_freedom"]),
        ("Computed statuses", VOCABULARY["computed_statuses"]),
        ("Asset roles", VOCABULARY["asset_roles"]),
        ("Manifest fields", VOCABULARY["manifest_fields"]),
        ("Markdown fields and normative keywords", VOCABULARY["markdown_keywords"]),
        ("Reserved markers", markers),
        (
            "Reserved paths",
            {
                VOCABULARY["reserved_paths"]["index"]: "Deterministic physical navigation.",
                VOCABULARY["reserved_paths"]["manifest"]: "Manifest and completeness registry.",
                VOCABULARY["reserved_paths"]["readme"]: "Portable SpecSpine introduction, reading guide, and vocabulary.",
            },
        ),
    ]
    return "\n\n".join(
        f"### {heading}\n\n{_term_lines(values)}"
        for heading, values in groups
    )


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
        "- `Known divergences` links accepted intent to conflicting observations. Do "
        "not silently turn code, `OBS`, or `INF` into accepted intent.\n"
        "- Update the canonical owner instead of copying a claim into another document; "
        "preserve unresolved conflicts and blocking questions explicitly."
    ),
    "glossary-heading": "SpecSpine glossary",
    "glossary": compact_glossary(),
    "contents-heading": "Contents",
    "nested-heading": "Nested SpecSpines",
    "empty": "No indexed entries.",
}


def render_root_readme(project: str, index_text: dict[str, str]) -> str:
    """Render portable SpecSpine information outside the deterministic index."""
    return "\n".join(
        [
            f"# {index_text['root-title'].format(project=project)}",
            "",
            index_text["purpose"],
            "",
            index_text["scope"],
            "",
            f"## {index_text['guide-heading']}",
            "",
            index_text["guide"],
            "",
            f"## {index_text['glossary-heading']}",
            "",
            index_text["glossary"],
            "",
        ]
    )
SECTION_PREFIX_KEYS = {
    definition["section"]: prefix
    for prefix, definition in VOCABULARY["semantic_prefixes"].items()
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
