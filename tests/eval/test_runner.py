import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
