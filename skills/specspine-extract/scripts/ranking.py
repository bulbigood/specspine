"""Query planning and ranking policy for the SpecSpine FTS accelerator."""

from __future__ import annotations

import math
import re
import sqlite3
from collections.abc import Callable, Iterable


QUERY_TOKEN_RE = re.compile(r"[^\W_]+(?:-[^\W_]+)*", re.UNICODE)
ID_QUERY_RE = re.compile(
    r"^(?:DEC|CON|OBS|INF|OQ)-[a-z0-9]+(?:-[a-z0-9]+)*$", re.IGNORECASE
)
BM25_EXPRESSION = "bm25(sections_fts, 0.0, 10.0, 5.0, 3.0, 1.0)"
EXACT_MATCH_SCORE = 100.0
SEMANTIC_ID_SCORE = 120.0
RARE_TOKEN_MAX_DOCUMENTS = 1


class InvalidRankingQuery(ValueError):
    """The query has no terms that can be routed through FTS."""


def fts_plan(
    query: str, connection: sqlite3.Connection | None = None
) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    raw_tokens = QUERY_TOKEN_RE.findall(query.casefold())[:32]
    tokens = list(dict.fromkeys(raw_tokens))
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
    if not tokens:
        raise InvalidRankingQuery("query has no searchable terms")
    return (
        " OR ".join(f'"{token.replace(chr(34), chr(34) * 2)}"' for token in tokens[:32]),
        tuple(tokens[:32]),
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


def weak_direct(item: dict[str, object]) -> bool:
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
    ranked: list[dict[str, object]], strong_match: bool
) -> float | None:
    if strong_match or not ranked:
        return None
    return max(5.0, float(ranked[0]["score"]) * 0.1)


def select_direct(
    ranked: list[dict[str, object]],
    *,
    limit: int,
    strong_match: bool,
    weak_limit: int,
) -> list[dict[str, object]]:
    cutoff = direct_cutoff(ranked, strong_match)
    selected: list[dict[str, object]] = []
    weak_count = 0
    for item in ranked:
        if cutoff is not None and float(item["score"]) < cutoff:
            continue
        if not strong_match and weak_direct(item):
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
