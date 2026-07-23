#!/usr/bin/env python3
"""Check deterministic integrity rules for a SpecSpine Markdown graph."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit


ID_RE = re.compile(r"^(DEC|CON|OBS|INF|OQ)-[a-z0-9]+(?:-[a-z0-9]+)*$")
ID_CANDIDATE_RE = re.compile(r"^(?:DEC|CON|OBS|INF|OQ)-.+$")
DEFINITION_RE = re.compile(r"^ {0,3}[-+*]\s+\*\*([^*\n]+)\*\*\s+—\s+")
FILENAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
DIRECTORY_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FENCE_RE = re.compile(r"^ {0,3}(?:>\s*)?(`{3,}|~{3,})")
ATX_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*)|[ \t]*)$")
REFERENCE_DEFINITION_RE = re.compile(
    r'^ {0,3}\[([^\]]+)\]:\s*(?:<([^>]+)>|(\S+?))(?:\s+(?:"[^"]*"|\'[^\']*\'|\([^)]*\)))?\s*$'
)
BASELINE_RE = re.compile(
    r"^<!-- specspine:evidence-baseline source=([^;<>]+); inspected=(\d{4}-\d{2}-\d{2}) -->$"
)
ID_REGION_BEGIN = "<!-- specspine:semantic-ids:begin -->"
ID_REGION_END = "<!-- specspine:semantic-ids:end -->"
SECTION_PREFIXES = {
    "Decisions": "DEC",
    "System-wide decisions": "DEC",
    "Constraints": "CON",
    "System-wide constraints": "CON",
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


def check(root: Path) -> list[Finding]:
    root = root.resolve()
    findings: list[Finding] = []
    if not root.is_dir():
        return [Finding("error", "ROOT_MISSING", ".", None, f"SpecSpine root does not exist: {root}")]

    index = root / "README.md"
    index_resolved = index.resolve(strict=False)
    index_is_internal = within(index_resolved, root)
    if not index_is_internal or not index.is_file():
        add(findings, "error", "INDEX_MISSING", index, root, "README.md architecture index is missing")

    files: list[Path] = []
    for candidate in sorted(root.rglob("*.md")):
        resolved = candidate.resolve(strict=False)
        if not within(resolved, root):
            add(findings, "note", "OUT_OF_SCOPE_ENTRY", candidate, root, "Markdown entry resolves outside the SpecSpine")
            continue
        if candidate.is_file():
            files.append(candidate)

    definitions: dict[tuple[Path, str], list[int]] = {}
    references: list[tuple[Path, int, str, str]] = []
    graph: dict[Path, set[Path]] = {path.resolve(): set() for path in files}
    invalid_directories: set[Path] = set()

    for path in files:
        relative = path.relative_to(root)
        current = root
        for directory in relative.parts[:-1]:
            current /= directory
            if not DIRECTORY_RE.fullmatch(directory):
                invalid_directories.add(current)
        if relative != Path("README.md") and not FILENAME_RE.fullmatch(path.name):
            add(findings, "warning", "INVALID_FILENAME", path, root, "filename should use lowercase kebab-case")

        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            add(findings, "error", "READ_ERROR", path, root, f"cannot read Markdown as UTF-8: {error}")
            continue

        lines = text.splitlines()
        section = ""
        section_line = 0
        section_has_content = True
        visible_lines: list[tuple[int, str]] = []
        reference_definitions: dict[str, str] = {}
        in_fence = False
        fence_char = ""
        fence_length = 0
        in_comment = False
        code_delimiter = 0
        id_region_depth = 0
        id_regions = 0
        region_definitions = 0
        observed_content = False
        baselines: list[tuple[int, str, str]] = []
        h1_count = 0

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

            stripped = raw_line.strip()
            if not in_comment and code_delimiter == 0 and stripped == ID_REGION_BEGIN:
                if id_region_depth:
                    add(findings, "error", "ID_REGION_NESTED", path, root, "semantic-ID regions must not nest", line_number)
                else:
                    id_regions += 1
                id_region_depth += 1
                continue
            if not in_comment and code_delimiter == 0 and stripped == ID_REGION_END:
                if not id_region_depth:
                    add(findings, "error", "ID_REGION_END", path, root, "semantic-ID region ends without a matching begin", line_number)
                else:
                    id_region_depth -= 1
                continue
            if not in_comment and code_delimiter == 0 and stripped.startswith("<!-- specspine:evidence-baseline"):
                baseline = BASELINE_RE.fullmatch(stripped)
                if not baseline:
                    add(findings, "warning", "INVALID_BASELINE", path, root, "invalid evidence-baseline syntax", line_number)
                else:
                    baselines.append((line_number, baseline.group(1).strip(), baseline.group(2)))
                    try:
                        dt.date.fromisoformat(baseline.group(2))
                    except ValueError:
                        add(findings, "warning", "INVALID_BASELINE_DATE", path, root, "invalid evidence-baseline date", line_number)
                continue

            masked, code_delimiter = mask_code_spans(raw_line, code_delimiter)
            line, in_comment = strip_comments(masked, in_comment)
            if not line.strip():
                continue
            visible_lines.append((line_number, line))

            heading = ATX_HEADING_RE.match(line)
            if heading:
                level = len(heading.group(1))
                title = re.sub(r"[ \t]+#+[ \t]*$", "", heading.group(2) or "").strip()
                if level == 1:
                    h1_count += 1
                if level == 2:
                    if section and not section_has_content:
                        add(findings, "warning", "EMPTY_SECTION", path, root, f"section '{section}' is empty", section_line)
                    section = title
                    section_line = line_number
                    section_has_content = False
                continue

            if section:
                section_has_content = True
                if section == "Observed":
                    observed_content = True

            definition = DEFINITION_RE.match(line)
            if definition:
                identifier = definition.group(1).strip()
                looks_like_id = bool(ID_CANDIDATE_RE.fullmatch(identifier))
                if id_region_depth:
                    region_definitions += 1
                    looks_like_id = True
                if looks_like_id:
                    if not id_region_depth:
                        add(findings, "warning", "ID_OUTSIDE_REGION", path, root, f"semantic ID is outside the marker region: {identifier}", line_number)
                    if not ID_RE.fullmatch(identifier):
                        add(findings, "error", "INVALID_ID", path, root, f"invalid semantic ID: {identifier}", line_number)
                    else:
                        expected = SECTION_PREFIXES.get(section)
                        actual = identifier.split("-", 1)[0]
                        if not section:
                            add(findings, "error", "ID_SECTION", path, root, f"{identifier} is not under a semantic section", line_number)
                        elif expected is None:
                            add(findings, "note", "ID_SECTION_UNVERIFIED", path, root, f"cannot mechanically verify the section for {identifier}: '{section}'", line_number)
                        elif expected != actual:
                            add(findings, "error", "ID_SECTION", path, root, f"{identifier} does not belong under '{section}'", line_number)
                        if id_region_depth:
                            definitions.setdefault((path.resolve(), identifier), []).append(line_number)

        if h1_count == 0:
            add(findings, "warning", "MISSING_H1", path, root, "document has no level-one heading", 1)
        if id_region_depth:
            add(findings, "error", "ID_REGION_UNCLOSED", path, root, "semantic-ID region is not closed")
        if id_regions > 1:
            add(findings, "error", "MULTIPLE_ID_REGIONS", path, root, "use at most one semantic-ID region")
        if id_regions and not region_definitions:
            add(findings, "warning", "EMPTY_ID_REGION", path, root, "semantic-ID region defines no IDs")
        if len(baselines) > 1:
            add(findings, "warning", "MULTIPLE_BASELINES", path, root, "use at most one evidence baseline", baselines[1][0])
        if observed_content and not baselines:
            add(findings, "warning", "MISSING_BASELINE", path, root, "Observed content has no evidence baseline")
        if section and not section_has_content:
            add(findings, "warning", "EMPTY_SECTION", path, root, f"section '{section}' is empty", section_line)

        reference_definition_lines: set[int] = set()
        for line_number, line in visible_lines:
            match = REFERENCE_DEFINITION_RE.match(line)
            if match:
                reference_definitions.setdefault(
                    normalize_reference(match.group(1)),
                    unescape_markdown(match.group(2) or match.group(3)),
                )
                reference_definition_lines.add(line_number)

        for line_number, line in visible_lines:
            if line_number in reference_definition_lines:
                continue
            for link in markdown_links(line):
                raw_target = link.target
                if raw_target is None and link.reference is not None:
                    raw_target = reference_definitions.get(link.reference)
                if raw_target is None:
                    continue
                if ID_CANDIDATE_RE.fullmatch(link.label):
                    references.append((path, line_number, link.label, raw_target))
                    if not ID_RE.fullmatch(link.label):
                        add(findings, "error", "INVALID_ID_REFERENCE", path, root, f"invalid referenced semantic ID: {link.label}", line_number)
                    if "#" in raw_target:
                        add(findings, "error", "ID_FRAGMENT", path, root, "semantic-ID reference must not use a Markdown fragment", line_number)

                scope, target = local_target(path, raw_target, root)
                if scope == "remote":
                    continue
                if scope == "outside":
                    add(findings, "note", "OUT_OF_SCOPE_LINK", path, root, f"local link points outside the SpecSpine and was not checked: {raw_target}", line_number)
                    continue
                assert target is not None
                if not target.exists():
                    add(findings, "error", "BROKEN_LINK", path, root, f"link target does not exist: {raw_target}", line_number)
                elif target.is_file() and target.suffix == ".md":
                    graph[path.resolve()].add(target.resolve())

    for directory in sorted(invalid_directories):
        add(findings, "note", "INVALID_DIRECTORY", directory, root, "directory should use lowercase kebab-case")

    for (path, identifier), line_numbers in definitions.items():
        if len(line_numbers) > 1:
            add(findings, "error", "DUPLICATE_ID", path, root, f"semantic ID is defined more than once: {identifier}", line_numbers[1])

    for source, line_number, identifier, raw_target in references:
        scope, target = local_target(source, raw_target, root)
        if scope == "inside" and target is not None and target.exists() and len(definitions.get((target, identifier), [])) != 1:
            add(findings, "error", "UNRESOLVED_ID", source, root, f"target does not define {identifier}: {raw_target}", line_number)

    if index_is_internal and index.is_file():
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


def _candidate_sections(path: Path, root: Path) -> list[Finding]:
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
                if responsibility_line is None and title == "Responsibility":
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


def check_candidates(spine_root: Path, staging_root: Path) -> list[Finding]:
    """Check staged Markdown against the live Spine without publishing it."""
    spine_root = spine_root.resolve()
    staging_root = staging_root.absolute()
    findings: list[Finding] = []
    if not spine_root.is_dir():
        return [Finding("error", "ROOT_MISSING", ".", None, f"SpecSpine root does not exist: {spine_root}")]
    if staging_root.is_symlink():
        return [Finding("error", "STAGED_SYMLINK", ".", None, "staging root must not be a symlink")]
    if not staging_root.is_dir():
        return [Finding("error", "STAGING_MISSING", ".", None, f"staging root does not exist: {staging_root}")]

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
        if relative == Path("README.md"):
            add(findings, "error", "STAGED_INDEX", path, staging_root, "a producer must not replace README.md")
            continue
        destination = spine_root / relative
        if destination.exists() or destination.is_symlink():
            add(findings, "error", "DESTINATION_COLLISION", path, staging_root, f"destination already exists: {relative}")
            continue
        candidates.append((path, relative))
        findings.extend(_candidate_sections(path, staging_root))

    if not candidates:
        return findings

    baseline = {_finding_key(item) for item in check(spine_root)}
    ignored_overlay_codes = {"ID_SECTION_UNVERIFIED", "UNREACHABLE_SPEC"}
    with tempfile.TemporaryDirectory(prefix="specspine-candidate-check-") as directory:
        overlay = Path(directory)
        for live in sorted(spine_root.rglob("*.md")):
            if live.is_file() and not live.is_symlink():
                _link_or_copy(live, overlay / live.relative_to(spine_root))
        for source, relative in candidates:
            _link_or_copy(source, overlay / relative)
        for item in check(overlay):
            if item.code in ignored_overlay_codes or _finding_key(item) in baseline:
                continue
            findings.append(item)

    order = {"error": 0, "warning": 1, "note": 2}
    return sorted(findings, key=lambda item: (order[item.severity], item.path, item.line or 0, item.code))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spine_root", type=Path)
    parser.add_argument("--candidates", type=Path, help="check a private staging root against the live Spine")
    parser.add_argument("--json", action="store_true", help="emit a JSON array")
    args = parser.parse_args()
    findings = (
        check_candidates(args.spine_root, args.candidates)
        if args.candidates
        else check(args.spine_root)
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
