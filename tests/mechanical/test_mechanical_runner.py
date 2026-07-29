import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "tests" / "run_mechanical.py"
SPEC = importlib.util.spec_from_file_location("run_mechanical", RUNNER_PATH)
assert SPEC and SPEC.loader
RUNNER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNNER
SPEC.loader.exec_module(RUNNER)


class MechanicalRunnerTests(unittest.TestCase):
    def test_default_jobs_leaves_one_available_cpu(self):
        self.assertEqual(7, RUNNER.default_jobs(8))

    def test_default_jobs_never_returns_less_than_one(self):
        self.assertEqual(1, RUNNER.default_jobs(1))
        with mock.patch.object(RUNNER.os, "cpu_count", return_value=None):
            self.assertEqual(1, RUNNER.default_jobs())

    def test_discovers_individual_test_cases(self):
        test_ids = RUNNER.discover_test_ids("test_mechanical_runner.py")
        self.assertIn(
            "test_mechanical_runner.MechanicalRunnerTests."
            "test_default_jobs_leaves_one_available_cpu",
            test_ids,
        )

    def test_worker_runs_one_discovered_test(self):
        outcome = RUNNER.run_test(
            "test_mechanical_runner.MechanicalRunnerTests."
            "test_default_jobs_leaves_one_available_cpu"
        )
        self.assertTrue(outcome.successful, outcome.output)
        self.assertEqual(1, outcome.tests_run)


if __name__ == "__main__":
    unittest.main()
