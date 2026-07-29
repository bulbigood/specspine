#!/usr/bin/env python3
"""Run the required SpecSpine skill pre-publication checks."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RENDERER = ROOT / "shared/scripts/render_vocabulary.py"


def run(command: list[str], *, environment: dict[str, str] | None = None) -> None:
    rendered = " ".join(command)
    print(f"+ {rendered}", flush=True)
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update-generated",
        action="store_true",
        help="regenerate the glossary before checking it",
    )
    parser.add_argument(
        "--skip-npx",
        action="store_true",
        help="skip the standalone npx installation check (not for publication)",
    )
    args = parser.parse_args()

    if args.update_generated:
        run([sys.executable, str(RENDERER), "--write"])
    run([sys.executable, str(RENDERER)])
    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests/mechanical",
            "-p",
            "test_*.py",
        ]
    )
    if not args.skip_npx:
        environment = dict(os.environ)
        environment["SPECSPINE_RUN_NPX"] = "1"
        run(
            [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                "tests/mechanical",
                "-p",
                "test_npx_install.py",
            ],
            environment=environment,
        )
    print("SpecSpine pre-publication checks passed.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
