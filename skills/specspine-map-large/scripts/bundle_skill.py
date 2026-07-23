#!/usr/bin/env python3
"""Bundle one skill body and all of its UTF-8 references into one file."""

from __future__ import annotations

import argparse
from pathlib import Path


SECTION_SEPARATOR = "\n\n---\n\n"


def strip_frontmatter(content: str) -> str:
    lines = content.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return content
    for index, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            return "".join(lines[index + 1 :]).lstrip("\r\n")
    raise ValueError("SKILL.md has an unclosed YAML frontmatter block")


def reference_files(references: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(references.rglob("*")):
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError(f"reference is not a readable regular file: {path}")
        files.append(path)
    if not files:
        raise ValueError(f"skill has no reference files: {references}")
    return files


def build_bundle(skill_root: Path) -> str:
    skill = skill_root / "SKILL.md"
    references = skill_root / "references"
    if not skill.is_file():
        raise ValueError(f"SKILL.md does not exist: {skill}")
    if not references.is_dir():
        raise ValueError(f"references directory does not exist: {references}")

    sections = [strip_frontmatter(skill.read_text(encoding="utf-8")).strip()]
    sections.extend(
        path.read_text(encoding="utf-8").strip()
        for path in reference_files(references)
    )
    return SECTION_SEPARATOR.join(sections) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        bundle = build_bundle(args.skill_root)
    except (OSError, UnicodeError, ValueError) as error:
        parser.error(str(error))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(bundle, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
