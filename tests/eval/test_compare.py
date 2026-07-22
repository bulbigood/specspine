import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).parents[2]
MODULE_PATH = PROJECT_ROOT / "tests" / "eval" / "compare.py"
SPEC = importlib.util.spec_from_file_location("specspine_compare", MODULE_PATH)
assert SPEC and SPEC.loader
COMPARE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = COMPARE
SPEC.loader.exec_module(COMPARE)


class ComparisonTests(unittest.TestCase):
    def test_inventory_defines_one_focused_experiment(self):
        comparisons = COMPARE.load_comparisons()
        self.assertEqual(4, len(comparisons))
        self.assertEqual({"value"}, set(COMPARE.EXPERIMENT_ARMS))
        for comparison in comparisons:
            self.assertEqual([], COMPARE.validate_comparison(comparison), comparison["id"])
            self.assertEqual(
                {"native-repository", "full-spine"},
                {arm["id"] for arm in comparison["arms"]},
            )

    def test_native_baseline_and_full_spine_use_same_repository(self):
        for comparison in COMPARE.load_comparisons():
            native = next(arm for arm in comparison["arms"] if arm["id"] == "native-repository")
            spine = next(arm for arm in comparison["arms"] if arm["id"] == "full-spine")
            self.assertEqual({}, COMPARE.context_files(native))
            self.assertIn("specspine/README.md", COMPARE.context_files(spine))
            self.assertEqual("node-express-boilerplate", comparison["repository"])

    def test_prompt_routes_agent_through_documentation_graph_without_handoff(self):
        comparison = COMPARE.load_comparisons()[0]
        native, spine = comparison["arms"]
        prompt = COMPARE.build_prompt(comparison, spine)
        self.assertEqual(prompt, COMPARE.build_prompt(comparison, native))
        self.assertIn("specspine/README.md", prompt)
        self.assertIn("navigate the documentation graph", prompt)
        self.assertNotIn("HANDOFF", prompt)

    def test_full_spine_protocol_requires_index_read_only(self):
        assertions = COMPARE.context_protocol_assertions({"id": "full-spine"})
        self.assertEqual(
            [{"type": "read_includes", "paths": ["specspine/README.md"]}],
            assertions,
        )
        self.assertEqual([], COMPARE.context_protocol_assertions({"id": "native-repository"}))

    def test_repository_descriptor_is_commit_and_hash_pinned(self):
        repository = COMPARE.load_repositories()["node-express-boilerplate"]
        self.assertEqual(40, len(repository["commit"]))
        self.assertEqual(64, len(repository["archive_sha256"]))
        self.assertIn(repository["commit"], repository["archive_url"])

    def test_run_arm_copies_native_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory) / "repository"
            (repository / "src" / "utils").mkdir(parents=True)
            (repository / "README.md").write_text("native docs\n", encoding="utf-8")
            (repository / "src" / "utils" / "pick.js").write_text(
                "module.exports = () => ({});\n", encoding="utf-8"
            )
            comparison = {
                "id": "synthetic",
                "experiment": "value",
                "repository": "synthetic",
                "prompt": "Change pick.",
                "architectural_rubric": {"scope": "local"},
                "assertions": [{"type": "path_exists", "path": "README.md"}],
                "irrelevant_read_patterns": [],
            }
            arm = {"id": "native-repository"}
            command = [
                sys.executable,
                "-c",
                "from pathlib import Path; import json,sys; sys.stdin.read(); "
                "Path('src/utils/pick.js').write_text('module.exports = x => x;\\n'); "
                "Path('.eval/trace.json').write_text(json.dumps({'files_read':['README.md'], 'token_usage':{'input_tokens':10}}))",
            ]
            with mock.patch.object(COMPARE, "materialize_repository", return_value=repository):
                result = COMPARE.run_arm(comparison, arm, 1, command, False)
            self.assertTrue(result["passed"], result["checks"])
            self.assertEqual(1, result["files_read"])
            self.assertEqual(10, result["input_tokens"])

    def test_judge_is_implementation_only_and_blind_to_arm(self):
        comparison = COMPARE.load_comparisons()[0]
        first = {"arm": "native-repository", "diff": "", "response": "done"}
        second = {"arm": "full-spine", "diff": "", "response": "done"}
        bundle = COMPARE.judge_bundle(first, comparison)
        self.assertEqual("implementation", bundle["submission_type"])
        self.assertEqual(comparison["architectural_rubric"], bundle["rubric"])
        self.assertEqual(
            COMPARE.judge_cache_key(first, comparison),
            COMPARE.judge_cache_key(second, comparison),
        )

    def test_semantic_phrasing_is_not_checked_mechanically(self):
        for comparison in COMPARE.load_comparisons():
            self.assertFalse(
                any(item["type"].startswith("response_") for item in comparison.get("assertions", [])),
                comparison["id"],
            )

    def test_report_contains_only_current_arms(self):
        results = [
            {
                "experiment": "value",
                "comparison": "value-example",
                "arm": arm,
                "sample": 1,
                "valid": True,
                "passed": True,
                "mechanical_passed": True,
                "context_words": 0,
                "files_read": 1,
                "irrelevant_files_read": [],
                "input_tokens": 10,
                "duration_seconds": 1.0,
                "checks": [],
            }
            for arm in ("native-repository", "full-spine")
        ]
        markdown = COMPARE.markdown_report({"results": results})
        self.assertIn("| value | native-repository |", markdown)
        self.assertIn("| value | full-spine |", markdown)
        self.assertNotIn("minimal-handoff", markdown)

    def test_summary_keeps_outcome_and_cost_separate(self):
        results = [
            {
                "experiment": "value",
                "comparison": "example",
                "arm": arm,
                "passed": True,
                "mechanical_passed": True,
                "context_words": index,
                "files_read": index + 1,
                "irrelevant_files_read": [],
                "input_tokens": 100 + index,
                "duration_seconds": 1.0,
            }
            for index, arm in enumerate(("native-repository", "full-spine"))
        ]
        summary = COMPARE.summarize(results)["example"]
        self.assertEqual(1.0, summary["native-repository"]["outcome_pass_rate"])
        self.assertEqual(101, summary["full-spine"]["median_input_tokens"])

    def test_execution_environment_must_be_complete_and_consistent(self):
        environment = {
            "kind": "docker",
            "image": "specspine-eval-agent:abc",
            "image_id": "sha256:image",
            "source_sha256": "source",
        }
        self.assertEqual(
            environment,
            COMPARE.execution_environment_settings(
                [
                    {"valid": True, "execution_environment": environment},
                    {"valid": True, "execution_environment": environment},
                ]
            ),
        )
        with self.assertRaisesRegex(ValueError, "missing execution environment"):
            COMPARE.execution_environment_settings(
                [{"valid": True, "execution_environment": environment}, {"valid": True}]
            )
        self.assertIsNone(COMPARE.execution_environment_settings([{"valid": False}]))


if __name__ == "__main__":
    unittest.main()
