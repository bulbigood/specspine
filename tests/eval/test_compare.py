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
            self.assertEqual(1, len({COMPARE.build_prompt(item) for item in selected}))

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
        prompt = COMPARE.build_prompt(comparison)
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


if __name__ == "__main__":
    unittest.main()
