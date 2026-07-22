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
    def test_inventory_defines_three_focused_experiments(self):
        comparisons = COMPARE.load_comparisons()
        self.assertEqual(10, len(comparisons))
        self.assertEqual(
            {"value": 4, "projection": 2, "handoff-production": 4},
            {
                experiment: sum(item["experiment"] == experiment for item in comparisons)
                for experiment in COMPARE.EXPERIMENT_ARMS
            },
        )
        for comparison in comparisons:
            self.assertEqual([], COMPARE.validate_comparison(comparison), comparison["id"])
            self.assertEqual(
                COMPARE.EXPERIMENT_ARMS[comparison["experiment"]],
                {arm["id"] for arm in comparison["arms"]},
            )

    def test_value_baseline_preserves_native_documentation(self):
        comparison = next(
            item for item in COMPARE.load_comparisons() if item["id"] == "value-auditor-role"
        )
        native = next(arm for arm in comparison["arms"] if arm["id"] == "native-repository")
        self.assertEqual({}, COMPARE.context_files(native))
        self.assertEqual("node-express-boilerplate", comparison["repository"])

    def test_reused_tasks_have_byte_identical_downstream_prompts(self):
        comparisons = COMPARE.load_comparisons()
        for task in ("auditor-role", "reset-revocation"):
            selected = [
                item
                for item in comparisons
                if item["task"] == task and item["experiment"] in {"value", "projection"}
            ]
            self.assertEqual(2, len(selected))
            prompts = {
                COMPARE.build_prompt(
                    item,
                    next(arm for arm in item["arms"] if arm["id"] == "minimal-handoff"),
                )
                for item in selected
            }
            self.assertEqual(1, len(prompts))

    def test_arm_protocols_force_the_intended_context_intervention(self):
        comparisons = COMPARE.load_comparisons()
        value = next(item for item in comparisons if item["id"] == "value-auditor-role")
        minimal = next(arm for arm in value["arms"] if arm["id"] == "minimal-handoff")
        self.assertIn("HANDOFF.md exists, read it", COMPARE.build_prompt(value, minimal))
        projection = next(item for item in comparisons if item["id"] == "projection-auditor-role")
        full = next(arm for arm in projection["arms"] if arm["id"] == "full-spine")
        self.assertIn("specspine/README.md exists, read it", COMPARE.build_prompt(projection, full))
        native = next(arm for arm in value["arms"] if arm["id"] == "native-repository")
        self.assertEqual(COMPARE.build_prompt(value, native), COMPARE.build_prompt(value, minimal))

    def test_context_bundles_keep_handoff_smaller_than_full_spine(self):
        full = COMPARE.context_files({"context_bundle": "node-express/full-spine"})
        handoff = COMPARE.context_files({"context_bundle": "node-express/auditor-role"})
        self.assertIn("specspine/README.md", full)
        self.assertIn("HANDOFF.md", handoff)
        self.assertNotIn("specspine/email.md", handoff)
        self.assertLess(sum(map(len, handoff.values())), sum(map(len, full.values())))

    def test_production_prompt_enforces_spine_only_evidence(self):
        comparison = next(
            item
            for item in COMPARE.load_comparisons()
            if item["id"] == "production-reset-revocation"
        )
        prompt = COMPARE.build_prompt(comparison, comparison["arms"][0])
        self.assertIn(".eval/skill/SKILL.md", prompt)
        self.assertIn("Do not inspect source code", prompt)
        self.assertNotIn("generated-handoff", prompt)

    def test_repository_descriptor_is_commit_and_hash_pinned(self):
        repository = COMPARE.load_repositories()["node-express-boilerplate"]
        self.assertEqual(40, len(repository["commit"]))
        self.assertEqual(64, len(repository["archive_sha256"]))
        self.assertIn(repository["commit"], repository["archive_url"])

    def test_run_arm_copies_native_repository_and_keeps_context_unchanged(self):
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
            arm = {"id": "minimal-handoff", "context_files": {"HANDOFF.md": "reviewed\n"}}
            command = [
                sys.executable,
                "-c",
                "from pathlib import Path; import json,sys; sys.stdin.read(); "
                "Path('src/utils/pick.js').write_text('module.exports = x => x;\\n'); "
                "Path('.eval/trace.json').write_text(json.dumps({'files_read':['README.md','HANDOFF.md'], 'token_usage':{'input_tokens':10}}))",
            ]
            with mock.patch.object(COMPARE, "materialize_repository", return_value=repository):
                result = COMPARE.run_arm(comparison, arm, 1, command, False)
            self.assertTrue(result["passed"], result["checks"])
            self.assertEqual("value", result["experiment"])
            self.assertEqual(2, result["files_read"])
            self.assertEqual(10, result["input_tokens"])
            self.assertNotIn("HANDOFF.md", result["changed_files"])

    def test_handoff_production_uses_a_dedicated_semantic_rubric(self):
        comparison = next(
            item for item in COMPARE.load_comparisons() if item["id"] == "production-bootstrap-admin-policy"
        )
        bundle = COMPARE.judge_bundle({"diff": "", "response": "handoff"}, comparison)
        self.assertEqual("handoff", bundle["submission_type"])
        self.assertEqual(comparison["handoff_rubric"], bundle["rubric"])
        self.assertIn("empty diff is required", COMPARE.build_judge_prompt(bundle))

    def test_semantic_phrasing_is_not_checked_mechanically(self):
        for comparison in COMPARE.load_comparisons():
            assertions = comparison.get("assertions", []) + comparison.get("production_assertions", [])
            self.assertFalse(
                any(item["type"].startswith("response_") for item in assertions),
                comparison["id"],
            )

    def test_judge_input_is_blind_to_experiment_and_arm(self):
        comparison = next(
            item for item in COMPARE.load_comparisons() if item["id"] == "value-local-utility"
        )
        first = {"arm": "native-repository", "experiment": "value", "diff": "", "response": "done"}
        second = {"arm": "minimal-handoff", "experiment": "value", "diff": "", "response": "done"}
        self.assertEqual(
            COMPARE.judge_cache_key(first, comparison),
            COMPARE.judge_cache_key(second, comparison),
        )

    def test_report_groups_rows_by_experiment(self):
        results = []
        for experiment, arm in (
            ("value", "native-repository"),
            ("projection", "full-spine"),
            ("handoff-production", "generated-handoff"),
        ):
            results.append(
                {
                    "experiment": experiment,
                    "comparison": f"{experiment}-example",
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
            )
        markdown = COMPARE.markdown_report({"results": results})
        self.assertIn("| Experiment | Arm |", markdown)
        self.assertIn("| value | native-repository |", markdown)
        self.assertIn("| projection | full-spine |", markdown)
        self.assertIn("| handoff-production | generated-handoff |", markdown)

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
            for index, arm in enumerate(("native-repository", "minimal-handoff"))
        ]
        summary = COMPARE.summarize(results)["example"]
        self.assertEqual(1.0, summary["native-repository"]["outcome_pass_rate"])
        self.assertEqual(101, summary["minimal-handoff"]["median_input_tokens"])

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
        with self.assertRaisesRegex(ValueError, "incomplete execution environment"):
            COMPARE.execution_environment_settings(
                [{"execution_environment": {**environment, "image_id": "unknown"}}]
            )


if __name__ == "__main__":
    unittest.main()
