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

    def test_comparison_snapshot_excludes_python_cache_noise(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src" / "__pycache__").mkdir(parents=True)
            (root / "src" / "module.py").write_text("value = 1\n", encoding="utf-8")
            (root / "src" / "__pycache__" / "module.pyc").write_bytes(b"cache")
            self.assertEqual(
                {"src/module.py"}, set(COMPARE.comparison_snapshot(root))
            )

    def test_identical_blind_judge_inputs_share_a_cache_key(self):
        comparison = next(
            item for item in COMPARE.load_comparisons() if item["id"] == "blocking-question"
        )
        first = {"arm": "repository-only", "diff": "", "response": "Blocked."}
        second = {"arm": "full-spine", "diff": "", "response": "Blocked."}
        self.assertEqual(
            COMPARE.judge_cache_key(first, comparison),
            COMPARE.judge_cache_key(second, comparison),
        )
        second["response"] = "Implemented."
        self.assertNotEqual(
            COMPARE.judge_cache_key(first, comparison),
            COMPARE.judge_cache_key(second, comparison),
        )

    def test_conflict_outcome_accepts_any_nonempty_provider_independent_session(self):
        comparison = next(
            item
            for item in COMPARE.load_comparisons()
            if item["id"] == "intended-observed-conflict"
        )
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            (workspace / "src").mkdir()
            (workspace / "src" / "login.py").write_text(
                "def provider_login(provider, provider_token):\n"
                "    if provider in {'google', 'github'}:\n"
                "        return 'opaque-local-session'\n"
                "    raise ValueError('unsupported provider')\n",
                encoding="utf-8",
            )
            result = COMPARE.RUNNER.evaluate_assertion(
                comparison["assertions"][0], workspace, {}, {}, "", None
            )
            self.assertTrue(result.passed, result.message)

    def test_cross_cutting_visible_test_accepts_package_imports_and_rejects_top_level_imports(self):
        comparison = next(
            item
            for item in COMPARE.load_comparisons()
            if item["id"] == "cross-cutting-change"
        )
        assertion = comparison["assertions"][0]
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            COMPARE.write_files(workspace, comparison["initial_files"])
            (workspace / "src" / "auth.py").write_text(
                "from .accounts import resolve_account\n"
                "from .sessions import create_session\n\n"
                "def login_external(provider_user_id, provider_token):\n"
                "    account = resolve_account(provider_user_id)\n"
                "    return create_session(account['user_id'])\n",
                encoding="utf-8",
            )
            accepted = COMPARE.RUNNER.evaluate_assertion(
                assertion, workspace, {}, {}, "", None
            )
            self.assertTrue(accepted.passed, accepted.message)
            (workspace / "src" / "auth.py").write_text(
                "import accounts\nimport sessions\n\n"
                "def login_external(provider_user_id, provider_token):\n"
                "    account = accounts.resolve_account(provider_user_id)\n"
                "    return sessions.create_session(account['user_id'])\n",
                encoding="utf-8",
            )
            rejected = COMPARE.RUNNER.evaluate_assertion(
                assertion, workspace, {}, {}, "", None
            )
            self.assertFalse(rejected.passed, rejected.message)

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

    def test_markdown_report_contains_summary_table_and_failure_details(self):
        result = {
            "comparison": "example",
            "arm": "repository-only",
            "sample": 1,
            "passed": False,
            "files_read": 2,
            "input_tokens": 123,
            "duration_seconds": 4.25,
            "checks": [{"passed": False, "message": "command failed | exit 1"}],
            "judge": {
                "valid": True,
                "passed": False,
                "total_score": 3,
                "max_score": 4,
                "violation_count": 1,
                "scores": {
                    "ownership": {"score": 1, "rationale": "Boundary is unclear."},
                    "constraints": {"score": 2, "rationale": "Satisfied."},
                },
            },
        }
        report = {
            "run": "007",
            "model": "agent-model",
            "reasoning": "medium",
            "comparisons": ["example"],
            "comparison_legend": {"example": "Tests an example change."},
            "judge": {"model": "judge-model", "reasoning": "low", "calls": 1},
            "results": [result],
        }
        markdown = COMPARE.markdown_report(report)
        self.assertIn("Run: **007**", markdown)
        self.assertIn("## Legend and methodology", markdown)
        self.assertIn(
            "| repository-only | Contents: frozen fixture repository and user request. No architectural context files. |",
            markdown,
        )
        self.assertIn("`example` — Tests an example change.", markdown)
        self.assertIn("### Testing process", markdown)
        self.assertIn("same clean fixture", markdown)
        self.assertIn("blind model judge", markdown)
        self.assertIn("Outcome: **0/1 passed**", markdown)
        self.assertIn("Architecture: **0/1 passed**", markdown)
        self.assertIn("### Summary by arm", markdown)
        self.assertIn("| repository-only | 1 | 0/1 (0%) | 0/1 (0%) | 0 | 3.0/4.0 |", markdown)
        self.assertIn("### Individual results", markdown)
        self.assertIn("| example | repository-only | 1 | FAIL | 3/4 | — |", markdown)
        self.assertIn("command failed \\| exit 1", markdown)
        self.assertIn("ownership (1/2): Boundary is unclear.", markdown)

    def test_markdown_report_orders_arms_from_least_to_most_context(self):
        results = [
            {
                "comparison": "example",
                "arm": arm,
                "sample": 1,
                "passed": True,
                "files_read": 1,
                "input_tokens": 1,
                "duration_seconds": 1.0,
                "checks": [],
            }
            for arm in reversed(COMPARE.ARM_ORDER)
        ]
        markdown = COMPARE.markdown_report({"results": results})
        positions = [markdown.index(f"| {arm} | Contents:") for arm in COMPARE.ARM_ORDER]
        self.assertEqual(sorted(positions), positions)

    def test_markdown_report_marks_outcome_judge_mismatch(self):
        result = {
            "comparison": "example",
            "arm": "full-spine",
            "sample": 1,
            "passed": False,
            "files_read": 3,
            "input_tokens": 100,
            "duration_seconds": 1.0,
            "checks": [],
            "judge": {
                "valid": True,
                "passed": True,
                "total_score": 2,
                "max_score": 2,
                "violation_count": 0,
                "scores": {"criterion": {"score": 2, "rationale": "Satisfied."}},
            },
        }
        markdown = COMPARE.markdown_report({"results": [result]})
        self.assertIn("| full-spine | 1 | 0/1 (0%) | 1/1 (100%) | 1 |", markdown)
        self.assertIn("| example | full-spine | 1 | FAIL | 2/2 | YES |", markdown)

    def test_allocate_run_directory_uses_sequential_numeric_names(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "comparison-runs"
            self.assertEqual("001", COMPARE.allocate_run_directory(root).name)
            self.assertEqual("002", COMPARE.allocate_run_directory(root).name)
            (root / "notes").mkdir()
            self.assertEqual("003", COMPARE.allocate_run_directory(root).name)

    def test_json_report_has_default_filename(self):
        self.assertEqual(Path("comparison-results.json"), COMPARE.DEFAULT_JSON_OUTPUT)

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

    def test_judge_response_is_strictly_scored_against_every_rubric_key(self):
        rubric = {"ownership": "owner remains stable", "constraint": "token is hidden"}
        response = json.dumps(
            {
                "scores": {
                    "ownership": {"score": 2, "rationale": "Owner is unchanged."},
                    "constraint": {"score": 1, "rationale": "Token handling is unclear."},
                },
                "summary": "One criterion is unclear.",
            }
        )
        judgment = COMPARE.parse_judge_response(response, rubric)
        self.assertEqual(3, judgment["total_score"])
        self.assertEqual(4, judgment["max_score"])
        self.assertEqual(1, judgment["violation_count"])
        self.assertFalse(judgment["passed"])
        with self.assertRaisesRegex(ValueError, "score keys differ"):
            COMPARE.parse_judge_response(
                '{"scores": {}, "summary": "missing"}', rubric
            )

    def test_run_judge_is_blind_and_records_model_metadata(self):
        comparison = next(
            item for item in COMPARE.load_comparisons() if item["id"] == "local-change"
        )
        scores = {
            key: {"score": 2, "rationale": "The diff satisfies the criterion."}
            for key in comparison["architectural_rubric"]
        }
        response = json.dumps({"scores": scores, "summary": "All criteria pass."})
        command = [
            sys.executable,
            "-c",
            "from pathlib import Path; import os, sys; prompt=sys.stdin.read(); "
            "assert 'repository-only' not in prompt; "
            "assert 'SPECSPINE_COMPARISON' not in os.environ; "
            "Path('.eval/trace.json').write_text('{\"model\":\"judge-model\",\"reasoning_effort\":\"high\"}', encoding='utf-8'); "
            "Path('.eval/codex-events.jsonl').write_text('{\"type\":\"turn.completed\"}\\n', encoding='utf-8'); "
            f"print({response!r})",
        ]
        with tempfile.TemporaryDirectory() as directory:
            result = {
                "diff": "--- a/src/profile.py\n+++ b/src/profile.py\n",
                "response": "Implementation complete.",
                "artifacts": directory,
            }
            judgment = COMPARE.run_judge(result, comparison, command, False)
            self.assertTrue(judgment["valid"], judgment)
            self.assertTrue(judgment["passed"])
            self.assertEqual("judge-model", judgment["actual_model"])
            self.assertEqual("high", judgment["actual_reasoning"])
            self.assertTrue((Path(directory) / "judge-prompt.md").is_file())
            self.assertTrue((Path(directory) / "judge-response.json").is_file())
            self.assertEqual(
                '{"type":"turn.completed"}\n',
                (Path(directory) / "judge" / "codex-events.jsonl").read_text(),
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
            "Path('.eval/codex-events.jsonl').write_text('{\"type\":\"turn.completed\"}\\n', encoding='utf-8'); "
            "Path('src/profile.py').write_text(\"def profile_title():\\n    return 'Account profile'\\n\", encoding='utf-8')",
        ]
        with tempfile.TemporaryDirectory() as directory:
            result = COMPARE.run_arm(comparison, arm, 1, command, False, Path(directory))
            artifact_path = Path(result["artifacts"])
            self.assertTrue((artifact_path / "prompt.md").is_file())
            self.assertTrue((artifact_path / "response.md").is_file())
            self.assertTrue((artifact_path / "diff.patch").is_file())
            self.assertTrue((artifact_path / "agent").is_dir())
            self.assertEqual(
                '{"type":"turn.completed"}\n',
                (artifact_path / "agent" / "codex-events.jsonl").read_text(),
            )
            bundle = json.loads((artifact_path / "judge-input.json").read_text(encoding="utf-8"))
            self.assertEqual({"request", "diff", "response", "rubric"}, set(bundle))
            self.assertNotIn("minimal-handoff", json.dumps(bundle))
            self.assertIn("src/profile.py", bundle["diff"])
            self.assertEqual(result["response"], bundle["response"])
            self.assertEqual(result["diff"], bundle["diff"])
            self.assertEqual(64, len(result["fixture_sha256"]))
            self.assertEqual(64, len(result["context_sha256"]))


if __name__ == "__main__":
    unittest.main()
