#!/usr/bin/env python3
"""Build a minimal architecture closure from a verified SpecSpine."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

POTENTIAL_LIMIT = 12
TASK_CONTEXT_DOCUMENT_LIMIT = 6
TASK_CONTEXT_DOCUMENT_CHARS = 1800
NORMALIZED_PREFIX_LENGTH = 4
FENCE_RE = re.compile(r"^ {0,3}(?:>\s*)?(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*)|[ \t]*)$")
QUERY_TOKEN_RE = re.compile(r"[^\W_]+(?:-[^\W_]+)*", re.UNICODE)
DEFINITION_RE = re.compile(r"^ {0,3}[-+*]\s+\*\*((?:DEC|CON|OBS|INF|OQ)-[a-z0-9]+(?:-[a-z0-9]+)*)\*\*\s+—\s+(.*)")
ID_RE = re.compile(r"^(?:DEC|CON|OBS|INF|OQ)-[a-z0-9]+(?:-[a-z0-9]+)*$")
DOCUMENT_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
IDENTITY_RE = re.compile(
    r"^\*\*ID:\*\*\s+`([^`]+)`\s+·\s+\*\*Kind:\*\*\s+`([^`]+)`\s*$"
)
CORE_RELATIONS = {
    "contains", "decomposes-into", "performs", "depends-on", "exposes",
    "consumes", "publishes", "reads-from", "writes-to", "owns-data",
    "constrained-by", "implemented-by", "has-evidence", "superseded-by",
    "related-to",
}


def load_checker_module():
    """Load the shared mechanical checker bundled beside this script."""
    path = Path(__file__).with_name("check_spine.py")
    name = f"{__name__}_checker"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load checker module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


CHECKER = load_checker_module()


@dataclass(frozen=True)
class MarkdownLink:
    label: str
    target: str | None


def within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


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
        elif char == "\\":
            escaped = True
        elif char == "(":
            depth += 1
        elif char == ")" and depth:
            depth -= 1
        elif char.isspace() and depth == 0:
            return value[:index]
    return value


def matching(text: str, start: int, opening: str, closing: str) -> int | None:
    depth = 0
    escaped = False
    angle = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif opening == "(" and char == "<" and depth == 1:
            angle = True
        elif opening == "(" and char == ">" and angle:
            angle = False
        elif not angle and char == opening:
            depth += 1
        elif not angle and char == closing:
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
        end = matching(line, start, "[", "]")
        if end is None:
            break
        label = unescape_markdown(line[start + 1 : end])
        after = end + 1
        link: MarkdownLink | None = None
        if after < len(line) and line[after] == "(":
            target_end = matching(line, after, "(", ")")
            if target_end is not None:
                target = destination_from_parentheses(line[after + 1 : target_end])
                link = MarkdownLink(label, unescape_markdown(target))
                cursor = target_end + 1
        if link is not None and not image:
            links.append(link)
        if cursor <= start:
            cursor = end + 1
    return links


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


def local_target(source: Path, raw_target: str, root: Path) -> Path | None:
    raw_target = raw_target.strip()
    if not raw_target or raw_target.startswith("#"):
        return None
    split = urlsplit(raw_target)
    if split.scheme or split.netloc or raw_target.startswith("//"):
        return None
    decoded = unquote(split.path)
    if not decoded:
        return None
    lexical = Path(decoded)
    if not lexical.is_absolute():
        lexical = source.parent / lexical
    lexical = Path(os.path.normpath(re.sub(r"/+$", "", str(lexical.absolute()))))
    if not within(lexical, root):
        return None
    resolved = lexical.resolve(strict=False)
    if not within(resolved, root) or resolved.suffix.casefold() != ".md":
        return None
    return lexical


def structural_lines(text: str) -> list[str]:
    """Preserve inline Markdown while removing fenced and HTML-comment content."""
    visible: list[str] = []
    in_fence = False
    fence_char = ""
    fence_length = 0
    in_comment = False
    for raw_line in text.splitlines():
        fence = FENCE_RE.match(raw_line)
        if in_fence:
            visible.append("")
            if fence and fence.group(1)[0] == fence_char and len(fence.group(1)) >= fence_length:
                in_fence = False
            continue
        if fence and not in_comment:
            in_fence = True
            fence_char = fence.group(1)[0]
            fence_length = len(fence.group(1))
            visible.append("")
            continue
        line, in_comment = strip_comments(raw_line, in_comment)
        visible.append(line)
    return visible


def read_selected_document(root: Path, relative: str) -> str:
    path = (root / relative).resolve()
    if not within(path, root) or path.suffix.casefold() != ".md" or not path.is_file():
        raise ValueError(f"selected document is unavailable: {relative}")
    return path.read_text(encoding="utf-8")


def normalized_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value).casefold()
    return unicodedata.normalize(
        "NFKC",
        "".join(
            character
            for character in decomposed
            if not unicodedata.combining(character)
        ),
    )


def expanded_tokens(value: str) -> tuple[str, ...]:
    return tuple(
        part
        for token in QUERY_TOKEN_RE.findall(normalized_text(value))
        for part in token.split("-")
        if part
    )


def morphological_token_match(query_token: str, document_token: str) -> bool:
    if query_token == document_token:
        return True
    if not query_token.isalpha() or not document_token.isalpha():
        return False
    shorter = min(len(query_token), len(document_token))
    if shorter < NORMALIZED_PREFIX_LENGTH:
        return False
    shared = 0
    for left, right in zip(query_token, document_token):
        if left != right:
            break
        shared += 1
    return shared >= max(NORMALIZED_PREFIX_LENGTH, math.ceil(shorter * 0.7))


def _cells(line: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in line.strip().strip("|").split("|"))


def _canonical_documents(root: Path) -> tuple[dict[str, dict[str, object]], list[str]]:
    documents: dict[str, dict[str, object]] = {}
    errors: list[str] = []
    paths: dict[Path, str] = {}
    for path in sorted(root.rglob("*.md")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        lines = structural_lines(text)
        title = next((match.group(2).strip() for line in lines if (match := HEADING_RE.match(line)) and len(match.group(1)) == 1), "")
        identities = [IDENTITY_RE.fullmatch(line.strip()) for line in lines]
        identities = [item for item in identities if item]
        if len(identities) != 1:
            errors.append(f"{relative}: missing or duplicate identity line")
            continue
        document_id, kind = identities[0].groups()
        if not DOCUMENT_ID_RE.fullmatch(document_id) or document_id in documents:
            errors.append(f"{relative}: invalid or duplicate document ID")
            continue
        identity_index = next(index for index, line in enumerate(lines) if IDENTITY_RE.fullmatch(line.strip()))
        aliases: list[str] = []
        cursor = identity_index + 1
        while cursor < len(lines) and not lines[cursor].strip():
            cursor += 1
        if cursor < len(lines) and lines[cursor].startswith("**Aliases:**"):
            aliases = [item.strip() for item in lines[cursor].split(":", 1)[1].split(",") if item.strip()]
            cursor += 1
            while cursor < len(lines) and not lines[cursor].strip():
                cursor += 1
        summary_lines: list[str] = []
        while cursor < len(lines) and lines[cursor].strip() and not lines[cursor].startswith("#"):
            summary_lines.append(lines[cursor].strip())
            cursor += 1
        sections: dict[str, str] = {}
        section_order: list[str] = []
        current: str | None = None
        body: list[str] = []
        for line in lines:
            heading = HEADING_RE.match(line)
            if heading and len(heading.group(1)) == 2:
                if current is not None:
                    sections[current] = "\n".join(body).strip()
                current = heading.group(2).strip()
                section_order.append(current)
                body = []
            elif current is not None:
                body.append(line)
        if current is not None:
            sections[current] = "\n".join(body).strip()
        statements: dict[str, dict[str, str]] = {}
        for heading, section_body in sections.items():
            for statement_line in section_body.splitlines():
                match = DEFINITION_RE.match(statement_line)
                if match is None:
                    continue
                identifier = match.group(1)
                statements[identifier] = {
                    "kind": identifier.split("-", 1)[0],
                    "statement": match.group(2).strip(),
                    "section": heading,
                }
        documents[document_id] = {
            "id": document_id, "kind": kind, "path": relative, "title": title,
            "aliases": aliases, "summary": " ".join(summary_lines),
            "responsibility": sections.get("Responsibility", ""),
            "sections": sections, "section_order": section_order,
            "statements": statements, "relationships": [], "divergences": [],
            "text": text,
        }
        paths[path.resolve()] = document_id
    for document in documents.values():
        source_path = (root / str(document["path"])).resolve()
        relationship_body = document["sections"].get("Relationships", "")
        relationship_lines = relationship_body.splitlines()
        if len(relationship_lines) >= 2 and _cells(relationship_lines[0]) == ("Relation", "Target", "Meaning"):
            for line in relationship_lines[2:]:
                cells = _cells(line)
                if len(cells) != 3:
                    continue
                relation = cells[0].strip("`")
                links = markdown_links(cells[1])
                if relation not in CORE_RELATIONS and not relation.startswith("x-"):
                    errors.append(f"{document['path']}: unknown relation {relation}")
                    continue
                if len(links) != 1 or not links[0].target:
                    errors.append(f"{document['path']}: malformed relationship target")
                    continue
                target_path = local_target(source_path, links[0].target, root)
                target_id = paths.get(target_path.resolve()) if target_path else None
                if not target_id:
                    errors.append(f"{document['path']}: unknown relationship target")
                    continue
                document["relationships"].append({
                    "relation": relation, "target": target_id,
                    "statement": links[0].label if ID_RE.fullmatch(links[0].label) else "",
                    "meaning": cells[2],
                })
        divergence_body = document["sections"].get("Known divergences", "")
        divergence_lines = divergence_body.splitlines()
        if len(divergence_lines) >= 2 and _cells(divergence_lines[0]) == ("Intended", "Observed", "Consequence"):
            for line in divergence_lines[2:]:
                cells = _cells(line)
                if len(cells) == 3:
                    intended, observed = markdown_links(cells[0]), markdown_links(cells[1])
                    if len(intended) == len(observed) == 1:
                        document["divergences"].append({
                            "intended": intended[0].label,
                            "observed": observed[0].label,
                            "consequence": cells[2],
                        })
    return documents, errors


def _coverage(index: dict[str, object], primary: dict[str, object]) -> tuple[str, str]:
    body = str(index["sections"].get("Coverage", ""))
    current = ""
    primary_id, primary_path = str(primary["id"]), str(primary["path"])
    primary_target = (Path(str(index["root"])) / primary_path).resolve()
    for line in body.splitlines():
        if line.startswith("### "):
            current = line[4:].strip().casefold()
        elif line.lstrip().startswith(("-", "*")):
            links = markdown_links(line)
            linked = False
            for link in links:
                if not link.target:
                    continue
                target = local_target(
                    Path(str(index["root"])) / str(index["path"]),
                    link.target,
                    Path(str(index["root"])),
                )
                if target is not None and target.resolve() == primary_target:
                    linked = True
                    break
            id_mentioned = bool(re.search(
                rf"(?<![a-z0-9-]){re.escape(primary_id)}(?![a-z0-9-])",
                line,
            ))
            if linked or id_mentioned:
                mapping = {
                    "mapped": "mapped",
                    "partially mapped": "partially-mapped",
                    "unmapped": "unmapped",
                }
                return mapping.get(current, "unknown"), line.lstrip("-* ").strip()
    return "unknown", "primary area is not classified in Coverage"


def _attach_concatenated_files(
    root: Path,
    result: dict[str, object],
    source_paths: list[str],
    token_budget: int,
) -> dict[str, object]:
    notice = (
        "The following content is the complete, concatenated content of "
        "the selected SpecSpine files."
    )
    blocks = [notice]
    returned: list[str] = []
    output = {
        "concatenated_files": notice,
        "concatenated_source_paths": returned,
        "concatenated_files_truncated": False,
        **result,
    }
    for relative in source_paths:
        block = "\n".join((
            f'<<<SPECSPINE_FILE path="{relative}">>>',
            read_selected_document(root, relative).rstrip("\n"),
            "<<<SPECSPINE_END_FILE>>>",
        ))
        trial = {
            **output,
            "concatenated_files": "\n".join((*blocks, block)),
            "concatenated_source_paths": [*returned, relative],
        }
        if _estimated_tokens(trial) > token_budget:
            output["concatenated_files_truncated"] = True
            continue
        blocks.append(block)
        returned.append(relative)
        output = trial
    if _estimated_tokens(output) > token_budget:
        output = {
            "concatenated_files": notice,
            "concatenated_source_paths": [],
            "concatenated_files_truncated": True,
            "closure_status": "truncated",
            "reason": "token_budget_exceeded",
            "omitted": [{"reason": "token_budget"}],
            "sources": source_paths,
        }
    return output


def _validate_query(payload: object) -> tuple[dict[str, object] | None, str | None]:
    if not isinstance(payload, dict):
        return None, "query must be an object"
    allowed = {"id", "targets", "semantic_ids", "paths", "terms", "facets", "token_budget"}
    unknown = set(payload) - allowed
    if unknown:
        return None, f"unsupported fields: {', '.join(sorted(unknown))}"
    query = dict(payload)
    for field in ("targets", "semantic_ids", "paths", "facets"):
        value = query.get(field, [])
        if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
            return None, f"{field} must be a list of non-empty strings"
        query[field] = value
    terms = query.get("terms", [])
    if not isinstance(terms, list) or any(
        not isinstance(group, list) or not group or any(not isinstance(term, str) or not term.strip() for term in group)
        for group in terms
    ):
        return None, "terms must be synonym groups"
    budget = query.get("token_budget", 8000)
    if not isinstance(budget, int) or budget < 128:
        return None, "token_budget must be an integer >= 128"
    query["token_budget"] = budget
    return query, None


def _normalize_query_paths(
    raw_paths: list[str], document_paths: set[str]
) -> set[str]:
    folded_paths = {
        path.casefold(): path
        for path in document_paths
    }
    return {
        folded_paths[candidate.casefold()]
        for raw_path in raw_paths
        if (
            candidate := raw_path.strip().removeprefix("./").replace("\\", "/")
        ).casefold() in folded_paths
    }


def _query_group_score(group: list[str], searchable: dict[str, str]) -> float:
    field_scores = {
        "title": 120.0,
        "alias": 110.0,
        "summary": 6.0,
        "responsibility": 5.0,
        "body": 1.0,
    }
    return max(
        (
            score
            for term in group
            for field, score in field_scores.items()
            if term.casefold() in searchable[field]
        ),
        default=0.0,
    )


def _morphological_phrase_match(query: str, document: str) -> bool:
    query_tokens = expanded_tokens(query)
    document_tokens = expanded_tokens(document)
    return bool(query_tokens) and all(
        any(
            morphological_token_match(query_token, document_token)
            for document_token in document_tokens
        )
        for query_token in query_tokens
    )


def _identity_overlap_score(
    document: dict[str, object], query: dict[str, object]
) -> float:
    identity_tokens = expanded_tokens(
        f"{document['id']} {document['path']}"
    )
    routing_tokens = {
        token
        for value in (
            *query["targets"],
            *query["facets"],
            *(term for group in query["terms"] for term in group),
        )
        for token in expanded_tokens(value)
    }
    return 10.0 * sum(
        any(
            morphological_token_match(query_token, identity_token)
            for identity_token in identity_tokens
        )
        for query_token in routing_tokens
    )


def _capsule_excerpt(
    document: dict[str, object], query: dict[str, object]
) -> list[dict[str, str]]:
    sections = document["sections"]
    assert isinstance(sections, dict)
    query_terms = [
        term.casefold()
        for group in query["terms"]
        for term in group
    ]
    priorities = {
        "Boundaries": 60,
        "Behavior": 50,
        "Lifecycle and invariants": 45,
        "Failure behavior": 40,
        "Interfaces": 35,
        "Relationships": 30,
    }
    ranked = []
    for heading, body in sections.items():
        if heading == "Responsibility" or not body:
            continue
        lexical = sum(term in body.casefold() for term in query_terms)
        ranked.append((lexical * 100 + priorities.get(heading, 0), heading, body))
    excerpts: list[dict[str, str]] = []
    remaining = TASK_CONTEXT_DOCUMENT_CHARS
    for _, heading, body in sorted(ranked, key=lambda item: (-item[0], item[1])):
        if remaining <= 0 or len(excerpts) >= 3:
            break
        content = body[:remaining].rstrip()
        if content:
            excerpts.append({"heading": heading, "content": content})
            remaining -= len(content)
    return excerpts


def _task_context(
    documents: dict[str, dict[str, object]],
    query: dict[str, object],
    primary_id: str,
    required_ids: set[str],
    candidates: dict[str, float],
    preferred_ids: list[str],
) -> dict[str, object]:
    group_scores = {
        document_id: [
            max(
                _query_group_score(
                    group,
                    {
                        "title": str(document["title"]).casefold(),
                        "alias": " ".join(document["aliases"]).casefold(),
                        "summary": str(document["summary"]).casefold(),
                        "responsibility": str(document["responsibility"]).casefold(),
                        "body": str(document["text"]).casefold(),
                    },
                ),
                90.0
                if any(
                    _morphological_phrase_match(
                        term, f"{document_id} {document['path']}"
                    )
                    for term in group
                )
                else 0.0,
                max(
                    (
                        score
                        for term in group
                        for field, score in (
                            ("title", 80.0),
                            ("summary", 20.0),
                            ("responsibility", 15.0),
                        )
                        if _morphological_phrase_match(
                            term, str(document[field])
                        )
                    ),
                    default=0.0,
                ),
            )
            for group in query["terms"]
        ]
        for document_id, document in documents.items()
        if document["kind"] != "index"
    }
    selected = [primary_id, *sorted(required_ids)]
    selected = list(dict.fromkeys(selected))[:TASK_CONTEXT_DOCUMENT_LIMIT]
    covered = {
        index
        for document_id in selected
        for index, score in enumerate(group_scores.get(document_id, []))
        if score >= 5
    }
    all_groups = set(range(len(query["terms"])))
    while len(selected) < TASK_CONTEXT_DOCUMENT_LIMIT and covered != all_groups:
        choice: tuple[tuple[float, ...], str] | None = None
        for document_id, scores in group_scores.items():
            if document_id in selected:
                continue
            new_groups = {
                index
                for index, score in enumerate(scores)
                if score >= 5 and index not in covered
            }
            if not new_groups:
                continue
            rank = (
                float(len(new_groups)),
                sum(scores[index] for index in new_groups),
                _identity_overlap_score(documents[document_id], query),
                candidates.get(document_id, 0.0),
            )
            candidate = (rank, document_id)
            if choice is None or candidate > choice:
                choice = candidate
        if choice is None:
            break
        selected.append(choice[1])
        covered.update(
            index
            for index, score in enumerate(group_scores[choice[1]])
            if score >= 5
        )
    identity_ranked = sorted(
        (
            (
                _identity_overlap_score(document, query),
                candidates.get(document_id, 0.0),
                document_id,
            )
            for document_id, document in documents.items()
            if document["kind"] != "index" and document_id not in selected
        ),
        reverse=True,
    )
    for identity_score, _, document_id in identity_ranked:
        if len(selected) >= TASK_CONTEXT_DOCUMENT_LIMIT or identity_score < 20:
            break
        selected.append(document_id)
        covered.update(
            index
            for index, score in enumerate(group_scores.get(document_id, []))
            if score >= 5
        )
    for document_id in preferred_ids:
        if len(selected) >= TASK_CONTEXT_DOCUMENT_LIMIT:
            break
        if document_id not in selected:
            selected.append(document_id)
            covered.update(
                index
                for index, score in enumerate(group_scores.get(document_id, []))
                if score >= 5
            )
    context_documents = []
    for document_id in selected:
        document = documents[document_id]
        matched = [
            query["terms"][index][0]
            for index, score in enumerate(group_scores.get(document_id, []))
            if score >= 5
        ]
        context_documents.append({
            "id": document_id,
            "path": document["path"],
            "role": (
                "primary"
                if document_id == primary_id
                else "required"
                if document_id in required_ids
                else "task_match"
            ),
            "matched_query_groups": matched,
            "responsibility": document["responsibility"],
            "excerpts": _capsule_excerpt(document, query),
        })
    uncovered = sorted(all_groups - covered)
    suggested_paths = {
        query["terms"][index][0]: [
            documents[document_id]["path"]
            for _, _, document_id in sorted(
                (
                    (
                        group_scores[document_id][index],
                        _identity_overlap_score(document, query),
                        document_id,
                    )
                    for document_id, document in documents.items()
                    if (
                        document["kind"] != "index"
                        and group_scores.get(document_id, [0] * len(query["terms"]))[
                            index
                        ] > 0
                    )
                ),
                reverse=True,
            )[:2]
        ]
        for index in uncovered
    }
    return {
        "complete": covered == all_groups,
        "covered_query_groups": [
            query["terms"][index][0] for index in sorted(covered)
        ],
        "uncovered_query_groups": [
            query["terms"][index][0] for index in uncovered
        ],
        "suggested_paths": suggested_paths,
        "documents": context_documents,
    }


def _estimated_tokens(value: object) -> int:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return max(1, (len(encoded) + 3) // 4)


def _apply_token_budget(
    result: dict[str, object], token_budget: int
) -> dict[str, object]:
    original_tokens = _estimated_tokens(result)
    if original_tokens <= token_budget:
        return result

    result["closure_status"] = "truncated"
    result["reason"] = "token_budget_exceeded"
    result["potentially_affected"] = []
    result.pop("coverage_detail", None)
    primary = result.get("primary")
    if isinstance(primary, dict):
        primary.pop("summary", None)
        primary.pop("title", None)
        primary.pop("kind", None)
    result["omitted"] = [{
        "reason": "token_budget",
        "estimated_tokens": original_tokens,
        "token_budget": token_budget,
        "omitted_sections": ["potentially_affected", "primary_summary"],
    }]
    if _estimated_tokens(result) <= token_budget:
        return result

    compact = {
        "closure_status": "truncated",
        "reason": "token_budget_exceeded",
        "coverage": result.get("coverage", "unknown"),
        "primary": {
            key: value
            for key, value in (primary or {}).items()
            if key in {"id", "path"}
        } if isinstance(primary, dict) else None,
        "required": [
            {
                key: value
                for key, value in item.items()
                if key in {"id", "path"}
            }
            for item in result.get("required", [])
            if isinstance(item, dict)
        ],
        "potentially_affected": [],
        "decisions": [],
        "constraints": [],
        "known_divergences": [],
        "blocking_questions": [],
        "omitted": [{
            "reason": "token_budget",
            "estimated_tokens": original_tokens,
            "token_budget": token_budget,
            "omitted_sections": [
                "details", "claims", "divergences", "questions", "impact",
            ],
        }],
        "sources": list(result.get("sources", [])),
    }
    if _estimated_tokens(compact) <= token_budget:
        return compact

    required_count = len(compact["required"])
    minimal = {
        "closure_status": "truncated",
        "reason": "token_budget_exceeded",
        "coverage": compact["coverage"],
        "primary": (
            {"id": compact["primary"].get("id")}
            if isinstance(compact["primary"], dict)
            else None
        ),
        "required": [],
        "potentially_affected": [],
        "decisions": [],
        "constraints": [],
        "known_divergences": [],
        "blocking_questions": [],
        "omitted": [{
            "reason": "token_budget",
            "required_count": required_count,
        }],
        "sources": [],
    }
    return minimal


def build_closure(root: Path, payload: object) -> dict[str, object]:
    query, query_error = _validate_query(payload)
    base: dict[str, object] = {
        "closure_status": "invalid", "reason": "invalid_query",
        "coverage": "unknown", "primary": None, "required": [],
        "potentially_affected": [], "decisions": [], "constraints": [],
        "known_divergences": [], "blocking_questions": [], "omitted": [],
        "sources": [],
    }
    if query_error:
        base["omitted"] = [{"reason": query_error}]
        return base
    root = root.resolve()
    if not root.is_dir():
        base["reason"] = "spine_root_missing"
        return base
    mechanical_errors = [
        finding
        for finding in CHECKER.check(root)
        if finding.severity == "error"
    ]
    if mechanical_errors:
        base["reason"] = "invalid_spine"
        base["omitted"] = [
            {
                "reason": "mechanical_error",
                "code": finding.code,
                "path": finding.path,
                **({"line": finding.line} if finding.line is not None else {}),
            }
            for finding in mechanical_errors
        ]
        return base
    documents, errors = _canonical_documents(root)
    for document in documents.values():
        document["root"] = str(root)
    index = next((item for item in documents.values() if item["kind"] == "index" and item["path"] == "README.md"), None)
    if errors or index is None:
        base["reason"] = "invalid_spine"
        base["omitted"] = [{"reason": error} for error in errors] or [{"reason": "root index missing"}]
        return base
    candidates: dict[str, float] = {}
    targets = set(query["targets"])
    semantic_ids = set(query["semantic_ids"])
    paths = _normalize_query_paths(
        query["paths"],
        {str(document["path"]) for document in documents.values()},
    )
    for document_id, document in documents.items():
        score = 0.0
        if document_id in targets:
            score += 130
        if str(document["path"]) in paths:
            score += 125
        if semantic_ids & set(document["statements"]):
            score += 140
        searchable = {
            "title": str(document["title"]).casefold(),
            "alias": " ".join(document["aliases"]).casefold(),
            "summary": str(document["summary"]).casefold(),
            "responsibility": str(document["responsibility"]).casefold(),
            "body": str(document["text"]).casefold(),
        }
        for group in query["terms"]:
            score += _query_group_score(group, searchable)
        if score:
            candidates[document_id] = score
    candidates.pop(str(index["id"]), None)
    if not candidates:
        base.update({"closure_status": "no-match", "reason": "primary_owner_not_found", "sources": ["README.md"]})
        return base
    primary_id = sorted(candidates, key=lambda item: (-candidates[item], item))[0]
    primary = documents[primary_id]
    coverage, coverage_detail = _coverage(index, primary)
    required: dict[str, set[str]] = {}
    potential: set[str] = set()
    strong_by_facet = {
        "external-contract": {"exposes"},
        "event": {"consumes", "publishes"},
        "data-mutation": {"owns-data", "reads-from", "writes-to"},
        "failure": {"constrained-by"},
        "lifecycle": {"constrained-by", "owns-data", "performs"},
    }
    mandatory = {"superseded-by", "constrained-by"}
    direct_context = {"depends-on", "consumes"}
    normalized_facets = {
        known
        for facet in query["facets"]
        for known in strong_by_facet
        if known == facet
        or known in re.findall(r"[a-z0-9]+", facet.casefold())
    }
    facet_relations = set().union(*(
        strong_by_facet[facet] for facet in normalized_facets
    ))
    queue: list[tuple[str, int]] = [(primary_id, 0)]
    traversed: set[str] = set()
    while queue:
        current_id, depth = queue.pop(0)
        if current_id in traversed or depth >= 2:
            continue
        traversed.add(current_id)
        for relation in documents[current_id]["relationships"]:
            relation_type = relation["relation"]
            target_id = relation["target"]
            if relation_type in mandatory or relation_type in facet_relations:
                if target_id != primary_id:
                    required.setdefault(target_id, set()).add(relation_type)
                queue.append((target_id, depth + 1))
            elif depth == 0 and relation_type in direct_context:
                if target_id != primary_id:
                    required.setdefault(target_id, set()).add(relation_type)
            elif relation_type == "related-to":
                potential.add(target_id)
    impact_targets = {primary_id, *required}
    for document in documents.values():
        for relation in document["relationships"]:
            if relation["target"] in impact_targets and relation["relation"] in {
                "exposes", "consumes", "publishes", "reads-from", "writes-to",
                "owns-data", "constrained-by", "depends-on",
            }:
                potential.add(str(document["id"]))
    strong_task_matches = {
        document_id
        for document_id, score in candidates.items()
        if score >= 100
    }
    potential.update(strong_task_matches - {primary_id, *required})
    selected_ids = {primary_id, *required}
    statements = {
        identifier: (str(document["id"]), statement)
        for document in documents.values()
        for identifier, statement in document["statements"].items()
    }
    decisions = []
    constraints = []
    questions = []
    divergences = []
    claim_owner_ids = {str(index["id"]), *selected_ids}
    for selected_id in sorted(claim_owner_ids):
        document = documents[selected_id]
        for identifier, statement in document["statements"].items():
            item = {"id": identifier, "owner": selected_id, "statement": statement["statement"]}
            if identifier.startswith("DEC-"):
                decisions.append(item)
            elif identifier.startswith("CON-"):
                constraints.append(item)
            elif identifier.startswith("OQ-"):
                questions.append(item)
    for document in documents.values():
        for divergence in document["divergences"]:
            intended = statements.get(divergence["intended"])
            observed = statements.get(divergence["observed"])
            if intended is None or observed is None:
                continue
            if (
                document["id"] == index["id"]
                or intended[0] in selected_ids
                or observed[0] in selected_ids
            ):
                divergences.append({"owner": document["id"], **divergence})
    source_paths = [str(index["path"]), str(primary["path"])] + [
        str(documents[item]["path"]) for item in sorted(required)
    ]
    potential_ids = sorted(
        potential - set(required) - {primary_id},
        key=lambda item: (-candidates.get(item, 0), item),
    )[:POTENTIAL_LIMIT]
    task_context = _task_context(
        documents,
        query,
        primary_id,
        set(required),
        candidates,
        potential_ids,
    )
    result = {
        "closure_status": "complete",
        "reason": "mapped_task_closure_satisfied",
        "coverage": coverage,
        "coverage_detail": coverage_detail,
        "primary": {
            "id": primary_id, "path": primary["path"], "kind": primary["kind"],
            "title": primary["title"], "summary": primary["summary"],
            "responsibility": primary["responsibility"],
        },
        "required": [
            {
                "id": item,
                "path": documents[item]["path"],
                "reason": "typed_graph_closure",
                "relations": sorted(required[item]),
            }
            for item in sorted(required)
        ],
        "potentially_affected": [
            {"id": item, "path": documents[item]["path"], "reason": "incoming_or_weak_relationship"}
            for item in potential_ids
        ],
        "decisions": decisions, "constraints": constraints,
        "known_divergences": divergences, "blocking_questions": questions,
        "task_context": task_context,
        "omitted": [], "sources": source_paths,
    }
    if coverage != "mapped":
        result["closure_status"] = "partial"
        result["reason"] = "coverage_incomplete"
        result["omitted"].append({"reason": coverage_detail})
    budgeted = _apply_token_budget(result, query["token_budget"])
    return _attach_concatenated_files(
        root,
        budgeted,
        source_paths,
        query["token_budget"],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spine_root", type=Path)
    parser.add_argument("--query-json", required=True, help="structured task query")
    args = parser.parse_args()
    try:
        payload = json.loads(args.query_json)
    except json.JSONDecodeError as error:
        result = {
            "closure_status": "invalid", "reason": "malformed_query",
            "coverage": "unknown", "primary": None, "required": [],
            "potentially_affected": [], "decisions": [], "constraints": [],
            "known_divergences": [], "blocking_questions": [],
            "omitted": [{"reason": str(error)}], "sources": [],
        }
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1
    result = build_closure(args.spine_root, payload)
    print(json.dumps(result, ensure_ascii=False))
    return 1 if result["closure_status"] == "invalid" else 0


if __name__ == "__main__":
    raise SystemExit(main())
