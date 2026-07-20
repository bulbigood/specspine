#!/usr/bin/env python3
"""Check deterministic integrity rules for a SpecSpine Markdown graph."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


ID_RE = re.compile(r"^(DEC|CON|OBS|INF|OQ)-[a-z0-9]+(?:-[a-z0-9]+)*$")
ID_LINK_RE = re.compile(r"\[((?:DEC|CON|OBS|INF|OQ)-[^\]]+)\]\(([^)]+)\)")
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
DEFINITION_RE = re.compile(r"^- \*\*((?:DEC|CON|OBS|INF|OQ)-[^*]+)\*\* — ")
FILENAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
SECTION_PREFIXES = {
    "Decisions": "DEC",
    "Constraints": "CON",
    "Observed": "OBS",
    "Inferred": "INF",
    "Open questions": "OQ",
}


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    line: int | None
    message: str


def add(findings: list[Finding], severity: str, code: str, path: Path, root: Path, message: str, line: int | None = None) -> None:
    try:
        relative = str(path.relative_to(root))
    except ValueError:
        relative = str(path)
    findings.append(Finding(severity, code, relative or ".", line, message))


def local_target(source: Path, raw_target: str) -> Path | None:
    target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
    if not target or "://" in target or target.startswith(("mailto:", "#")):
        return None
    return (source.parent / target.split("#", 1)[0]).resolve()


def check(root: Path) -> list[Finding]:
    root = root.resolve()
    findings: list[Finding] = []
    if not root.is_dir():
        return [Finding("error", "ROOT_MISSING", ".", None, f"SpecSpine root does not exist: {root}")]

    index = root / "README.md"
    if not index.is_file():
        add(findings, "error", "INDEX_MISSING", index, root, "README.md architecture index is missing")

    files = sorted(path for path in root.rglob("*.md") if path.is_file())
    definitions: dict[tuple[Path, str], list[int]] = {}
    references: list[tuple[Path, int, str, str]] = []
    graph: dict[Path, set[Path]] = {path.resolve(): set() for path in files}

    for path in files:
        relative = path.relative_to(root)
        if len(relative.parts) > 1:
            add(findings, "warning", "NESTED_SPEC", path, root, "specification is nested; the standard organization is flat")
        if path.name != "README.md" and not FILENAME_RE.fullmatch(path.name):
            add(findings, "error", "INVALID_FILENAME", path, root, "filename must use lowercase kebab-case")

        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        if not lines or not re.fullmatch(r"#\s+\S.*", lines[0]):
            add(findings, "error", "MISSING_H1", path, root, "first line must be a level-one heading", 1)
        if re.search(r"\{\{[^{}]+\}\}", text):
            add(findings, "error", "TEMPLATE_PLACEHOLDER", path, root, "unresolved template placeholder")

        section = ""
        section_line = 0
        section_has_content = True
        for line_number, line in enumerate(lines, 1):
            heading = re.match(r"^##\s+(.+?)\s*$", line)
            if heading:
                if section and not section_has_content:
                    add(findings, "warning", "EMPTY_SECTION", path, root, f"section '{section}' is empty", section_line)
                section = heading.group(1)
                section_line = line_number
                section_has_content = False
                continue
            if section and line.strip() and not line.startswith("###"):
                section_has_content = True

            definition = DEFINITION_RE.match(line)
            if definition:
                identifier = definition.group(1)
                if not ID_RE.fullmatch(identifier):
                    add(findings, "error", "INVALID_ID", path, root, f"invalid semantic ID: {identifier}", line_number)
                expected = SECTION_PREFIXES.get(section)
                actual = identifier.split("-", 1)[0]
                if expected != actual:
                    add(findings, "error", "ID_SECTION", path, root, f"{identifier} does not belong under '{section or 'no section'}'", line_number)
                definitions.setdefault((path.resolve(), identifier), []).append(line_number)

        if section and not section_has_content:
            add(findings, "warning", "EMPTY_SECTION", path, root, f"section '{section}' is empty", section_line)

        for line_number, line in enumerate(lines, 1):
            for identifier, target in ID_LINK_RE.findall(line):
                references.append((path, line_number, identifier, target))
                if not ID_RE.fullmatch(identifier):
                    add(findings, "error", "INVALID_ID_REFERENCE", path, root, f"invalid referenced semantic ID: {identifier}", line_number)
                if "#" in target:
                    add(findings, "error", "ID_FRAGMENT", path, root, "semantic-ID reference must not use a Markdown fragment", line_number)
            for raw_target in LINK_RE.findall(line):
                target = local_target(path, raw_target)
                if target is None:
                    continue
                if not target.exists():
                    add(findings, "error", "BROKEN_LINK", path, root, f"link target does not exist: {raw_target}", line_number)
                    continue
                try:
                    target.relative_to(root)
                except ValueError:
                    add(findings, "warning", "EXTERNAL_LINK", path, root, f"local link points outside the SpecSpine: {raw_target}", line_number)
                else:
                    if target.is_file() and target.suffix == ".md":
                        graph[path.resolve()].add(target.resolve())

    for (path, identifier), line_numbers in definitions.items():
        if len(line_numbers) > 1:
            add(findings, "error", "DUPLICATE_ID", path, root, f"semantic ID is defined more than once: {identifier}", line_numbers[1])

    for source, line_number, identifier, raw_target in references:
        target = local_target(source, raw_target)
        if target is not None and target.exists() and len(definitions.get((target, identifier), [])) != 1:
            add(findings, "error", "UNRESOLVED_ID", source, root, f"target does not define {identifier}: {raw_target}", line_number)

    if index.is_file():
        reachable: set[Path] = set()
        pending = [index.resolve()]
        while pending:
            current = pending.pop()
            if current in reachable:
                continue
            reachable.add(current)
            pending.extend(graph.get(current, set()) - reachable)
        for path in files:
            if path.resolve() not in reachable:
                add(findings, "warning", "UNREACHABLE_SPEC", path, root, "specification is not reachable from README.md")

    return sorted(findings, key=lambda item: ({"error": 0, "warning": 1, "note": 2}[item.severity], item.path, item.line or 0, item.code))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spine_root", type=Path)
    parser.add_argument("--json", action="store_true", help="emit a JSON array")
    args = parser.parse_args()
    findings = check(args.spine_root)
    if args.json:
        print(json.dumps([asdict(item) for item in findings], indent=2))
    elif not findings:
        print("No mechanical defects found within the checked SpecSpine.")
    else:
        for item in findings:
            location = f"{item.path}:{item.line}" if item.line else item.path
            print(f"{item.severity.upper()} {item.code} {location} — {item.message}")
    return 1 if any(item.severity == "error" for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
