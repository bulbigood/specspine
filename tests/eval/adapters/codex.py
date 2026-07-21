#!/usr/bin/env python3
"""Run a live Codex eval and emit a conservative file-read trace."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def relative_files(root: Path) -> list[str]:
    return sorted(
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.is_file() and ".eval" not in path.relative_to(root).parts
    )


def traced_files(command: str, candidates: list[str]) -> set[str]:
    found = {path for path in candidates if re.search(rf"(?<![\w./-]){re.escape(path)}(?![\w./-])", command)}
    broad_reader = re.search(r"(?:^|[;&|]\s*)(?:rg|grep)\b", command)
    if broad_reader and re.search(r"(?:\s|^)(?:\.|\./|\*|\*\*)(?:\s|$)", command):
        found.update(candidates)
    return found


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
        "--ignore-rules",
        "-s",
        "workspace-write",
        "-C",
        str(root),
        "-",
    ]
    completed = subprocess.run(command, input=prompt, text=True, capture_output=True, check=False)
    reads: set[str] = set()
    messages: list[str] = []
    for line in completed.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get("item", {})
        if item.get("type") == "command_execution":
            reads.update(traced_files(str(item.get("command", "")), candidates))
        elif item.get("type") == "agent_message" and item.get("text"):
            messages.append(str(item["text"]))
    trace_path = root / ".eval" / "trace.json"
    trace_path.write_text(json.dumps({"files_read": sorted(reads)}, indent=2) + "\n", encoding="utf-8")
    if messages:
        print(messages[-1])
    if completed.returncode and completed.stderr:
        print(completed.stderr, file=sys.stderr)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
