#!/usr/bin/env python3
"""Synchronize shared resources between canonical publishable skills."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


PACKAGES = (
    "specspine-connect",
    "specspine-extract",
    "specspine-grow",
    "specspine-map",
    "specspine-doctor",
)
IGNORED_NAMES = {
    ".DS_Store",
    "__pycache__",
    ".generated-by-specspine-adapter-generator.json",
}
SHARED_OWNER = "specspine-grow"
SHARED_CONSUMERS = ("specspine-map", "specspine-doctor")
SHARED_REFERENCES = (
    "spec-format.md",
    "spec-semantics.md",
)
WORD_BUDGETS = {
    ("specspine-connect", "SKILL.md"): 850,
    ("specspine-connect", "assets/templates/agent-bootstrap.md"): 60,
    ("specspine-doctor", "SKILL.md"): 700,
}


def files_under(root: Path) -> dict[str, Path]:
    if not root.is_dir():
        return {}
    return {
        str(path.relative_to(root)): path
        for path in root.rglob("*")
        if path.is_file() and not any(part in IGNORED_NAMES for part in path.relative_to(root).parts)
    }


def package_files(skills_root: Path, name: str) -> dict[str, Path]:
    return files_under(skills_root / name)


def check_word_budgets(name: str, files: dict[str, Path]) -> list[str]:
    errors: list[str] = []
    for (package, relative), maximum in WORD_BUDGETS.items():
        if package != name or relative not in files:
            continue
        count = len(files[relative].read_text(encoding="utf-8").split())
        if count > maximum:
            errors.append(f"{name}: {relative} uses {count} words; budget is {maximum}")
    return errors


def shared_files(skills_root: Path) -> dict[str, Path]:
    owner_references = skills_root / SHARED_OWNER / "references"
    return {
        f"references/{filename}": owner_references / filename
        for filename in SHARED_REFERENCES
    }


def check_shared_files(source_files: dict[str, Path], target: Path) -> list[str]:
    errors: list[str] = []
    for relative, source in sorted(source_files.items()):
        destination = target / relative
        if not destination.is_file():
            errors.append(f"{target.name}: missing shared {relative}")
        elif source.read_bytes() != destination.read_bytes():
            errors.append(f"{target.name}: drifted shared {relative}")
    return errors


def write_files(source_files: dict[str, Path], target: Path) -> None:
    for relative, source in sorted(source_files.items()):
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + ".generated.tmp")
        shutil.copy2(source, temporary)
        temporary.replace(destination)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, help="repository root; inferred by default")
    parser.add_argument("--skill", action="append", choices=PACKAGES, help="generate or check only this package")
    parser.add_argument("--check", action="store_true", help="report drift without writing")
    args = parser.parse_args()

    tool_root = Path(__file__).resolve().parents[1]
    repo_root = args.repo_root.resolve() if args.repo_root else tool_root.parents[1]
    skills_root = repo_root / "skills"
    selected = tuple(args.skill or PACKAGES)
    selected_consumers = (
        SHARED_CONSUMERS
        if SHARED_OWNER in selected
        else tuple(name for name in selected if name in SHARED_CONSUMERS)
    )
    validation_names = tuple(
        name for name in PACKAGES if name in selected or name in selected_consumers
    )

    errors: list[str] = []
    for name in validation_names:
        source = skills_root / name
        if not (source / "SKILL.md").is_file():
            errors.append(f"{name}: canonical skill is missing SKILL.md")
            continue
        errors.extend(check_word_budgets(name, package_files(skills_root, name)))

    sources = shared_files(skills_root) if selected_consumers else {}
    if selected_consumers:
        for relative, source in sources.items():
            if not source.is_file():
                errors.append(f"{SHARED_OWNER}: canonical shared resource is missing {relative}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    for consumer in selected_consumers:
        target = skills_root / consumer
        if args.check:
            errors.extend(check_shared_files(sources, target))
        else:
            write_files(sources, target)
            print(f"synchronized shared resources for {consumer}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    if args.check:
        print(f"canonical skills and shared resources are current: {len(selected)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
