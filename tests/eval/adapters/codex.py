#!/usr/bin/env python3
"""Run a live Codex eval and emit a conservative file-read trace."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


FORBIDDEN_SCOPE_MARKERS = (
    "$HOME",
    "${HOME}",
    "~/",
    "/tmp/",
    "/private/tmp/",
    "/private/var/",
    "/Users/",
    "/Volumes/",
)

SANDBOX_PROTECTED_NAMES = (".git", ".agents", ".codex")

def relative_files(root: Path) -> list[str]:
    return sorted(
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.is_file()
        and not {".eval", ".git"}.intersection(path.relative_to(root).parts)
    )


def traced_files(command: str, candidates: list[str]) -> set[str]:
    command = shell_source(command)
    found = indirect_reads(command, candidates)
    for segment in shell_segments(command):
        if re.search(r"\brg\b[^;&|]*\s--files(?:\s|$)", segment) or re.search(r"(?:^|\s)find\s", segment):
            continue
        if re.match(r"^(?:then\s+)?(?:echo|printf)\b", segment.strip()):
            continue
        if re.search(r"(?:^|\s)rg\b", segment):
            found.update(rg_content_reads(segment, candidates))
            continue
        found.update(
            path
            for path in candidates
            if re.search(rf"(?<![\w./-]){re.escape(path)}(?![\w./-])", segment)
        )
        broad_reader = re.search(r"(?:^|\s)(?:rg|grep)\b", segment)
        if broad_reader and re.search(r"(?:\s|^)(?:\.|\./|\*|\*\*)(?:\s|$)", segment):
            found.update(candidates)
    return found


def shell_source(command: str) -> str:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return command
    for index, token in enumerate(tokens[:-1]):
        if token in {"-c", "-lc"} and index > 0 and Path(tokens[index - 1]).name in {"sh", "bash", "zsh"}:
            return tokens[index + 1]
    return command


def shell_segments(command: str) -> list[str]:
    segments: list[str] = []
    current: list[str] = []
    quote = ""
    escaped = False
    index = 0
    while index < len(command):
        char = command[index]
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\" and quote != "'":
            current.append(char)
            escaped = True
        elif quote:
            current.append(char)
            if char == quote:
                quote = ""
        elif char in {"'", '"'}:
            current.append(char)
            quote = char
        elif char in {";", "|", "\n", "&"}:
            segment = "".join(current).strip()
            if segment:
                segments.append(segment)
            current = []
            if index + 1 < len(command) and command[index + 1] == char:
                index += 1
        else:
            current.append(char)
        index += 1
    segment = "".join(current).strip()
    if segment:
        segments.append(segment)
    return segments


def rg_content_reads(segment: str, candidates: list[str]) -> set[str]:
    try:
        tokens = shlex.split(segment)
    except ValueError:
        return set(candidates)
    try:
        index = next(i for i, token in enumerate(tokens) if Path(token).name == "rg")
    except StopIteration:
        return set()
    value_options = {"-g", "--glob", "-t", "--type", "--type-add", "--encoding", "-f", "--file"}
    positional: list[str] = []
    skip_next = False
    for token in tokens[index + 1 :]:
        if skip_next:
            skip_next = False
            continue
        if token in value_options:
            skip_next = True
            continue
        if token.startswith("-"):
            continue
        positional.append(token)
    roots = positional[1:] if positional else []
    if not roots:
        roots = ["."]
    found: set[str] = set()
    for root in roots:
        root = root.removeprefix("./").rstrip("/")
        if root in {"", "."}:
            found.update(candidates)
        elif "*" in root or "?" in root:
            found.update(path for path in candidates if fnmatch_path(path, root))
        else:
            found.update(path for path in candidates if path == root or path.startswith(root + "/"))
    return found


def indirect_reads(command: str, candidates: list[str]) -> set[str]:
    """Infer files consumed through bounded shell loops or known checker commands."""
    found: set[str] = set()
    for match in re.finditer(r"\bcheck_spine\.py\s+([^\s;&|]+)", command):
        root = match.group(1).strip("'\"").rstrip("/")
        if root and not root.startswith("-"):
            found.update(path for path in candidates if path == root or path.startswith(root + "/"))

    if re.search(r"\bfor\b", command):
        for loop in re.finditer(
            r"\bfor\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+([^;]+);\s*do\b(.*?)\bdone\b",
            command,
            re.DOTALL,
        ):
            variable, raw_values, body = loop.groups()
            if "$(" in raw_values or "`" in raw_values:
                continue
            try:
                values = shlex.split(raw_values)
            except ValueError:
                continue
            for value in values:
                if not value or any(marker in value for marker in ("$", "*", "?")):
                    continue
                expanded = re.sub(
                    rf"\$(?:\{{{re.escape(variable)}\}}|{re.escape(variable)}\b)",
                    value,
                    body,
                )
                found.update(traced_files(expanded, candidates))
        content_reader = re.search(r"(?:^|[\s;|])(?:cat|sed|head|tail|awk)\b", command)
        if content_reader:
            for pattern in re.findall(r"(?:[\w.-]+/)+[^\s;'\"]*[*?][^\s;'\"]*", command):
                cleaned = pattern.rstrip(");}")
                found.update(path for path in candidates if fnmatch_path(path, cleaned))
        for match in re.finditer(r"\brg\s+--files\s+([^;&|)$]+)", command):
            for root in match.group(1).split():
                root = root.strip("'\"").rstrip("/")
                if root and not root.startswith("-"):
                    found.update(path for path in candidates if path == root or path.startswith(root + "/"))
        return found

    for segment in shell_segments(command):
        if not re.search(r"(?:^|\s)(?:cat|sed|head|tail|awk)\b", segment):
            continue
        for pattern in re.findall(r"(?:[\w.-]+/)+[^\s;'\"]*[*?][^\s;'\"]*", segment):
            cleaned = pattern.rstrip(");}")
            found.update(path for path in candidates if fnmatch_path(path, cleaned))
    return found


def fnmatch_path(path: str, pattern: str) -> bool:
    pattern_re = re.escape(pattern).replace(r"\*\*", ".*").replace(r"\*", "[^/]*").replace(r"\?", "[^/]")
    return re.fullmatch(pattern_re, path) is not None


def parse_events(stdout: str, candidates: list[str]) -> tuple[set[str], list[str], list[str]]:
    reads: set[str] = set()
    commands: list[str] = []
    messages: list[str] = []
    completed_item_ids: set[str] = set()
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        event_type = event.get("type")
        if event_type not in {None, "item.completed"}:
            continue
        item = event.get("item", {})
        item_id = item.get("id")
        if item_id is not None:
            item_id = str(item_id)
            if item_id in completed_item_ids:
                continue
            completed_item_ids.add(item_id)
        if item.get("type") == "command_execution":
            command = str(item.get("command", ""))
            commands.append(command)
            reads.update(traced_files(command, candidates))
        elif item.get("type") == "agent_message" and item.get("text"):
            messages.append(str(item["text"]))
    return reads, commands, messages


def command_category(command: str, inferred_reads: set[str]) -> str:
    source = shell_source(command)
    if "search_spine.py" in source:
        return "retrieval"
    if any(marker in source for marker in (".eval/skill/", ".eval/companions/", ".eval/tools/")):
        return "skill_context"
    if inferred_reads:
        return "project_content"
    if re.search(r"\brg\b[^;&|]*\s--files(?:\s|$)", source) or re.search(
        r"(?:^|\s)find\s", source
    ):
        return "discovery"
    return "other"


def parse_event_metrics(stdout: str, candidates: list[str]) -> dict[str, object]:
    """Preserve compact tool-cycle diagnostics without retaining tool output."""
    event_counts: dict[str, int] = {}
    item_counts: dict[str, int] = {}
    command_metrics: list[dict[str, object]] = []
    completed_item_ids: set[str] = set()
    agent_message_count = 0
    turn_count = 0
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        event_type = str(event.get("type") or "legacy")
        event_counts[event_type] = event_counts.get(event_type, 0) + 1
        if event_type == "turn.completed":
            turn_count += 1
        if event.get("type") not in {None, "item.completed"}:
            continue
        item = event.get("item", {})
        if not isinstance(item, dict):
            continue
        item_id = item.get("id")
        if item_id is not None:
            item_id = str(item_id)
            if item_id in completed_item_ids:
                continue
            completed_item_ids.add(item_id)
        item_type = str(item.get("type") or "unknown")
        item_counts[item_type] = item_counts.get(item_type, 0) + 1
        if item_type == "agent_message":
            agent_message_count += 1
            continue
        if item_type != "command_execution":
            continue
        command = str(item.get("command", ""))
        output = str(item.get("aggregated_output", ""))
        inferred_reads = traced_files(command, candidates)
        command_metrics.append(
            {
                "number": len(command_metrics) + 1,
                "event_id": item_id,
                "category": command_category(command, inferred_reads),
                "status": item.get("status"),
                "exit_code": item.get("exit_code"),
                "output_chars": len(output),
                "output_utf8_bytes": len(output.encode("utf-8")),
                "output_lines": len(output.splitlines()),
                "inferred_file_count": len(inferred_reads),
                "inferred_file_paths": sorted(inferred_reads),
                "command_excerpt": shell_source(command)[:1000],
            }
        )
    return {
        "event_counts": event_counts,
        "item_counts": item_counts,
        "command_count": len(command_metrics),
        "command_output_chars": sum(
            int(item["output_chars"]) for item in command_metrics
        ),
        "command_output_utf8_bytes": sum(
            int(item["output_utf8_bytes"]) for item in command_metrics
        ),
        "command_metrics": command_metrics,
        "agent_message_count": agent_message_count,
        "turn_count": turn_count,
    }


def command_option(command: str, option: str) -> str | None:
    try:
        tokens = shlex.split(shell_source(command))
    except ValueError:
        return None
    for index, token in enumerate(tokens):
        if token == option and index + 1 < len(tokens):
            values = []
            for value in tokens[index + 1:]:
                if value.startswith("--"):
                    break
                values.append(value)
            return " ".join(values) or None
        if token.startswith(option + "="):
            return token.split("=", 1)[1]
    return None


def parse_retrieval_attempts(stdout: str) -> list[dict[str, object]]:
    attempts: list[dict[str, object]] = []
    completed_item_ids: set[str] = set()
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") not in {None, "item.completed"}:
            continue
        item = event.get("item", {})
        item_id = item.get("id")
        if item_id is not None:
            item_id = str(item_id)
            if item_id in completed_item_ids:
                continue
            completed_item_ids.add(item_id)
        command = str(item.get("command", ""))
        if item.get("type") != "command_execution" or "search_spine.py" not in command:
            continue
        raw_output = str(item.get("aggregated_output", ""))
        payload = None
        parsed_json = False
        for output_line in raw_output.splitlines():
            try:
                candidate = json.loads(output_line.strip())
            except json.JSONDecodeError:
                continue
            parsed_json = True
            if isinstance(candidate, dict) and candidate.get("mode") in {
                "sqlite-fts5", "fallback", "error"
            }:
                payload = candidate
        direct_documents = (
            payload.get("direct_matches", [])
            if isinstance(payload, dict)
            else []
        )
        graph_documents = (
            payload.get("graph_neighbors", []) if isinstance(payload, dict) else []
        )
        if payload is not None:
            failure_kind = None
        elif not raw_output.strip():
            failure_kind = "missing_output"
        elif parsed_json:
            failure_kind = "invalid_payload"
        else:
            failure_kind = "malformed_output"
        direct_matches = []
        for candidate in direct_documents if isinstance(direct_documents, list) else []:
            if not isinstance(candidate, dict) or not isinstance(candidate.get("path"), str):
                continue
            direct_matches.append(
                {
                    key: candidate[key]
                    for key in ("path", "score", "origins", "signals", "headings", "title")
                    if key in candidate
                }
            )
        graph_neighbors = []
        for candidate in graph_documents if isinstance(graph_documents, list) else []:
            if not isinstance(candidate, dict) or not isinstance(candidate.get("path"), str):
                continue
            graph_neighbors.append(
                {
                    key: candidate[key]
                    for key in (
                        "path",
                        "score",
                        "origins",
                        "title",
                        "relevance",
                        "transitions",
                    )
                    if key in candidate
                }
            )
        candidates = direct_matches + graph_neighbors
        attempts.append(
            {
                "attempt_number": len(attempts) + 1,
                "event_id": str(item_id) if item_id is not None else None,
                "mode": payload.get("mode", "unknown") if isinstance(payload, dict) else "unknown",
                "query": command_option(command, "--query"),
                "candidate_count": len(candidates),
                "candidate_paths": [candidate["path"] for candidate in candidates],
                "candidates": candidates,
                "direct_count": len(direct_matches),
                "graph_count": len(graph_neighbors),
                "direct_matches": direct_matches,
                "graph_neighbors": graph_neighbors,
                "exit_code": item.get("exit_code"),
                "failure_kind": failure_kind,
                "reason_code": payload.get("reason_code") if isinstance(payload, dict) else None,
                "reason": payload.get("reason") if isinstance(payload, dict) else None,
                "documents": payload.get("documents") if isinstance(payload, dict) else None,
                "refreshed": payload.get("refreshed") if isinstance(payload, dict) else None,
                "index_state": payload.get("index_state") if isinstance(payload, dict) else None,
                "retrieval_strategy": payload.get("retrieval_strategy") if isinstance(payload, dict) else None,
                "selection": payload.get("selection", {}) if isinstance(payload, dict) else {},
                "timings": payload.get("timings", {}) if isinstance(payload, dict) else {},
                "runtime": payload.get("runtime", {}) if isinstance(payload, dict) else {},
                "output_chars": len(raw_output),
                "output_utf8_bytes": len(raw_output.encode("utf-8")),
                "output_excerpt": raw_output.strip()[:1000] if payload is None else None,
            }
        )
    return attempts


def read_retrieval_telemetry(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        return []
    records: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            records.append(value)
    return records


def merge_retrieval_telemetry(
    attempts: list[dict[str, object]], records: list[dict[str, object]]
) -> None:
    for attempt, record in zip(attempts, records):
        query = attempt.get("query")
        expected_hash = (
            hashlib.sha256(str(query).encode("utf-8")).hexdigest() if query else None
        )
        if expected_hash and record.get("query_sha256") != expected_hash:
            attempt["telemetry_mismatch"] = True
            continue
        for key in (
            "reason_code",
            "reason",
            "documents",
            "refreshed",
            "index_state",
            "retrieval_strategy",
            "selection",
            "timings",
            "runtime",
            "production_output_utf8_bytes",
        ):
            if key in record:
                attempt[key] = record[key]
        attempt["telemetry_level"] = record.get("telemetry_level")


def deterministic_cost_ledger(
    root: Path,
    prompt: str,
    response: str,
    reads: set[str],
    event_metrics: dict[str, object],
    retrieval_attempts: list[dict[str, object]],
) -> dict[str, int]:
    """Record stable byte/cycle proxies separately from stochastic token counters."""
    declared_context = [
        root / ".eval" / "skill" / "SKILL.md",
        root / ".eval" / "skill" / "references" / "context-handoff.md",
    ]
    project_source_bytes = 0
    for relative in reads:
        source = root / relative
        try:
            if source.is_file():
                project_source_bytes += source.stat().st_size
        except OSError:
            continue
    command_count = event_metrics.get("command_count")
    command_output = event_metrics.get("command_output_utf8_bytes")
    return {
        "prompt_utf8_bytes": len(prompt.encode("utf-8")),
        "project_agent_instruction_utf8_bytes": (
            (root / "AGENTS.md").stat().st_size
            if (root / "AGENTS.md").is_file()
            else 0
        ),
        "declared_skill_context_utf8_bytes": sum(
            path.stat().st_size for path in declared_context if path.is_file()
        ),
        "retrieval_output_utf8_bytes": sum(
            int(attempt.get("output_utf8_bytes", 0)) for attempt in retrieval_attempts
        ),
        "project_source_file_bytes": project_source_bytes,
        "command_output_utf8_bytes": int(command_output or 0),
        "final_response_utf8_bytes": len(response.encode("utf-8")),
        "tool_cycles": int(command_count or 0),
    }


def retrieval_usefulness(
    reads: set[str], retrieval_attempts: list[dict[str, object]]
) -> dict[str, object]:
    """Relate routed documents to conservatively inferred project reads."""
    direct = {
        f"specspine/{candidate['path']}"
        for attempt in retrieval_attempts
        for candidate in attempt.get("direct_matches", [])
        if isinstance(candidate, dict) and isinstance(candidate.get("path"), str)
    }
    graph = {
        f"specspine/{candidate['path']}"
        for attempt in retrieval_attempts
        for candidate in attempt.get("graph_neighbors", [])
        if isinstance(candidate, dict) and isinstance(candidate.get("path"), str)
    } - direct
    relevant_reads = {
        path for path in reads
        if path.startswith("specspine/") and path != "specspine/README.md"
    }
    read_direct = relevant_reads & direct
    read_graph = relevant_reads & graph
    outside = relevant_reads - direct - graph
    return {
        "returned_direct": len(direct),
        "returned_graph": len(graph),
        "read_returned_direct": len(read_direct),
        "read_returned_graph": len(read_graph),
        "read_outside_results": len(outside),
        "unread_returned_direct": len(direct - relevant_reads),
        "unread_returned_graph": len(graph - relevant_reads),
        "read_outside_result_paths": sorted(outside),
    }


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def optional_file_sha256(path: Path) -> str | None:
    return file_sha256(path) if path.is_file() else None


def command_version(command: str) -> str | None:
    try:
        completed = subprocess.run(
            [command, "--version"], capture_output=True, text=True, check=False, timeout=10
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = (completed.stdout or completed.stderr).strip()
    return value[:300] if completed.returncode == 0 and value else None


def parse_token_usage(stdout: str) -> dict[str, int]:
    """Return the latest top-level cumulative turn counters emitted by Codex."""
    known = {
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
        "total_tokens",
    }
    usage: dict[str, int] = {}
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "turn.completed":
            continue
        value = event.get("usage")
        if not isinstance(value, dict):
            continue
        counters = {
            key: count
            for key, count in value.items()
            if key in known and isinstance(count, int) and not isinstance(count, bool)
        }
        if counters:
            usage = counters
    return usage


def environment_errors(stdout: str, stderr: str = "") -> list[str]:
    """Recognize known host/container failures, not ordinary command failures."""
    evidence: list[str] = []

    def bubblewrap_errors(output: str) -> list[str]:
        return [line.strip() for line in output.splitlines() if line.lstrip().startswith("bwrap:")]

    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") not in {None, "item.completed"}:
            continue
        item = event.get("item", {})
        if item.get("type") != "command_execution":
            continue
        failed = item.get("status") == "failed" or (
            isinstance(item.get("exit_code"), int) and item["exit_code"] != 0
        )
        if not failed:
            continue
        output = str(item.get("aggregated_output", ""))
        evidence.extend(bubblewrap_errors(output))
    evidence.extend(bubblewrap_errors(stderr))
    return [f"Codex command sandbox unavailable: {detail}" for detail in dict.fromkeys(evidence)]


def scope_violations(
    commands: list[str], root: Path, allowed_roots: tuple[Path, ...] = ()
) -> list[str]:
    authorized_roots = sorted(
        {str(path.resolve()).rstrip("/") for path in (root, *allowed_roots)},
        key=len,
        reverse=True,
    )
    violations: list[str] = []
    for command in commands:
        # Codex serializes shell invocations as `/bin/sh -c <source>`. Audit
        # the decoded source, otherwise quoting inserted by the event stream
        # can split a harmless negative glob around `.eval` and look like a
        # direct path operand.
        inspected = shell_source(command)
        for authorized_root in authorized_roots:
            inspected = re.sub(
                rf"{re.escape(authorized_root)}(?=$|[/\s'\";&|)])",
                "<AUTHORIZED_ROOT>",
                inspected,
            )
        markers = [marker for marker in FORBIDDEN_SCOPE_MARKERS if marker in inspected]
        audit_text = inspected
        if re.search(
            r"(?:^|[;&|]\s*|\s)(?:cd|find|ls|tree|du)\s+(?:-[^\s]+\s+)*/(?:\s|$)",
            inspected,
        ):
            markers.append("filesystem-root traversal (`/`)")
        allowed_eval = re.sub(
            r"(?:\./)?\.eval/(?:skill|companions|tools)(?:/[^\s'\"]*)?",
            "<ALLOWED_EVAL_CONTEXT>",
            audit_text,
        )
        # Mentioning evaluator internals in an exclusion does not inspect them.
        # Mask only recognized negative selectors; direct path operands remain
        # visible to the check below.
        for pattern in (
            r"--exclude-dir(?:=|\s+)[\"']?(?:\./)?\.eval[\"']?",
            r"--exclude(?:=|\s+)[\"']?(?:\./)?\.eval(?:/[^\s\"']*)?[\"']?",
            r"(?:-not|!)\s+-path\s+[\"']*(?:\./)?\.eval(?:[^\s\"']*)?[\"']*",
            r"-path\s+[\"']*(?:\./)?\.eval(?:/?)[\"']*\s+-prune\b",
            r"(?:-g|--glob)(?:=|\s+)[\"']*!\s*(?:\./)?\.eval(?:/[^\s\"']*)?[\"']*",
            r"(?:-g|--glob)(?:=|\s+)[\"']*![^\"']*\.eval[^\"']*[\"']*",
        ):
            allowed_eval = re.sub(pattern, "<EVAL_EXCLUSION>", allowed_eval)
        # A depth-one directory listing cannot descend into evaluator files.
        # Permit excluding the `.eval` directory by name in that bounded form,
        # but keep rejecting the same predicate on an unbounded `find`.
        def mask_bounded_find(match: re.Match[str]) -> str:
            return re.sub(
                r"(?:-not|!)\s+-name\s+[\"']?\.eval[\"']?",
                "<EVAL_EXCLUSION>",
                match.group(0),
            )

        allowed_eval = re.sub(
            r"\bfind[ \t]+\.[ \t]+[^;&|\r\n]*-maxdepth[ \t]+1\b[^;&|\r\n]*",
            mask_bounded_find,
            allowed_eval,
        )
        if re.search(r"(?:^|[\s'\"])(?:\./)?\.eval(?:/|\b)", allowed_eval):
            markers.append("evaluator internals (`.eval`)")
        if markers:
            violations.append(
                f"external path marker(s) {', '.join(sorted(set(markers)))} in command: "
                + inspected[:500].replace("\n", "\\n")
            )
    return violations


def prepare_sandbox_mountpoints(root: Path, runtime_root: Path) -> list[Path]:
    """Materialize paths that Codex re-protects below writable roots.

    Codex's bubblewrap policy layers these paths back as read-only. Some CLI
    versions intermittently generate a bind/remount from a missing path when
    several shell tools start concurrently. Empty mountpoints avoid that race;
    newly created workspace placeholders are removed after the run.
    """
    created_in_workspace: list[Path] = []
    for parent in (root, runtime_root):
        for name in SANDBOX_PROTECTED_NAMES:
            path = parent / name
            if path.exists():
                continue
            path.mkdir()
            if parent == root:
                created_in_workspace.append(path)
    return created_in_workspace


def remove_empty_mountpoints(paths: list[Path]) -> None:
    for path in reversed(paths):
        try:
            path.rmdir()
        except (FileNotFoundError, OSError):
            # Preserve anything the agent created in a placeholder. The
            # ordinary workspace snapshot/scope audit will then expose it.
            pass


def write_codex_artifacts(
    eval_dir: Path,
    *,
    prompt: str,
    command: list[str],
    stdout: str,
    stderr: str,
    returncode: int,
    duration_seconds: float,
) -> None:
    """Persist every unfiltered stream exposed by `codex exec --json`."""
    eval_dir.mkdir(parents=True, exist_ok=True)
    (eval_dir / "codex-prompt.md").write_text(prompt, encoding="utf-8")
    (eval_dir / "codex-events.jsonl").write_text(stdout, encoding="utf-8")
    (eval_dir / "codex-stderr.txt").write_text(stderr, encoding="utf-8")
    (eval_dir / "codex-invocation.json").write_text(
        json.dumps(
            {
                "command": command,
                "duration_seconds": duration_seconds,
                "returncode": returncode,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def sandbox_path(runtime_root: Path | None = None) -> str:
    """Keep usable system tools while excluding inaccessible user shims."""
    home = str(Path.home().resolve()).rstrip("/") + "/"
    paths = [
        item
        for item in os.environ.get("PATH", "").split(os.pathsep)
        if item
        and not str(Path(item).expanduser()).startswith(home)
        and "pyenv" not in item.lower()
        and not item.startswith("/var/")
    ]
    developer_tools = Path("/Applications/Xcode.app/Contents/Developer/usr/bin")
    if developer_tools.is_dir():
        paths.insert(0, str(developer_tools))
    if runtime_root is not None:
        paths.insert(0, str(runtime_root / "bin"))
    return os.pathsep.join(dict.fromkeys(paths))


def prepare_codex_home(runtime_root: Path) -> Path:
    """Create a private Codex home containing credentials but no shared state."""
    codex_home = runtime_root / "codex-home"
    codex_home.mkdir(parents=True)
    source_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    source_auth = source_home / "auth.json"
    if source_auth.is_file():
        target_auth = codex_home / "auth.json"
        shutil.copyfile(source_auth, target_auth)
        target_auth.chmod(0o600)
    return codex_home


def macos_external_dependencies(executable: Path) -> list[Path]:
    """Return absolute non-system dependencies of a Mach-O file."""
    if sys.platform != "darwin" or not shutil.which("otool"):
        return []
    try:
        output = subprocess.check_output(
            ["otool", "-L", str(executable)],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    return [
        Path(dependency)
        for line in output.splitlines()[1:]
        if line.strip()
        for dependency in [line.strip().split(" ", 1)[0]]
        if dependency.startswith("/")
        and not dependency.startswith(("/usr/lib/", "/System/Library/"))
    ]


def bundle_macos_dependencies(executable: Path, runtime_root: Path) -> None:
    """Copy external dylibs beside a tool and rewrite it to use the bundle."""
    install_name_tool = shutil.which("install_name_tool")
    codesign = shutil.which("codesign")
    if not install_name_tool or not codesign:
        raise RuntimeError("install_name_tool and codesign are required to bundle macOS tools")

    library_dir = runtime_root / "lib"
    library_dir.mkdir(exist_ok=True)
    pending: list[tuple[Path, Path | None]] = [(executable, None)]
    processed: set[Path] = set()
    modified: list[Path] = []

    while pending:
        target, source = pending.pop()
        if target in processed:
            continue
        processed.add(target)
        for dependency in macos_external_dependencies(target):
            if source is not None and dependency.resolve() == source.resolve():
                continue
            bundled = library_dir / dependency.name
            if not bundled.exists():
                shutil.copy2(dependency.resolve(), bundled)
            replacement = (
                f"@executable_path/../lib/{bundled.name}"
                if source is None
                else f"@loader_path/{bundled.name}"
            )
            subprocess.run(
                [install_name_tool, "-change", str(dependency), replacement, str(target)],
                check=True,
                capture_output=True,
                text=True,
            )
            pending.append((bundled, dependency))
        if source is not None:
            subprocess.run(
                [install_name_tool, "-id", f"@loader_path/{target.name}", str(target)],
                check=True,
                capture_output=True,
                text=True,
            )
        modified.append(target)

    for target in reversed(modified):
        subprocess.run(
            [codesign, "--force", "--sign", "-", str(target)],
            check=True,
            capture_output=True,
            text=True,
        )

    remaining = {
        dependency
        for target in modified
        for dependency in macos_external_dependencies(target)
    }
    if remaining:
        raise RuntimeError(f"unbundled macOS dependencies: {sorted(map(str, remaining))}")


def stage_runtime_tools(runtime_root: Path) -> None:
    """Copy user-installed tools and bundle their non-system macOS libraries."""
    for name in ("node", "rg"):
        source = shutil.which(name)
        if not source:
            continue
        resolved = Path(source).resolve()
        if resolved.is_file():
            staged = runtime_root / "bin" / name
            shutil.copy2(resolved, staged)
            if macos_external_dependencies(staged):
                bundle_macos_dependencies(staged, runtime_root)
            verified = subprocess.run(
                [str(staged), "--version"],
                capture_output=True,
                text=True,
                check=False,
            )
            if verified.returncode:
                raise RuntimeError(f"staged {name} failed startup verification: {verified.stderr.strip()}")


def build_codex_command(
    model: str,
    reasoning_effort: str,
    root: Path,
    runtime_root: Path,
    accelerator_mode: str = "enabled",
    retrieval_telemetry: str | None = None,
) -> list[str]:
    runtime_root = runtime_root.resolve()
    private_home = runtime_root / "home"
    private_cache = runtime_root / "cache"
    private_config = runtime_root / "config"
    private_data = runtime_root / "data"
    private_state = runtime_root / "state"
    python_cache = runtime_root / "pycache"
    private_tmp = runtime_root / "tmp"
    git_config = runtime_root / "gitconfig"
    workspace_roots = "{" + f'"."=true,{json.dumps(str(runtime_root))}=true' + "}"
    writable_roots = (
        "{"
        + '"."="write",".git"="read"'
        + "}"
    )
    environment = {
        "GIT_CONFIG_GLOBAL": str(git_config),
        "GIT_CONFIG_NOSYSTEM": "1",
        "HOME": str(private_home),
        "PATH": sandbox_path(runtime_root),
        "PIP_CACHE_DIR": str(private_cache / "pip"),
        "PYTHONPYCACHEPREFIX": str(python_cache),
        "TMPDIR": str(private_tmp),
        "XDG_CACHE_HOME": str(private_cache),
        "XDG_CONFIG_HOME": str(private_config),
        "XDG_DATA_HOME": str(private_data),
        "XDG_STATE_HOME": str(private_state),
        "ZDOTDIR": str(private_home),
    }
    if accelerator_mode == "fallback":
        environment["SPECSPINE_CACHE_DIR"] = str(runtime_root / "accelerator-unavailable")
    else:
        environment["SPECSPINE_CACHE_DIR"] = str(runtime_root / "accelerator-cache")
    if retrieval_telemetry:
        environment["SPECSPINE_PRODUCTION_SEARCH"] = str(
            root / ".eval" / "tools" / "search_spine_production.py"
        )
        environment["SPECSPINE_RETRIEVAL_TELEMETRY_FILE"] = str(
            runtime_root / "retrieval-telemetry.jsonl"
        )
        environment["SPECSPINE_RETRIEVAL_TELEMETRY_LEVEL"] = retrieval_telemetry
    environment_config = "{" + ",".join(
        f"{key}={json.dumps(value)}" for key, value in environment.items()
    ) + "}"
    return [
        "codex",
        "-a",
        "never",
        "--model",
        model,
        "--config",
        f'model_reasoning_effort="{reasoning_effort}"',
        "--config",
        'default_permissions="specspine_eval"',
        "--config",
        f"permissions.specspine_eval.workspace_roots={workspace_roots}",
        "--config",
        f'permissions.specspine_eval.filesystem={{":minimal"="read",":workspace_roots"={writable_roots}}}',
        "--config",
        "permissions.specspine_eval.network.enabled=false",
        "--config",
        'shell_environment_policy.inherit="core"',
        "--config",
        "shell_environment_policy.ignore_default_excludes=false",
        "--config",
        f"shell_environment_policy.set={environment_config}",
        "--config",
        "allow_login_shell=false",
        "exec",
        "--strict-config",
        "--json",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "-C",
        str(root),
        "-",
    ]


def prewarm_accelerator(root: Path, runtime_root: Path) -> None:
    script = root / ".eval" / "skill" / "scripts" / "search_spine.py"
    python = shutil.which("python3", path=sandbox_path(runtime_root))
    if not python:
        raise RuntimeError("python3 is unavailable for accelerator prewarm")
    environment = os.environ.copy()
    environment["SPECSPINE_CACHE_DIR"] = str(runtime_root / "accelerator-cache")
    environment["TMPDIR"] = str(runtime_root / "tmp")
    completed = subprocess.run(
        [
            python,
            str(script),
            str(root / "specspine"),
            "--query=README.md",
            "--limit=1",
            "--graph-depth=0",
            "--graph-limit=0",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
        timeout=60,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"accelerator prewarm failed: {detail}")


def enable_retrieval_telemetry(root: Path, level: str) -> None:
    """Observe the disposable staged script without changing agent instructions."""
    skill = root / ".eval" / "skill" / "SKILL.md"
    marker = "python3 <skill-root>/scripts/search_spine.py"
    content = skill.read_text(encoding="utf-8")
    if content.count(marker) != 1:
        raise RuntimeError(
            "cannot enable retrieval telemetry: retrieval command is ambiguous"
        )
    source = (
        Path(__file__).resolve().parents[3]
        / "tools"
        / "specspine-extract"
        / "search_spine_diagnostics.py"
    )
    production = root / ".eval" / "skill" / "scripts" / "search_spine.py"
    preserved = root / ".eval" / "tools" / "search_spine_production.py"
    preserved.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(production, preserved)
    shutil.copy2(production.with_name("ranking.py"), preserved.with_name("ranking.py"))
    shutil.copy2(source, production)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gpt-5.6-luna")
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument(
        "--accelerator-mode",
        choices=("enabled", "fallback"),
        default="enabled",
        help="make the optional retrieval cache available or force its normal fallback",
    )
    parser.add_argument(
        "--cache-profile",
        choices=("isolated-cold", "prewarmed"),
        default="isolated-cold",
        help="start with a private empty cache or prebuild the private index before the agent",
    )
    parser.add_argument(
        "--retrieval-telemetry",
        choices=("minimal", "full"),
        help="observe staged retrieval out of band; omitted matches production",
    )
    args = parser.parse_args()
    if args.accelerator_mode == "fallback" and args.cache_profile != "isolated-cold":
        parser.error("fallback mode supports only isolated-cold cache profile")
    evaluation_profile = os.environ.get("SPECSPINE_EVAL_PROFILE", "extract")
    if evaluation_profile == "no-extract" and args.cache_profile != "isolated-cold":
        parser.error("no-extract profile supports only isolated-cold cache profile")
    if evaluation_profile == "no-extract" and args.retrieval_telemetry:
        parser.error("no-extract profile cannot enable retrieval telemetry")

    root = Path.cwd()
    prompt = sys.stdin.read()
    candidates = relative_files(root)
    eval_dir = root / ".eval"
    configured_runtime = os.environ.get("SPECSPINE_EVAL_RUNTIME_DIR")
    runtime_parent = Path(configured_runtime) if configured_runtime else root.parent
    runtime_parent.mkdir(parents=True, exist_ok=True)
    runtime_root = Path(tempfile.mkdtemp(prefix="specspine-runtime-", dir=runtime_parent))
    workspace_mountpoints: list[Path] = []
    prewarm_seconds = 0.0
    retrieval_telemetry: list[dict[str, object]] = []
    try:
        for directory in (
            runtime_root / "bin",
            runtime_root / "home",
            runtime_root / "cache",
            runtime_root / "config",
            runtime_root / "data",
            runtime_root / "state",
            runtime_root / "pycache",
            runtime_root / "tmp",
        ):
            directory.mkdir(parents=True, exist_ok=True)
        workspace_mountpoints = prepare_sandbox_mountpoints(root, runtime_root)
        stage_runtime_tools(runtime_root)
        codex_home = prepare_codex_home(runtime_root)
        (runtime_root / "gitconfig").touch()
        safe_path = sandbox_path(runtime_root)
        profile = f"export PATH={shlex.quote(safe_path)}\n"
        (runtime_root / "home" / ".zshenv").write_text(profile, encoding="utf-8")
        (runtime_root / "home" / ".zprofile").write_text(profile, encoding="utf-8")
        tool_targets = {
            "git": Path("/Applications/Xcode.app/Contents/Developer/usr/bin/git"),
            "python": Path("/Applications/Xcode.app/Contents/Developer/usr/bin/python3"),
            "python3": Path("/Applications/Xcode.app/Contents/Developer/usr/bin/python3"),
        }
        for name, target in tool_targets.items():
            if target.is_file():
                (runtime_root / "bin" / name).symlink_to(target)
        if args.accelerator_mode == "fallback":
            (runtime_root / "accelerator-unavailable").touch()
        elif args.cache_profile == "prewarmed":
            prewarm_started = time.monotonic()
            prewarm_accelerator(root, runtime_root)
            prewarm_seconds = time.monotonic() - prewarm_started
        if args.retrieval_telemetry:
            enable_retrieval_telemetry(root, args.retrieval_telemetry)
        command = build_codex_command(
            args.model,
            args.reasoning_effort,
            root,
            runtime_root,
            args.accelerator_mode,
            args.retrieval_telemetry,
        )
        process_environment = os.environ.copy()
        process_environment["CODEX_HOME"] = str(codex_home)
        codex_version = command_version(command[0])
        started_at = utc_now()
        started = time.monotonic()
        completed = subprocess.run(
            command,
            input=prompt,
            text=True,
            capture_output=True,
            check=False,
            env=process_environment,
        )
        retrieval_telemetry = read_retrieval_telemetry(
            runtime_root / "retrieval-telemetry.jsonl"
        )
    finally:
        remove_empty_mountpoints(workspace_mountpoints)
        shutil.rmtree(runtime_root)
    duration_seconds = round(time.monotonic() - started, 3)
    finished_at = utc_now()
    write_codex_artifacts(
        eval_dir,
        prompt=prompt,
        command=command,
        stdout=completed.stdout,
        stderr=completed.stderr,
        returncode=completed.returncode,
        duration_seconds=duration_seconds,
    )
    reads, commands, messages = parse_events(completed.stdout, candidates)
    retrieval_attempts = parse_retrieval_attempts(completed.stdout)
    merge_retrieval_telemetry(retrieval_attempts, retrieval_telemetry)
    event_metrics = parse_event_metrics(completed.stdout, candidates)
    token_usage = parse_token_usage(completed.stdout)
    execution_errors = environment_errors(completed.stdout, completed.stderr)
    boundary_violations = scope_violations(commands, root, (runtime_root,))
    final_response = messages[-1] if messages else ""
    cost_ledger = deterministic_cost_ledger(
        root,
        prompt,
        final_response,
        reads,
        event_metrics,
        retrieval_attempts,
    )
    usefulness = retrieval_usefulness(reads, retrieval_attempts)
    trace_path = eval_dir / "trace.json"
    trace_path.write_text(
        json.dumps(
            {
                "commands": commands,
                "evaluation_profile": evaluation_profile,
                "accelerator_mode": args.accelerator_mode,
                "retrieval_telemetry": args.retrieval_telemetry,
                "retrieval_attempts": retrieval_attempts,
                "retrieval_mode": retrieval_attempts[-1]["mode"] if retrieval_attempts else None,
                "retrieval_attempt_count": len(retrieval_attempts),
                "unexpected_retry": len(retrieval_attempts) > 1,
                "unknown_attempt_count": sum(
                    attempt.get("mode") == "unknown" for attempt in retrieval_attempts
                ),
                "event_metrics": event_metrics,
                "cost_ledger": cost_ledger,
                "retrieval_usefulness": usefulness,
                "duration_seconds": duration_seconds,
                "started_at": started_at,
                "finished_at": finished_at,
                "eval_case": os.environ.get("SPECSPINE_EVAL_CASE", ""),
                "eval_run": os.environ.get("SPECSPINE_EVAL_RUN", ""),
                "files_read": sorted(reads),
                "environment_invalid": bool(execution_errors),
                "environment_errors": execution_errors,
                "scope_violations": boundary_violations,
                "model": args.model,
                "reasoning_effort": args.reasoning_effort,
                "cache_profile": args.cache_profile,
                "cache_scope": "private-per-sample",
                "prewarm_seconds": round(prewarm_seconds, 6),
                "runtime": {
                    "adapter_sha256": file_sha256(Path(__file__)),
                    "effective_skill_sha256": optional_file_sha256(
                        root / ".eval" / "skill" / "SKILL.md"
                    ),
                    "retrieval_tool_sha256": (
                        optional_file_sha256(
                            root / ".eval" / "skill" / "scripts" / "search_spine.py"
                        )
                        if args.retrieval_telemetry
                        else None
                    ),
                    "codex_cli": codex_version,
                    "python": platform.python_version(),
                    "platform": sys.platform,
                },
                "token_usage": token_usage,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (eval_dir / "response.md").write_text(final_response + ("\n" if final_response else ""), encoding="utf-8")
    if final_response:
        print(final_response)
    if completed.returncode and completed.stderr:
        print(completed.stderr, file=sys.stderr)
    return 70 if execution_errors else completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
