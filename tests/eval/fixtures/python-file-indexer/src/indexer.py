from pathlib import Path


def build_index(source: Path, destination: Path) -> None:
    entries = sorted(path.name for path in source.glob("*.txt") if path.is_file())
    destination.write_text("\n".join(entries) + "\n", encoding="utf-8")
