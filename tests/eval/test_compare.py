import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[2]
MODULE_PATH = PROJECT_ROOT / "tests" / "eval" / "compare.py"
SPEC = importlib.util.spec_from_file_location("specspine_compare", MODULE_PATH)
assert SPEC and SPEC.loader
COMPARE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = COMPARE
SPEC.loader.exec_module(COMPARE)


class ComparisonTests(unittest.TestCase):
    def test_all_comparisons_define_valid_isolated_arms(self):
        comparisons = COMPARE.load_comparisons()
        self.assertEqual(4, len(comparisons))
        for comparison in comparisons:
            self.assertEqual([], COMPARE.validate_comparison(comparison), comparison["id"])
            arms = {arm["id"]: arm for arm in comparison["arms"]}
            self.assertEqual(COMPARE.REQUIRED_ARMS, set(arms))
            self.assertEqual({}, arms["repository-only"]["context_files"])

    def test_all_arms_receive_the_same_prompt_without_arm_labels(self):
        comparison = COMPARE.load_comparisons()[0]
        prompts = [COMPARE.build_prompt(comparison) for _arm in comparison["arms"]]
        self.assertEqual(1, len(set(prompts)))
        for arm in COMPARE.REQUIRED_ARMS:
            self.assertNotIn(arm, prompts[0])
        self.assertNotIn("ARCHITECTURE.md", prompts[0])
        self.assertNotIn("HANDOFF.md", prompts[0])

    def test_summary_keeps_outcome_and_cost_separate(self):
        results = [
            {
                "arm": arm,
                "comparison": "example",
                "passed": arm != "repository-only",
                "context_words": index * 10,
                "files_read": index + 1,
                "irrelevant_files_read": [] if index else ["src/unrelated.py"],
                "input_tokens": 100 + index,
                "duration_seconds": 1.0 + index,
            }
            for index, arm in enumerate(sorted(COMPARE.REQUIRED_ARMS))
        ]
        summary = COMPARE.summarize(results)
        self.assertEqual({"example"}, set(summary))
        self.assertEqual(4, len(summary["example"]))
        self.assertIn("outcome_pass_rate", summary["example"]["repository-only"])
        self.assertIn("median_input_tokens", summary["example"]["minimal-handoff"])

    def test_report_settings_come_from_complete_actual_traces(self):
        results = [
            {"actual_model": "fixed-model", "actual_reasoning": "medium"},
            {"actual_model": "fixed-model", "actual_reasoning": "medium"},
        ]
        self.assertEqual(
            {"model": "fixed-model", "reasoning": "medium"},
            COMPARE.actual_settings(results),
        )
        results[1].pop("actual_model")
        self.assertEqual(
            {"model": "unknown", "reasoning": "unknown"},
            COMPARE.actual_settings(results),
        )

    def test_report_rejects_conflicting_actual_settings(self):
        with self.assertRaisesRegex(ValueError, "inconsistent actual models"):
            COMPARE.actual_settings(
                [
                    {"actual_model": "model-a", "actual_reasoning": "medium"},
                    {"actual_model": "model-b", "actual_reasoning": "medium"},
                ]
            )

    def test_run_arm_executes_downstream_assertions_in_isolation(self):
        comparison = next(
            item for item in COMPARE.load_comparisons() if item["id"] == "local-change"
        )
        arm = next(item for item in comparison["arms"] if item["id"] == "repository-only")
        command = [
            sys.executable,
            "-c",
            "from pathlib import Path; import os, sys; sys.stdin.read(); "
            "assert 'SPECSPINE_COMPARISON_ARM' not in os.environ; "
            "Path('src/profile.py').write_text(\"def profile_title():\\n    return 'Account profile'\\n\", encoding='utf-8'); "
            "Path('.eval/trace.json').write_text(\"{\\\"files_read\\\": [\\\"src/profile.py\\\"], \\\"token_usage\\\": {\\\"input_tokens\\\": 12}}\", encoding='utf-8')",
        ]
        result = COMPARE.run_arm(comparison, arm, 1, command, False)
        self.assertTrue(result["passed"], result["checks"])
        self.assertEqual(["src/profile.py"], result["changed_files"])
        self.assertEqual(1, result["files_read"])
        self.assertEqual(12, result["input_tokens"])

    def test_run_arm_rejects_supplied_context_changes(self):
        comparison = next(
            item for item in COMPARE.load_comparisons() if item["id"] == "local-change"
        )
        arm = next(
            item for item in comparison["arms"] if item["id"] == "architecture-document"
        )
        command = [
            sys.executable,
            "-c",
            "from pathlib import Path; import sys; sys.stdin.read(); "
            "Path('ARCHITECTURE.md').write_text('changed', encoding='utf-8'); "
            "Path('src/profile.py').write_text(\"def profile_title():\\n    return 'Account profile'\\n\", encoding='utf-8')",
        ]
        result = COMPARE.run_arm(comparison, arm, 1, command, False)
        self.assertFalse(result["passed"])
        self.assertTrue(
            any("supplied context changed" in check["message"] for check in result["checks"])
        )

    def test_run_arm_archives_reproducible_and_blind_judge_artifacts(self):
        comparison = next(
            item for item in COMPARE.load_comparisons() if item["id"] == "local-change"
        )
        arm = next(item for item in comparison["arms"] if item["id"] == "minimal-handoff")
        command = [
            sys.executable,
            "-c",
            "from pathlib import Path; import os, sys; sys.stdin.read(); "
            "assert 'minimal-handoff' not in str(Path.cwd()); "
            "assert 'SPECSPINE_COMPARISON_ARM' not in os.environ; "
            "Path('src/profile.py').write_text(\"def profile_title():\\n    return 'Account profile'\\n\", encoding='utf-8')",
        ]
        with tempfile.TemporaryDirectory() as directory:
            result = COMPARE.run_arm(comparison, arm, 1, command, False, Path(directory))
            artifact_path = Path(result["artifacts"])
            self.assertTrue((artifact_path / "prompt.md").is_file())
            self.assertTrue((artifact_path / "response.md").is_file())
            self.assertTrue((artifact_path / "diff.patch").is_file())
            bundle = json.loads((artifact_path / "judge-input.json").read_text(encoding="utf-8"))
            self.assertEqual({"request", "diff", "rubric"}, set(bundle))
            self.assertNotIn("minimal-handoff", json.dumps(bundle))
            self.assertIn("src/profile.py", bundle["diff"])
            self.assertEqual(result["diff"], bundle["diff"])
            self.assertEqual(64, len(result["fixture_sha256"]))
            self.assertEqual(64, len(result["context_sha256"]))


if __name__ == "__main__":
    unittest.main()
