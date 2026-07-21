#!/usr/bin/env python3
"""Run a live Codex eval and emit a conservative file-read trace."""

from __future__ import annotations

import argparse
import json
import os
import re
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
    found: set[str] = set()
    for segment in re.split(r"\s*(?:&&|\|\||[;|])\s*", command):
        if re.search(r"\brg\b[^;&|]*\s--files(?:\s|$)", segment) or re.search(r"(?:^|\s)find\s", segment):
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gpt-5.6-terra")
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
