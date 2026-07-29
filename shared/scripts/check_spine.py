#!/usr/bin/env python3
"""Check deterministic integrity rules for a SpecSpine v3 bundle."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from spec_contract import (
    ASSET_ROLES,
    CORE_KINDS,
    CORE_RELATIONS,
    DEFAULT_HEADINGS,
    DOCUMENT_ID_PATTERN,
    FACET_NAMES,
    FACET_VALUES,
    FORMAT_MAJOR,
    INDEX_NAME,
    INSPECTION_FACET_VALUES,
    INSPECTION_MODES,
    KIND_REQUIRED_FACETS,
    MANIFEST_NAME,
    NORMATIVE_PREFIXES,
    PresentationError,
    SEMANTIC_ID_PATTERN,
    SEMANTIC_PREFIX_PATTERN,
    SECTION_PREFIX_KEYS,
    canonical_heading,
    presentation,
)

ID_RE = re.compile(SEMANTIC_ID_PATTERN)
DOCUMENT_ID_RE = re.compile(DOCUMENT_ID_PATTERN)
IDENTITY_RE = re.compile(
    r"^\*\*ID:\*\*\s+`([^`]+)`\s+·\s+\*\*Kind:\*\*\s+`([^`]+)`\s*$"
)
DEFINITION_RE = re.compile(r"^ {0,3}[-+*]\s+\*\*([^*\n]+)\*\*\s+—\s+")
SEMANTIC_BULLET_RE = re.compile(
    rf"^ {{0,3}}[-+*]\s+\*\*({SEMANTIC_PREFIX_PATTERN}"
    r"-[a-z0-9]+(?:-[a-z0-9]+)*)\*\*"
)
LEGACY_SEMANTIC_DEFINITION_RE = re.compile(
    rf"^\*\*ID:\*\*\s+`({SEMANTIC_PREFIX_PATTERN}-[^`]+)`"
    r"\s+·\s+\*\*Status:\*\*"
)
FENCE_RE = re.compile(r"^ {0,3}(?:>\s*)?(`{3,}|~{3,})")
ATX_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*)|[ \t]*)$")
REFERENCE_DEFINITION_RE = re.compile(
    r'^ {0,3}\[([^\]]+)\]:\s*(?:<([^>]+)>|(\S+?))(?:\s+(?:"[^"]*"|\'[^\']*\'|\([^)]*\)))?\s*$'
)
ID_REGION_BEGIN = "<!-- specspine:semantic-ids:begin -->"
ID_REGION_END = "<!-- specspine:semantic-ids:end -->"
EVIDENCE_BASELINE_RE = re.compile(
    r"<!--\s*specspine:evidence-baseline\s+"
    r"source=[^;>\s]+;\s*inspected=\d{4}-\d{2}-\d{2}\s*-->"
)
MARKDOWN_COMPLETENESS_SECTIONS = {
    "Coverage",
    "SpecSpine readiness",
    "Reconstruction status",
    "Facet status",
}
RELATION_HEADER = ("Relation", "Target", "Meaning")
DIVERGENCE_HEADER = ("Intended", "Observed", "Consequence")
MANIFEST_KEYS = {
    "specspine", "project", "implementation_freedom", "areas", "assets",
    "presentation",
}
REQUIRED_MANIFEST_KEYS = MANIFEST_KEYS - {"presentation"}
AREA_REQUIRED_KEYS = {"owner", "facets", "blockers"}
AREA_KEYS = AREA_REQUIRED_KEYS | {"inspection"}
FACET_NAME_SET = set(FACET_NAMES)
ASSET_KEYS = {"path", "owner", "role", "format", "normative", "verifies"}
FACET_SUPPORT_SECTIONS = {
    "behavior": {
        "behavior", "lifecycle-and-invariants", "requirements", "guarantees",
        "invariants", "decisions", "constraints",
    },
    "interfaces": {
        "interfaces", "configuration-contract", "compatibility",
    },
    "data": {
        "information-model", "data-ownership", "lifecycle-and-invariants",
    },
    "failure": {"failure-behavior", "edge-cases"},
    "quality": {"quality-constraints"},
}


def is_spine_root(path: Path) -> bool:
    return (path / INDEX_NAME).is_file() and (path / MANIFEST_NAME).is_file()


def owned_files(root: Path) -> list[Path]:
    """Return files owned by root without descending into nested Spines."""
    result: list[Path] = []
    for current, directories, files in os.walk(root):
        directory = Path(current)
        if directory != root and is_spine_root(directory):
            directories[:] = []
            continue
        result.extend(
            directory / name
            for name in files
            if not (directory / name).is_symlink()
        )
    return sorted(result)


def owned_directories(root: Path) -> list[Path]:
    result: list[Path] = []
    for current, directories, _ in os.walk(root):
        directory = Path(current)
        if directory != root and is_spine_root(directory):
            directories[:] = []
            continue
        result.append(directory)
    return sorted(result)


def nested_spine_roots(root: Path) -> list[Path]:
    result: list[Path] = []
    for current, directories, _ in os.walk(root):
        directory = Path(current)
        if directory != root and is_spine_root(directory):
            result.append(directory)
            directories[:] = []
    return sorted(result)
FACET_SUPPORT_PREFIXES = {
    "behavior": {"DEC-", "CON-", "REQ-", "GUA-", "INV-"},
    "quality": {"QLT-"},
}
FACET_SUPPORT_ASSET_ROLES = {
    "behavior": {"scenario", "fixture"},
    "interfaces": {"interface-contract"},
    "data": {"data-schema"},
    "failure": {"scenario", "fixture"},
}
FACET_SUPPORT_RELATIONS = {
    "interfaces": {
        "exposes", "consumes", "publishes", "specified-by",
        "compatible-with",
    },
    "data": {"reads-from", "writes-to", "owns-data"},
}


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    line: int | None
    message: str


@dataclass(frozen=True)
class MarkdownLink:
    label: str
    target: str | None
    reference: str | None


def add(
    findings: list[Finding],
    severity: str,
    code: str,
    path: Path,
    root: Path,
    message: str,
    line: int | None = None,
) -> None:
    try:
        relative = str(path.relative_to(root))
    except ValueError:
        relative = str(path)
    findings.append(Finding(severity, code, relative or ".", line, message))


def within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def normalize_reference(label: str) -> str:
    return " ".join(label.split()).casefold()


def unescape_markdown(value: str) -> str:
    return re.sub(r"\\([!\"#$%&'()*+,./:;<=>?@\[\\\]^_`{|}~-])", r"\1", value)


def destination_from_parentheses(value: str) -> str:
    value = value.strip()
    if value.startswith("<"):
        end = value.find(">", 1)
        return value[1:end] if end >= 0 else value[1:]

    escaped = False
    depth = 0
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "(":
            depth += 1
        elif char == ")" and depth:
            depth -= 1
        elif char.isspace() and depth == 0:
            return value[:index]
    return value


def matching_bracket(text: str, start: int) -> int | None:
    depth = 0
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return index
    return None


def matching_parenthesis(text: str, start: int) -> int | None:
    depth = 0
    escaped = False
    angle = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "<" and depth == 1:
            angle = True
        elif char == ">" and angle:
            angle = False
        elif not angle and char == "(":
            depth += 1
        elif not angle and char == ")":
            depth -= 1
            if depth == 0:
                return index
    return None


def markdown_links(line: str) -> list[MarkdownLink]:
    links: list[MarkdownLink] = []
    cursor = 0
    while cursor < len(line):
        start = line.find("[", cursor)
        if start < 0:
            break
        image = start > 0 and line[start - 1] == "!" and (start < 2 or line[start - 2] != "\\")
        end = matching_bracket(line, start)
        if end is None:
            break
        label = unescape_markdown(line[start + 1 : end])
        after = end + 1
        link: MarkdownLink | None = None
        if after < len(line) and line[after] == "(":
            target_end = matching_parenthesis(line, after)
            if target_end is not None:
                target = destination_from_parentheses(line[after + 1 : target_end])
                link = MarkdownLink(label, unescape_markdown(target), None)
                cursor = target_end + 1
        elif after < len(line) and line[after] == "[":
            reference_end = matching_bracket(line, after)
            if reference_end is not None:
                reference = line[after + 1 : reference_end] or label
                link = MarkdownLink(label, None, normalize_reference(reference))
                cursor = reference_end + 1
        else:
            link = MarkdownLink(label, None, normalize_reference(label))
            cursor = after
        if link is not None and not image:
            links.append(link)
        if cursor <= start:
            cursor = end + 1
    return links


def mask_code_spans(line: str, delimiter: int) -> tuple[str, int]:
    output: list[str] = []
    cursor = 0
    while cursor < len(line):
        if line[cursor] != "`":
            output.append(" " if delimiter else line[cursor])
            cursor += 1
            continue
        end = cursor
        while end < len(line) and line[end] == "`":
            end += 1
        run = end - cursor
        output.extend(" " * run)
        if delimiter == 0:
            delimiter = run
        elif run == delimiter:
            delimiter = 0
        cursor = end
    return "".join(output), delimiter


def strip_comments(line: str, in_comment: bool) -> tuple[str, bool]:
    visible = ""
    rest = line
    while rest:
        if in_comment:
            end = rest.find("-->")
            if end < 0:
                return visible, True
            rest = rest[end + 3 :]
            in_comment = False
        else:
            start = rest.find("<!--")
            if start < 0:
                visible += rest
                break
            visible += rest[:start]
            rest = rest[start + 4 :]
            in_comment = True
    return visible, in_comment


def local_target(source: Path, raw_target: str, root: Path) -> tuple[str, Path | None]:
    raw_target = raw_target.strip()
    if not raw_target or raw_target.startswith("#"):
        return "remote", None
    split = urlsplit(raw_target)
    if split.scheme or split.netloc or raw_target.startswith("//"):
        return "remote", None
    decoded = unquote(split.path)
    if not decoded:
        return "remote", None

    lexical = Path(decoded)
    if not lexical.is_absolute():
        lexical = source.parent / lexical
    lexical = Path(re.sub(r"/+$", "", str(lexical)))
    lexical_absolute = Path(re.sub(r"/+$", "", str(lexical.absolute())))
    if not within(lexical_absolute, root):
        return "outside", lexical_absolute
    resolved = lexical.resolve(strict=False)
    if not within(resolved, root):
        return "outside", resolved
    return "inside", resolved


@dataclass
class _Node:
    path: Path
    lines: list[str]
    title: str = ""
    document_id: str = ""
    kind: str = ""
    identity_line: int | None = None
    summary: str = ""
    sections: dict[str, tuple[int, list[str]]] | None = None
    statements: dict[str, tuple[str, int]] | None = None
    links: list[tuple[int, MarkdownLink]] | None = None
    active_lines: set[int] | None = None


def _table_rows(lines: list[str], start: int) -> tuple[tuple[str, ...], list[tuple[int, tuple[str, ...]]]]:
    """Return a simple GFM table beginning after a level-two heading."""
    visible: list[tuple[int, str]] = []
    for index in range(start, len(lines)):
        value = lines[index].strip()
        if value.startswith("## "):
            break
        if value.startswith("|") and value.endswith("|"):
            visible.append((index + 1, value))
        elif visible and value:
            break
    if len(visible) < 2:
        return (), []

    def cells(value: str) -> tuple[str, ...]:
        return tuple(part.strip() for part in value.strip("|").split("|"))

    header = cells(visible[0][1])
    separator = cells(visible[1][1])
    if len(header) != len(separator) or not all(re.fullmatch(r":?-{3,}:?", part) for part in separator):
        return header, []
    return header, [(number, cells(value)) for number, value in visible[2:]]


def _parse_node(
    path: Path,
    root: Path,
    findings: list[Finding],
    manifest: dict[str, object] | None = None,
) -> _Node:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        add(findings, "error", "READ_ERROR", path, root, str(error))
        return _Node(path, [])
    node = _Node(path, lines, sections={}, statements={}, links=[])
    headings: list[tuple[int, int, str]] = []
    active_lines: set[int] = set()
    in_fence = False
    fence_char = ""
    fence_length = 0
    for number, line in enumerate(lines, 1):
        fence = FENCE_RE.match(line)
        if in_fence:
            if fence and fence.group(1)[0] == fence_char and len(fence.group(1)) >= fence_length:
                in_fence = False
            continue
        if fence:
            in_fence = True
            fence_char, fence_length = fence.group(1)[0], len(fence.group(1))
            continue
        active_lines.add(number)
        heading = ATX_HEADING_RE.match(line)
        if heading:
            title = re.sub(r"[ \t]+#+[ \t]*$", "", heading.group(2) or "").strip()
            headings.append((number, len(heading.group(1)), title))
        identity = IDENTITY_RE.fullmatch(line.strip())
        if identity:
            if node.identity_line is not None:
                add(findings, "error", "MULTIPLE_IDENTITY", path, root, "document has multiple identity lines", number)
            else:
                node.document_id, node.kind, node.identity_line = identity.group(1), identity.group(2), number
    node.active_lines = active_lines

    h1 = [(number, title) for number, level, title in headings if level == 1]
    if not h1:
        add(findings, "error", "MISSING_H1", path, root, "document has no level-one heading", 1)
    elif len(h1) > 1:
        add(findings, "error", "MULTIPLE_H1", path, root, "document must have exactly one level-one heading", h1[1][0])
    else:
        node.title = h1[0][1]
    if node.identity_line is None:
        add(findings, "error", "MISSING_DOCUMENT_ID", path, root, "missing canonical ID/Kind identity line")
    else:
        if not DOCUMENT_ID_RE.fullmatch(node.document_id):
            add(findings, "error", "MALFORMED_DOCUMENT_ID", path, root, f"invalid document ID: {node.document_id}", node.identity_line)
        if node.kind not in CORE_KINDS and not re.fullmatch(r"x-[a-z0-9]+(?:-[a-z0-9]+)*", node.kind):
            add(findings, "warning", "UNKNOWN_KIND", path, root, f"unknown non-extension kind: {node.kind}", node.identity_line)

    for index, (number, level, title) in enumerate(headings):
        if level != 2:
            continue
        end = next((candidate - 1 for candidate, candidate_level, _ in headings[index + 1:] if candidate_level <= 2), len(lines))
        body = lines[number:end]
        section_key = canonical_heading(title, manifest) or title
        node.sections[section_key] = (number, body)
        if not any(line.strip() for line in body):
            add(
                findings,
                "warning",
                "EMPTY_SECTION",
                path,
                root,
                f"section '{title}' is empty",
                number,
            )

    if node.identity_line is not None:
        cursor = node.identity_line
        while cursor < len(lines) and (
            not lines[cursor].strip()
            or lines[cursor].startswith("**Aliases:**")
            or lines[cursor].strip().startswith("<!--")
        ):
            cursor += 1
        paragraph: list[str] = []
        while cursor < len(lines) and lines[cursor].strip() and not lines[cursor].lstrip().startswith("#"):
            paragraph.append(lines[cursor].strip())
            cursor += 1
        node.summary = " ".join(paragraph)
    if not node.summary and node.kind != "index":
        add(findings, "error", "MISSING_SUMMARY", path, root, "missing summary immediately after identity and aliases")
    if node.kind != "index":
        responsibility = node.sections.get("responsibility")
        if responsibility is None:
            add(findings, "error", "MISSING_RESPONSIBILITY", path, root, "non-index node has no Responsibility section")
        elif not any(line.strip() for line in responsibility[1]):
            add(findings, "error", "EMPTY_RESPONSIBILITY", path, root, "Responsibility section is empty", responsibility[0])

    region_depth = 0
    regions = 0
    section = ""
    reference_definitions: dict[str, str] = {}
    for number, line in enumerate(lines, 1):
        if number not in active_lines:
            continue
        stripped = line.strip()
        legacy_definition = LEGACY_SEMANTIC_DEFINITION_RE.match(line)
        if legacy_definition:
            add(
                findings,
                "error",
                "LEGACY_SEMANTIC_DEFINITION",
                path,
                root,
                "v3 semantic definitions must be bold bullets with an em dash",
                number,
            )
        if stripped == ID_REGION_BEGIN:
            regions += 1
            region_depth += 1
            continue
        if stripped == ID_REGION_END:
            if not region_depth:
                add(findings, "error", "ID_REGION_END", path, root, "semantic-ID region ends without begin", number)
            else:
                region_depth -= 1
            continue
        heading = ATX_HEADING_RE.match(line)
        if heading and len(heading.group(1)) == 2:
            rendered = re.sub(
                r"[ \t]+#+[ \t]*$", "", heading.group(2) or ""
            ).strip()
            section = canonical_heading(rendered, manifest) or rendered
        definition = DEFINITION_RE.match(line)
        semantic_bullet = SEMANTIC_BULLET_RE.match(line)
        if semantic_bullet and not definition:
            add(
                findings,
                "error",
                "MALFORMED_ID_DEFINITION",
                path,
                root,
                "semantic definition requires an em dash and text on its first line",
                number,
            )
        if definition:
            identifier = definition.group(1).strip()
            if not ID_RE.fullmatch(identifier):
                add(findings, "error", "INVALID_ID", path, root, f"invalid semantic ID: {identifier}", number)
            elif identifier in node.statements:
                add(findings, "error", "DUPLICATE_ID", path, root, f"duplicate semantic ID: {identifier}", number)
            else:
                expected = SECTION_PREFIX_KEYS.get(section)
                if identifier.startswith("OBS-") and section != "observed":
                    add(
                        findings,
                        "error",
                        "ID_SECTION",
                        path,
                        root,
                        f"{identifier} belongs only under observed",
                        number,
                    )
                elif expected and not identifier.startswith(expected + "-"):
                    add(findings, "error", "ID_SECTION", path, root, f"{identifier} does not belong under {section}", number)
                node.statements[identifier] = (section, number)
            if not region_depth:
                add(findings, "warning", "ID_OUTSIDE_REGION", path, root, f"semantic ID is outside marker region: {identifier}", number)
        reference = REFERENCE_DEFINITION_RE.match(line)
        if reference:
            reference_definitions[normalize_reference(reference.group(1))] = unescape_markdown(reference.group(2) or reference.group(3))
    if region_depth:
        add(findings, "error", "ID_REGION_UNCLOSED", path, root, "semantic-ID region is not closed")
    if regions > 1:
        add(findings, "error", "MULTIPLE_ID_REGIONS", path, root, "use at most one semantic-ID region")
    in_comment = False
    code_delimiter = 0
    for number, raw_line in enumerate(lines, 1):
        if number not in active_lines:
            continue
        masked, code_delimiter = mask_code_spans(raw_line, code_delimiter)
        line, in_comment = strip_comments(masked, in_comment)
        for link in markdown_links(line):
            target = link.target
            if target is None and link.reference:
                target = reference_definitions.get(link.reference)
            node.links.append((number, MarkdownLink(link.label, target, link.reference)))
    return node


def _load_manifest(root: Path, findings: list[Finding]) -> dict[str, object] | None:
    path = root / MANIFEST_NAME
    if not path.is_file() or path.is_symlink():
        add(
            findings, "error", "MANIFEST_MISSING", path, root,
            f"root {MANIFEST_NAME} is required",
        )
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        add(findings, "error", "MANIFEST_INVALID", path, root, str(error))
        return None
    if not isinstance(value, dict):
        add(
            findings, "error", "MANIFEST_INVALID", path, root,
            "manifest root must be an object",
        )
        return None
    unknown = set(value) - MANIFEST_KEYS
    missing = REQUIRED_MANIFEST_KEYS - set(value)
    if unknown:
        add(
            findings, "error", "MANIFEST_UNKNOWN_KEY", path, root,
            f"unknown manifest key: {sorted(unknown)[0]}",
        )
    if missing:
        add(
            findings, "error", "MANIFEST_MISSING_KEY", path, root,
            f"missing manifest key: {sorted(missing)[0]}",
        )
    if value.get("specspine") != FORMAT_MAJOR:
        add(
            findings, "error", "MANIFEST_VERSION", path, root,
            f"specspine must be the integer {FORMAT_MAJOR}",
        )
    try:
        presentation(value)
    except PresentationError as error:
        add(
            findings, "error", "MANIFEST_PRESENTATION", path, root, str(error),
        )
    if not isinstance(value.get("project"), str) or not value.get("project", "").strip():
        add(
            findings, "error", "MANIFEST_PROJECT", path, root,
            "project must be a nonempty string",
        )
    if value.get("implementation_freedom") not in {
        "contract-equivalent", "architecture-constrained", "exact",
    }:
        add(
            findings, "error", "MANIFEST_IMPLEMENTATION_FREEDOM", path, root,
            "implementation_freedom must be contract-equivalent, "
            "architecture-constrained, or exact",
        )
    for key in ("areas", "assets"):
        if not isinstance(value.get(key), list):
            add(
                findings, "error", "MANIFEST_INVALID", path, root,
                f"{key} must be an array",
            )
    return value


def _observation_evidence(node: _Node) -> list[tuple[str, int, list[str]]]:
    """Return OBS IDs, definition lines, and evidence code spans."""
    result: list[tuple[str, int, list[str]]] = []
    active = node.active_lines or set()
    statements = [
        (number, match.group(1))
        for number, line in enumerate(node.lines, 1)
        if number in active
        if (match := SEMANTIC_BULLET_RE.match(line))
    ]
    h2_lines = [
        number
        for number, line in enumerate(node.lines, 1)
        if number in active and line.startswith("## ")
    ]
    for index, (line, identifier) in enumerate(statements):
        if not identifier.startswith("OBS-"):
            continue
        boundaries = [
            candidate
            for candidate in (
                statements[index + 1][0] if index + 1 < len(statements) else None,
                next((value for value in h2_lines if value > line), None),
            )
            if candidate is not None
        ]
        end = min(boundaries) if boundaries else len(node.lines) + 1
        block = "\n".join(node.lines[line - 1 : end - 1])
        marker = block.find("Evidence:")
        evidence = (
            re.findall(r"`([^`\n]+)`", block[marker + len("Evidence:") :])
            if marker >= 0
            else []
        )
        result.append((identifier, line, evidence))
    return result


def check(
    root: Path,
    *,
    repository_root: Path | None = None,
) -> list[Finding]:
    """Validate the canonical v3 specification graph and manifest."""
    root = root.resolve()
    findings: list[Finding] = []
    if not root.is_dir():
        return [Finding("error", "ROOT_MISSING", ".", None, f"SpecSpine root does not exist: {root}")]
    manifest = _load_manifest(root, findings)
    files = [path for path in owned_files(root) if path.suffix.casefold() == ".md"]
    index = root / INDEX_NAME
    if not index.is_file():
        add(findings, "error", "INDEX_MISSING", index, root, f"root {INDEX_NAME} is required")
    nodes = [_parse_node(path, root, findings, manifest) for path in files]
    by_path = {node.path.resolve(): node for node in nodes}
    nested_roots = nested_spine_roots(root)
    for directory in owned_directories(root):
        directory_index = directory / INDEX_NAME
        if not directory_index.is_file():
            add(
                findings,
                "error",
                "DIRECTORY_INDEX_MISSING",
                directory_index,
                root,
                f"every directory in a Spine requires {INDEX_NAME}",
            )
            continue
        node = by_path.get(directory_index.resolve())
        if node is not None and node.kind != "index":
            add(
                findings,
                "error",
                "INDEX_KIND",
                directory_index,
                root,
                f"{INDEX_NAME} must use Kind `index`",
                node.identity_line,
            )
        expected: set[Path] = set()
        for child in directory.iterdir():
            if child.name == INDEX_NAME or child.is_symlink():
                continue
            if child.is_file():
                expected.add(child.resolve())
            elif child.is_dir() and (child / INDEX_NAME).is_file():
                expected.add((child / INDEX_NAME).resolve())
        if directory == root:
            expected.update((child / INDEX_NAME).resolve() for child in nested_roots)
        actual: set[Path] = set()
        if node is not None:
            for _, link in node.links or []:
                if not link.target or "#" in link.target:
                    continue
                scope, target = local_target(node.path, link.target, root)
                if scope == "inside" and target is not None:
                    actual.add(target.resolve())
        for missing in sorted(expected - actual):
            add(
                findings,
                "error",
                "INDEX_ENTRY_MISSING",
                directory_index,
                root,
                f"missing deterministic entry for {missing.relative_to(root)}",
            )
        for extra in sorted(actual - expected):
            add(
                findings,
                "error",
                "INDEX_ENTRY_EXTRA",
                directory_index,
                root,
                f"unexpected deterministic entry for {extra.relative_to(root)}",
            )
    by_id: dict[str, _Node] = {}
    global_statements: dict[str, tuple[_Node, str, int]] = {}
    for node in nodes:
        for number, line in enumerate(node.lines, 1):
            if (
                number in (node.active_lines or set())
                and re.search(r"<\s*/?\s*details(?:\s|>)", line, re.IGNORECASE)
            ):
                add(
                    findings,
                    "error",
                    "SEMANTIC_DISCLOSURE",
                    node.path,
                    root,
                    "canonical semantic content must not use HTML details disclosure",
                    number,
                )
        if node.kind == "index" and node.statements:
            add(
                findings,
                "error",
                "INDEX_SEMANTIC_CONTENT",
                node.path,
                root,
                "generated indexes cannot own semantic claims",
            )
        for section in sorted(
            MARKDOWN_COMPLETENESS_SECTIONS & set(node.sections or {})
        ):
            add(
                findings,
                "error",
                "COMPLETENESS_IN_MARKDOWN",
                node.path,
                root,
                "v3 completeness belongs only in specspine.json; "
                f"remove {section}",
                node.sections[section][0],
            )
        if repository_root is not None:
            observations = _observation_evidence(node)
            if observations and not any(
                EVIDENCE_BASELINE_RE.search(line) for line in node.lines
            ):
                add(
                    findings,
                    "error",
                    "EVIDENCE_BASELINE_MISSING",
                    node.path,
                    root,
                    "a document with OBS claims requires one evidence baseline",
                )
            for identifier, line, evidence in observations:
                if not evidence:
                    add(
                        findings,
                        "error",
                        "OBS_EVIDENCE_MISSING",
                        node.path,
                        root,
                        f"{identifier} requires repository-relative Evidence paths",
                        line,
                    )
                    continue
                for value in evidence:
                    evidence_path = Path(value.rstrip("/"))
                    if (
                        evidence_path.is_absolute()
                        or ".." in evidence_path.parts
                        or not evidence_path.parts
                    ):
                        add(
                            findings,
                            "error",
                            "EVIDENCE_PATH_INVALID",
                            node.path,
                            root,
                            f"{identifier} has unsafe Evidence path: {value}",
                            line,
                        )
                    elif not (repository_root / evidence_path).exists():
                        add(
                            findings,
                            "error",
                            "EVIDENCE_PATH_MISSING",
                            node.path,
                            root,
                            f"{identifier} Evidence path does not exist: {value}",
                            line,
                        )
        if node.document_id:
            if node.document_id in by_id:
                add(findings, "error", "DUPLICATE_DOCUMENT_ID", node.path, root, f"document ID already owned by {by_id[node.document_id].path.relative_to(root)}", node.identity_line)
            else:
                by_id[node.document_id] = node
        for identifier, (section, number) in (node.statements or {}).items():
            if identifier in global_statements:
                add(findings, "error", "DUPLICATE_GLOBAL_ID", node.path, root, f"semantic ID already defined in {global_statements[identifier][0].path.relative_to(root)}", number)
            else:
                global_statements[identifier] = (node, section, number)

    edges: list[tuple[_Node, str, _Node, str, int]] = []
    edge_keys: set[tuple[str, str, str, str]] = set()
    graph: dict[Path, set[Path]] = {node.path.resolve(): set() for node in nodes}
    linked_assets: dict[Path, set[str]] = {}
    for node in nodes:
        for number, link in node.links or []:
            if not link.target:
                continue
            scope, target = local_target(node.path, link.target, root)
            if scope == "outside":
                add(findings, "note", "OUT_OF_SCOPE_LINK", node.path, root, f"local link points outside the Spine: {link.target}", number)
            elif scope == "inside" and target is not None:
                if not target.exists():
                    add(findings, "error", "BROKEN_LINK", node.path, root, f"link target does not exist: {link.target}", number)
                elif target.resolve() in by_path:
                    graph[node.path.resolve()].add(target.resolve())
                    if ID_RE.fullmatch(link.label) and link.label not in (by_path[target.resolve()].statements or {}):
                        add(findings, "error", "UNRESOLVED_ID", node.path, root, f"target does not define {link.label}", number)
                elif target.is_file():
                    linked_assets.setdefault(target.resolve(), set()).add(
                        node.document_id
                    )
            if ID_RE.fullmatch(link.label) and "#" in link.target:
                add(findings, "error", "ID_FRAGMENT", node.path, root, "semantic-ID reference must not use a fragment", number)

        relationships = (node.sections or {}).get("relationships")
        if relationships:
            header, rows = _table_rows(node.lines, relationships[0])
            if header != RELATION_HEADER:
                add(findings, "error", "RELATIONSHIP_HEADER", node.path, root, "Relationships columns must be Relation | Target | Meaning", relationships[0])
            for number, cells in rows:
                if len(cells) != 3:
                    add(findings, "error", "MALFORMED_RELATIONSHIP", node.path, root, "relationship row must have three cells", number)
                    continue
                relation_cell, target_cell, meaning = cells
                relation_match = re.fullmatch(r"`([^`]+)`", relation_cell)
                links = markdown_links(target_cell)
                if not relation_match or len(links) != 1 or not links[0].target or not meaning:
                    add(findings, "error", "MALFORMED_RELATIONSHIP", node.path, root, "relationship needs canonical token, one relative link, and Meaning", number)
                    continue
                relation = relation_match.group(1)
                if relation not in CORE_RELATIONS and not re.fullmatch(r"x-[a-z0-9]+(?:-[a-z0-9]+)*", relation):
                    add(findings, "warning", "UNKNOWN_RELATION", node.path, root, f"unknown non-extension relation: {relation}", number)
                scope, target_path = local_target(node.path, links[0].target, root)
                target_node = by_path.get(target_path.resolve()) if scope == "inside" and target_path else None
                if target_node is None:
                    add(findings, "error", "UNKNOWN_RELATION_TARGET", node.path, root, f"unknown relationship target: {links[0].target}", number)
                    continue
                statement = links[0].label if ID_RE.fullmatch(links[0].label) else ""
                if statement and statement not in (target_node.statements or {}):
                    add(findings, "error", "UNKNOWN_RELATION_STATEMENT", node.path, root, f"target does not define {statement}", number)
                key = (node.document_id, relation, target_node.document_id, statement)
                if key in edge_keys:
                    add(findings, "error", "DUPLICATE_RELATIONSHIP", node.path, root, f"duplicate relationship key: {key}", number)
                edge_keys.add(key)
                edges.append((node, relation, target_node, statement, number))

    registered_assets: set[Path] = set()
    area_owners: set[str] = set()
    area_facets: dict[str, dict[str, str]] = {}
    owner_asset_roles: dict[str, set[str]] = {}
    verification_support: set[str] = {
        node.document_id
        for node in nodes
        if any(identifier.startswith("VER-") for identifier in (node.statements or {}))
    }
    if manifest is not None:
        areas = manifest.get("areas", [])
        if isinstance(areas, list):
            for position, area in enumerate(areas):
                label = f"areas[{position}]"
                if not isinstance(area, dict):
                    add(findings, "error", "MANIFEST_AREA", root / MANIFEST_NAME, root, f"{label} must be an object")
                    continue
                unknown = set(area) - AREA_KEYS
                missing = AREA_REQUIRED_KEYS - set(area)
                if unknown or missing:
                    detail = (
                        f"unknown key {sorted(unknown)[0]}"
                        if unknown else f"missing key {sorted(missing)[0]}"
                    )
                    add(findings, "error", "MANIFEST_AREA", root / MANIFEST_NAME, root, f"{label}: {detail}")
                owner = area.get("owner")
                if not isinstance(owner, str) or owner not in by_id or by_id[owner].kind == "index":
                    add(findings, "error", "MANIFEST_AREA_OWNER", root / MANIFEST_NAME, root, f"{label} has unknown non-index owner")
                    continue
                if owner in area_owners:
                    add(findings, "error", "MANIFEST_DUPLICATE_AREA", root / MANIFEST_NAME, root, f"duplicate area owner: {owner}")
                area_owners.add(owner)
                facets = area.get("facets")
                if not isinstance(facets, dict) or set(facets) != FACET_NAME_SET:
                    add(findings, "error", "MANIFEST_FACETS", root / MANIFEST_NAME, root, f"{label}.facets must contain exactly {', '.join(sorted(FACET_NAMES))}")
                else:
                    area_facets[owner] = dict(facets)
                    for facet, status in facets.items():
                        if status not in FACET_VALUES:
                            add(findings, "error", "MANIFEST_FACET_VALUE", root / MANIFEST_NAME, root, f"{label}.facets.{facet} has invalid value: {status}")
                    for facet in KIND_REQUIRED_FACETS.get(by_id[owner].kind, {"architecture"}):
                        if facets.get(facet) == "not-applicable":
                            add(findings, "error", "MANIFEST_REQUIRED_FACET", root / MANIFEST_NAME, root, f"{owner} kind {by_id[owner].kind} requires facet {facet}")
                blockers = area.get("blockers")
                if not isinstance(blockers, list) or not all(isinstance(item, str) for item in blockers):
                    add(findings, "error", "MANIFEST_BLOCKERS", root / MANIFEST_NAME, root, f"{label}.blockers must be an array of OQ IDs")
                else:
                    if len(blockers) != len(set(blockers)):
                        add(findings, "error", "MANIFEST_DUPLICATE_BLOCKER", root / MANIFEST_NAME, root, f"{label}.blockers contains duplicates")
                    for blocker in blockers:
                        statement = global_statements.get(blocker)
                        if statement is None or not blocker.startswith("OQ-"):
                            add(findings, "error", "MANIFEST_BLOCKER", root / MANIFEST_NAME, root, f"{label} references unknown blocking question: {blocker}")
                inspection = area.get("inspection")
                if inspection is not None:
                    expected = {"source", "inspected", "mode", "facets"}
                    if not isinstance(inspection, dict) or set(inspection) != expected:
                        add(findings, "error", "MANIFEST_INSPECTION", root / MANIFEST_NAME, root, f"{label}.inspection must contain exactly source, inspected, mode, and facets")
                    else:
                        source = inspection.get("source")
                        inspected = inspection.get("inspected")
                        mode = inspection.get("mode")
                        inspected_facets = inspection.get("facets")
                        if not isinstance(source, str) or not source.strip():
                            add(findings, "error", "MANIFEST_INSPECTION_SOURCE", root / MANIFEST_NAME, root, f"{label}.inspection.source must be nonempty")
                        if not isinstance(inspected, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", inspected) is None:
                            add(findings, "error", "MANIFEST_INSPECTION_DATE", root / MANIFEST_NAME, root, f"{label}.inspection.inspected must be YYYY-MM-DD")
                        if mode not in INSPECTION_MODES:
                            add(findings, "error", "MANIFEST_INSPECTION_MODE", root / MANIFEST_NAME, root, f"{label}.inspection.mode is invalid")
                        if not isinstance(inspected_facets, dict) or set(inspected_facets) != FACET_NAME_SET:
                            add(findings, "error", "MANIFEST_INSPECTION_FACETS", root / MANIFEST_NAME, root, f"{label}.inspection.facets must contain exactly {', '.join(sorted(FACET_NAMES))}")
                        else:
                            for facet, status in inspected_facets.items():
                                if status not in INSPECTION_FACET_VALUES:
                                    add(findings, "error", "MANIFEST_INSPECTION_FACET_VALUE", root / MANIFEST_NAME, root, f"{label}.inspection.facets.{facet} has invalid value: {status}")

        assets = manifest.get("assets", [])
        if isinstance(assets, list):
            for position, asset in enumerate(assets):
                label = f"assets[{position}]"
                if not isinstance(asset, dict):
                    add(findings, "error", "MANIFEST_ASSET", root / MANIFEST_NAME, root, f"{label} must be an object")
                    continue
                unknown = set(asset) - ASSET_KEYS
                missing = ASSET_KEYS - set(asset)
                if unknown or missing:
                    detail = (
                        f"unknown key {sorted(unknown)[0]}"
                        if unknown else f"missing key {sorted(missing)[0]}"
                    )
                    add(findings, "error", "MANIFEST_ASSET", root / MANIFEST_NAME, root, f"{label}: {detail}")
                relative = asset.get("path")
                owner = asset.get("owner")
                if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
                    add(findings, "error", "MANIFEST_ASSET_PATH", root / MANIFEST_NAME, root, f"{label}.path must be a relative path")
                    continue
                if Path(relative).suffix.casefold() == ".md":
                    add(findings, "error", "MANIFEST_ASSET_PATH", root / MANIFEST_NAME, root, f"{label}.path must name a non-Markdown file")
                    continue
                target = (root / relative).resolve()
                if not within(target, root) or target == (root / MANIFEST_NAME).resolve():
                    add(findings, "error", "MANIFEST_ASSET_PATH", root / MANIFEST_NAME, root, f"{label}.path escapes the Spine or names the manifest")
                    continue
                if target in registered_assets:
                    add(findings, "error", "MANIFEST_DUPLICATE_ASSET", root / MANIFEST_NAME, root, f"duplicate asset path: {relative}")
                registered_assets.add(target)
                if not target.is_file() or target.is_symlink():
                    add(findings, "error", "MANIFEST_ASSET_MISSING", root / MANIFEST_NAME, root, f"registered asset does not exist: {relative}")
                if not isinstance(owner, str) or owner not in by_id or by_id[owner].kind == "index":
                    add(findings, "error", "MANIFEST_ASSET_OWNER", root / MANIFEST_NAME, root, f"{label} has unknown non-index owner")
                elif owner not in linked_assets.get(target, set()):
                    add(findings, "error", "MANIFEST_ASSET_LINK", root / MANIFEST_NAME, root, f"{relative} must be linked from its owner {owner}")
                if asset.get("role") not in ASSET_ROLES:
                    add(findings, "error", "MANIFEST_ASSET_ROLE", root / MANIFEST_NAME, root, f"{label}.role is invalid")
                if not isinstance(asset.get("format"), str) or not asset.get("format", "").strip():
                    add(findings, "error", "MANIFEST_ASSET_FORMAT", root / MANIFEST_NAME, root, f"{label}.format must be nonempty")
                if not isinstance(asset.get("normative"), bool):
                    add(findings, "error", "MANIFEST_ASSET_NORMATIVE", root / MANIFEST_NAME, root, f"{label}.normative must be boolean")
                verifies = asset.get("verifies")
                if not isinstance(verifies, list) or not all(isinstance(item, str) for item in verifies):
                    add(findings, "error", "MANIFEST_ASSET_VERIFIES", root / MANIFEST_NAME, root, f"{label}.verifies must be an array of VER IDs")
                else:
                    if len(verifies) != len(set(verifies)):
                        add(findings, "error", "MANIFEST_DUPLICATE_VERIFICATION", root / MANIFEST_NAME, root, f"{label}.verifies contains duplicates")
                    for identifier in verifies:
                        if identifier not in global_statements or not identifier.startswith("VER-"):
                            add(findings, "error", "MANIFEST_ASSET_VERIFICATION", root / MANIFEST_NAME, root, f"{label} references unknown verification: {identifier}")
                if (
                    isinstance(owner, str)
                    and (
                        asset.get("role") == "verification"
                        or isinstance(verifies, list) and bool(verifies)
                    )
                ):
                    verification_support.add(owner)
                if isinstance(owner, str) and isinstance(asset.get("role"), str):
                    owner_asset_roles.setdefault(owner, set()).add(asset["role"])

    changed = True
    while changed:
        changed = False
        for source, relation, target, _, _ in edges:
            if (
                relation == "verified-by"
                and target.document_id in verification_support
                and source.document_id not in verification_support
            ):
                verification_support.add(source.document_id)
                changed = True
    for owner, facets in area_facets.items():
        if facets.get("verification") == "complete" and owner not in verification_support:
            add(
                findings, "error", "MANIFEST_VERIFICATION_UNSUPPORTED",
                root / MANIFEST_NAME, root,
                f"{owner} marks verification complete without VER claims, "
                "a verification asset, or a verified-by owner",
            )
        node = by_id[owner]
        sections = set((node.sections or {}).keys())
        identifiers = set((node.statements or {}).keys())
        outgoing_relations = {
            relation
            for source, relation, _, _, _ in edges
            if source.document_id == owner
        }
        asset_roles = owner_asset_roles.get(owner, set())
        for facet in ("behavior", "interfaces", "data", "failure", "quality"):
            if facets.get(facet) != "complete":
                continue
            supported = bool(sections & FACET_SUPPORT_SECTIONS.get(facet, set()))
            supported = supported or any(
                identifier.startswith(prefix)
                for identifier in identifiers
                for prefix in FACET_SUPPORT_PREFIXES.get(facet, set())
            )
            supported = supported or bool(
                asset_roles & FACET_SUPPORT_ASSET_ROLES.get(facet, set())
            )
            supported = supported or bool(
                outgoing_relations & FACET_SUPPORT_RELATIONS.get(facet, set())
            )
            if not supported:
                add(
                    findings,
                    "warning",
                    "MANIFEST_FACET_SUPPORT_UNVERIFIED",
                    node.path,
                    root,
                    f"{owner} marks {facet} complete without machine-resolvable "
                    "support; translated or prose-only support requires semantic review",
                )

    for node in nodes:
        if node.kind != "index" and node.document_id not in area_owners:
            add(findings, "error", "MANIFEST_AREA_MISSING", node.path, root, "every non-index specification requires exactly one manifest area")
    physical_assets = {
        path.resolve()
        for path in owned_files(root)
        if path.is_file()
        and path.suffix.casefold() != ".md"
        and path.name != MANIFEST_NAME
    }
    for asset in sorted(physical_assets - registered_assets):
        add(findings, "error", "UNREGISTERED_SPEC_ASSET", asset, root, "every non-Markdown specification asset must be registered in specspine.json")

    if index in [node.path for node in nodes]:
        index_node = by_path[index.resolve()]
        if index_node.kind != "index":
            add(findings, "error", "INDEX_KIND", index, root, f"root {INDEX_NAME} must use Kind `index`", index_node.identity_line)

    for node in nodes:
        divergence = (node.sections or {}).get("known-divergences")
        if not divergence:
            continue
        header, rows = _table_rows(node.lines, divergence[0])
        if header != DIVERGENCE_HEADER:
            add(findings, "error", "DIVERGENCE_HEADER", node.path, root, "Known divergences columns must be Intended | Observed | Consequence", divergence[0])
        seen: set[tuple[str, str]] = set()
        for number, cells in rows:
            if len(cells) != 3 or not cells[2]:
                add(findings, "error", "MALFORMED_DIVERGENCE", node.path, root, "divergence row must have three nonempty cells", number)
                continue
            intended, observed = markdown_links(cells[0]), markdown_links(cells[1])
            if len(intended) != 1 or len(observed) != 1:
                add(findings, "error", "MALFORMED_DIVERGENCE", node.path, root, "Intended and Observed must each contain one semantic link", number)
                continue
            intended_id, observed_id = intended[0].label, observed[0].label
            if not intended_id.startswith(NORMATIVE_PREFIXES):
                add(findings, "error", "DIVERGENCE_INTENDED_KIND", node.path, root, "Intended must reference a normative statement", number)
            if not observed_id.startswith("OBS-"):
                add(findings, "error", "DIVERGENCE_OBSERVED_KIND", node.path, root, "Observed must reference OBS", number)
            if intended_id not in global_statements or observed_id not in global_statements:
                add(findings, "error", "DIVERGENCE_UNKNOWN_STATEMENT", node.path, root, "divergence references an unknown semantic statement", number)
            if (intended_id, observed_id) in seen:
                add(findings, "error", "DUPLICATE_DIVERGENCE", node.path, root, "duplicate Known divergence", number)
            seen.add((intended_id, observed_id))

    for relation in ("contains", "decomposes-into"):
        adjacency: dict[str, set[str]] = {}
        edge_lines: dict[tuple[str, str], tuple[_Node, int]] = {}
        for source, edge_relation, target, _, number in edges:
            if edge_relation == relation:
                adjacency.setdefault(source.document_id, set()).add(target.document_id)
                edge_lines[(source.document_id, target.document_id)] = (source, number)
        visiting: set[str] = set()
        visited: set[str] = set()
        def visit(current: str) -> None:
            if current in visited:
                return
            visiting.add(current)
            for target in adjacency.get(current, set()):
                if target in visiting:
                    source, number = edge_lines[(current, target)]
                    add(findings, "error", "RELATIONSHIP_CYCLE", source.path, root, f"cycle in {relation}", number)
                else:
                    visit(target)
            visiting.discard(current)
            visited.add(current)
        for current in sorted(adjacency):
            visit(current)

    if index.is_file():
        reachable: set[Path] = set()
        pending = [index.resolve()]
        while pending:
            current = pending.pop()
            if current in reachable:
                continue
            reachable.add(current)
            pending.extend(graph.get(current, set()) - reachable)
        for node in nodes:
            if node.path.resolve() not in reachable:
                add(findings, "error", "UNREACHABLE_SPEC", node.path, root, f"specification is not reachable from {INDEX_NAME}")
    order = {"error": 0, "warning": 1, "note": 2}
    return sorted(findings, key=lambda item: (order[item.severity], item.path, item.line or 0, item.code))


def _finding_key(finding: Finding) -> tuple[str, str, str, int | None, str]:
    return (
        finding.severity,
        finding.code,
        finding.path,
        finding.line,
        finding.message,
    )


def _link_or_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def _candidate_sections(
    path: Path,
    root: Path,
    manifest: dict[str, object] | None,
) -> list[Finding]:
    findings: list[Finding] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return findings

    h1_line: int | None = None
    first_h2: int | None = None
    responsibility_line: int | None = None
    next_heading: int | None = None
    visible: list[tuple[int, str]] = []
    in_comment = False
    in_fence = False
    fence_char = ""
    fence_length = 0
    code_delimiter = 0

    for line_number, raw_line in enumerate(lines, 1):
        fence = FENCE_RE.match(raw_line)
        if in_fence:
            if fence and fence.group(1)[0] == fence_char and len(fence.group(1)) >= fence_length:
                in_fence = False
            continue
        if fence and not in_comment and code_delimiter == 0:
            in_fence = True
            fence_char = fence.group(1)[0]
            fence_length = len(fence.group(1))
            continue
        masked, code_delimiter = mask_code_spans(raw_line, code_delimiter)
        line, in_comment = strip_comments(masked, in_comment)
        stripped = line.strip()
        if not stripped:
            continue
        heading = ATX_HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            title = re.sub(r"[ \t]+#+[ \t]*$", "", heading.group(2) or "").strip()
            if level == 1 and h1_line is None:
                h1_line = line_number
            elif level == 2:
                if first_h2 is None:
                    first_h2 = line_number
                if (
                    responsibility_line is None
                    and canonical_heading(title, manifest) == "responsibility"
                ):
                    responsibility_line = line_number
                elif responsibility_line is not None and next_heading is None:
                    next_heading = line_number
            continue
        visible.append((line_number, stripped))

    summary_end = first_h2 or len(lines) + 1
    if h1_line is not None and not any(h1_line < number < summary_end for number, _ in visible):
        add(findings, "error", "MISSING_SUMMARY", path, root, "candidate has no summary below its title")
    if responsibility_line is None:
        add(findings, "error", "MISSING_RESPONSIBILITY", path, root, "candidate has no Responsibility section")
    else:
        responsibility_end = next_heading or len(lines) + 1
        if not any(responsibility_line < number < responsibility_end for number, _ in visible):
            add(findings, "error", "EMPTY_RESPONSIBILITY", path, root, "candidate Responsibility section is empty")
    return findings


def check_candidates(
    spine_root: Path,
    staging_root: Path,
    *,
    allowed_replacements: set[str] | None = None,
    repository_root: Path | None = None,
) -> list[Finding]:
    """Check staged Markdown against the live Spine without publishing it."""
    spine_root = spine_root.resolve()
    staging_root = staging_root.absolute()
    replacements = allowed_replacements or set()
    findings: list[Finding] = []
    if not spine_root.is_dir():
        return [Finding("error", "ROOT_MISSING", ".", None, f"SpecSpine root does not exist: {spine_root}")]
    if staging_root.is_symlink():
        return [Finding("error", "STAGED_SYMLINK", ".", None, "staging root must not be a symlink")]
    if not staging_root.is_dir():
        return [Finding("error", "STAGING_MISSING", ".", None, f"staging root does not exist: {staging_root}")]

    manifest_findings: list[Finding] = []
    manifest = _load_manifest(spine_root, manifest_findings)
    candidates: list[tuple[Path, Path]] = []
    for path in sorted(staging_root.rglob("*")):
        relative = path.relative_to(staging_root)
        if path.is_symlink():
            add(findings, "error", "STAGED_SYMLINK", path, staging_root, "staged entries must not be symlinks")
            continue
        if path.is_dir():
            continue
        if not path.is_file():
            add(findings, "error", "STAGED_SPECIAL_FILE", path, staging_root, "staged entries must be regular files")
            continue
        if path.suffix != ".md":
            add(findings, "error", "STAGED_NON_MARKDOWN", path, staging_root, "staging may contain only Markdown files")
            continue
        if relative == Path(INDEX_NAME):
            add(findings, "error", "STAGED_INDEX", path, staging_root, f"a producer must not replace {INDEX_NAME}")
            continue
        destination = spine_root / relative
        if destination.is_symlink() or (
            destination.exists() and not destination.is_file()
        ):
            add(findings, "error", "DESTINATION_COLLISION", path, staging_root, f"destination already exists: {relative}")
            continue
        if destination.exists() and relative.as_posix() not in replacements:
            add(findings, "error", "DESTINATION_COLLISION", path, staging_root, f"destination already exists: {relative}")
            continue
        candidates.append((path, relative))
        findings.extend(_candidate_sections(path, staging_root, manifest))

    if not candidates:
        return findings

    baseline = {
        _finding_key(item)
        for item in check(spine_root, repository_root=repository_root)
    }
    ignored_overlay_codes = {
        # Indexes are integration-owned. A producer may introduce the first
        # document in a new directory but must not stage its deterministic
        # _INDEX.md.
        "DIRECTORY_INDEX_MISSING",
        "ID_SECTION_UNVERIFIED",
        "UNREACHABLE_SPEC",
        "MANIFEST_AREA_MISSING",
        "INDEX_ENTRY_MISSING",
    }
    with tempfile.TemporaryDirectory(prefix="specspine-candidate-check-") as directory:
        overlay = Path(directory)
        for live in sorted(spine_root.rglob("*.md")):
            if live.is_file() and not live.is_symlink():
                _link_or_copy(live, overlay / live.relative_to(spine_root))
        manifest = spine_root / MANIFEST_NAME
        if manifest.is_file() and not manifest.is_symlink():
            _link_or_copy(manifest, overlay / MANIFEST_NAME)
        for source, relative in candidates:
            destination = overlay / relative
            if destination.exists():
                destination.unlink()
            _link_or_copy(source, destination)
        for item in check(overlay, repository_root=repository_root):
            if item.code in ignored_overlay_codes or _finding_key(item) in baseline:
                continue
            findings.append(item)

    order = {"error": 0, "warning": 1, "note": 2}
    return sorted(findings, key=lambda item: (order[item.severity], item.path, item.line or 0, item.code))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spine_root", type=Path)
    parser.add_argument("--candidates", type=Path, help="check a private staging root against the live Spine")
    parser.add_argument(
        "--replace-existing",
        action="append",
        default=[],
        metavar="RELATIVE_PATH",
        help="allow one reserved existing Markdown destination; repeat as needed",
    )
    parser.add_argument("--json", action="store_true", help="emit a JSON array")
    parser.add_argument(
        "--repository-root",
        type=Path,
        help="validate OBS Evidence paths against this repository root",
    )
    args = parser.parse_args()
    replacements: set[str] = set()
    for value in args.replace_existing:
        path = Path(value)
        if (
            path.is_absolute()
            or ".." in path.parts
            or path.suffix != ".md"
            or path == Path(INDEX_NAME)
        ):
            parser.error(f"unsafe replacement path: {value}")
        replacements.add(path.as_posix())
    findings = (
        check_candidates(
            args.spine_root,
            args.candidates,
            allowed_replacements=replacements,
            repository_root=args.repository_root,
        )
        if args.candidates
        else check(args.spine_root, repository_root=args.repository_root)
    )
    if args.json:
        print(json.dumps([asdict(item) for item in findings], indent=2))
    elif not findings:
        print("No mechanical defects found within the checked SpecSpine.")
    else:
        for item in findings:
            location = f"{item.path}:{item.line}" if item.line else item.path
            print(f"{item.severity.upper()} {item.code} {location} — {item.message}")
    return 1 if findings and (args.candidates or any(item.severity == "error" for item in findings)) else 0


if __name__ == "__main__":
    raise SystemExit(main())
