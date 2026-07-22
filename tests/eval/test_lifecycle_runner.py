import importlib.util
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("run.py")
SPEC = importlib.util.spec_from_file_location("specspine_lifecycle_eval", MODULE_PATH)
assert SPEC and SPEC.loader
RUNNER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNNER
SPEC.loader.exec_module(RUNNER)


class LifecycleRunnerTests(unittest.TestCase):
    def staged_case(self):
        return {
            "id": "lifecycle-self-test",
            "scenario": "tests/scenarios/initialize-project.md",
            "status": "executable",
            "category": "core",
            "initial_files": {"seed.txt": "seed\n"},
            "stages": [
                {
                    "id": "grow",
                    "skill": "skills/specspine-grow",
                    "prompt": "Create the first lifecycle marker.",
                    "assertions": [
                        {"type": "path_exists", "path": "first.txt"},
                        {"type": "changed_only", "paths": ["first.txt"]},
                    ],
                },
                {
                    "id": "external-change",
                    "fixture": {
                        "write_files": {"src/runtime.txt": "implemented\n"},
                        "remove_files": ["seed.txt"],
                    },
                    "assertions": [
                        {"type": "path_exists", "path": "src/runtime.txt"},
                        {"type": "path_absent", "path": "seed.txt"},
                    ],
                },
                {
                    "id": "map",
                    "skill": "skills/specspine-map",
                    "prompt": "Read the external change and create the final lifecycle marker.",
                    "assertions": [
                        {"type": "path_exists", "path": "final.txt"},
                        {"type": "read_includes", "paths": ["src/runtime.txt"]},
                    ],
                },
            ],
            "final_assertions": [
                {"type": "path_exists", "path": "first.txt"},
                {"type": "path_exists", "path": "final.txt"},
            ],
        }

    def test_validates_staged_manifest_and_rejects_unsafe_mutation(self):
        case = self.staged_case()
        self.assertEqual([], RUNNER.validate_case(case))
        case["stages"][1]["fixture"]["write_files"] = {"../escape.txt": "bad\n"}
        self.assertIn("stage 2 has unsafe fixture path: ../escape.txt", RUNNER.validate_case(case))

    def test_stage_prompt_contains_only_current_request(self):
        case = self.staged_case()
        prompt = RUNNER.build_prompt(case, case["stages"][0])
        self.assertIn("Create the first lifecycle marker.", prompt)
        self.assertNotIn("Read the external change", prompt)

    def test_project_glob_assertions_ignore_eval_resources(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            (workspace / ".eval/skill/references").mkdir(parents=True)
            (workspace / ".eval/skill/references/context-handoff.md").write_text("bundled\n", encoding="utf-8")
            (workspace / "specspine").mkdir()
            (workspace / "specspine/payment.md").write_text("OBS-payment-runtime\n", encoding="utf-8")
            count = RUNNER.evaluate_assertion(
                {"type": "glob_count", "glob": "**/*handoff*.md", "max": 0},
                workspace,
                {},
                {},
                "",
                None,
            )
            content = RUNNER.evaluate_assertion(
                {"type": "glob_contains", "glob": "specspine/*.md", "value": "OBS-payment-runtime"},
                workspace,
                {},
                {},
                "",
                None,
            )
            self.assertTrue(count.passed, count.message)
            self.assertTrue(content.passed, content.message)

    def test_runs_doctor_mechanical_assertion_recursively(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            nested = workspace / "specspine/domains/payments"
            nested.mkdir(parents=True)
            (workspace / "specspine/README.md").write_text(
                "# Architecture\n\n[Payments](domains/payments/payment-processing.md)\n",
                encoding="utf-8",
            )
            (nested / "payment-processing.md").write_text("# Payment processing\n", encoding="utf-8")
            clean = RUNNER.evaluate_assertion(
                {"type": "spine_mechanical_valid"}, workspace, {}, {}, "", None
            )
            self.assertTrue(clean.passed, clean.message)
            (nested / "payment-processing.md").write_text(
                "# Payment processing\n\n[Missing](missing.md)\n", encoding="utf-8"
            )
            broken = RUNNER.evaluate_assertion(
                {"type": "spine_mechanical_valid"}, workspace, {}, {}, "", None
            )
            self.assertFalse(broken.passed)

    def test_runs_agent_and_fixture_stages_in_one_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            workspace.mkdir()
            adapter = Path(directory) / "adapter.py"
            adapter.write_text(
                "import json, os, sys\n"
                "from pathlib import Path\n"
                "prompt = sys.stdin.read()\n"
                "stage = os.environ['SPECSPINE_EVAL_STAGE']\n"
                "if stage == 'grow':\n"
                "    Path('first.txt').write_text(prompt, encoding='utf-8')\n"
                "    reads = []\n"
                "elif stage == 'map':\n"
                "    observed = Path('src/runtime.txt').read_text(encoding='utf-8')\n"
                "    Path('final.txt').write_text(observed, encoding='utf-8')\n"
                "    reads = ['src/runtime.txt']\n"
                "else:\n"
                "    raise SystemExit(2)\n"
                "Path('.eval/trace.json').write_text(json.dumps({'files_read': reads}), encoding='utf-8')\n",
                encoding="utf-8",
            )
            case = self.staged_case()
            RUNNER.write_fixture(case, workspace)
            env = {
                **os.environ,
                "SPECSPINE_EVAL_CASE": case["id"],
                "SPECSPINE_EVAL_WORKSPACE": str(workspace),
            }
            output = io.StringIO()
            self.assertTrue(
                RUNNER.run_staged_case(
                    case, [sys.executable, str(adapter)], workspace, env, output=output
                )
            )
            self.assertIn("stage 2: external-change (fixture)", output.getvalue())
            self.assertNotIn("stage 2: external-change (agent exit", output.getvalue())
            self.assertFalse((workspace / "seed.txt").exists())
            self.assertEqual("implemented\n", (workspace / "src/runtime.txt").read_text(encoding="utf-8"))
            self.assertTrue((workspace / ".eval/stages/01-grow/response.md").is_file())
            self.assertTrue((workspace / ".eval/stages/03-map/trace.json").is_file())


if __name__ == "__main__":
    unittest.main()
