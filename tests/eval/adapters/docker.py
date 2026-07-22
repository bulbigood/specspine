#!/usr/bin/env python3
"""Run one Codex evaluation in a fresh, restricted Docker container."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DOCKERFILE = ROOT / "tests" / "eval" / "docker" / "agent.Dockerfile"
IMAGE_INPUTS = (
    DOCKERFILE,
    ROOT / "tests" / "eval" / "docker" / "preflight.sh",
    ROOT / "tests" / "eval" / "adapters" / "codex.py",
)
DEFAULT_IMAGE_REPOSITORY = "specspine-eval-agent"


class EnvironmentFailure(RuntimeError):
    pass


def cache_root() -> Path:
    configured = os.environ.get("SPECSPINE_EVAL_DOCKER_CACHE_DIR")
    root = Path(configured).expanduser() if configured else Path.home() / ".cache" / "specspine-eval" / "docker"
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def image_source_hash() -> str:
    digest = hashlib.sha256()
    for path in IMAGE_INPUTS:
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\n")
    return digest.hexdigest()


def image_reference() -> str:
    repository = os.environ.get("SPECSPINE_EVAL_DOCKER_IMAGE", DEFAULT_IMAGE_REPOSITORY)
    return f"{repository}:{image_source_hash()[:16]}"


def run_checked(command: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise EnvironmentFailure(f"command failed ({completed.returncode}): {' '.join(command)}\n{detail}")
    return completed


def inspect_image(reference: str) -> str | None:
    completed = subprocess.run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", reference],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def docker_user() -> tuple[int, int]:
    return os.getuid(), os.getgid()


def common_security_args(uid: int, gid: int) -> list[str]:
    return [
        "--user", f"{uid}:{gid}",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--pids-limit=256",
        "--memory", os.environ.get("SPECSPINE_EVAL_DOCKER_MEMORY", "2g"),
        "--cpus", os.environ.get("SPECSPINE_EVAL_DOCKER_CPUS", "2"),
        "--tmpfs", f"/runtime:rw,nosuid,nodev,size=512m,uid={uid},gid={gid},mode=0700",
        "--tmpfs", f"/home/eval:rw,nosuid,nodev,size=128m,uid={uid},gid={gid},mode=0700",
    ]


def run_preflight(reference: str, image_id: str, cache: Path) -> None:
    marker = cache / "preflight" / f"{image_source_hash()}.json"
    if marker.is_file():
        try:
            if json.loads(marker.read_text(encoding="utf-8")).get("image_id") == image_id:
                return
        except (json.JSONDecodeError, OSError):
            pass
    marker.parent.mkdir(parents=True, exist_ok=True)
    workspaces = cache / "preflight-workspaces"
    workspaces.mkdir(parents=True, exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix="preflight-", dir=workspaces))
    uid, gid = docker_user()
    try:
        command = [
            "docker", "run", "--rm", "--network=none",
            *common_security_args(uid, gid),
            "--mount", f"type=bind,src={workspace},dst=/workspace",
            "--workdir", "/workspace",
            "--entrypoint", "/usr/local/bin/specspine-preflight",
            reference,
        ]
        run_checked(command)
        marker.write_text(
            json.dumps({"image": reference, "image_id": image_id}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    finally:
        shutil.rmtree(workspace)


def ensure_image() -> tuple[str, str]:
    if not shutil.which("docker"):
        raise EnvironmentFailure("docker CLI is unavailable")
    cache = cache_root()
    lock_path = cache / "image.lock"
    with lock_path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        reference = image_reference()
        image_id = inspect_image(reference)
        if image_id is None:
            completed = subprocess.run(
                [
                    "docker", "build",
                    "--file", str(DOCKERFILE),
                    "--tag", reference,
                    "--label", f"org.specspine.eval.source-sha256={image_source_hash()}",
                    str(ROOT),
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            if completed.returncode:
                raise EnvironmentFailure(f"Docker image build failed\n{completed.stdout.strip()}")
            image_id = inspect_image(reference)
            if image_id is None:
                raise EnvironmentFailure(f"built image cannot be inspected: {reference}")
        run_preflight(reference, image_id, cache)
        return reference, image_id


def auth_file() -> Path:
    configured = os.environ.get("SPECSPINE_EVAL_AUTH_FILE")
    source = Path(configured).expanduser() if configured else Path(
        os.environ.get("CODEX_HOME", Path.home() / ".codex")
    ) / "auth.json"
    source = source.resolve()
    if not source.is_file():
        raise EnvironmentFailure(f"Codex authentication file is missing: {source}")
    return source


def write_environment_failure(root: Path, message: str) -> None:
    target = root / ".eval"
    target.mkdir(exist_ok=True)
    (target / "trace.json").write_text(
        json.dumps(
            {
                "environment_invalid": True,
                "environment_errors": [message],
                "files_read": [],
                "scope_violations": [],
                "token_usage": {},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def enrich_trace(root: Path, reference: str, image_id: str) -> None:
    path = root / ".eval" / "trace.json"
    if not path.is_file():
        raise EnvironmentFailure("container did not produce .eval/trace.json")
    trace = json.loads(path.read_text(encoding="utf-8"))
    trace["execution_environment"] = {
        "kind": "docker",
        "image": reference,
        "image_id": image_id,
        "source_sha256": image_source_hash(),
    }
    path.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gpt-5.6-luna")
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    root = Path.cwd().resolve()
    try:
        reference, image_id = ensure_image()
        if args.preflight:
            print(json.dumps({"image": reference, "image_id": image_id}, sort_keys=True))
            return 0
        prompt = sys.stdin.read()
        authentication = auth_file()
        uid, gid = docker_user()
        name = "specspine-eval-" + uuid.uuid4().hex[:16]
        command = [
            "docker", "run", "--rm", "--interactive", "--name", name,
            *common_security_args(uid, gid),
            "--mount", f"type=bind,src={root},dst=/workspace",
            "--mount", f"type=bind,src={authentication},dst=/auth/auth.json,readonly",
            "--workdir", "/workspace",
            "--env", "CODEX_HOME=/auth",
            "--env", "HOME=/home/eval",
            "--env", "OPENSSL_CONF=/dev/null",
        ]
        for key in (
            "SPECSPINE_COMPARISON",
            "SPECSPINE_COMPARISON_SAMPLE",
            "SPECSPINE_EVAL_CASE",
            "SPECSPINE_EVAL_RUN",
            "SPECSPINE_EVAL_STAGE",
        ):
            value = os.environ.get(key)
            if value is not None:
                command.extend(["--env", f"{key}={value}"])
        command.extend(
            [reference, "--model", args.model, "--reasoning-effort", args.reasoning_effort]
        )
        completed = subprocess.run(
            command,
            input=prompt,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.stdout:
            sys.stdout.write(completed.stdout)
        if completed.stderr:
            sys.stderr.write(completed.stderr)
        if completed.returncode:
            raise EnvironmentFailure(f"agent container exited with {completed.returncode}")
        enrich_trace(root, reference, image_id)
        return 0
    except (EnvironmentFailure, json.JSONDecodeError, OSError) as error:
        message = str(error)
        write_environment_failure(root, message)
        print(message, file=sys.stderr)
        return 70


if __name__ == "__main__":
    raise SystemExit(main())
