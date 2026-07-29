#!/usr/bin/env python3
"""Validate or repair skill symlinks to canonical shared resources."""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path


PACKAGES = (
    "specspine-extract",
    "specspine-grow",
    "specspine-map",
    "specspine-doctor",
    "specspine-verify",
)
IGNORED_NAMES = {
    ".DS_Store",
    "__pycache__",
}
SKILL_REFERENCES = {
    "specspine-grow": {
        "spec-format.md": "spec-format.md",
        "spec-semantics.md": "spec-semantics.md",
        "specspine.schema.json": "specspine.schema.json",
    },
    "specspine-map": {
        "spec-format.md": "spec-format.md",
        "spec-semantics.md": "spec-semantics.md",
        "specspine.schema.json": "specspine.schema.json",
    },
    "specspine-doctor": {
        "spec-format.md": "spec-format.md",
        "spec-semantics.md": "spec-semantics.md",
        "specspine.schema.json": "specspine.schema.json",
    },
    "specspine-verify": {
        "spec-format.md": "spec-format.md",
        "spec-semantics.md": "spec-semantics.md",
        "specspine.schema.json": "specspine.schema.json",
    },
}
SKILL_SCRIPTS = {
    "specspine-extract": {
        "check_spine.py": "check_spine.py",
    },
    "specspine-grow": {
        "check_spine.py": "check_spine.py",
    },
    "specspine-map": {
        "bootstrap_spine.py": "bootstrap_spine.py",
        "check_spine.py": "check_spine.py",
    },
    "specspine-doctor": {
        "bootstrap_spine.py": "bootstrap_spine.py",
        "check_spine.py": "check_spine.py",
    },
    "specspine-verify": {
        "check_spine.py": "check_spine.py",
    },
}
SKILL_ASSETS = {
    "specspine-grow": {
        "templates/specspine.json": "templates/specspine.json",
    },
    "specspine-map": {
        "templates/specspine.json": "templates/specspine.json",
    },
    "specspine-doctor": {
        "templates/specspine.json": "templates/specspine.json",
    },
}
WORD_BUDGETS = {
    ("specspine-doctor", "SKILL.md"): 850,
    ("specspine-doctor", "assets/templates/agent-bootstrap.md"): 60,
    ("specspine-map", "SKILL.md"): 850,
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
    shared_root = repo_root / "shared"
    references = {
        f"references/{filename}": shared_root / "references" / shared_relative
        for filename, shared_relative in SKILL_REFERENCES.get(name, {}).items()
    }
    scripts = {
        f"scripts/{filename}": shared_root / "scripts" / shared_relative
        for filename, shared_relative in SKILL_SCRIPTS.get(name, {}).items()
    }
    assets = {
        f"assets/{filename}": shared_root / "assets" / shared_relative
        for filename, shared_relative in SKILL_ASSETS.get(name, {}).items()
    }
    return references | scripts | assets


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


def check_resource_ownership(repo_root: Path) -> list[str]:
    errors: list[str] = []
    consumers_by_source: dict[Path, set[str]] = {}
    for name in PACKAGES:
        for source in shared_files(repo_root, name).values():
            consumers_by_source.setdefault(source, set()).add(name)

    for source in files_under(repo_root / "shared").values():
        consumers = consumers_by_source.get(source, set())
        if len(consumers) < 2:
            relative = source.relative_to(repo_root)
            errors.append(
                f"{relative}: shared resource has {len(consumers)} skill consumers; "
                "keep resources used by only one skill in that skill"
            )

    duplicates: dict[bytes, list[Path]] = {}
    for name in PACKAGES:
        for path in package_files(repo_root / "skills", name).values():
            if path.is_symlink():
                continue
            digest = hashlib.sha256(path.read_bytes()).digest()
            duplicates.setdefault(digest, []).append(path)
    for paths in duplicates.values():
        skills = {path.relative_to(repo_root / "skills").parts[0] for path in paths}
        if len(skills) > 1:
            rendered = ", ".join(str(path.relative_to(repo_root)) for path in sorted(paths))
            errors.append(
                f"duplicate regular skill resources must use a shared owner and symlinks: {rendered}"
            )
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
    selected_resource_skills = tuple(
        name for name in selected if name in SKILL_REFERENCES or name in SKILL_SCRIPTS
    )

    errors: list[str] = []
    errors.extend(check_resource_ownership(repo_root))
    for name in selected:
        source = skills_root / name
        if not (source / "SKILL.md").is_file():
            errors.append(f"{name}: canonical skill is missing SKILL.md")
            continue
        errors.extend(check_word_budgets(name, package_files(skills_root, name)))

    sources_by_skill = {
        name: shared_files(repo_root, name) for name in selected_resource_skills
    }
    if selected_resource_skills:
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

    for name in selected_resource_skills:
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
