#!/usr/bin/env python3
"""Render and verify the human-readable SpecSpine vocabulary reference."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
VOCABULARY_PATH = ROOT / "shared/references/vocabulary.json"
GLOSSARY_PATH = ROOT / "docs/reference/glossary.md"


def code_list(values: list[str]) -> str:
    return ", ".join(f"`{value}`" for value in values)


def render(vocabulary: dict[str, Any]) -> str:
    patterns = vocabulary["identifier_patterns"]
    reserved = vocabulary["reserved_paths"]
    lines = [
        "# SpecSpine v3 glossary",
        "",
        "This file is generated from the canonical",
        "[`shared/references/vocabulary.json`](../../shared/references/vocabulary.json).",
        "The JSON vocabulary owns tokens, identifier families, and enumerated values;",
        "the format and semantics references own their normative usage.",
        "",
        "## Identifiers and reserved paths",
        "",
        "| Name | Syntax or value | Meaning |",
        "|---|---|---|",
        f"| Document ID | `{patterns['document']}` | Stable globally unique document identity. |",
        f"| Semantic ID | `{patterns['semantic'].replace('|', '&#124;')}` | Stable globally unique addressable statement identity. |",
        f"| Extension token | `{vocabulary['extension_pattern']}` | Project-specific document kind or relation. |",
        f"| Root index | `{reserved['index']}` | Deterministic physical navigation entry point. |",
        f"| Manifest | `{reserved['manifest']}` | Completeness, blockers, inspection, freedom, and asset registry. |",
        "",
        "## Semantic identifier families",
        "",
        "| Prefix | Canonical section | Meaning | Authority |",
        "|---|---|---|---|",
    ]
    for prefix, definition in vocabulary["semantic_prefixes"].items():
        authority = "normative" if definition["normative"] else "non-normative"
        lines.append(
            f"| `{prefix}` | `{definition['section']}` | {definition['meaning']} | {authority} |"
        )
    lines.extend(["", "## Document kinds", ""])
    for token, meaning in vocabulary["document_kinds"].items():
        lines.append(f"- `{token}` — {meaning}")
    lines.extend([
        "",
        "Project-specific kinds use `x-*`. Statement kinds are not document kinds.",
        "",
        "## Manifest vocabulary",
        "",
    ])
    for title, key in (
        ("Facets", "facets"),
        ("Facet values", "facet_values"),
        ("Inspection modes", "inspection_modes"),
        ("Inspection facet values", "inspection_facet_values"),
        ("Implementation freedom", "implementation_freedom"),
        ("Computed statuses", "computed_statuses"),
        ("Asset roles", "asset_roles"),
    ):
        lines.extend([f"### {title}", "", "| Token | Meaning |", "|---|---|"])
        for token, meaning in vocabulary[key].items():
            lines.append(f"| `{token}` | {meaning} |")
        lines.append("")
    lines.extend(["", "## Core relations", ""])
    for token, meaning in vocabulary["relations"].items():
        lines.append(f"- `{token}` — {meaning}")
    lines.extend([
        "",
        "Project-specific relations use `x-*`.",
        "",
        "## Canonical section keys",
        "",
    ])
    for key, rendered in vocabulary["headings"].items():
        lines.append(f"- `{key}` — default rendering: “{rendered}”.")
    lines.extend([
        "",
        "Presentation profiles may translate rendered headings but never these keys.",
        "",
        "## Reserved markers",
        "",
        "| Purpose | Marker |",
        "|---|---|",
    ])
    labels = {
        "semantic-ids": "Semantic definitions",
        "evidence-baseline": "Evidence baseline",
        "connection": "Project instruction connection",
        "readme": "Optional project README link",
    }
    for key, marker in vocabulary["markers"].items():
        lines.append(f"| {labels[key]} | `{marker}` |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    vocabulary = json.loads(VOCABULARY_PATH.read_text(encoding="utf-8"))
    expected = render(vocabulary)
    if args.write:
        GLOSSARY_PATH.write_text(expected, encoding="utf-8")
        return 0
    if not GLOSSARY_PATH.is_file() or GLOSSARY_PATH.read_text(encoding="utf-8") != expected:
        print(
            "docs/reference/glossary.md is stale; run "
            "python3 shared/scripts/render_vocabulary.py --write",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
