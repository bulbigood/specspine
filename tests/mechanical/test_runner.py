import importlib.util
import io
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).parents[1] / "eval" / "run.py"
SPEC = importlib.util.spec_from_file_location("specspine_eval", MODULE_PATH)
assert SPEC and SPEC.loader
RUNNER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNNER
SPEC.loader.exec_module(RUNNER)


class RunnerTests(unittest.TestCase):
    def test_runner_supports_three_extract_benchmark_profiles(self):
        self.assertEqual(
            {"extract", "fallback", "no-extract"},
            RUNNER.EXECUTION_PROFILES,
        )

    def test_compact_trace_preserves_retrieval_policy(self):
        compact = RUNNER.compact_agent_trace(
            {
                "ranking_system": "normalized",
                "graph_depth": 1,
                "graph_limit": 2,
                "cost_ledger": {"prompt_utf8_bytes": 12},
                "retrieval_usefulness": {"returned_direct": 2},
            }
        )

        self.assertEqual("normalized", compact["ranking_system"])
        self.assertEqual(1, compact["graph_depth"])
        self.assertEqual(2, compact["graph_limit"])
        self.assertEqual(12, compact["cost_ledger"]["prompt_utf8_bytes"])
        self.assertEqual(2, compact["retrieval_usefulness"]["returned_direct"])

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
            spine = workspace / "specspine"
            spine.mkdir()
            (spine / "README.md").write_text("# Architecture\n\n[Missing](missing.md)\n", encoding="utf-8")
            result = RUNNER.evaluate_assertion(
                {"type": "markdown_links_valid"}, workspace, {}, {}, "", None
            )
            self.assertFalse(result.passed)

    def test_command_succeeds_checks_downstream_behavior(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            passed = RUNNER.evaluate_assertion(
                {"type": "command_succeeds", "command": [sys.executable, "-c", "raise SystemExit(0)"]},
                workspace,
                {},
                {},
                "",
                None,
            )
            failed = RUNNER.evaluate_assertion(
                {"type": "command_succeeds", "command": [sys.executable, "-c", "raise SystemExit(3)"]},
                workspace,
                {},
                {},
                "",
                None,
            )
            self.assertTrue(passed.passed)
            self.assertFalse(failed.passed)

    def test_semantic_id_assertion_uses_doctor_commonmark_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            spine = workspace / "specspine"
            spine.mkdir()
            (spine / "README.md").write_text(
                "# Architecture\n\n[Owner](owner.md)\n[Consumer](consumer.md)\n", encoding="utf-8"
            )
            (spine / "owner.md").write_text(
                "# Owner\n\n<!-- specspine:semantic-ids:begin -->\n"
                "## Ограничения ##\n\n+ **CON-retry-limit** — Stop retrying.\n"
                "<!-- specspine:semantic-ids:end -->\n",
                encoding="utf-8",
            )
            (spine / "consumer.md").write_text(
                "# Consumer\n\n"
                "Preserve [CON-retry-limit](owner.md).\n", encoding="utf-8"
            )
            result = RUNNER.evaluate_assertion(
                {"type": "semantic_ids_valid"}, workspace, {}, {}, "", None
            )
            self.assertTrue(result.passed, result.message)

    def test_rejects_semantic_id_url_fragment(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            spine = workspace / "specspine"
            spine.mkdir()
            (spine / "README.md").write_text(
                "# Architecture\n\n[Owner](owner.md)\n[Consumer](consumer.md)\n", encoding="utf-8"
            )
            (spine / "owner.md").write_text(
                "# Owner\n\n<!-- specspine:semantic-ids:begin -->\n## Constraints\n\n"
                "- **CON-retry-limit** — Stop retrying.\n<!-- specspine:semantic-ids:end -->\n",
                encoding="utf-8",
            )
            (spine / "consumer.md").write_text(
                "# Consumer\n\n"
                "Preserve [CON-retry-limit](owner.md#CON-retry-limit).\n", encoding="utf-8"
            )
            result = RUNNER.evaluate_assertion(
                {"type": "semantic_ids_valid"}, workspace, {}, {}, "", None
            )
            self.assertFalse(result.passed)

    def test_rejects_semantic_id_in_wrong_section(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            spine = workspace / "specspine"
            spine.mkdir()
            (spine / "README.md").write_text(
                "# Architecture\n\n<!-- specspine:semantic-ids:begin -->\n## Decisions\n\n"
                "- **OBS-current-shape** — Current behavior.\n<!-- specspine:semantic-ids:end -->\n",
                encoding="utf-8",
            )
            result = RUNNER.evaluate_assertion(
                {"type": "semantic_ids_valid"}, workspace, {}, {}, "", None
            )
            self.assertFalse(result.passed)

    def test_mechanical_valid_ignores_advisories_unless_forbidden(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            spine = workspace / "specspine"
            spine.mkdir()
            (spine / "README.md").write_text("No level-one heading.\n", encoding="utf-8")
            default = RUNNER.evaluate_assertion(
                {"type": "spine_mechanical_valid"}, workspace, {}, {}, "", None
            )
            strict = RUNNER.evaluate_assertion(
                {"type": "spine_mechanical_valid", "forbidden_codes": ["MISSING_H1"]},
                workspace,
                {},
                {},
                "",
                None,
            )
            self.assertTrue(default.passed, default.message)
            self.assertFalse(strict.passed)

    def test_accepts_any_existing_path(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            (workspace / "email-delivery.md").write_text("# Email delivery\n", encoding="utf-8")
            result = RUNNER.evaluate_assertion(
                {"type": "path_exists_any", "paths": ["notification-delivery.md", "email-delivery.md"]},
                workspace,
                {},
                {},
                "",
                None,
            )
            self.assertTrue(result.passed, result.message)

    def test_word_budget_checks_each_file_and_total(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            spine = workspace / "specspine"
            spine.mkdir()
            (spine / "README.md").write_text("one two three\n", encoding="utf-8")
            (spine / "payments.md").write_text("four five six seven\n", encoding="utf-8")
            (workspace / ".eval").mkdir()
            (workspace / ".eval/ignored.md").write_text("ignored " * 100, encoding="utf-8")

            passing = RUNNER.evaluate_assertion(
                {"type": "word_budget", "glob": "specspine/*.md", "max_each": 4, "max_total": 7},
                workspace, {}, {}, "", None,
            )
            per_file_failure = RUNNER.evaluate_assertion(
                {"type": "word_budget", "glob": "specspine/*.md", "max_each": 3, "max_total": 20},
                workspace, {}, {}, "", None,
            )
            total_failure = RUNNER.evaluate_assertion(
                {"type": "word_budget", "glob": "specspine/*.md", "max_each": 10, "max_total": 6},
                workspace, {}, {}, "", None,
            )

            self.assertTrue(passing.passed, passing.message)
            self.assertFalse(per_file_failure.passed)
            self.assertFalse(total_failure.passed)

    def test_word_budget_fails_when_target_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            result = RUNNER.evaluate_assertion(
                {"type": "word_budget", "path": "specspine/missing.md", "max_total": 10},
                Path(directory), {}, {}, "", None,
            )
            self.assertFalse(result.passed)

    def test_checks_recorded_command_text(self):
        result = RUNNER.evaluate_assertion(
            {"type": "command_includes", "value": "check_spine.py"},
            Path("."),
            {},
            {},
            "",
            {"commands": ["python3 .eval/skill/scripts/check_spine.py specspine"]},
        )
        self.assertTrue(result.passed, result.message)

        excluded = RUNNER.evaluate_assertion(
            {"type": "command_excludes", "value": "search_spine.py"},
            Path("."),
            {},
            {},
            "",
            {"commands": ["sed -n 1,80p specspine/README.md"]},
        )
        forbidden = RUNNER.evaluate_assertion(
            {"type": "command_excludes", "value": "search_spine.py"},
            Path("."),
            {},
            {},
            "",
            {
                "commands": [
                    "python3 .eval/skill/scripts/search_spine.py specspine "
                    "--queries-json '[]'"
                ]
            },
        )
        self.assertTrue(excluded.passed, excluded.message)
        self.assertFalse(forbidden.passed)

    def test_trace_condition_limits_reads_only_in_fts_mode(self):
        assertion = {
            "type": "max_files_read",
            "max": 12,
            "when_trace": {"retrieval_mode": "sqlite-fts5"},
        }
        enabled = RUNNER.evaluate_assertion(
            assertion,
            Path("."),
            {},
            {},
            "",
            {"retrieval_mode": "sqlite-fts5", "files_read": [f"{index}.md" for index in range(13)]},
        )
        fallback = RUNNER.evaluate_assertion(
            assertion,
            Path("."),
            {},
            {},
            "",
            {"retrieval_mode": "fallback", "files_read": [f"{index}.md" for index in range(32)]},
        )
        missing_trace = RUNNER.evaluate_assertion(
            assertion, Path("."), {}, {}, "", None
        )

        self.assertFalse(enabled.passed)
        self.assertTrue(fallback.passed)
        self.assertFalse(missing_trace.passed)

    def test_trace_equals_checks_observed_runtime_value(self):
        assertion = {
            "type": "trace_equals",
            "field": "retrieval_mode",
            "value": "sqlite-fts5",
        }
        passed = RUNNER.evaluate_assertion(
            assertion, Path("."), {}, {}, "", {"retrieval_mode": "sqlite-fts5"}
        )
        failed = RUNNER.evaluate_assertion(
            assertion, Path("."), {}, {}, "", {"retrieval_mode": "fallback"}
        )

        self.assertTrue(passed.passed)
        self.assertFalse(failed.passed)

    def test_checks_structured_response_without_prose_contracts(self):
        response = (
            "# Handoff\n\n## Primary specification\n\n"
            "- `specspine/retry-policy.md`\n\n"
            "```markdown\n## Ignored example\n```\n\n"
            "## Blocking questions\n\n- `OQ-retry-policy`\n"
        )
        section = RUNNER.evaluate_assertion(
            {
                "type": "response_section_contains",
                "section": "Primary specification",
                "value": "specspine/retry-policy.md",
            },
            Path("."), {}, {}, response, None,
        )
        sections = RUNNER.evaluate_assertion(
            {
                "type": "response_sections_only",
                "sections": ["Primary specification", "Blocking questions"],
            },
            Path("."), {}, {}, response, None,
        )
        budget = RUNNER.evaluate_assertion(
            {"type": "response_word_budget", "max": 20},
            Path("."), {}, {}, response, None,
        )
        too_small = RUNNER.evaluate_assertion(
            {"type": "response_word_budget", "max": 2},
            Path("."), {}, {}, response, None,
        )
        self.assertTrue(section.passed, section.message)
        self.assertTrue(sections.passed, sections.message)
        self.assertTrue(budget.passed, budget.message)
        self.assertFalse(too_small.passed)

    def test_response_contains_any_accepts_each_alternative(self):
        assertion = {"type": "response_contains_any", "values": ["inference", "inferred"]}
        for response in ("This is an inference.", "This is inferred from repetition."):
            with self.subTest(response=response):
                result = RUNNER.evaluate_assertion(
                    assertion, Path("."), {}, {}, response, None
                )
                self.assertTrue(result.passed, result.message)
        missing = RUNNER.evaluate_assertion(
            assertion, Path("."), {}, {}, "This is uncertain.", None
        )
        self.assertFalse(missing.passed)

    def test_file_contains_any_accepts_semantically_equivalent_text(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            (workspace / "README.md").write_text(
                "Coverage remains intentionally incomplete.\n", encoding="utf-8"
            )
            result = RUNNER.evaluate_assertion(
                {
                    "type": "file_contains_any",
                    "path": "README.md",
                    "values": ["partial", "incomplete", "not mapped"],
                },
                workspace,
                {},
                {},
                "",
                None,
            )
            self.assertTrue(result.passed, result.message)

    def test_prompt_composes_runtime_inputs(self):
        case = {
            "scenario": "tests/scenarios/initialize-project.md",
            "skill": "skills/specspine-grow",
            "prompt": "REQUEST_SENTINEL_7b4c",
            "entrypoint": "ENTRYPOINT_SENTINEL_7b4c.md",
            "eval_language": "LANGUAGE_SENTINEL_7b4c",
        }
        prompt = RUNNER.build_prompt(case)
        self.assertIn(RUNNER.WORKSPACE_BOUNDARY_INSTRUCTIONS, prompt)
        self.assertEqual(1, prompt.count(case["entrypoint"]))
        self.assertEqual(1, prompt.count(case["eval_language"]))
        self.assertTrue(prompt.endswith(case["prompt"] + "\n"))

    def test_no_extract_prompt_and_fixture_do_not_expose_skill(self):
        case = {
            "id": "no-extract-sentinel",
            "scenario": "tests/scenarios/initialize-project.md",
            "skill": "skills/specspine-grow",
            "prompt": "REQUEST_SENTINEL_no_extract",
            "initial_files": {"README.md": "# Project\n"},
            "assertions": [],
            "_execution_profile": "no-extract",
        }
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            RUNNER.write_fixture(case, workspace)
            prompt = RUNNER.build_prompt(case)
            self.assertFalse((workspace / ".eval/skill").exists())

        self.assertNotIn(".eval/skill/", prompt)
        self.assertTrue(prompt.endswith(case["prompt"] + "\n"))

    def test_profile_specific_assertions_are_selected(self):
        assertions = [
            {"type": "max_changed_files", "max": 0},
            {"type": "command_includes", "value": "extract", "profiles": ["extract"]},
            {"type": "command_excludes", "value": "extract", "profiles": ["no-extract"]},
        ]

        selected = RUNNER.active_assertions(
            assertions, {"_execution_profile": "no-extract"}
        )

        self.assertEqual(
            ["max_changed_files", "command_excludes"],
            [assertion["type"] for assertion in selected],
        )

    def test_case_fingerprint_is_stable_across_execution_profiles(self):
        case = next(
            item
            for item in RUNNER.load_cases()
            if item["id"] == "extract-backend-multislice"
        )

        extract = RUNNER.case_fingerprint({**case, "_execution_profile": "extract"})
        baseline = RUNNER.case_fingerprint(
            {**case, "_execution_profile": "no-extract"}
        )

        self.assertEqual(extract, baseline)

    def test_prompt_exposes_only_user_request_from_scenario(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scenario = root / "scenario.md"
            scenario.write_text(
                "# Scenario\n\n## User request\nREQUEST_SENTINEL_c219\n\n"
                "## Hidden evaluator context\nHIDDEN_SENTINEL_c219\n",
                encoding="utf-8",
            )
            case = {
                "scenario": "scenario.md",
                "skill": "skills/specspine-grow",
                "assertions": [{"value": "ASSERTION_SENTINEL_c219"}],
            }
            with patch.object(RUNNER, "ROOT", root):
                prompt = RUNNER.build_prompt(case)
        self.assertTrue(prompt.endswith("REQUEST_SENTINEL_c219\n"))
        self.assertNotIn("HIDDEN_SENTINEL_c219", prompt)
        self.assertNotIn("ASSERTION_SENTINEL_c219", prompt)

    def test_workspace_does_not_expose_hidden_scenario(self):
        case = next(case for case in RUNNER.load_cases() if case["id"] == "doctor-semantic-health")
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            RUNNER.write_fixture(case, workspace)
            self.assertFalse((workspace / ".eval/scenario.md").exists())
            self.assertTrue((workspace / ".eval/skill/SKILL.md").is_file())

    def test_external_initial_tree_is_copied_and_fingerprinted(self):
        case = {"initial_tree": "fixture", "skill": "skill", "prompt": "Extract."}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "fixture/specspine").mkdir(parents=True)
            source = root / "fixture/specspine/README.md"
            source.write_text("# First\n", encoding="utf-8")
            (root / "skill").mkdir()
            (root / "skill/SKILL.md").write_text("# Skill\n", encoding="utf-8")
            workspace = root / "workspace"
            workspace.mkdir()
            with patch.object(RUNNER, "ROOT", root):
                RUNNER.write_fixture(case, workspace)
                first = RUNNER.case_fingerprint(case)
                source.write_text("# Second\n", encoding="utf-8")
                second = RUNNER.case_fingerprint(case)
            self.assertEqual(
                "# First\n",
                (workspace / "specspine/README.md").read_text(encoding="utf-8"),
            )
            self.assertNotEqual(first, second)

    def test_initial_tree_validation_rejects_missing_and_ambiguous_sources(self):
        base = {
            "id": "fixture-source",
            "scenario": "tests/scenarios/initialize-project.md",
            "status": "executable",
            "category": "core",
            "skill": "skills/specspine-grow",
            "assertions": [{"type": "max_changed_files", "max": 0}],
        }
        self.assertIn(
            "case requires exactly one of initial_files or initial_tree",
            RUNNER.validate_case(base),
        )
        ambiguous = {**base, "initial_files": {}, "initial_tree": "tests/eval"}
        self.assertIn(
            "case requires exactly one of initial_files or initial_tree",
            RUNNER.validate_case(ambiguous),
        )
        missing = {**base, "initial_tree": "tests/eval/context-bundles/missing"}
        self.assertIn(
            "initial tree does not exist: tests/eval/context-bundles/missing",
            RUNNER.validate_case(missing),
        )

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

    def test_aggregates_token_usage_across_agent_invocations(self):
        total = {}
        RUNNER.add_token_usage(
            total,
            {"token_usage": {"input_tokens": 100, "cached_input_tokens": 40, "output_tokens": 20}},
        )
        RUNNER.add_token_usage(
            total,
            {"token_usage": {"input_tokens": 70, "cached_input_tokens": 10, "output_tokens": 30}},
        )
        self.assertEqual(
            {"input_tokens": 170, "cached_input_tokens": 50, "output_tokens": 50},
            total,
        )
        self.assertEqual(
            "case time: 1.250s; Codex tokens: total 220; input 170 (cached 50); output 50",
            RUNNER.format_metrics(1.25, total),
        )

    def test_prefers_reported_total_tokens_and_handles_missing_usage(self):
        self.assertEqual(
            "case time: 2.000s; Codex tokens: total 42; input 30; output 12",
            RUNNER.format_metrics(
                2.0, {"total_tokens": 42, "input_tokens": 30, "output_tokens": 12}
            ),
        )
        self.assertEqual(
            "case time: 2.000s; Codex tokens unavailable",
            RUNNER.format_metrics(2.0, {}),
        )

    def test_aggregates_structured_case_report_tokens_for_summary(self):
        reports = [
            RUNNER.CaseReport("first", True, "", 1.0, {"total_tokens": 15, "input_tokens": 10}),
            RUNNER.CaseReport("second", False, "", 2.0, {"total_tokens": 25, "input_tokens": 20}),
        ]
        self.assertEqual(
            {"total_tokens": 40, "input_tokens": 30},
            RUNNER.aggregate_token_usage(reports),
        )

    def test_run_case_prints_tokens_summed_across_all_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = Path(directory) / "adapter.py"
            adapter.write_text(
                "import json, os, sys\n"
                "from pathlib import Path\n"
                "sys.stdin.read()\n"
                "Path('.eval/trace.json').write_text(json.dumps({"
                "'files_read': [], 'token_usage': {'input_tokens': 10, "
                "'output_tokens': 5, 'total_tokens': 15}}))\n",
                encoding="utf-8",
            )
            case = {
                "id": "metrics-self-test",
                "scenario": "tests/scenarios/initialize-project.md",
                "skill": "skills/specspine-grow",
                "runs": 2,
                "initial_files": {},
                "assertions": [{"type": "max_changed_files", "max": 0}],
            }
            output = io.StringIO()
            with patch("sys.stdout", output):
                self.assertTrue(RUNNER.run_case(case, [sys.executable, str(adapter)], False))
            self.assertIn(
                "Codex tokens: total 30; input 20; output 10",
                output.getvalue(),
            )

    def test_jobs_run_selected_cases_concurrently_and_queue_the_rest(self):
        cases = [
            {
                "id": case_id,
                "scenario": "tests/scenarios/initialize-project.md",
                "skill": "skills/specspine-grow",
                "status": "executable",
                "category": "core",
                "initial_files": {},
                "assertions": [{"type": "path_exists", "path": "result.md"}],
            }
            for case_id in ("parallel-a", "parallel-b", "parallel-c")
        ]
        barrier = threading.Barrier(2)
        fast_finished = threading.Event()
        queued_started_after_fast = threading.Event()
        lock = threading.Lock()
        called: list[str] = []

        def fake_run_case(
            case, command, keep_workspace, output=None, metrics=None, sample_number=1
        ):
            with lock:
                called.append(case["id"])
                call_number = len(called)
                if call_number == 3 and fast_finished.is_set():
                    queued_started_after_fast.set()
            print(f"START {case['id']}", file=output)
            if call_number <= 2:
                barrier.wait(timeout=2)
            if call_number == 1:
                fast_finished.wait(timeout=2)
            elif call_number == 2:
                fast_finished.set()
            print(f"END {case['id']}", file=output)
            return True

        argv = ["run.py", "--category", "core", "--jobs", "2", "--agent-command", "fake-agent"]
        stdout = io.StringIO()
        with (
            patch.object(RUNNER, "load_cases", return_value=cases),
            patch.object(RUNNER, "validate_collection", return_value=[]),
            patch.object(RUNNER, "validate_case", return_value=[]),
            patch.object(RUNNER, "run_case", side_effect=fake_run_case),
            patch.object(sys, "argv", argv),
            patch("sys.stdout", stdout),
        ):
            self.assertEqual(0, RUNNER.main())
        self.assertCountEqual(["parallel-a", "parallel-b", "parallel-c"], called)
        report = stdout.getvalue()
        for case_id in ("parallel-a", "parallel-b", "parallel-c"):
            self.assertIn(f"START {case_id}\nEND {case_id}\n", report)
        self.assertTrue(queued_started_after_fast.is_set())

    def test_default_runs_selected_cases_concurrently(self):
        cases = [
            {
                "id": case_id,
                "scenario": "tests/scenarios/initialize-project.md",
                "skill": "skills/specspine-grow",
                "status": "executable",
                "category": "core",
                "initial_files": {},
                "assertions": [],
            }
            for case_id in (f"default-{number}" for number in range(9))
        ]
        barrier = threading.Barrier(8)
        lock = threading.Lock()
        calls = 0
        worker_counts: list[int] = []
        real_executor = RUNNER.ThreadPoolExecutor

        def fake_run_case(
            case, command, keep_workspace, output=None, metrics=None, sample_number=1
        ):
            nonlocal calls
            with lock:
                calls += 1
                call_number = calls
            if call_number <= 8:
                barrier.wait(timeout=2)
            return True

        def recording_executor(max_workers):
            worker_counts.append(max_workers)
            return real_executor(max_workers=max_workers)

        argv = ["run.py", "--category", "core", "--agent-command", "fake-agent"]
        with (
            patch.object(RUNNER, "load_cases", return_value=cases),
            patch.object(RUNNER, "validate_collection", return_value=[]),
            patch.object(RUNNER, "validate_case", return_value=[]),
            patch.object(RUNNER, "run_case", side_effect=fake_run_case),
            patch.object(RUNNER, "ThreadPoolExecutor", side_effect=recording_executor),
            patch.object(sys, "argv", argv),
        ):
            self.assertEqual(0, RUNNER.main())
        self.assertEqual([8], worker_counts)

    def test_one_job_runs_selected_cases_sequentially(self):
        cases = [
            {
                "id": case_id,
                "scenario": "tests/scenarios/initialize-project.md",
                "skill": "skills/specspine-grow",
                "status": "executable",
                "category": "core",
                "initial_files": {},
                "assertions": [],
            }
            for case_id in ("sequential-a", "sequential-b")
        ]
        called: list[str] = []

        def fake_run_case(
            case, command, keep_workspace, output=None, metrics=None, sample_number=1
        ):
            called.append(case["id"])
            return True

        argv = ["run.py", "--category", "core", "--jobs", "1", "--agent-command", "fake-agent"]
        with (
            patch.object(RUNNER, "load_cases", return_value=cases),
            patch.object(RUNNER, "validate_collection", return_value=[]),
            patch.object(RUNNER, "validate_case", return_value=[]),
            patch.object(RUNNER, "run_case", side_effect=fake_run_case),
            patch.object(RUNNER, "ThreadPoolExecutor") as executor,
            patch.object(sys, "argv", argv),
        ):
            self.assertEqual(0, RUNNER.main())
        executor.assert_not_called()
        self.assertEqual(["sequential-a", "sequential-b"], called)

    def test_prints_test_summary_after_execution(self):
        cases = [
            {
                "id": case_id,
                "scenario": "tests/scenarios/initialize-project.md",
                "skill": "skills/specspine-grow",
                "status": "executable",
                "category": "core",
                "initial_files": {},
                "assertions": [],
            }
            for case_id in ("passing", "failing")
        ]
        output = io.StringIO()
        argv = ["run.py", "--category", "core", "--jobs", "1", "--agent-command", "fake-agent"]
        with (
            patch.object(RUNNER, "load_cases", return_value=cases),
            patch.object(RUNNER, "validate_collection", return_value=[]),
            patch.object(RUNNER, "validate_case", return_value=[]),
            patch.object(RUNNER, "run_case", side_effect=[True, False]),
            patch.object(sys, "argv", argv),
            patch("sys.stdout", output),
        ):
            self.assertEqual(1, RUNNER.main())
        report = output.getvalue()
        self.assertIn("[1/2 completed]", report)
        self.assertIn("[2/2 completed]", report)
        self.assertIn("SUMMARY: 1/2 tests passed", report)
        self.assertIn("wall time:", report)
        self.assertIn("summed case time:", report)
        self.assertIn("Codex tokens unavailable", report)
        self.assertIn("failed: failing", report)

    def test_samples_report_independent_success_rate(self):
        cases = [
            {
                "id": "sampled",
                "scenario": "tests/scenarios/initialize-project.md",
                "skill": "skills/specspine-grow",
                "status": "executable",
                "category": "core",
                "initial_files": {},
                "assertions": [],
            }
        ]
        seen_samples = []

        def fake_run_case(
            case, command, keep_workspace, output=None, metrics=None, sample_number=1
        ):
            seen_samples.append(sample_number)
            metrics.update(
                duration_seconds=float(sample_number),
                token_usage={"total_tokens": sample_number * 10},
            )
            print(f"sample {sample_number}", file=output)
            return sample_number != 2

        output = io.StringIO()
        argv = [
            "run.py", "--case", "sampled", "--samples", "3", "--jobs", "1",
            "--agent-command", "fake-agent",
        ]
        with (
            patch.object(RUNNER, "load_cases", return_value=cases),
            patch.object(RUNNER, "validate_collection", return_value=[]),
            patch.object(RUNNER, "validate_case", return_value=[]),
            patch.object(RUNNER, "run_case", side_effect=fake_run_case),
            patch.object(sys, "argv", argv),
            patch("sys.stdout", output),
        ):
            self.assertEqual(1, RUNNER.main())
        report = output.getvalue()
        self.assertEqual([1, 2, 3], seen_samples)
        self.assertIn("SUMMARY: 2/3 samples passed", report)
        self.assertIn("summed case time: 6.000s", report)
        self.assertIn("Codex tokens: total 60", report)
        self.assertIn("failed: sampled#2", report)
        self.assertIn("sampled: 2/3 (66.7%)", report)

    def test_jobs_must_be_positive(self):
        self.assertEqual(3, RUNNER.positive_int("3"))
        with self.assertRaises(RUNNER.argparse.ArgumentTypeError):
            RUNNER.positive_int("0")

    def test_json_report_preserves_per_sample_agent_metrics(self):
        case = next(
            item
            for item in RUNNER.load_cases()
            if item["id"] == "extract-backend-multislice"
        )
        report = RUNNER.CaseReport(
            case_id=case["id"],
            passed=False,
            output="",
            duration_seconds=12.0,
            token_usage={"input_tokens": 90, "total_tokens": 100},
            sample_number=2,
            agent_runs=(
                {
                    "retrieval_mode": "sqlite-fts5",
                    "duration_seconds": 10.0,
                    "environment_invalid": False,
                    "files_read": 5,
                    "model": "model-1",
                    "reasoning_effort": "medium",
                    "event_metrics": {
                        "command_count": 4,
                        "command_output_chars": 321,
                    },
                    "token_usage": {"input_tokens": 90, "total_tokens": 100},
                },
            ),
            failed_checks=({"type": "sentinel-check", "message": "sentinel"},),
            started_at="2026-07-22T10:00:00+00:00",
            finished_at="2026-07-22T10:00:10+00:00",
            queue_seconds=0.25,
            response="response-sentinel",
            stderr="stderr-sentinel",
        )
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "report.json"

            RUNNER.write_json_report(
                target, "production", "agent", [report], [case], 3, 8
            )

            payload = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(2, payload["schema_version"])
        self.assertEqual(8, payload["jobs"])
        self.assertFalse(payload["samples"][0]["passed"])
        self.assertEqual(10.0, payload["samples"][0]["agent_duration_seconds"])
        self.assertEqual(100, payload["samples"][0]["token_usage"]["total_tokens"])
        self.assertEqual(
            4,
            payload["samples"][0]["agent_runs"][0]["event_metrics"]["command_count"],
        )
        self.assertTrue(payload["samples"][0]["environment_valid"])
        self.assertEqual("sentinel-check", payload["samples"][0]["failed_checks"][0]["type"])
        self.assertEqual(64, len(payload["cases"][case["id"]]["fingerprint"]))
        self.assertEqual(64, len(payload["fingerprints"]["runner"]))
        self.assertIn("run_id", payload["run"])
        self.assertEqual(["extract"], payload["run"]["execution_profile"])
        self.assertEqual(
            64,
            len(payload["run"]["prompt_fingerprints"][case["id"]]),
        )
        self.assertEqual(0.25, payload["samples"][0]["queue_seconds"])
        self.assertEqual(
            "response-sentinel", payload["samples"][0]["diagnostics"]["response"]
        )

    def test_agent_execution_requires_case_or_category(self):
        with patch.object(sys, "argv", ["run.py", "--agent-command", "fake-agent"]):
            with self.assertRaises(SystemExit) as raised:
                RUNNER.main()
        self.assertEqual(2, raised.exception.code)


if __name__ == "__main__":
    unittest.main()
