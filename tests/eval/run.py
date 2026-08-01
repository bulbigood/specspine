#!/usr/bin/env python3
"""Run Gherkin skill scenarios and let an independent LLM judge the outcome."""

from __future__ import annotations

import argparse
import concurrent.futures
import difflib
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FEATURES = Path(__file__).with_name("features")
FIXTURE = ROOT / "examples/node-express-boilerplate"
SCHEMA = Path(__file__).with_name("judge.schema.json")
DEFAULT_AGENT = "codex exec --ephemeral --skip-git-repo-check -s workspace-write -"
DEFAULT_JUDGE = (
    f"codex exec --ephemeral --skip-git-repo-check -s read-only "
    f"-m gpt-5.6-sol -c model_reasoning_effort=\"low\" "
    f"--output-schema {shlex.quote(str(SCHEMA))} -"
)


@dataclass(frozen=True)
class Scenario:
    feature: str
    name: str
    preparation: str
    request: str
    rubric: str

    @property
    def slug(self) -> str:
        value = "-".join(self.name.lower().split())
        return "".join(ch for ch in value if ch.isalnum() or ch == "-")


def parse_feature(path: Path) -> list[Scenario]:
    feature = ""
    current: dict[str, str] | None = None
    scenarios: list[Scenario] = []
    capture: str | None = None
    captured: list[str] = []

    def finish_capture() -> None:
        nonlocal capture, captured
        if current is not None and capture:
            current[capture] = "\n".join(captured).strip()
        capture, captured = None, []

    def finish_scenario() -> None:
        if current is None:
            return
        required = {"name", "preparation", "request", "rubric"}
        missing = required - current.keys()
        if missing:
            raise ValueError(f"{path}: incomplete scenario {current.get('name')}: {sorted(missing)}")
        scenarios.append(Scenario(feature=feature, **current))

    lines = path.read_text(encoding="utf-8").splitlines()
    for raw in lines:
        line = raw.strip()
        if line == '"""':
            if capture:
                finish_capture()
            elif current is not None:
                capture = "request" if "request" not in current else "rubric"
            continue
        if capture:
            captured.append(raw.strip())
        elif line.startswith("Feature:"):
            feature = line.removeprefix("Feature:").strip()
        elif line.startswith("Scenario:"):
            finish_scenario()
            current = {"name": line.removeprefix("Scenario:").strip()}
        elif line.startswith('Given preparation "') and current is not None:
            current["preparation"] = line.split('"', 2)[1]
    finish_capture()
    finish_scenario()
    return scenarios


def replace(path: Path, old: str, new: str) -> None:
    value = path.read_text(encoding="utf-8")
    if old not in value:
        raise ValueError(f"Preparation anchor not found in {path}: {old!r}")
    path.write_text(value.replace(old, new), encoding="utf-8")


def prepare(workspace: Path, name: str) -> None:
    if name == "baseline":
        return
    authentication = workspace / "specspine/authentication.md"
    if name == "missing-inactive-login":
        replace(
            authentication,
            "- REQ-invalid-credentials — Invalid credentials reveal no account secrets.\n",
            "- REQ-invalid-credentials — Invalid credentials reveal no account secrets.\n"
            "- REQ-inactive-login — Inactive users must be rejected without revealing whether the account exists.\n",
        )
        replace(
            authentication,
            "- VER-login — Black-box login tests cover success and invalid credentials.\n",
            "- VER-login — Black-box login tests cover success and invalid credentials.\n"
            "- VER-inactive-login — A black-box test proves inactive users receive the same generic rejection as invalid credentials.\n",
        )
        return
    if name == "forbidden-registration":
        replace(
            authentication,
            "## Verification\n",
            "## Invariants\n\n- INV-no-public-registration — Public self-registration must not be exposed.\n\n"
            "## Verification\n",
        )
        return
    if name == "uncovered-audit-webhook":
        replace(authentication, "external-boundary: open", "external-boundary: exhaustive")
        service = workspace / "src/services/audit.service.js"
        service.write_text(
            "const https = require('https');\n\n"
            "const recordLogin = (userId) => https.get(`https://audit.invalid/login/${userId}`);\n\n"
            "module.exports = { recordLogin };\n",
            encoding="utf-8",
        )
        controller = workspace / "src/controllers/auth.controller.js"
        replace(
            controller,
            "const { authService, userService, tokenService, emailService } = require('../services');",
            "const { authService, userService, tokenService, emailService } = require('../services');\n"
            "const auditService = require('../services/audit.service');",
        )
        replace(controller, "  const tokens = await tokenService.generateAuthTokens(user);\n  res.send({ user, tokens });", "  const tokens = await tokenService.generateAuthTokens(user);\n  auditService.recordLogin(user.id);\n  res.send({ user, tokens });")
        return
    if name == "unsafe-user-export":
        route = workspace / "src/routes/v1/user.route.js"
        replace(
            route,
            "router\n  .route('/')",
            "router.get('/export', auth('getUsers'), async (req, res) => {\n"
            "  const users = await require('../../models/user.model').find({}).select('+password').lean();\n"
            "  res.send(users);\n"
            "});\n\nrouter\n  .route('/')",
        )
        return
    raise ValueError(f"Unknown preparation: {name}")


def files(workspace: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(workspace.rglob("*")):
        if not path.is_file() or ".git" in path.parts or "node_modules" in path.parts:
            continue
        relative = str(path.relative_to(workspace))
        try:
            result[relative] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            result[relative] = f"<binary sha256={hashlib.sha256(path.read_bytes()).hexdigest()}>"
    return result


def diff(before: dict[str, str], after: dict[str, str]) -> str:
    chunks: list[str] = []
    for name in sorted(before.keys() | after.keys()):
        if before.get(name) == after.get(name):
            continue
        chunks.extend(
            difflib.unified_diff(
                before.get(name, "").splitlines(),
                after.get(name, "").splitlines(),
                fromfile=f"before/{name}",
                tofile=f"after/{name}",
                lineterm="",
            )
        )
    return "\n".join(chunks)


def run_command(command: str, prompt: str, cwd: Path, timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        shlex.split(command), input=prompt, text=True, capture_output=True,
        cwd=cwd, timeout=timeout, check=False,
    )


def install_project_skills(workspace: Path) -> None:
    destination = workspace / ".agents/skills"
    destination.mkdir(parents=True, exist_ok=True)
    for source in sorted((ROOT / "skills").glob("iwe-spec-*")):
        # Renamed working trees may temporarily retain dangling legacy symlinks.
        # They are not part of the skill contract and must not block an eval.
        shutil.copytree(
            source,
            destination / source.name,
            symlinks=False,
            ignore_dangling_symlinks=True,
        )


def agent_prompt(scenario: Scenario) -> str:
    paths = ", ".join(f".agents/skills/{name}/SKILL.md" for name in (
        "iwe-spec-map", "iwe-spec-specify", "iwe-spec-verify", "iwe-spec-implement"
    ))
    return (
        f"You are operating in an isolated test repository. The relevant skills are {paths}. "
        "Read every skill explicitly named by the operator and follow it. Act autonomously, "
        "edit when requested, and leave the workspace in the requested final state. Node.js "
        "dependencies and test environment are already prepared; do not install or upgrade "
        "packages. Run focused Jest tests when implementation changes.\n\n"
        f"Operator request:\n{scenario.request}\n"
    )


def judge_prompt(scenario: Scenario, transcript: str, changes: str) -> str:
    return f"""You are the independent AI judge for a skill integration test.
Inspect the current workspace directly. Evaluate semantics, not exact strings or a mechanical
golden patch. Do not modify files. Be strict: pass only if the operator request and rubric are
substantively satisfied. Agent claims are not evidence unless supported by workspace artifacts
or credible command output. A score below 80 must set pass=false.

Feature: {scenario.feature}
Scenario: {scenario.name}
Operator request:
{scenario.request}

Rubric:
{scenario.rubric}

Workspace diff produced by the agent:
{changes or '<no file changes>'}

Agent final output and command log:
{transcript}

Return only the JSON object required by the configured schema.
"""


def load_scenarios() -> list[Scenario]:
    return [scenario for path in sorted(FEATURES.glob("*.feature")) for scenario in parse_feature(path)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", action="append", help="substring filter; repeatable")
    parser.add_argument("--exclude-scenario", action="append", help="substring exclusion; repeatable")
    parser.add_argument("--list", action="store_true", help="list scenarios without running")
    parser.add_argument("--keep-workspaces", action="store_true")
    parser.add_argument("--jobs", type=int, default=10, help="parallel scenarios (default: 10)")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--agent-command", default=os.environ.get("SPECSPINE_AGENT_COMMAND", DEFAULT_AGENT))
    parser.add_argument("--judge-command", default=os.environ.get("SPECSPINE_JUDGE_COMMAND", DEFAULT_JUDGE))
    args = parser.parse_args(argv)
    scenarios = load_scenarios()
    if args.scenario:
        scenarios = [item for item in scenarios if any(value.lower() in item.name.lower() for value in args.scenario)]
    if args.exclude_scenario:
        scenarios = [item for item in scenarios if not any(value.lower() in item.name.lower() for value in args.exclude_scenario)]
    if args.list:
        for item in scenarios:
            print(f"{item.feature} :: {item.name} [{item.preparation}]")
        return 0
    if not scenarios:
        parser.error("no scenarios selected")
    if args.jobs < 1:
        parser.error("--jobs must be at least 1")

    dependency_root = FIXTURE / "node_modules"
    if not (dependency_root / ".bin/jest").is_file():
        installed = subprocess.run(
            ["yarn", "install", "--frozen-lockfile", "--ignore-scripts"],
            cwd=FIXTURE,
            text=True,
            check=False,
        )
        if installed.returncode != 0:
            parser.error("could not install fixture dependencies with yarn")
    runtime_probe = subprocess.run(
        [
            "node",
            "-e",
            "const {MongoMemoryServer}=require('mongodb-memory-server');"
            "MongoMemoryServer.create().then(async server=>server.stop())"
            ".catch(error=>{console.error(error);process.exit(1)});",
        ],
        cwd=FIXTURE,
        text=True,
        check=False,
    )
    if runtime_probe.returncode != 0:
        parser.error("could not start the fixture's in-memory MongoDB test runtime")

    report_dir = Path(__file__).with_name("reports")
    report_dir.mkdir(exist_ok=True)

    def run_scenario(scenario: Scenario) -> bool:
        temporary = Path(tempfile.mkdtemp(prefix=f"iwe-eval-{scenario.slug[:32]}-"))
        workspace = temporary / "workspace"
        try:
            shutil.copytree(FIXTURE, workspace, ignore=shutil.ignore_patterns("node_modules"))
            (workspace / "node_modules").symlink_to(dependency_root, target_is_directory=True)
            shutil.copy2(workspace / ".env.example", workspace / ".env")
            prepare(workspace, scenario.preparation)
            install_project_skills(workspace)
            before = files(workspace)
            agent = run_command(args.agent_command, agent_prompt(scenario), workspace, args.timeout)
            after = files(workspace)
            changes = diff(before, after)
            transcript = f"exit={agent.returncode}\nstdout:\n{agent.stdout}\nstderr:\n{agent.stderr}"
            judge = run_command(args.judge_command, judge_prompt(scenario, transcript, changes), workspace, args.timeout)
            try:
                verdict = json.loads(judge.stdout)
            except json.JSONDecodeError:
                verdict = {"pass": False, "score": 0, "rationale": "Judge returned invalid JSON", "evidence": [judge.stdout, judge.stderr]}
            if agent.returncode != 0 or judge.returncode != 0:
                verdict["pass"] = False
                verdict["rationale"] = f"Execution failure. {verdict.get('rationale', '')}".strip()
            result = {"feature": scenario.feature, "scenario": scenario.name, "preparation": scenario.preparation, "agent_exit": agent.returncode, "judge_exit": judge.returncode, "verdict": verdict, "workspace": str(workspace) if args.keep_workspaces else None}
            (report_dir / f"{scenario.slug}.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            status = "PASS" if verdict.get("pass") else "FAIL"
            print(
                f"{status} {scenario.name}: {verdict.get('score', 0)} — "
                f"{verdict.get('rationale', '')}",
                flush=True,
            )
            return bool(verdict.get("pass"))
        finally:
            if not args.keep_workspaces:
                shutil.rmtree(temporary)

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(args.jobs, len(scenarios))) as executor:
        results = list(executor.map(run_scenario, scenarios))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
