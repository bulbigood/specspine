#!/usr/bin/env python3
"""Run a live Codex eval and emit a conservative file-read trace."""

from __future__ import annotations

import argparse
import json
import os
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


def scope_violations(commands: list[str], root: Path) -> list[str]:
    root_text = str(root.resolve()).rstrip("/")
    violations: list[str] = []
    for command in commands:
        inspected = command.replace(root_text, "<WORKSPACE>")
        markers = [marker for marker in FORBIDDEN_SCOPE_MARKERS if marker in inspected]
        audit_text = re.sub(r"!\.\./[^\s'\"|;&]*", "<NEGATED_PARENT_GLOB>", inspected)
        if re.search(r"(?<![.\w])\.\.(?:/|\b)", audit_text):
            markers.append("parent traversal (`..`)")
        if re.search(
            r"(?:^|[;&|]\s*|\s)(?:cd|find|ls|tree|du)\s+(?:-[^\s]+\s+)*/(?:\s|$)",
            inspected,
        ):
            markers.append("filesystem-root traversal (`/`)")
        allowed_eval = re.sub(
            r"(?:\./)?\.eval/(?:skill|companions)(?:/[^\s'\"]*)?",
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
        ):
            allowed_eval = re.sub(pattern, "<EVAL_EXCLUSION>", allowed_eval)
        if re.search(r"(?:^|[\s'\"])(?:\./)?\.eval(?:/|\b)", allowed_eval):
            markers.append("evaluator internals (`.eval`)")
        if markers:
            violations.append(
                f"external path marker(s) {', '.join(sorted(set(markers)))} in command: "
                + inspected[:500].replace("\n", "\\n")
            )
    return violations


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


def stage_runtime_tools(runtime_root: Path) -> None:
    """Copy essential user-installed executables into the permitted ephemeral runtime."""
    for name in ("node", "rg"):
        source = shutil.which(name)
        if not source:
            continue
        resolved = Path(source).resolve()
        if resolved.is_file():
            shutil.copy2(resolved, runtime_root / "bin" / name)


def build_codex_command(model: str, reasoning_effort: str, root: Path, runtime_root: Path) -> list[str]:
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
        + '"."="write",".git"="read",".agents"="read",".codex"="read"'
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gpt-5.6-luna")
    parser.add_argument("--reasoning-effort", default="medium")
    args = parser.parse_args()

    root = Path.cwd()
    prompt = sys.stdin.read()
    candidates = relative_files(root)
    eval_dir = root / ".eval"
    runtime_root = Path(tempfile.mkdtemp(prefix="specspine-runtime-", dir=root.parent))
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
        command = build_codex_command(args.model, args.reasoning_effort, root, runtime_root)
        process_environment = os.environ.copy()
        process_environment["CODEX_HOME"] = str(codex_home)
        started = time.monotonic()
        completed = subprocess.run(
            command,
            input=prompt,
            text=True,
            capture_output=True,
            check=False,
            env=process_environment,
        )
    finally:
        shutil.rmtree(runtime_root)
    duration_seconds = round(time.monotonic() - started, 3)
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
    token_usage = parse_token_usage(completed.stdout)
    boundary_violations = scope_violations(commands, root)
    final_response = messages[-1] if messages else ""
    trace_path = eval_dir / "trace.json"
    trace_path.write_text(
        json.dumps(
            {
                "commands": commands,
                "duration_seconds": duration_seconds,
                "eval_case": os.environ.get("SPECSPINE_EVAL_CASE", ""),
                "eval_run": os.environ.get("SPECSPINE_EVAL_RUN", ""),
                "files_read": sorted(reads),
                "scope_violations": boundary_violations,
                "model": args.model,
                "reasoning_effort": args.reasoning_effort,
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
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
