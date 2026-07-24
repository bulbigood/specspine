#!/usr/bin/env python3
"""Bundle the bounded SpecSpine Map producer contract into one file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


SECTION_SEPARATOR = "\n\n---\n\n"
PRODUCER_REFERENCE_NAMES = (
    "bounded-mode.md",
    "spec-semantics.md",
    "spec-format.md",
    "mapping-method.md",
)


def producer_reference_files(skill_root: Path) -> list[Path]:
    references = skill_root / "references"
    files = [references / name for name in PRODUCER_REFERENCE_NAMES]
    for path in files:
        if not path.is_file():
            raise ValueError(f"producer reference is not a readable regular file: {path}")
    return files


def template_files(templates: Path) -> list[Path]:
    if not templates.exists():
        return []
    if not templates.is_dir():
        raise ValueError(f"templates path is not a directory: {templates}")
    files: list[Path] = []
    for path in sorted(templates.rglob("*.md")):
        if not path.is_file():
            raise ValueError(f"template is not a readable regular file: {path}")
        files.append(path)
    return files


def build_bundle(skill_root: Path) -> str:
    templates = skill_root / "assets" / "templates"
    sections = [
        path.read_text(encoding="utf-8").strip()
        for path in producer_reference_files(skill_root)
    ]
    sections.extend(
        path.read_text(encoding="utf-8").strip()
        for path in template_files(templates)
    )
    return SECTION_SEPARATOR.join(sections) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--print",
        action="store_true",
        dest="print_bundle",
        help="also write the complete bundle to stdout",
    )
    args = parser.parse_args()
    try:
        bundle = build_bundle(args.skill_root)
    except (OSError, UnicodeError, ValueError) as error:
        parser.error(str(error))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(bundle, encoding="utf-8")
    if args.print_bundle:
        sys.stdout.write(bundle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
