#!/usr/bin/env python3
"""Validate or repair skill symlinks to canonical shared resources."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


PACKAGES = (
    "specspine-connect",
    "specspine-extract",
    "specspine-grow",
    "specspine-map",
    "specspine-map-large",
    "specspine-doctor",
)
IGNORED_NAMES = {
    ".DS_Store",
    "__pycache__",
    ".generated-by-specspine-adapter-generator.json",
}
SKILL_REFERENCES = {
    "specspine-connect": {
        "bootstrap-contract.md": "specspine-connect/bootstrap-contract.md",
    },
    "specspine-grow": {
        "examples.md": "specspine-grow/examples.md",
        "spec-format.md": "spec-format.md",
        "spec-semantics.md": "spec-semantics.md",
    },
    "specspine-map": {
        "examples.md": "specspine-map/examples.md",
        "mapping-method.md": "specspine-map/mapping-method.md",
        "spec-format.md": "spec-format.md",
        "spec-semantics.md": "spec-semantics.md",
    },
    "specspine-map-large": {
        "mapping-method.md": "specspine-map/mapping-method.md",
        "orchestration.md": "specspine-map-large/orchestration.md",
        "spec-format.md": "spec-format.md",
        "spec-semantics.md": "spec-semantics.md",
    },
    "specspine-doctor": {
        "review-method.md": "specspine-doctor/review-method.md",
        "spec-format.md": "spec-format.md",
        "spec-semantics.md": "spec-semantics.md",
    },
}
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


def shared_files(repo_root: Path, name: str) -> dict[str, Path]:
    shared_references = repo_root / "shared" / "references"
    return {
        f"references/{filename}": shared_references / shared_relative
        for filename, shared_relative in SKILL_REFERENCES.get(name, {}).items()
    }


def expected_link(source: Path, destination: Path) -> str:
    return Path(os.path.relpath(source, destination.parent)).as_posix()


def check_shared_links(source_files: dict[str, Path], target: Path) -> list[str]:
    errors: list[str] = []
    for relative, source in sorted(source_files.items()):
        destination = target / relative
        wanted = expected_link(source, destination)
        if not destination.is_symlink():
            errors.append(f"{target.name}: shared {relative} is not a symlink")
        elif os.readlink(destination) != wanted:
            errors.append(
                f"{target.name}: shared {relative} points to "
                f"{os.readlink(destination)!r}; expected {wanted!r}"
            )
        elif not destination.is_file():
            errors.append(f"{target.name}: shared {relative} symlink is broken")
    return errors


def write_links(source_files: dict[str, Path], target: Path) -> None:
    for relative, source in sorted(source_files.items()):
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + ".generated.tmp")
        if os.path.lexists(temporary):
            temporary.unlink()
        temporary.symlink_to(expected_link(source, destination))
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
    selected_reference_skills = tuple(name for name in selected if name in SKILL_REFERENCES)

    errors: list[str] = []
    for name in selected:
        source = skills_root / name
        if not (source / "SKILL.md").is_file():
            errors.append(f"{name}: canonical skill is missing SKILL.md")
            continue
        errors.extend(check_word_budgets(name, package_files(skills_root, name)))

    sources_by_skill = {
        name: shared_files(repo_root, name) for name in selected_reference_skills
    }
    if selected_reference_skills:
        unique_sources = {
            source
            for sources in sources_by_skill.values()
            for source in sources.values()
        }
        for source in sorted(unique_sources):
            if not source.is_file():
                errors.append(
                    "shared: canonical resource is missing "
                    f"{source.relative_to(repo_root)}"
                )

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    for name in selected_reference_skills:
        target = skills_root / name
        sources = sources_by_skill[name]
        if args.check:
            errors.extend(check_shared_links(sources, target))
        else:
            write_links(sources, target)
            print(f"repaired shared-resource symlinks for {name}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    if args.check:
        print(f"canonical skills and shared-resource symlinks are current: {len(selected)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
