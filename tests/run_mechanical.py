#!/usr/bin/env python3
"""Discover and run the mechanical test suite in parallel worker processes."""

from __future__ import annotations

import argparse
import io
import os
import sys
import tempfile
import unittest
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEST_DIRECTORY = ROOT / "tests" / "mechanical"


def default_jobs(cpu_count: int | None = None) -> int:
    """Leave one logical CPU available for the host, but always run a worker."""
    available = os.cpu_count() if cpu_count is None else cpu_count
    return max(1, (available or 1) - 1)


def discover_test_ids(pattern: str) -> list[str]:
    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=str(TEST_DIRECTORY),
        pattern=pattern,
        top_level_dir=str(TEST_DIRECTORY),
    )
    return [test.id() for test in _flatten(suite)]


def _flatten(suite: unittest.TestSuite) -> list[unittest.TestCase]:
    tests: list[unittest.TestCase] = []
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            tests.extend(_flatten(test))
        else:
            tests.append(test)
    return tests


@dataclass(frozen=True)
class TestOutcome:
    test_id: str
    tests_run: int
    failures: int
    errors: int
    skipped: int
    expected_failures: int
    unexpected_successes: int
    output: str

    @property
    def successful(self) -> bool:
        return not (self.failures or self.errors or self.unexpected_successes)


def run_test(test_id: str) -> TestOutcome:
    """Run one test in a worker and return a serializable result."""
    sys.path.insert(0, str(TEST_DIRECTORY))
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromName(test_id)
    with tempfile.TemporaryFile() as captured:
        saved_stdout = os.dup(1)
        saved_stderr = os.dup(2)
        try:
            sys.stdout.flush()
            sys.stderr.flush()
            os.dup2(captured.fileno(), 1)
            os.dup2(captured.fileno(), 2)
            result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
            sys.stdout.flush()
            sys.stderr.flush()
        finally:
            os.dup2(saved_stdout, 1)
            os.dup2(saved_stderr, 2)
            os.close(saved_stdout)
            os.close(saved_stderr)
        captured.seek(0)
        child_output = captured.read().decode(errors="replace")
    output = stream.getvalue()
    if child_output:
        output += f"\nCaptured process output:\n{child_output}"
    return TestOutcome(
        test_id=test_id,
        tests_run=result.testsRun,
        failures=len(result.failures),
        errors=len(result.errors),
        skipped=len(result.skipped),
        expected_failures=len(result.expectedFailures),
        unexpected_successes=len(result.unexpectedSuccesses),
        output=output,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=default_jobs(),
        help="parallel worker processes (default: available CPUs minus one)",
    )
    parser.add_argument(
        "-p",
        "--pattern",
        default="test_*.py",
        help="unittest discovery filename pattern",
    )
    args = parser.parse_args(argv)
    if args.jobs < 1:
        parser.error("--jobs must be at least 1")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    test_ids = discover_test_ids(args.pattern)
    if not test_ids:
        print(f"No mechanical tests found for pattern {args.pattern!r}.", file=sys.stderr)
        return 1

    worker_count = min(args.jobs, len(test_ids))
    print(
        f"Running {len(test_ids)} mechanical tests with "
        f"{worker_count} parallel workers.",
        flush=True,
    )
    outcomes: list[TestOutcome] = []
    with ProcessPoolExecutor(max_workers=worker_count) as executor:
        futures = {executor.submit(run_test, test_id): test_id for test_id in test_ids}
        for future in as_completed(futures):
            test_id = futures[future]
            try:
                outcome = future.result()
            except BaseException as error:
                outcome = TestOutcome(
                    test_id=test_id,
                    tests_run=0,
                    failures=0,
                    errors=1,
                    skipped=0,
                    expected_failures=0,
                    unexpected_successes=0,
                    output=f"Worker failed: {error!r}\n",
                )
            outcomes.append(outcome)
            print("." if outcome.successful else "F", end="", flush=True)
    print()

    failed = [outcome for outcome in outcomes if not outcome.successful]
    for outcome in sorted(failed, key=lambda item: item.test_id):
        print(f"\nFAIL: {outcome.test_id}\n{outcome.output}", end="")

    print(
        f"\nDiscovered {len(test_ids)} tests; "
        f"ran {sum(item.tests_run for item in outcomes)}: "
        f"{len(failed)} failed, "
        f"{sum(item.skipped for item in outcomes)} skipped, "
        f"{sum(item.expected_failures for item in outcomes)} expected failures."
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
