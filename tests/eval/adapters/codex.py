#!/usr/bin/env python3
"""Run a live Codex eval and emit a conservative file-read trace."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path


def relative_files(root: Path) -> list[str]:
    return sorted(
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.is_file() and ".eval" not in path.relative_to(root).parts
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

    content_reader = re.search(r"(?:^|[\s;|])(?:cat|sed|head|tail|awk)\b", command)
    if not content_reader:
        return found

    for pattern in re.findall(r"(?:[\w.-]+/)+[^\s;'\"]*[*?][^\s;'\"]*", command):
        cleaned = pattern.rstrip(");}")
        found.update(path for path in candidates if fnmatch_path(path, cleaned))

    if re.search(r"\bfor\b", command):
        for match in re.finditer(r"\brg\s+--files\s+([^;&|)$]+)", command):
            for root in match.group(1).split():
                root = root.strip("'\"").rstrip("/")
                if root and not root.startswith("-"):
                    found.update(path for path in candidates if path == root or path.startswith(root + "/"))
    return found


def fnmatch_path(path: str, pattern: str) -> bool:
    pattern_re = re.escape(pattern).replace(r"\*\*", ".*").replace(r"\*", "[^/]*").replace(r"\?", "[^/]")
    return re.fullmatch(pattern_re, path) is not None


def parse_events(stdout: str, candidates: list[str]) -> tuple[set[str], list[str], list[str]]:
    reads: set[str] = set()
    commands: list[str] = []
    messages: list[str] = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get("item", {})
        if item.get("type") == "command_execution":
            command = str(item.get("command", ""))
            commands.append(command)
            reads.update(traced_files(command, candidates))
        elif item.get("type") == "agent_message" and item.get("text"):
            messages.append(str(item["text"]))
    return reads, commands, messages


def parse_token_usage(stdout: str) -> dict[str, int]:
    """Return the latest cumulative token counters emitted by Codex."""
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
        stack = [event]
        while stack:
            value = stack.pop()
            if isinstance(value, dict):
                counters = {
                    key: count
                    for key, count in value.items()
                    if key in known and isinstance(count, int) and not isinstance(count, bool)
                }
                if counters:
                    usage.update(counters)
                stack.extend(value.values())
            elif isinstance(value, list):
                stack.extend(value)
    return usage


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gpt-5.6-luna")
    parser.add_argument("--reasoning-effort", default="medium")
    args = parser.parse_args()

    root = Path.cwd()
    prompt = sys.stdin.read()
    candidates = relative_files(root)
    command = [
        "codex",
        "-a",
        "never",
        "--model",
        args.model,
        "--config",
        f'model_reasoning_effort="{args.reasoning_effort}"',
        "exec",
        "--json",
        "--ephemeral",
        "--skip-git-repo-check",
        "-s",
        "workspace-write",
        "-C",
        str(root),
        "-",
    ]
    started = time.monotonic()
    completed = subprocess.run(command, input=prompt, text=True, capture_output=True, check=False)
    duration_seconds = round(time.monotonic() - started, 3)
    reads, commands, messages = parse_events(completed.stdout, candidates)
    token_usage = parse_token_usage(completed.stdout)
    final_response = messages[-1] if messages else ""
    trace_path = root / ".eval" / "trace.json"
    trace_path.write_text(
        json.dumps(
            {
                "commands": commands,
                "duration_seconds": duration_seconds,
                "eval_case": os.environ.get("SPECSPINE_EVAL_CASE", ""),
                "eval_run": os.environ.get("SPECSPINE_EVAL_RUN", ""),
                "files_read": sorted(reads),
                "model": args.model,
                "reasoning_effort": args.reasoning_effort,
                "token_usage": token_usage,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (root / ".eval" / "response.md").write_text(final_response + ("\n" if final_response else ""), encoding="utf-8")
    if final_response:
        print(final_response)
    if completed.returncode and completed.stderr:
        print(completed.stderr, file=sys.stderr)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
