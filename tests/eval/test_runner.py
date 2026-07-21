import importlib.util
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).with_name("run.py")
SPEC = importlib.util.spec_from_file_location("specspine_eval", MODULE_PATH)
assert SPEC and SPEC.loader
RUNNER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNNER
SPEC.loader.exec_module(RUNNER)


class RunnerTests(unittest.TestCase):
    def test_all_documented_scenarios_are_registered(self):
        documented, registered, _ = RUNNER.scenario_coverage(RUNNER.load_cases())
        self.assertEqual(documented, registered)

    def test_manifests_are_valid(self):
        failures = {
            case["id"]: RUNNER.validate_case(case)
            for case in RUNNER.load_cases()
            if RUNNER.validate_case(case)
        }
        self.assertEqual({}, failures)
        self.assertEqual([], RUNNER.validate_collection(RUNNER.load_cases()))

    def test_detects_broken_markdown_link(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            (workspace / "README.md").write_text("[Missing](missing.md)\n", encoding="utf-8")
            result = RUNNER.check_markdown_links(workspace, "**/*.md")
            self.assertFalse(result.passed)

    def test_validates_cross_file_semantic_id(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            (workspace / "owner.md").write_text(
                "## Constraints\n\n- **CON-retry-limit** — Stop retrying.\n", encoding="utf-8"
            )
            (workspace / "consumer.md").write_text(
                "Preserve [CON-retry-limit](owner.md).\n", encoding="utf-8"
            )
            result = RUNNER.check_semantic_ids(workspace, "**/*.md")
            self.assertTrue(result.passed, result.message)

    def test_rejects_semantic_id_url_fragment(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            (workspace / "owner.md").write_text(
                "## Constraints\n\n- **CON-retry-limit** — Stop retrying.\n", encoding="utf-8"
            )
            (workspace / "consumer.md").write_text(
                "Preserve [CON-retry-limit](owner.md#CON-retry-limit).\n", encoding="utf-8"
            )
            result = RUNNER.check_semantic_ids(workspace, "**/*.md")
            self.assertFalse(result.passed)

    def test_rejects_semantic_id_in_wrong_section(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            (workspace / "owner.md").write_text(
                "## Decisions\n\n- **OBS-current-shape** — Current behavior.\n", encoding="utf-8"
            )
            result = RUNNER.check_semantic_ids(workspace, "**/*.md")
            self.assertFalse(result.passed)

    def test_runs_agent_in_isolated_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = Path(directory) / "adapter.py"
            adapter.write_text(
                "from pathlib import Path\n"
                "import sys\n"
                "sys.stdin.read()\n"
                "Path('result.md').write_text('# Result\\n', encoding='utf-8')\n",
                encoding="utf-8",
            )
            case = {
                "id": "runner-self-test",
                "scenario": "tests/scenarios/initialize-project.md",
                "skill": "skills/specspine-grow",
                "initial_files": {"protected.txt": "keep\n"},
                "assertions": [
                    {"type": "path_exists", "path": "result.md"},
                    {"type": "unchanged", "paths": ["protected.txt"]},
                    {"type": "changed_only", "paths": ["result.md"]},
                ],
            }
            self.assertTrue(RUNNER.run_case(case, [sys.executable, str(adapter)], False))

    def test_repeats_agent_in_the_same_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = Path(directory) / "adapter.py"
            adapter.write_text(
                "from pathlib import Path\n"
                "import sys\n"
                "sys.stdin.read()\n"
                "path = Path('runs.txt')\n"
                "path.write_text(path.read_text() + 'x' if path.exists() else 'x')\n",
                encoding="utf-8",
            )
            case = {
                "id": "repeat-self-test",
                "scenario": "tests/scenarios/initialize-project.md",
                "skill": "skills/specspine-grow",
                "runs": 2,
                "initial_files": {},
                "assertions": [{"type": "file_contains", "path": "runs.txt", "value": "xx"}],
            }
            self.assertTrue(RUNNER.run_case(case, [sys.executable, str(adapter)], False))

    def test_parallel_jobs_run_selected_cases_concurrently_and_queue_the_rest(self):
        cases = [
            {
                "id": case_id,
                "scenario": "tests/scenarios/initialize-project.md",
                "skill": "skills/specspine-grow",
                "status": "executable",
                "initial_files": {},
                "assertions": [{"type": "path_exists", "path": "result.md"}],
            }
            for case_id in ("parallel-a", "parallel-b", "parallel-c")
        ]
        barrier = threading.Barrier(2)
        lock = threading.Lock()
        called: list[str] = []

        def fake_run_case(case, command, keep_workspace):
            with lock:
                called.append(case["id"])
                call_number = len(called)
            if call_number <= 2:
                barrier.wait(timeout=2)
            return True

        argv = ["run.py", "--parallel", "--jobs", "2", "--agent-command", "fake-agent"]
        with (
            patch.object(RUNNER, "load_cases", return_value=cases),
            patch.object(RUNNER, "validate_collection", return_value=[]),
            patch.object(RUNNER, "validate_case", return_value=[]),
            patch.object(RUNNER, "run_case", side_effect=fake_run_case),
            patch.object(sys, "argv", argv),
        ):
            self.assertEqual(0, RUNNER.main())
        self.assertCountEqual(["parallel-a", "parallel-b", "parallel-c"], called)

    def test_jobs_must_be_positive(self):
        self.assertEqual(3, RUNNER.positive_int("3"))
        with self.assertRaises(RUNNER.argparse.ArgumentTypeError):
            RUNNER.positive_int("0")


if __name__ == "__main__":
    unittest.main()
