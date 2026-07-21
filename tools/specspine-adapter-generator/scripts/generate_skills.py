#!/usr/bin/env python3
"""Generate autonomous SpecSpine runtime skills from canonical package sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path


PACKAGES = (
    "specspine-init",
    "specspine-grow",
    "specspine-map",
    "specspine-doctor",
)
MANIFEST = ".generated-by-specspine-adapter-generator.json"
CONTRACT_VERSION = 1
IGNORED_NAMES = {".DS_Store", "__pycache__", MANIFEST}
SHARED_REFERENCES = (
    "spec-format.md",
    "spec-semantics.md",
    "context-handoff.md",
)
WORD_BUDGETS = {
    ("specspine-init", "SKILL.md"): 850,
    ("specspine-init", "assets/templates/agent-bootstrap.md"): 60,
    ("specspine-init", "assets/templates/project-binding.md"): 110,
    ("specspine-doctor", "SKILL.md"): 700,
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files_under(root: Path) -> dict[str, Path]:
    return {
        str(path.relative_to(root)): path
        for path in root.rglob("*")
        if path.is_file() and not any(part in IGNORED_NAMES for part in path.relative_to(root).parts)
    }


def package_files(source_root: Path, name: str) -> dict[str, Path]:
    files = files_under(source_root / name)
    entrypoint = files.pop("SKILL.md.src", None)
    if entrypoint is not None:
        files["SKILL.md"] = entrypoint
    if name in {"specspine-map", "specspine-doctor"}:
        common = source_root / "specspine-grow" / "references"
        for filename in SHARED_REFERENCES:
            files[f"references/{filename}"] = common / filename
    return files


def check_word_budgets(name: str, files: dict[str, Path]) -> list[str]:
    errors: list[str] = []
    for (package, relative), maximum in WORD_BUDGETS.items():
        if package != name or relative not in files:
            continue
        count = len(files[relative].read_text(encoding="utf-8").split())
        if count > maximum:
            errors.append(f"{name}: {relative} uses {count} words; budget is {maximum}")
    return errors


def read_manifest(target: Path) -> set[str]:
    path = target / MANIFEST
    if not path.is_file():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(item) for item in data.get("files", {})}


def check_package(source_files: dict[str, Path], target: Path) -> list[str]:
    errors: list[str] = []
    target_files = files_under(target) if target.is_dir() else {}
    for relative in sorted(source_files.keys() - target_files.keys()):
        errors.append(f"{target.name}: missing {relative}")
    for relative in sorted(target_files.keys() - source_files.keys()):
        errors.append(f"{target.name}: unexpected {relative}")
    for relative in sorted(source_files.keys() & target_files.keys()):
        if source_files[relative].read_bytes() != target_files[relative].read_bytes():
            errors.append(f"{target.name}: drifted {relative}")
    manifest = target / MANIFEST
    if not manifest.is_file():
        errors.append(f"{target.name}: missing {MANIFEST}")
    else:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        expected_hashes = {relative: digest(path) for relative, path in source_files.items()}
        if data.get("contract_version") != CONTRACT_VERSION:
            errors.append(f"{target.name}: incompatible SpecSpine contract version")
        if data.get("files") != expected_hashes:
            errors.append(f"{target.name}: stale generated manifest")
    return errors


def write_package(source_files: dict[str, Path], source: Path, target: Path) -> None:
    previously_generated = read_manifest(target)
    target.mkdir(parents=True, exist_ok=True)

    for relative in sorted(previously_generated - source_files.keys()):
        stale = target / relative
        if stale.is_file():
            stale.unlink()

    for relative, source_path in sorted(source_files.items()):
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + ".generated.tmp")
        shutil.copy2(source_path, temporary)
        temporary.replace(destination)

    for directory in sorted((path for path in target.rglob("*") if path.is_dir()), reverse=True):
        if not any(directory.iterdir()):
            directory.rmdir()

    manifest_data = {
        "contract_version": CONTRACT_VERSION,
        "generator": "specspine-adapter-generator",
        "source": f"assets/skill-sources/{source.name}",
        "files": {relative: digest(path) for relative, path in sorted(source_files.items())},
    }
    manifest_path = target / MANIFEST
    manifest_path.write_text(json.dumps(manifest_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, help="repository root; inferred by default")
    parser.add_argument("--skill", action="append", choices=PACKAGES, help="generate or check only this package")
    parser.add_argument("--check", action="store_true", help="report drift without writing")
    args = parser.parse_args()

    skill_root = Path(__file__).resolve().parents[1]
    repo_root = args.repo_root.resolve() if args.repo_root else skill_root.parents[1]
    source_root = skill_root / "assets" / "skill-sources"
    output_root = repo_root / "skills"
    selected = tuple(args.skill or PACKAGES)

    errors: list[str] = []
    prepared: list[tuple[str, Path, Path, dict[str, Path]]] = []
    for name in selected:
        source = source_root / name
        target = output_root / name
        if not (source / "SKILL.md.src").is_file():
            errors.append(f"{name}: canonical source is missing SKILL.md.src")
            continue
        generated_files = package_files(source_root, name)
        errors.extend(check_word_budgets(name, generated_files))
        prepared.append((name, source, target, generated_files))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    for name, source, target, generated_files in prepared:
        if args.check:
            errors.extend(check_package(generated_files, target))
        else:
            write_package(generated_files, source, target)
            print(f"generated {name}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    if args.check:
        print(f"generated packages are current: {len(selected)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
