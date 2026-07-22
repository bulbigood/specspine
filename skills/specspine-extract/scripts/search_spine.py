#!/usr/bin/env python3
"""Find candidate SpecSpine documents with an optional derived SQLite FTS5 index."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

try:
    import sqlite3
except ImportError as error:
    print(json.dumps({"mode": "fallback", "reason": f"sqlite3 is unavailable: {error}"}))
    raise SystemExit(2) from error


SCHEMA_VERSION = "1"
FALLBACK_EXIT = 2
BUILD_LOCK_TIMEOUT_MS = 10_000
SQLITE_BUSY_TIMEOUT_MS = 10_000
FENCE_RE = re.compile(r"^ {0,3}(?:>\s*)?(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*)|[ \t]*)$")
DEFINITION_RE = re.compile(r"^ {0,3}[-+*]\s+\*\*((?:DEC|CON|OBS|INF|OQ)-[a-z0-9]+(?:-[a-z0-9]+)*)\*\*\s+—\s+(.*)")
REFERENCE_DEFINITION_RE = re.compile(
    r'^ {0,3}\[([^\]]+)\]:\s*(?:<([^>]+)>|(\S+?))(?:\s+(?:"[^"]*"|\'[^\']*\'|\([^)]*\)))?\s*$'
)
QUERY_TOKEN_RE = re.compile(r"[^\W_]+(?:-[^\W_]+)*", re.UNICODE)
ID_RE = re.compile(r"^(?:DEC|CON|OBS|INF|OQ)-[a-z0-9]+(?:-[a-z0-9]+)*$")
ID_QUERY_RE = re.compile(r"^(?:DEC|CON|OBS|INF|OQ)-[a-z0-9]+(?:-[a-z0-9]+)*$", re.IGNORECASE)
SECTION_KINDS = {
    "decisions": "DEC",
    "system-wide decisions": "DEC",
    "constraints": "CON",
    "system-wide constraints": "CON",
    "observed": "OBS",
    "inferred": "INF",
    "open questions": "OQ",
}


class AcceleratorUnavailable(RuntimeError):
    """The optional accelerator cannot be used; callers should traverse links."""


@dataclass(frozen=True)
class MarkdownLink:
    label: str
    target: str | None
    reference: str | None


@dataclass(frozen=True)
class Section:
    ordinal: int
    heading: str
    kind: str | None
    body: str


@dataclass(frozen=True)
class Link:
    target_path: str
    label: str
    semantic_id: str | None


@dataclass(frozen=True)
class SemanticId:
    identifier: str
    kind: str
    statement: str


@dataclass(frozen=True)
class Document:
    path: str
    title: str
    summary: str
    content_hash: str
    size: int
    mtime_ns: int
    ctime_ns: int
    sections: tuple[Section, ...]
    links: tuple[Link, ...]
    semantic_ids: tuple[SemanticId, ...]


def within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def normalize_reference(value: str) -> str:
    return " ".join(value.split()).casefold()


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
                link = MarkdownLink(label, unescape_markdown(target), None)
                cursor = target_end + 1
        elif after < len(line) and line[after] == "[":
            reference_end = matching(line, after, "[", "]")
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


def visible_lines(text: str) -> list[str]:
    visible: list[str] = []
    in_fence = False
    fence_char = ""
    fence_length = 0
    in_comment = False
    code_delimiter = 0
    for raw_line in text.splitlines():
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
        visible.append(line)
    return visible


def parse_document(path: Path, root: Path, stat: os.stat_result) -> Document:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    lines = visible_lines(text)
    title = path.stem.replace("-", " ")
    current_heading = "Summary"
    current_body: list[str] = []
    sections: list[Section] = []
    semantic_ids: list[SemanticId] = []

    def finish_section() -> None:
        body = "\n".join(current_body).strip()
        if body:
            kind = SECTION_KINDS.get(current_heading.casefold())
            sections.append(Section(len(sections), current_heading, kind, body))

    for line in lines:
        heading = HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            value = re.sub(r"[ \t]+#+[ \t]*$", "", heading.group(2) or "").strip()
            if level == 1 and value:
                title = value
                continue
            if level >= 2:
                finish_section()
                current_heading = value or "Untitled"
                current_body = []
                continue
        current_body.append(line)
        definition = DEFINITION_RE.match(line)
        if definition:
            identifier = definition.group(1)
            semantic_ids.append(SemanticId(identifier, identifier.split("-", 1)[0], definition.group(2).strip()))
    finish_section()
    if not sections:
        sections.append(Section(0, "Summary", None, ""))

    summary = ""
    for section in sections:
        if section.heading != "Summary":
            continue
        paragraphs = re.split(r"\n\s*\n", section.body)
        summary = next((" ".join(item.split()) for item in paragraphs if item.strip()), "")
        break
    if not summary:
        summary = next((" ".join(section.body.split()) for section in sections if section.body), "")
    summary = summary[:500]

    reference_definitions: dict[str, str] = {}
    for line in lines:
        match = REFERENCE_DEFINITION_RE.match(line)
        if match:
            reference_definitions[normalize_reference(match.group(1))] = unescape_markdown(match.group(2) or match.group(3))

    links: list[Link] = []
    seen_links: set[tuple[str, str, str | None]] = set()
    for line in lines:
        if REFERENCE_DEFINITION_RE.match(line):
            continue
        for link in markdown_links(line):
            raw_target = link.target
            if raw_target is None and link.reference is not None:
                raw_target = reference_definitions.get(link.reference)
            if raw_target is None:
                continue
            target = local_target(path, raw_target, root)
            if target is None:
                continue
            relative = target.relative_to(root).as_posix()
            semantic_id = link.label if ID_RE.fullmatch(link.label) else None
            key = (relative, link.label, semantic_id)
            if key not in seen_links:
                links.append(Link(*key))
                seen_links.add(key)

    relative_path = path.relative_to(root).as_posix()
    return Document(
        relative_path,
        title,
        summary,
        hashlib.sha256(raw).hexdigest(),
        stat.st_size,
        stat.st_mtime_ns,
        stat.st_ctime_ns,
        tuple(sections),
        tuple(links),
        tuple(semantic_ids),
    )


SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE documents (
    path TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    size INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    ctime_ns INTEGER NOT NULL
);
CREATE TABLE sections (
    id INTEGER PRIMARY KEY,
    document_path TEXT NOT NULL REFERENCES documents(path) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL,
    heading TEXT NOT NULL,
    kind TEXT,
    body TEXT NOT NULL,
    UNIQUE(document_path, ordinal)
);
CREATE TABLE links (
    source_path TEXT NOT NULL REFERENCES documents(path) ON DELETE CASCADE,
    target_path TEXT NOT NULL,
    label TEXT NOT NULL,
    semantic_id TEXT,
    UNIQUE(source_path, target_path, label)
);
CREATE INDEX links_target_idx ON links(target_path);
CREATE TABLE semantic_ids (
    document_path TEXT NOT NULL REFERENCES documents(path) ON DELETE CASCADE,
    semantic_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    statement TEXT NOT NULL,
    PRIMARY KEY(document_path, semantic_id)
);
CREATE INDEX semantic_id_idx ON semantic_ids(semantic_id);
CREATE VIRTUAL TABLE sections_fts USING fts5(
    path UNINDEXED,
    title,
    summary,
    heading,
    body,
    tokenize = 'unicode61 remove_diacritics 2'
);
"""


def cache_path(root: Path) -> Path:
    configured = os.environ.get("SPECSPINE_CACHE_DIR")
    base = Path(configured).expanduser() if configured else Path(tempfile.gettempdir()) / "specspine-cache"
    key = hashlib.sha256(str(root).encode("utf-8")).hexdigest()[:24]
    directory = base / key
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    return directory / f"index-v{SCHEMA_VERSION}.sqlite"


def connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path, timeout=SQLITE_BUSY_TIMEOUT_MS / 1000)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}")
    return connection


def acquire_cache_lock(index_path: Path) -> sqlite3.Connection:
    """Serialize index creation or replacement without blocking normal readers."""
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(
            index_path.with_suffix(".lock.sqlite"),
            timeout=BUILD_LOCK_TIMEOUT_MS / 1000,
        )
        connection.execute(f"PRAGMA busy_timeout = {BUILD_LOCK_TIMEOUT_MS}")
        connection.execute("CREATE TABLE IF NOT EXISTS cache_lock (id INTEGER PRIMARY KEY)")
        connection.commit()
        connection.execute("BEGIN IMMEDIATE")
        return connection
    except (OSError, sqlite3.Error) as error:
        if connection is not None:
            connection.close()
        raise AcceleratorUnavailable(f"derived index is busy or cannot be locked: {error}") from error


def sqlite_error_code(error: sqlite3.Error) -> int | None:
    code = getattr(error, "sqlite_errorcode", None)
    return code & 0xFF if isinstance(code, int) else None


def is_lock_error(error: sqlite3.Error) -> bool:
    code = sqlite_error_code(error)
    return code in {5, 6} or any(word in str(error).casefold() for word in ("busy", "locked"))


def is_rebuildable_error(error: sqlite3.Error) -> bool:
    # SQLITE_ERROR covers missing/incompatible schema; the other codes are
    # SQLITE_CORRUPT, SQLITE_SCHEMA, and SQLITE_NOTADB.
    return sqlite_error_code(error) in {1, 11, 17, 26}


def probe_fts5() -> None:
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(":memory:")
        connection.execute("CREATE VIRTUAL TABLE fts_probe USING fts5(content)")
    except (sqlite3.Error, OSError) as error:
        raise AcceleratorUnavailable(f"SQLite FTS5 is unavailable: {error}") from error
    finally:
        if connection is not None:
            connection.close()


def discover(root: Path) -> dict[str, tuple[Path, os.stat_result]]:
    files: dict[str, tuple[Path, os.stat_result]] = {}
    for candidate in sorted(root.rglob("*.md")):
        resolved = candidate.resolve(strict=False)
        if not within(resolved, root) or not candidate.is_file():
            continue
        relative = candidate.relative_to(root).as_posix()
        files[relative] = (candidate, candidate.stat())
    return files


def create_index(path: Path, root: Path, files: dict[str, tuple[Path, os.stat_result]]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.unlink(missing_ok=True)
    connection: sqlite3.Connection | None = None
    try:
        connection = connect(temporary)
        connection.execute("PRAGMA journal_mode = DELETE")
        connection.executescript(SCHEMA)
        connection.execute("INSERT INTO meta VALUES ('schema_version', ?)", (SCHEMA_VERSION,))
        connection.execute("INSERT INTO meta VALUES ('root_hash', ?)", (hashlib.sha256(str(root).encode()).hexdigest(),))
        for _, (source, stat) in files.items():
            insert_document(connection, parse_document(source, root, stat))
        connection.commit()
        if connection.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise AcceleratorUnavailable("new index failed SQLite quick_check")
        connection.close()
        connection = None
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    except (OSError, UnicodeError, sqlite3.Error) as error:
        raise AcceleratorUnavailable(f"cannot build derived index: {error}") from error
    finally:
        if connection is not None:
            connection.close()
        temporary.unlink(missing_ok=True)


def insert_document(connection: sqlite3.Connection, document: Document) -> None:
    connection.execute(
        "INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            document.path,
            document.title,
            document.summary,
            document.content_hash,
            document.size,
            document.mtime_ns,
            document.ctime_ns,
        ),
    )
    for section in document.sections:
        connection.execute(
            "INSERT INTO sections(document_path, ordinal, heading, kind, body) VALUES (?, ?, ?, ?, ?)",
            (document.path, section.ordinal, section.heading, section.kind, section.body),
        )
        connection.execute(
            "INSERT INTO sections_fts(path, title, summary, heading, body) VALUES (?, ?, ?, ?, ?)",
            (document.path, document.title, document.summary, section.heading, section.body),
        )
    connection.executemany(
        "INSERT OR IGNORE INTO links VALUES (?, ?, ?, ?)",
        [(document.path, item.target_path, item.label, item.semantic_id) for item in document.links],
    )
    connection.executemany(
        "INSERT OR REPLACE INTO semantic_ids VALUES (?, ?, ?, ?)",
        [(document.path, item.identifier, item.kind, item.statement) for item in document.semantic_ids],
    )


def refresh_index(connection: sqlite3.Connection, root: Path, files: dict[str, tuple[Path, os.stat_result]]) -> int:
    existing = {
        row["path"]: (row["size"], row["mtime_ns"], row["ctime_ns"])
        for row in connection.execute("SELECT path, size, mtime_ns, ctime_ns FROM documents")
    }
    removed = set(existing) - set(files)
    changed = [
        relative
        for relative, (_, stat) in files.items()
        if relative not in existing
        or existing[relative] != (stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
    ]
    parsed = [parse_document(files[relative][0], root, files[relative][1]) for relative in changed]
    if not removed and not parsed:
        return 0
    connection.execute("BEGIN IMMEDIATE")
    try:
        for relative in sorted(removed | set(changed)):
            connection.execute("DELETE FROM sections_fts WHERE path = ?", (relative,))
            connection.execute("DELETE FROM documents WHERE path = ?", (relative,))
        for document in parsed:
            insert_document(connection, document)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return len(removed) + len(parsed)


def release_cache_lock(connection: sqlite3.Connection) -> None:
    connection.rollback()
    connection.close()


def create_index_under_lock(
    path: Path,
    root: Path,
    files: dict[str, tuple[Path, os.stat_result]],
    *,
    force: bool,
) -> None:
    lock = acquire_cache_lock(path)
    try:
        if force or not path.is_file():
            create_index(path, root, files)
    finally:
        release_cache_lock(lock)


def index_metadata_is_current(connection: sqlite3.Connection, root: Path) -> bool:
    version = connection.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
    root_hash = connection.execute("SELECT value FROM meta WHERE key = 'root_hash'").fetchone()
    expected_root = hashlib.sha256(str(root).encode()).hexdigest()
    return bool(
        version is not None
        and version[0] == SCHEMA_VERSION
        and root_hash is not None
        and root_hash[0] == expected_root
    )


def rebuild_invalid_index(
    path: Path,
    root: Path,
    files: dict[str, tuple[Path, os.stat_result]],
) -> None:
    lock = acquire_cache_lock(path)
    connection: sqlite3.Connection | None = None
    try:
        try:
            connection = connect(path)
            if index_metadata_is_current(connection, root):
                return
        except sqlite3.Error:
            pass
        finally:
            if connection is not None:
                connection.close()
        create_index(path, root, files)
    finally:
        release_cache_lock(lock)


def ensure_index(root: Path, path: Path, rebuild: bool) -> tuple[sqlite3.Connection, int]:
    files = discover(root)
    if rebuild:
        create_index_under_lock(path, root, files, force=True)
    elif not path.is_file():
        create_index_under_lock(path, root, files, force=False)
    connection: sqlite3.Connection | None = None
    try:
        connection = connect(path)
        if not index_metadata_is_current(connection, root):
            connection.close()
            rebuild_invalid_index(path, root, files)
            connection = connect(path)
        connection.execute("PRAGMA journal_mode = WAL")
        changed = refresh_index(connection, root, files)
        return connection, changed
    except sqlite3.Error as error:
        if connection is not None:
            connection.close()
        if is_lock_error(error) or not is_rebuildable_error(error):
            raise AcceleratorUnavailable(f"cannot use derived index: {error}") from error
        try:
            rebuild_invalid_index(path, root, files)
            connection = connect(path)
            connection.execute("PRAGMA journal_mode = WAL")
            return connection, len(files)
        except (AcceleratorUnavailable, OSError, UnicodeError, sqlite3.Error) as rebuild_error:
            raise AcceleratorUnavailable(f"cannot refresh derived index: {rebuild_error}") from error
    except (OSError, UnicodeError) as error:
        if connection is not None:
            connection.close()
        raise AcceleratorUnavailable(f"cannot use derived index: {error}") from error


def fts_query(query: str, connection: sqlite3.Connection | None = None) -> str:
    raw_tokens = QUERY_TOKEN_RE.findall(query.casefold())[:32]
    tokens: list[str] = []
    for token in raw_tokens:
        if token not in tokens:
            tokens.append(token)
    if connection is not None and tokens:
        document_count = connection.execute("SELECT count(*) FROM documents").fetchone()[0]
        maximum_frequency = max(2, math.ceil(document_count * 0.25))
        phrases = list(dict.fromkeys(
            " ".join(raw_tokens[index:index + 2])
            for index in range(len(raw_tokens) - 1)
        ))
        matching_phrases = [
            phrase
            for phrase in phrases
            if 0 < connection.execute(
                "SELECT count(DISTINCT path) FROM sections_fts WHERE sections_fts MATCH ?",
                (f'"{phrase}"',),
            ).fetchone()[0] <= maximum_frequency
        ]
        frequencies = [
            (
                token,
                connection.execute(
                    "SELECT count(DISTINCT path) FROM sections_fts WHERE sections_fts MATCH ?",
                    (f'"{token.replace(chr(34), chr(34) * 2)}"',),
                ).fetchone()[0],
            )
            for token in tokens[:32]
        ]
        present = [(token, frequency) for token, frequency in frequencies if frequency]
        informative = [token for token, frequency in present if frequency <= maximum_frequency]
        tokens = informative or [
            token for token, _ in sorted(present, key=lambda item: (item[1], item[0]))[:8]
        ]
        clauses = [f'"{phrase}"' for phrase in matching_phrases[:12]]
        clauses.extend(
            f'"{token.replace(chr(34), chr(34) * 2)}"'
            for token in tokens[: 32 - len(clauses)]
        )
        if clauses:
            return " OR ".join(dict.fromkeys(clauses))
    if not tokens:
        raise AcceleratorUnavailable("query has no searchable terms")
    return " OR ".join(f'"{token.replace(chr(34), chr(34) * 2)}"' for token in tokens[:32])


def search(connection: sqlite3.Connection, query: str, limit: int, graph_depth: int) -> list[dict[str, object]]:
    candidates: dict[str, dict[str, object]] = {}

    def add(path: str, score: float, reason: str, title: str | None = None, summary: str | None = None, heading: str | None = None) -> None:
        item = candidates.setdefault(path, {"path": path, "score": 0.0, "reasons": [], "headings": []})
        item["score"] = max(float(item["score"]), score)
        if reason not in item["reasons"]:
            item["reasons"].append(reason)
        if heading and heading not in item["headings"]:
            item["headings"].append(heading)
        if title is not None:
            item["title"] = title
        if summary is not None:
            item["summary"] = summary

    normalized = query.strip().casefold()
    for row in connection.execute(
        "SELECT path, title, summary FROM documents WHERE lower(path) = ? OR lower(title) = ?",
        (normalized, normalized),
    ):
        add(row["path"], 100.0, "exact document match", row["title"], row["summary"])
    for token in QUERY_TOKEN_RE.findall(normalized):
        if not ID_QUERY_RE.fullmatch(token):
            continue
        for row in connection.execute(
            "SELECT d.path, d.title, d.summary FROM semantic_ids s JOIN documents d ON d.path = s.document_path WHERE lower(s.semantic_id) = ?",
            (token,),
        ):
            add(row["path"], 120.0, f"semantic ID {token}", row["title"], row["summary"])

    match_query = fts_query(query, connection)
    batch_size = max(limit * 10, 50)
    offset = 0
    document_ranks: dict[str, int] = {}
    while len(document_ranks) < limit:
        rows = connection.execute(
            "SELECT path, title, summary, heading, bm25(sections_fts, 0.0, 10.0, 5.0, 3.0, 1.0) AS rank "
            "FROM sections_fts WHERE sections_fts MATCH ? ORDER BY rank LIMIT ? OFFSET ?",
            (match_query, batch_size, offset),
        ).fetchall()
        for row in rows:
            document_rank = document_ranks.setdefault(row["path"], len(document_ranks))
            add(
                row["path"],
                60.0 / (document_rank + 1),
                "full-text match",
                row["title"],
                row["summary"],
                row["heading"],
            )
        if len(rows) < batch_size:
            break
        offset += batch_size

    frontier = sorted(candidates, key=lambda path: float(candidates[path]["score"]), reverse=True)[:limit]
    visited = set(frontier)
    for depth in range(graph_depth):
        next_frontier: list[str] = []
        for source in frontier:
            base = float(candidates[source]["score"])
            outgoing = connection.execute("SELECT target_path FROM links WHERE source_path = ?", (source,)).fetchall()
            incoming = connection.execute("SELECT source_path FROM links WHERE target_path = ?", (source,)).fetchall()
            for neighbor, direction in [(row[0], "linked from candidate") for row in outgoing] + [
                (row[0], "links to candidate") for row in incoming
            ]:
                document = connection.execute(
                    "SELECT title, summary FROM documents WHERE path = ?", (neighbor,)
                ).fetchone()
                if document is None:
                    continue
                add(neighbor, base * (0.25 ** (depth + 1)), direction, document["title"], document["summary"])
                if neighbor not in visited:
                    visited.add(neighbor)
                    next_frontier.append(neighbor)
        frontier = next_frontier

    ordered = sorted(candidates.values(), key=lambda item: (-float(item["score"]), str(item["path"])))[:limit]
    for item in ordered:
        item["score"] = round(float(item["score"]), 3)
        item["headings"] = item["headings"][:4]
        if len(str(item.get("summary", ""))) > 300:
            item["summary"] = str(item["summary"])[:297] + "..."
    return ordered


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spine_root", type=Path)
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--graph-depth", type=int, choices=(0, 1, 2), default=1)
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()

    root = args.spine_root.resolve()
    if not root.is_dir() or not (root / "README.md").is_file():
        print(json.dumps({"mode": "error", "reason": "SpecSpine root or README.md is missing"}))
        return 3
    if args.limit < 1 or args.limit > 50:
        print(json.dumps({"mode": "error", "reason": "limit must be between 1 and 50"}))
        return 3

    connection: sqlite3.Connection | None = None
    try:
        probe_fts5()
        index_path = cache_path(root)
        connection, changed = ensure_index(root, index_path, args.rebuild)
        candidates = search(connection, args.query, args.limit, args.graph_depth)
        count = connection.execute("SELECT count(*) FROM documents").fetchone()[0]
        print(json.dumps({"mode": "sqlite-fts5", "documents": count, "refreshed": changed, "candidates": candidates}, ensure_ascii=False))
        return 0 if candidates else FALLBACK_EXIT
    except AcceleratorUnavailable as error:
        print(json.dumps({"mode": "fallback", "reason": str(error)}, ensure_ascii=False))
        return FALLBACK_EXIT
    except Exception as error:
        print(json.dumps({"mode": "fallback", "reason": f"accelerator failed: {error}"}, ensure_ascii=False))
        return FALLBACK_EXIT
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
