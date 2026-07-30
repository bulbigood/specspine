import importlib.util
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).parents[2]
PREPUBLISH_PATH = ROOT / "shared/scripts/prepublish.py"


def load_prepublish():
    specification = importlib.util.spec_from_file_location(
        "prepublish_test", PREPUBLISH_PATH
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


class PrepublishTests(unittest.TestCase):
    def test_default_gate_checks_generated_files_tests_and_npx_install(self):
        prepublish = load_prepublish()
        calls = []

        def record(command, *, environment=None):
            calls.append((command, environment))

        with patch.object(sys, "argv", ["prepublish.py"]), patch.object(
            prepublish, "run", side_effect=record
        ):
            self.assertEqual(0, prepublish.main())

        self.assertEqual(
            [sys.executable, str(prepublish.RENDERER)],
            calls[0][0],
        )
        self.assertEqual(
            [sys.executable, "tests/run_mechanical.py", "-p", "test_*.py"],
            calls[1][0],
        )
        self.assertEqual(
            [sys.executable, "tests/run_mechanical.py", "-p", "test_npx_install.py"],
            calls[2][0],
        )
        self.assertEqual("1", calls[2][1]["SPECSPINE_RUN_NPX"])

    def test_update_and_skip_modes_are_explicit(self):
        prepublish = load_prepublish()
        calls = []

        with patch.object(
            sys,
            "argv",
            ["prepublish.py", "--update-generated", "--skip-npx"],
        ), patch.object(
            prepublish,
            "run",
            side_effect=lambda command, *, environment=None: calls.append(command),
        ):
            self.assertEqual(0, prepublish.main())

        self.assertEqual(
            [
                [sys.executable, str(prepublish.RENDERER), "--write"],
                [sys.executable, str(prepublish.RENDERER)],
                [sys.executable, "tests/run_mechanical.py", "-p", "test_*.py"],
            ],
            calls,
        )

    def test_run_uses_repository_root_and_propagates_failure(self):
        prepublish = load_prepublish()
        completed = subprocess.CompletedProcess(["check"], 7)
        environment = dict(os.environ)
        with patch.object(
            prepublish.subprocess, "run", return_value=completed
        ) as subprocess_run:
            with self.assertRaisesRegex(SystemExit, "7"):
                prepublish.run(["check"], environment=environment)
        subprocess_run.assert_called_once_with(
            ["check"],
            cwd=prepublish.ROOT,
            env=environment,
            check=False,
        )


if __name__ == "__main__":
    unittest.main()
