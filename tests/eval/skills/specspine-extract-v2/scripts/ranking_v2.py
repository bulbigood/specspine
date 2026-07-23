"""Query planning and ranking policy for the SpecSpine FTS accelerator."""

from __future__ import annotations

import json
import math
import re
import sqlite3
from collections.abc import Callable, Iterable
from dataclasses import dataclass


QUERY_TOKEN_RE = re.compile(r"[^\W_]+(?:-[^\W_]+)*", re.UNICODE)
ID_QUERY_RE = re.compile(
    r"^(?:DEC|CON|OBS|INF|OQ)-[a-z0-9]+(?:-[a-z0-9]+)*$", re.IGNORECASE
)
LEGACY = "legacy"
FACETED_BM25 = "faceted-bm25"
RANKING_SYSTEMS = (LEGACY, FACETED_BM25)
DEFAULT_RANKING_SYSTEM = LEGACY
BM25_EXPRESSION = "bm25(sections_fts, 0.0, 10.0, 5.0, 3.0, 1.0)"
DOCUMENT_BM25_EXPRESSION = "bm25(documents_fts, 0.0, 10.0, 5.0, 3.0, 1.0)"
EXACT_MATCH_SCORE = 100.0
EXACT_PATH_SCORE = 110.0
SEMANTIC_ID_SCORE = 120.0
RARE_TOKEN_MAX_DOCUMENTS = 1
MAX_SLICES = 8
MAX_GROUPS = 8
MAX_SYNONYMS = 8
MAX_TERM_LENGTH = 120


class InvalidRankingQuery(ValueError):
    """The query has no terms that can be routed through FTS."""


@dataclass(frozen=True)
class QuerySlice:
    identifier: str
    must: tuple[tuple[str, ...], ...]
    should: tuple[tuple[str, ...], ...] = ()

    def legacy_query(self) -> str:
        return " ".join(dict.fromkeys(
            term for group in (*self.must, *self.should) for term in group
        ))


@dataclass(frozen=True)
class GroupMatch:
    score: float
    term: str
    origin: str


def validate_ranking_system(value: str) -> str:
    if value not in RANKING_SYSTEMS:
        raise InvalidRankingQuery(
            f"ranking system must be one of: {', '.join(RANKING_SYSTEMS)}"
        )
    return value


def normalize_group(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value or len(value) > MAX_SYNONYMS:
        raise InvalidRankingQuery(
            f"{field} groups must contain 1 to {MAX_SYNONYMS} terms"
        )
    terms: list[str] = []
    for raw in value:
        if not isinstance(raw, str):
            raise InvalidRankingQuery(f"{field} terms must be strings")
        term = " ".join(raw.split()).casefold()
        if (
            not term
            or len(term) > MAX_TERM_LENGTH
            or not QUERY_TOKEN_RE.search(term)
        ):
            raise InvalidRankingQuery(f"{field} contains an invalid term")
        if term not in terms:
            terms.append(term)
    return tuple(terms)


def normalize_groups(
    value: object, field: str, *, required: bool
) -> tuple[tuple[str, ...], ...]:
    if value is None and not required:
        return ()
    if not isinstance(value, list) or (required and not value) or len(value) > MAX_GROUPS:
        minimum = 1 if required else 0
        raise InvalidRankingQuery(
            f"{field} must contain {minimum} to {MAX_GROUPS} groups"
        )
    return tuple(normalize_group(group, field) for group in value)


def parse_query_slices(raw: str) -> tuple[QuerySlice, ...]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise InvalidRankingQuery(f"queries-json is malformed: {error.msg}") from error
    if not isinstance(payload, list) or not payload or len(payload) > MAX_SLICES:
        raise InvalidRankingQuery(
            f"queries-json must contain 1 to {MAX_SLICES} slices"
        )
    slices: list[QuerySlice] = []
    identifiers: set[str] = set()
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise InvalidRankingQuery("each query slice must be an object")
        identifier = item.get("id", f"slice-{index + 1}")
        if (
            not isinstance(identifier, str)
            or not identifier.strip()
            or len(identifier) > 64
        ):
            raise InvalidRankingQuery("slice ids must be unique non-empty strings")
        identifier = identifier.strip()
        if identifier in identifiers:
            raise InvalidRankingQuery("slice ids must be unique non-empty strings")
        unknown = set(item) - {"id", "must", "should"}
        if unknown:
            raise InvalidRankingQuery(
                f"unsupported query slice fields: {', '.join(sorted(unknown))}"
            )
        identifiers.add(identifier)
        slices.append(QuerySlice(
            identifier,
            normalize_groups(item.get("must"), "must", required=True),
            normalize_groups(item.get("should"), "should", required=False),
        ))
    return tuple(slices)


def plain_query_slice(query: str, identifier: str = "query") -> QuerySlice:
    terms = tuple(dict.fromkeys(QUERY_TOKEN_RE.findall(query.casefold())[:32]))
    if not terms:
        raise InvalidRankingQuery("query has no searchable terms")
    return QuerySlice(identifier, tuple((term,) for term in terms))


def quote_fts_phrase(value: str) -> str:
    return f'"{value.replace(chr(34), chr(34) * 2)}"'


def group_expression(group: tuple[str, ...]) -> str:
    clauses = " OR ".join(quote_fts_phrase(term) for term in group)
    return f"({clauses})"


def faceted_match_query(query: QuerySlice) -> str:
    return " AND ".join(group_expression(group) for group in query.must)


def fts_plan(
    query: str, connection: sqlite3.Connection | None = None
) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    raw_tokens = QUERY_TOKEN_RE.findall(query.casefold())[:32]
    tokens = list(dict.fromkeys(raw_tokens))
    fallback_tokens = tuple(tokens)
    if connection is not None and tokens:
        document_count = connection.execute(
            "SELECT count(*) FROM documents"
        ).fetchone()[0]
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
        informative = [
            token for token, frequency in present if frequency <= maximum_frequency
        ]
        tokens = informative or [
            token for token, _ in sorted(present, key=lambda item: (item[1], item[0]))[:8]
        ]
        clauses = [f'"{phrase}"' for phrase in matching_phrases[:12]]
        clauses.extend(
            f'"{token.replace(chr(34), chr(34) * 2)}"'
            for token in tokens[: 32 - len(clauses)]
        )
        if clauses:
            return (
                " OR ".join(dict.fromkeys(clauses)),
                tuple(tokens[:32]),
                tuple(matching_phrases[:12]),
            )
    if not fallback_tokens:
        raise InvalidRankingQuery("query has no searchable terms")
    return (
        " OR ".join(
            f'"{token.replace(chr(34), chr(34) * 2)}"'
            for token in fallback_tokens
        ),
        fallback_tokens,
        (),
    )


def fts_query(query: str, connection: sqlite3.Connection | None = None) -> str:
    return fts_plan(query, connection)[0]


def routing_stem(token: str) -> str:
    """Normalize common English inflections for metadata reranking only."""
    value = token.casefold()
    if len(value) > 4 and value.endswith("ies"):
        return value[:-3] + "y"
    if len(value) > 4 and value.endswith("ing"):
        value = value[:-3]
        return value[:-1] if len(value) > 2 and value[-1:] == value[-2:-1] else value
    if len(value) > 3 and value.endswith("ed"):
        return value[:-2]
    if len(value) > 3 and value.endswith("s") and not value.endswith("ss"):
        return value[:-1]
    return value


def direct_fts_score(
    document_rank: int,
    query_tokens: int,
    token_hits: int,
    phrase_hits: int,
    metadata_hits: int,
) -> float:
    rank_score = 40.0 / math.sqrt(document_rank + 1)
    if query_tokens >= 3 and token_hits < 2 and phrase_hits < 2:
        rank_score *= 0.25
    coverage_score = 30.0 * token_hits / max(1, query_tokens)
    phrase_score = min(9.0, 3.0 * phrase_hits)
    metadata_score = min(30.0, 20.0 * metadata_hits)
    return rank_score + coverage_score + phrase_score + metadata_score


def faceted_term_qualities(
    connection: sqlite3.Connection,
    terms: Iterable[str],
) -> dict[str, dict[str, float]]:
    qualities: dict[str, dict[str, float]] = {}
    for term in dict.fromkeys(terms):
        rows = connection.execute(
            f"SELECT path, {DOCUMENT_BM25_EXPRESSION} AS rank "
            "FROM documents_fts "
            "WHERE documents_fts MATCH ? AND path != 'README.md'",
            (quote_fts_phrase(term),),
        ).fetchall()
        qualities[term] = {
            str(row["path"]): max(0.0, -float(row["rank"]))
            for row in rows
        }
    return qualities


def faceted_group_matches(
    group: tuple[str, ...],
    term_qualities: dict[str, dict[str, float]],
    exact_matches: dict[str, dict[str, GroupMatch]],
) -> dict[str, GroupMatch]:
    matches: dict[str, GroupMatch] = {}
    for term in group:
        for path, score in term_qualities.get(term, {}).items():
            candidate = GroupMatch(score, term, "bm25")
            if path not in matches or candidate.score > matches[path].score:
                matches[path] = candidate
        for path, candidate in exact_matches.get(term, {}).items():
            if path not in matches or candidate.score > matches[path].score:
                matches[path] = candidate
    return matches


def normalize_faceted_scores(items: list[dict[str, object]]) -> None:
    strongest = max((float(item["score"]) for item in items), default=0.0)
    if strongest <= 0:
        return
    for item in items:
        normalized = 100.0 * float(item["score"]) / strongest
        item["score"] = normalized
        scores = item.get("_scores")
        if isinstance(scores, dict) and "faceted_bm25" in scores:
            scores["faceted_bm25"] = normalized


def weak_direct(
    item: dict[str, object], ranking_system: str = DEFAULT_RANKING_SYSTEM
) -> bool:
    validate_ranking_system(ranking_system)
    if ranking_system == FACETED_BM25:
        return False
    signals = item["signals"]
    assert isinstance(signals, dict)
    return int(signals.get("query_tokens") or 0) >= 3 and not (
        signals.get("exact")
        or signals.get("semantic_ids")
        or int(signals.get("token_hits") or 0) >= 2
        or int(signals.get("rare_token_hits") or 0) >= 1
        or int(signals.get("phrase_hits") or 0) >= 1
        or int(signals.get("graph_support") or 0) >= 1
    )


def rank_direct(items: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(
        items,
        key=lambda item: (-float(item["score"]), str(item["path"])),
    )


def direct_cutoff(
    ranked: list[dict[str, object]],
    strong_match: bool,
    ranking_system: str = DEFAULT_RANKING_SYSTEM,
) -> float | None:
    validate_ranking_system(ranking_system)
    if strong_match or not ranked:
        return None
    if ranking_system == FACETED_BM25:
        return 0.0
    return max(5.0, float(ranked[0]["score"]) * 0.1)


def select_direct(
    ranked: list[dict[str, object]],
    *,
    limit: int,
    strong_match: bool,
    weak_limit: int,
    ranking_system: str = DEFAULT_RANKING_SYSTEM,
) -> list[dict[str, object]]:
    validate_ranking_system(ranking_system)
    cutoff = direct_cutoff(ranked, strong_match, ranking_system)
    selected: list[dict[str, object]] = []
    weak_count = 0
    for item in ranked:
        if cutoff is not None and float(item["score"]) < cutoff:
            continue
        if not strong_match and weak_direct(item, ranking_system):
            if weak_count >= weak_limit:
                continue
            weak_count += 1
        selected.append(item)
        if len(selected) >= limit:
            break
    return selected


def graph_relevance(
    path: str,
    title: str,
    routing_tokens: tuple[str, ...],
    path_matches: Callable[[str, str], bool],
    *,
    strong_match: bool,
) -> int:
    if strong_match:
        return 0
    metadata_tokens = {
        part
        for token in QUERY_TOKEN_RE.findall(f"{path} {title}".casefold())
        for part in (token, *token.split("-"))
    }
    metadata_hits = sum(token in metadata_tokens for token in routing_tokens)
    document_hits = sum(path_matches(path, token) for token in routing_tokens)
    return metadata_hits * 3 + document_hits


def transition_score(source_score: float) -> float:
    return source_score * 0.25


def direct_graph_bonus(source_score: float) -> float:
    return min(5.0, transition_score(source_score))


def combined_graph_score(scores: Iterable[float]) -> float:
    values = [float(value) for value in scores]
    strongest = max(values)
    return min(sum(values), strongest * 2.0)


def rank_graph(items: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(
        items,
        key=lambda item: (
            -int(item.get("_relevance") or 0),
            -float(item["score"]),
            str(item["path"]),
        ),
    )


def select_graph(
    ranked: list[dict[str, object]],
    *,
    graph_limit: int,
    direct_count: int,
) -> tuple[list[dict[str, object]], float | None]:
    if not ranked or not graph_limit:
        return [], None
    threshold = max(5.0, float(ranked[0]["score"]) * 0.4)
    adaptive_limit = min(graph_limit, max(2, direct_count))
    if (
        len(ranked) > 1
        and int(ranked[0].get("_relevance") or 0)
        >= int(ranked[1].get("_relevance") or 0) + 3
    ):
        adaptive_limit = 1
    selected = [item for item in ranked if float(item["score"]) >= threshold]
    return selected[:adaptive_limit], threshold
