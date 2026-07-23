#!/usr/bin/env python3
"""Find and return marked SpecSpine documents with batched SQLite FTS5 queries."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

try:
    import sqlite3
except ImportError as error:
    print(json.dumps({"schema_version": 2, "mode": "fallback"}))
    raise SystemExit(2) from error


SCHEMA_VERSION = "6"
FALLBACK_EXIT = 2
BUILD_LOCK_TIMEOUT_MS = 10_000
SQLITE_BUSY_TIMEOUT_MS = 10_000
DIRECT_LIMIT = 10
GRAPH_LIMIT = 2
GRAPH_DEPTH = 1
MAX_OUTPUT_BYTES = 128 * 1024
FENCE_RE = re.compile(r"^ {0,3}(?:>\s*)?(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*)|[ \t]*)$")
DEFINITION_RE = re.compile(r"^ {0,3}[-+*]\s+\*\*((?:DEC|CON|OBS|INF|OQ)-[a-z0-9]+(?:-[a-z0-9]+)*)\*\*\s+—\s+(.*)")
REFERENCE_DEFINITION_RE = re.compile(
    r'^ {0,3}\[([^\]]+)\]:\s*(?:<([^>]+)>|(\S+?))(?:\s+(?:"[^"]*"|\'[^\']*\'|\([^)]*\)))?\s*$'
)
ID_RE = re.compile(r"^(?:DEC|CON|OBS|INF|OQ)-[a-z0-9]+(?:-[a-z0-9]+)*$")
SECTION_KINDS = {
    "decisions": "DEC",
    "system-wide decisions": "DEC",
    "constraints": "CON",
    "system-wide constraints": "CON",
    "observed": "OBS",
    "inferred": "INF",
    "open questions": "OQ",
}


def load_ranking_module():
    """Load the sibling policy module under direct and diagnostic execution."""
    path = Path(__file__).with_name("ranking.py")
    name = f"{__name__}_ranking"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load ranking module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


try:
    RANKING = load_ranking_module()
except (ImportError, OSError) as error:
    print(json.dumps({"schema_version": 2, "mode": "fallback"}))
    raise SystemExit(2) from error
QUERY_TOKEN_RE = RANKING.QUERY_TOKEN_RE
ID_QUERY_RE = RANKING.ID_QUERY_RE


class AcceleratorUnavailable(RuntimeError):
    """The optional accelerator cannot be used; callers should traverse links."""

    def __init__(self, message: str, reason_code: str = "unexpected_error") -> None:
        super().__init__(message)
        self.reason_code = reason_code


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


@dataclass(frozen=True)
class SearchOutcome:
    exit_code: int
    mode: str
    direct_matches: tuple[dict[str, object], ...] = ()
    graph_neighbors: tuple[dict[str, object], ...] = ()
    documents: int | None = None
    refreshed: int | None = None
    index_state: str | None = None
    retrieval_strategy: str | None = None
    selection: dict[str, object] | None = None
    timings: dict[str, float] | None = None
    reason_code: str | None = None
    reason: str | None = None
    ranking_system: str = RANKING.RANKING_SYSTEM


@dataclass(frozen=True)
class SliceOutcome:
    identifier: str
    outcome: SearchOutcome


@dataclass(frozen=True)
class BatchSearchOutcome:
    exit_code: int
    mode: str
    ranking_system: str
    slices: tuple[SliceOutcome, ...] = ()
    documents: int | None = None
    refreshed: int | None = None
    index_state: str | None = None
    timings: dict[str, float] | None = None
    reason_code: str | None = None
    reason: str | None = None


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
            char = line[cursor]
            output.append(
                char
                if not delimiter or char.isalnum() or char in "_-."
                else " "
            )
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


def stat_signature(stat: os.stat_result) -> tuple[int, int, int]:
    return stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


def stable_read(path: Path, expected: os.stat_result) -> tuple[bytes, os.stat_result]:
    current = expected
    for _ in range(2):
        raw = path.read_bytes()
        observed = path.stat()
        if len(raw) == observed.st_size and stat_signature(current) == stat_signature(observed):
            return raw, observed
        current = observed
    raise AcceleratorUnavailable(
        f"source changed while it was being indexed: {path}",
        "source_changed_during_index",
    )


def parse_document(path: Path, root: Path, stat: os.stat_result) -> Document:
    raw, stat = stable_read(path, stat)
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
CREATE VIRTUAL TABLE documents_fts USING fts5(
    path UNINDEXED,
    title,
    summary,
    headings,
    body,
    tokenize = 'unicode61 remove_diacritics 2'
);
CREATE TABLE normalized_tokens (
    document_path TEXT NOT NULL REFERENCES documents(path) ON DELETE CASCADE,
    token TEXT NOT NULL,
    prefix TEXT NOT NULL,
    PRIMARY KEY(document_path, token)
);
CREATE INDEX normalized_token_idx ON normalized_tokens(token);
CREATE INDEX normalized_prefix_idx ON normalized_tokens(prefix);
CREATE TABLE unicode_runs (
    document_path TEXT NOT NULL REFERENCES documents(path) ON DELETE CASCADE,
    run TEXT NOT NULL,
    PRIMARY KEY(document_path, run)
);
CREATE TABLE unicode_ngrams (
    document_path TEXT NOT NULL REFERENCES documents(path) ON DELETE CASCADE,
    ngram TEXT NOT NULL,
    PRIMARY KEY(document_path, ngram)
);
CREATE INDEX unicode_ngram_idx ON unicode_ngrams(ngram);
"""


def cache_path(root: Path) -> Path:
    configured = os.environ.get("SPECSPINE_CACHE_DIR")
    base = Path(configured).expanduser() if configured else Path(tempfile.gettempdir()) / "specspine-cache"
    key = hashlib.sha256(str(root).encode("utf-8")).hexdigest()[:24]
    directory = base / key
    try:
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    except OSError as error:
        raise AcceleratorUnavailable(
            f"cannot create derived cache directory: {error}", "cache_unusable"
        ) from error
    return directory / f"index-v{SCHEMA_VERSION}.sqlite"


def connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path, timeout=SQLITE_BUSY_TIMEOUT_MS / 1000)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}")
    return connection


def acquire_cache_lock(index_path: Path) -> tuple[sqlite3.Connection, float]:
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
        started = time.perf_counter()
        connection.execute("BEGIN IMMEDIATE")
        return connection, time.perf_counter() - started
    except (OSError, sqlite3.Error) as error:
        if connection is not None:
            connection.close()
        raise AcceleratorUnavailable(
            f"derived index is busy or cannot be locked: {error}", "lock_timeout"
        ) from error


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
        raise AcceleratorUnavailable(
            f"SQLite FTS5 is unavailable: {error}", "fts5_unavailable"
        ) from error
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
            raise AcceleratorUnavailable(
                "new index failed SQLite quick_check", "corrupt_index"
            )
        connection.close()
        connection = None
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    except (OSError, UnicodeError, sqlite3.Error) as error:
        raise AcceleratorUnavailable(
            f"cannot build derived index: {error}", "cache_unusable"
        ) from error
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
    connection.execute(
        "INSERT INTO documents_fts(path, title, summary, headings, body) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            document.path,
            document.title,
            document.summary,
            "\n".join(section.heading for section in document.sections),
            "\n".join(section.body for section in document.sections),
        ),
    )
    if document.path != "README.md":
        searchable = "\n".join((
            document.title,
            document.summary,
            *(section.heading for section in document.sections),
            *(section.body for section in document.sections),
        ))
        tokens, unicode_runs, unicode_ngrams = RANKING.normalized_index_terms(searchable)
        connection.executemany(
            "INSERT INTO normalized_tokens(document_path, token, prefix) "
            "VALUES (?, ?, ?)",
            (
                (
                    document.path,
                    token,
                    RANKING.normalized_prefix(token),
                )
                for token in tokens
            ),
        )
        connection.executemany(
            "INSERT INTO unicode_runs(document_path, run) VALUES (?, ?)",
            ((document.path, run) for run in unicode_runs),
        )
        connection.executemany(
            "INSERT INTO unicode_ngrams(document_path, ngram) VALUES (?, ?)",
            ((document.path, ngram) for ngram in unicode_ngrams),
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
            connection.execute("DELETE FROM documents_fts WHERE path = ?", (relative,))
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
) -> tuple[str, float, float]:
    lock, wait_seconds = acquire_cache_lock(path)
    build_seconds = 0.0
    try:
        if force or not path.is_file():
            started = time.perf_counter()
            create_index(path, root, files)
            build_seconds = time.perf_counter() - started
            return ("rebuild" if force else "cold_build", wait_seconds, build_seconds)
        return "waited_for_builder", wait_seconds, build_seconds
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
) -> tuple[str, float, float]:
    lock, wait_seconds = acquire_cache_lock(path)
    connection: sqlite3.Connection | None = None
    build_seconds = 0.0
    try:
        try:
            connection = connect(path)
            if index_metadata_is_current(connection, root):
                return "waited_for_builder", wait_seconds, build_seconds
        except sqlite3.Error:
            pass
        finally:
            if connection is not None:
                connection.close()
        started = time.perf_counter()
        create_index(path, root, files)
        build_seconds = time.perf_counter() - started
        return "rebuild", wait_seconds, build_seconds
    finally:
        release_cache_lock(lock)


def ensure_index(
    root: Path, path: Path, rebuild: bool
) -> tuple[sqlite3.Connection, int, dict[str, object]]:
    discovery_started = time.perf_counter()
    files = discover(root)
    discovery_seconds = time.perf_counter() - discovery_started
    index_state = "warm"
    lock_wait_seconds = 0.0
    build_seconds = 0.0
    if rebuild:
        index_state, lock_wait_seconds, build_seconds = create_index_under_lock(
            path, root, files, force=True
        )
    elif not path.is_file():
        index_state, lock_wait_seconds, build_seconds = create_index_under_lock(
            path, root, files, force=False
        )
    connection: sqlite3.Connection | None = None
    try:
        connection = connect(path)
        if not index_metadata_is_current(connection, root):
            connection.close()
            index_state, waited, built = rebuild_invalid_index(path, root, files)
            lock_wait_seconds += waited
            build_seconds += built
            connection = connect(path)
        connection.execute("PRAGMA journal_mode = WAL")
        refresh_started = time.perf_counter()
        changed = refresh_index(connection, root, files)
        refresh_seconds = time.perf_counter() - refresh_started
        if changed and index_state == "warm":
            index_state = "incremental_refresh"
        return connection, changed, {
            "index_state": index_state,
            "discovery_seconds": discovery_seconds,
            "lock_wait_seconds": lock_wait_seconds,
            "build_seconds": build_seconds,
            "refresh_seconds": refresh_seconds,
        }
    except sqlite3.Error as error:
        if connection is not None:
            connection.close()
        if is_lock_error(error) or not is_rebuildable_error(error):
            reason_code = "lock_timeout" if is_lock_error(error) else "cache_unusable"
            raise AcceleratorUnavailable(
                f"cannot use derived index: {error}", reason_code
            ) from error
        try:
            index_state, waited, built = rebuild_invalid_index(path, root, files)
            lock_wait_seconds += waited
            build_seconds += built
            connection = connect(path)
            connection.execute("PRAGMA journal_mode = WAL")
            return connection, len(files), {
                "index_state": index_state,
                "discovery_seconds": discovery_seconds,
                "lock_wait_seconds": lock_wait_seconds,
                "build_seconds": build_seconds,
                "refresh_seconds": 0.0,
            }
        except (AcceleratorUnavailable, OSError, UnicodeError, sqlite3.Error) as rebuild_error:
            raise AcceleratorUnavailable(
                f"cannot refresh derived index: {rebuild_error}", "corrupt_index"
            ) from error
    except (OSError, UnicodeError) as error:
        if connection is not None:
            connection.close()
        raise AcceleratorUnavailable(
            f"cannot use derived index: {error}", "cache_unusable"
        ) from error


def search_normalized(
    connection: sqlite3.Connection,
    query: object,
    limit: int,
    graph_depth: int,
    graph_limit: int,
) -> tuple[list[dict[str, object]], list[dict[str, object]], str, dict[str, object]]:
    candidates: dict[str, dict[str, object]] = {}

    def add(
        path: str,
        score: float,
        origin: str,
        title: str | None = None,
        heading: str | None = None,
        signals: dict[str, object] | None = None,
    ) -> None:
        item = candidates.setdefault(
            path,
            {
                "path": path,
                "score": 0.0,
                "_scores": {},
                "origins": [],
                "headings": [],
                "signals": {"graph_support": 0},
            },
        )
        scores = item["_scores"]
        assert isinstance(scores, dict)
        scores[origin] = max(float(scores.get(origin, 0.0)), score)
        item["score"] = sum(float(value) for value in scores.values())
        if origin not in item["origins"]:
            item["origins"].append(origin)
        if title is not None:
            item["title"] = title
        if heading and heading not in item["headings"]:
            item["headings"].append(heading)
        if signals:
            stored = item["signals"]
            assert isinstance(stored, dict)
            for key, value in signals.items():
                if key == "graph_support":
                    stored[key] = int(stored.get(key) or 0) + int(value)
                else:
                    stored[key] = value

    all_groups = (*query.must, *query.should)
    all_terms = tuple(dict.fromkeys(
        term for group in all_groups for term in group
    ))
    documents = {
        str(row["path"]): str(row["title"])
        for row in connection.execute(
            "SELECT path, title FROM documents WHERE path != 'README.md'"
        )
    }
    paths_by_identity: dict[str, list[str]] = {}
    titles_by_identity: dict[str, list[str]] = {}
    for path, title in documents.items():
        paths_by_identity.setdefault(path.casefold(), []).append(path)
        titles_by_identity.setdefault(title.casefold(), []).append(path)
    semantic_paths: dict[str, list[str]] = {}
    for row in connection.execute(
        "SELECT document_path, semantic_id FROM semantic_ids "
        "WHERE document_path != 'README.md'"
    ):
        semantic_paths.setdefault(
            str(row["semantic_id"]).casefold(), []
        ).append(str(row["document_path"]))

    exact_matches: dict[str, dict[str, RANKING.GroupMatch]] = {}
    for term in all_terms:
        matches: dict[str, RANKING.GroupMatch] = {}
        normalized_path = term.removeprefix("./").replace("\\", "/")
        for path in paths_by_identity.get(normalized_path.casefold(), ()):
            matches[path] = RANKING.GroupMatch(
                RANKING.EXACT_PATH_SCORE, term, "exact_path"
            )
        for path in titles_by_identity.get(term.casefold(), ()):
            candidate = RANKING.GroupMatch(
                RANKING.EXACT_MATCH_SCORE, term, "exact_title"
            )
            stored = matches.get(path)
            if stored is None or candidate.score > stored.score:
                matches[path] = candidate
        for path in semantic_paths.get(term.casefold(), ()):
            candidate = RANKING.GroupMatch(
                RANKING.SEMANTIC_ID_SCORE, term, "semantic_id"
            )
            stored = matches.get(path)
            if stored is None or candidate.score > stored.score:
                matches[path] = candidate
        exact_matches[term] = matches

    term_qualities = RANKING.strict_term_qualities(connection, all_terms)
    normalized_matches = RANKING.normalized_term_matches(
        connection,
        all_terms,
        term_qualities,
    )
    must_matches = tuple(
        RANKING.group_matches(
            group,
            term_qualities,
            exact_matches,
            normalized_matches,
        )
        for group in query.must
    )
    should_matches = tuple(
        RANKING.group_matches(
            group,
            term_qualities,
            exact_matches,
            normalized_matches,
        )
        for group in query.should
    )
    candidate_paths = set(must_matches[0])
    for group_matches in must_matches[1:]:
        candidate_paths.intersection_update(group_matches)
    joint_document_frequency = len(candidate_paths)

    for path in sorted(candidate_paths):
        matched_must = tuple(group[path] for group in must_matches)
        matched_should = tuple(
            group[path] for group in should_matches if path in group
        )
        should_quality = 0.5 * sum(
            min(item.score, 4.0) for item in matched_should
        )
        quality = sum(item.score for item in matched_must) + should_quality
        exact_origins = sorted({
            item.origin
            for item in (*matched_must, *matched_should)
            if item.origin in {"exact_path", "exact_title", "semantic_id"}
        })
        normalized_origins = sorted({
            item.origin
            for item in (*matched_must, *matched_should)
            if item.origin in {"morphology", "normalized_tokens", "unicode_substring"}
        })
        add(
            path,
            quality,
            "facet_score",
            documents[path],
            signals={
                "must_groups": len(query.must),
                "matched_must_groups": len(matched_must),
                "matched_must_terms": [item.term for item in matched_must],
                "should_groups": len(query.should),
                "matched_should_groups": len(matched_should),
                "matched_should_terms": [item.term for item in matched_should],
                "match_origins": [
                    item.origin for item in (*matched_must, *matched_should)
                ],
                "exact_match_origins": exact_origins,
                "normalized_match_origins": normalized_origins,
                "joint_document_frequency": joint_document_frequency,
                "ranking_quality": quality,
            },
        )
    RANKING.normalize_scores(list(candidates.values()))

    routing_tokens = tuple(dict.fromkeys(
        part
        for group in all_groups
        for term in group
        for token in QUERY_TOKEN_RE.findall(term)
        for part in (token, *token.split("-"))
    ))

    def path_matches(path: str, clause: str) -> bool:
        return bool(connection.execute(
            "SELECT 1 FROM sections_fts "
            "WHERE path = ? AND sections_fts MATCH ? LIMIT 1",
            (path, RANKING.quote_fts_phrase(clause)),
        ).fetchone())

    direct_paths = set(candidates)
    preliminary_direct = RANKING.select_direct(
        RANKING.rank_direct(candidates.values()),
        limit=limit,
        strong_match=False,
    )
    frontier = [str(item["path"]) for item in preliminary_direct]
    visited = set(frontier)
    graph_candidates: dict[str, dict[str, object]] = {}
    for depth in range(graph_depth):
        next_frontier: list[str] = []
        for source in frontier:
            source_candidate = candidates.get(source) or graph_candidates[source]
            root_path = (
                source
                if source in candidates
                else str(source_candidate.get("_root_path", source))
            )
            base = float(source_candidate["score"])
            outgoing = connection.execute(
                "SELECT target_path, label, semantic_id FROM links "
                "WHERE source_path = ?",
                (source,),
            ).fetchall()
            incoming = connection.execute(
                "SELECT source_path, label, semantic_id FROM links "
                "WHERE target_path = ?",
                (source,),
            ).fetchall()
            transitions = [
                (row[0], "outgoing", row[1], row[2]) for row in outgoing
            ] + [
                (row[0], "incoming", row[1], row[2]) for row in incoming
            ]
            for neighbor, direction, edge_label, semantic_id in transitions:
                if neighbor == "README.md":
                    continue
                document = connection.execute(
                    "SELECT title FROM documents WHERE path = ?", (neighbor,)
                ).fetchone()
                if document is None:
                    continue
                origin = f"graph_{direction}"
                score = RANKING.transition_score(base)
                if neighbor in direct_paths:
                    add(
                        neighbor,
                        RANKING.direct_graph_bonus(base),
                        origin,
                        document["title"],
                        signals={"graph_support": 1},
                    )
                else:
                    graph = graph_candidates.setdefault(
                        neighbor,
                        {
                            "path": neighbor,
                            "score": 0.0,
                            "_scores": {},
                            "origins": [],
                            "_transitions": {},
                            "_root_path": root_path,
                            "_relevance": RANKING.graph_relevance(
                                neighbor,
                                str(document["title"]),
                                routing_tokens,
                                path_matches,
                                strong_match=False,
                            ),
                            "title": document["title"],
                        },
                    )
                    scores = graph["_scores"]
                    assert isinstance(scores, dict)
                    signal = f"{source}:{origin}"
                    scores[signal] = max(float(scores.get(signal, 0.0)), score)
                    strongest = max(float(value) for value in scores.values())
                    graph["score"] = RANKING.combined_graph_score(scores.values())
                    if origin not in graph["origins"]:
                        graph["origins"].append(origin)
                    stored_transitions = graph["_transitions"]
                    assert isinstance(stored_transitions, dict)
                    transition_key = (
                        root_path,
                        source,
                        direction,
                        edge_label,
                        semantic_id,
                        depth + 1,
                    )
                    stored_transitions[transition_key] = max(
                        score, float(stored_transitions.get(transition_key, 0.0))
                    )
                    if score >= strongest:
                        graph["_root_path"] = root_path
                if neighbor not in visited:
                    visited.add(neighbor)
                    next_frontier.append(neighbor)
        frontier = next_frontier

    ranked_direct = RANKING.rank_direct(candidates.values())
    direct = RANKING.select_direct(
        ranked_direct,
        limit=limit,
        strong_match=False,
    )
    direct_cutoff_score = RANKING.direct_cutoff(ranked_direct, False)
    returned_direct_paths = {str(item["path"]) for item in direct}
    usable_graph: list[dict[str, object]] = []
    for item in graph_candidates.values():
        stored_transitions = item["_transitions"]
        assert isinstance(stored_transitions, dict)
        retained = {
            key: value
            for key, value in stored_transitions.items()
            if key[0] in returned_direct_paths
        }
        if retained:
            item["_transitions"] = retained
            item["score"] = RANKING.combined_graph_score(retained.values())
            usable_graph.append(item)
    ranked_graph = RANKING.rank_graph(usable_graph)
    graph, graph_threshold = RANKING.select_graph(
        ranked_graph,
        graph_limit=graph_limit,
        direct_count=len(direct),
    )
    section_query = " OR ".join(
        RANKING.group_expression(group) for group in all_groups
    )
    for item in direct:
        item["headings"] = [
            row[0]
            for row in connection.execute(
                f"SELECT heading FROM sections_fts "
                f"WHERE path = ? AND sections_fts MATCH ? "
                f"ORDER BY {RANKING.BM25_EXPRESSION} LIMIT 4",
                (item["path"], section_query),
            )
        ]
        item.pop("_scores", None)
        item["score"] = round(float(item["score"]), 6)
        item["headings"] = item["headings"][:4]
        signals = item["signals"]
        assert isinstance(signals, dict)
        item["signals"] = {
            key: round(value, 9) if isinstance(value, float) else value
            for key, value in signals.items()
            if value not in (False, None, 0, [], ())
        }
    for item in graph:
        item.pop("_scores", None)
        item.pop("_root_path", None)
        item["relevance"] = item.pop("_relevance", 0)
        stored_transitions = item.pop("_transitions", {})
        assert isinstance(stored_transitions, dict)
        item["transitions"] = [
            {
                "root_path": key[0],
                "source_path": key[1],
                "direction": key[2],
                "edge_label": key[3],
                **({"semantic_id": key[4]} if key[4] else {}),
                "depth": key[5],
                "score": round(float(value), 3),
            }
            for key, value in sorted(
                stored_transitions.items(),
                key=lambda entry: (-float(entry[1]), entry[0]),
            )[:3]
        ]
        item["score"] = round(float(item["score"]), 3)
    fallback_origins = {"morphology", "normalized_tokens", "unicode_substring"}
    normalized_direct = sum(
        any(
            origin in fallback_origins
            for origin in item.get("signals", {}).get("match_origins", ())
        )
        for item in direct
    )
    selection = {
        "ranking_system": RANKING.RANKING_SYSTEM,
        "match_tier": "normalized" if normalized_direct else "strict",
        "joint_document_frequency": joint_document_frequency,
        "term_queries": len(all_terms),
        "normalized_direct": normalized_direct,
        "direct_considered": len(ranked_direct),
        "direct_returned": len(direct),
        "direct_cutoff_score": (
            round(direct_cutoff_score, 6)
            if direct_cutoff_score is not None
            else None
        ),
        "graph_considered": len(ranked_graph),
        "graph_returned": len(graph),
        "graph_cutoff_score": (
            round(graph_threshold, 3) if graph_threshold is not None else None
        ),
    }
    return direct, graph, RANKING.RANKING_SYSTEM, selection


def execute_searches(
    spine_root: Path,
    query_slices: tuple[object, ...],
    *,
    limit: int = DIRECT_LIMIT,
    graph_limit: int = GRAPH_LIMIT,
    graph_depth: int = GRAPH_DEPTH,
    rebuild: bool = False,
) -> BatchSearchOutcome:
    total_started = time.perf_counter()
    root = spine_root.resolve()
    if not root.is_dir() or not (root / "README.md").is_file():
        return BatchSearchOutcome(
            3,
            "error",
            RANKING.RANKING_SYSTEM,
            reason_code="invalid_root",
            reason="SpecSpine root or README.md is missing",
            timings={"total_seconds": time.perf_counter() - total_started},
        )
    if limit < 1 or limit > 50:
        return BatchSearchOutcome(
            3,
            "error",
            RANKING.RANKING_SYSTEM,
            reason_code="invalid_limit",
            reason="limit must be between 1 and 50",
            timings={"total_seconds": time.perf_counter() - total_started},
        )
    if graph_limit < 0 or graph_limit > 50:
        return BatchSearchOutcome(
            3,
            "error",
            RANKING.RANKING_SYSTEM,
            reason_code="invalid_graph_limit",
            reason="graph-limit must be between 0 and 50",
            timings={"total_seconds": time.perf_counter() - total_started},
        )
    if graph_depth not in {0, 1, 2}:
        return BatchSearchOutcome(
            3,
            "error",
            RANKING.RANKING_SYSTEM,
            reason_code="invalid_graph_depth",
            reason="graph-depth must be 0, 1, or 2",
            timings={"total_seconds": time.perf_counter() - total_started},
        )

    connection: sqlite3.Connection | None = None
    try:
        probe_fts5()
        index_path = cache_path(root)
        connection, changed, timings = ensure_index(root, index_path, rebuild)
        index_state = str(timings.pop("index_state"))
        document_count = connection.execute(
            "SELECT count(*) FROM documents"
        ).fetchone()[0]
        slices: list[SliceOutcome] = []
        search_seconds = 0.0
        for query_slice in query_slices:
            search_started = time.perf_counter()
            direct, graph, strategy, selection = search_normalized(
                connection,
                query_slice,
                limit,
                graph_depth,
                graph_limit,
            )
            elapsed = time.perf_counter() - search_started
            search_seconds += elapsed
            slices.append(SliceOutcome(
                query_slice.identifier,
                SearchOutcome(
                    0 if direct else FALLBACK_EXIT,
                    "sqlite-fts5",
                    tuple(direct),
                    tuple(graph),
                    document_count,
                    changed,
                    index_state,
                    strategy,
                    selection,
                    {"search_seconds": elapsed},
                    ranking_system=RANKING.RANKING_SYSTEM,
                ),
            ))
        timings["search_seconds"] = search_seconds
        timings["total_seconds"] = time.perf_counter() - total_started
        return BatchSearchOutcome(
            0,
            "sqlite-fts5",
            RANKING.RANKING_SYSTEM,
            tuple(slices),
            document_count,
            changed,
            index_state,
            {key: float(value) for key, value in timings.items()},
        )
    except RANKING.InvalidRankingQuery as error:
        return BatchSearchOutcome(
            FALLBACK_EXIT,
            "fallback",
            RANKING.RANKING_SYSTEM,
            reason_code="invalid_query",
            reason=str(error),
            timings={"total_seconds": time.perf_counter() - total_started},
        )
    except AcceleratorUnavailable as error:
        return BatchSearchOutcome(
            FALLBACK_EXIT,
            "fallback",
            RANKING.RANKING_SYSTEM,
            reason_code=error.reason_code,
            reason=str(error),
            timings={"total_seconds": time.perf_counter() - total_started},
        )
    except Exception as error:
        return BatchSearchOutcome(
            FALLBACK_EXIT,
            "fallback",
            RANKING.RANKING_SYSTEM,
            reason_code="unexpected_error",
            reason=f"accelerator failed: {error}",
            timings={"total_seconds": time.perf_counter() - total_started},
        )
    finally:
        if connection is not None:
            connection.close()


def protocol_marker(name: str, **metadata: object) -> str:
    encoded = json.dumps(metadata, ensure_ascii=False, separators=(",", ":"))
    return f"<<<SPECSPINE_{name} {encoded}>>>"


def selected_documents(
    outcome: SearchOutcome,
) -> tuple[tuple[str, str, dict[str, object]], ...]:
    selected: list[tuple[str, str, dict[str, object]]] = []
    seen: set[str] = set()
    for origin, items in (
        ("direct", outcome.direct_matches),
        ("graph", outcome.graph_neighbors),
    ):
        for item in items:
            path = str(item["path"])
            if path not in seen:
                seen.add(path)
                selected.append((path, origin, item))
    return tuple(selected)


def read_selected_document(root: Path, relative: str) -> str:
    path = (root / relative).resolve()
    if not within(path, root) or path.suffix.casefold() != ".md" or not path.is_file():
        raise AcceleratorUnavailable(
            f"selected document is unavailable: {relative}",
            reason_code="selected_document_unavailable",
        )
    return path.read_text(encoding="utf-8")


def render_batch_output(
    spine_root: Path,
    outcome: BatchSearchOutcome,
    *,
    max_output_bytes: int = MAX_OUTPUT_BYTES,
) -> str:
    slice_lines: list[str] = []
    selected_paths: list[str] = []
    seen_paths: set[str] = set()
    root_fallback = False
    if outcome.mode == "sqlite-fts5":
        for item in outcome.slices:
            selection = item.outcome.selection or {}
            status = "matched" if item.outcome.direct_matches else "no_match"
            slice_metadata: dict[str, object] = {
                "id": item.identifier,
                "status": status,
            }
            if selection.get("match_tier") is not None:
                slice_metadata["match_tier"] = selection["match_tier"]
            if selection.get("joint_document_frequency") is not None:
                slice_metadata["joint_df"] = selection[
                    "joint_document_frequency"
                ]
            slice_lines.append(protocol_marker("SLICE", **slice_metadata))
            if status == "no_match":
                root_fallback = True
                slice_lines.append(protocol_marker(
                    "HIT",
                    path="README.md",
                    origin="root_fallback",
                ))
            for relative, origin, candidate in selected_documents(item.outcome):
                metadata: dict[str, object] = {
                    "path": relative,
                    "origin": origin,
                }
                signals = candidate.get("signals")
                if origin == "direct" and isinstance(signals, dict):
                    for key in (
                        "matched_must_terms",
                        "matched_should_terms",
                        "exact_match_origins",
                    ):
                        if signals.get(key):
                            metadata[key] = signals[key]
                slice_lines.append(protocol_marker("HIT", **metadata))
                if relative not in seen_paths:
                    seen_paths.add(relative)
                    selected_paths.append(relative)
            slice_lines.append("<<<SPECSPINE_END_SLICE>>>")
    elif outcome.mode == "fallback":
        root_fallback = True

    root = spine_root.resolve()
    if (
        root_fallback
        and (root / "README.md").is_file()
        and "README.md" not in seen_paths
    ):
        seen_paths.add("README.md")
        selected_paths.append("README.md")

    result_metadata: dict[str, object] = {
        "version": 2,
        "mode": outcome.mode,
        "ranking": outcome.ranking_system,
        "graph_depth": GRAPH_DEPTH,
        "graph_limit": GRAPH_LIMIT,
    }
    if root_fallback and "README.md" in seen_paths:
        result_metadata["root_fallback"] = "README.md"
    if outcome.reason_code:
        result_metadata["reason"] = outcome.reason_code
    provisional_header = protocol_marker(
        "RESULT", **result_metadata, truncated=False
    )
    base_lines = [provisional_header, *slice_lines, "<<<SPECSPINE_END_RESULT>>>"]
    remaining = max_output_bytes - len(
        ("\n".join(base_lines) + "\n").encode("utf-8")
    )
    document_lines: list[str] = []
    truncated = False
    for relative in selected_paths:
        content = read_selected_document(root, relative).rstrip("\n")
        block = "\n".join((
            protocol_marker(
                "DOCUMENT",
                path=relative,
                utf8_bytes=len(content.encode("utf-8")),
            ),
            content,
            "<<<SPECSPINE_END_DOCUMENT>>>",
        ))
        block_size = len((block + "\n").encode("utf-8"))
        if block_size <= remaining:
            document_lines.append(block)
            remaining -= block_size
            continue
        truncated = True
        omitted = protocol_marker(
            "DOCUMENT_OMITTED", path=relative, reason="output_budget"
        )
        omitted_size = len((omitted + "\n").encode("utf-8"))
        if omitted_size <= remaining:
            document_lines.append(omitted)
            remaining -= omitted_size

    result_metadata["truncated"] = truncated
    lines = [
        protocol_marker("RESULT", **result_metadata),
        *slice_lines,
        *document_lines,
        "<<<SPECSPINE_END_RESULT>>>",
    ]
    rendered = "\n".join(lines) + "\n"
    if len(rendered.encode("utf-8")) <= max_output_bytes:
        return rendered
    minimal_metadata = {
        "version": 2,
        "mode": outcome.mode,
        "ranking": outcome.ranking_system,
        "graph_depth": GRAPH_DEPTH,
        "graph_limit": GRAPH_LIMIT,
        "reason": "output_metadata_budget",
        "truncated": True,
    }
    return "\n".join((
        protocol_marker("RESULT", **minimal_metadata),
        "<<<SPECSPINE_END_RESULT>>>",
        "",
    ))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spine_root", type=Path)
    parser.add_argument("--queries-json", required=True)
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    try:
        query_slices = RANKING.parse_query_slices(args.queries_json)
    except RANKING.InvalidRankingQuery:
        batch = BatchSearchOutcome(
            FALLBACK_EXIT,
            "fallback",
            RANKING.RANKING_SYSTEM,
            reason_code="invalid_query",
        )
        print(
            render_batch_output(args.spine_root, batch),
            end="",
        )
        return FALLBACK_EXIT
    batch = execute_searches(
        args.spine_root,
        query_slices,
        rebuild=args.rebuild,
    )
    try:
        output = render_batch_output(args.spine_root, batch)
    except AcceleratorUnavailable:
        batch = BatchSearchOutcome(
            FALLBACK_EXIT,
            "fallback",
            RANKING.RANKING_SYSTEM,
            reason_code="selected_document_unavailable",
        )
        output = render_batch_output(args.spine_root, batch)
    print(output, end="")
    return batch.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
