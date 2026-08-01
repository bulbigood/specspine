#!/usr/bin/env python3
"""Run the deterministic Specspine v5 integration suite."""

from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEST_DIRECTORY = ROOT / "tests/mechanical"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-p", "--pattern", default="test_*.py")
    args = parser.parse_args(argv)
    suite = unittest.defaultTestLoader.discover(
        str(TEST_DIRECTORY), pattern=args.pattern, top_level_dir=str(TEST_DIRECTORY)
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
