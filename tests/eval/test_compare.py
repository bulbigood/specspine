import importlib.util
import sys
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

    def test_prompts_disclose_only_the_selected_context_mode(self):
        comparison = COMPARE.load_comparisons()[0]
        prompts = {
            arm["id"]: COMPARE.build_prompt(comparison, arm)
            for arm in comparison["arms"]
        }
        self.assertIn("No architectural context", prompts["repository-only"])
        self.assertIn("ARCHITECTURE.md", prompts["architecture-document"])
        self.assertIn("linked specifications", prompts["full-spine"])
        self.assertIn("HANDOFF.md", prompts["minimal-handoff"])

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

    def test_run_arm_executes_downstream_assertions_in_isolation(self):
        comparison = next(
            item for item in COMPARE.load_comparisons() if item["id"] == "local-change"
        )
        arm = next(item for item in comparison["arms"] if item["id"] == "repository-only")
        command = [
            sys.executable,
            "-c",
            "from pathlib import Path; import sys; sys.stdin.read(); "
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


if __name__ == "__main__":
    unittest.main()
