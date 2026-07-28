import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "eval" / "benchmark_extract_agents.py"
SPEC = importlib.util.spec_from_file_location("benchmark_extract_agents", SCRIPT)
BENCHMARK = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(BENCHMARK)

GRAFANA_SCRIPT = Path(__file__).parents[1] / "eval" / "benchmark_extract_grafana.py"
GRAFANA_SPEC = importlib.util.spec_from_file_location(
    "benchmark_extract_grafana", GRAFANA_SCRIPT
)
GRAFANA_BENCHMARK = importlib.util.module_from_spec(GRAFANA_SPEC)
assert GRAFANA_SPEC.loader is not None
GRAFANA_SPEC.loader.exec_module(GRAFANA_BENCHMARK)

GROW_GRAFANA_SCRIPT = (
    Path(__file__).parents[1] / "eval" / "benchmark_extract_grow_grafana.py"
)
GROW_GRAFANA_SPEC = importlib.util.spec_from_file_location(
    "benchmark_extract_grow_grafana", GROW_GRAFANA_SCRIPT
)
GROW_GRAFANA_BENCHMARK = importlib.util.module_from_spec(GROW_GRAFANA_SPEC)
assert GROW_GRAFANA_SPEC.loader is not None
GROW_GRAFANA_SPEC.loader.exec_module(GROW_GRAFANA_BENCHMARK)


class ExtractAgentBenchmarkTests(unittest.TestCase):
    def test_grafana_cases_use_large_external_fixture_and_fixed_arms(self):
        fixture = Path("/fixtures/grafana")
        cases = [
            GRAFANA_BENCHMARK.grafana_case(fixture, "extract", scenario)
            for scenario in GRAFANA_BENCHMARK.SCENARIOS
        ]
        self.assertEqual(7, len(cases))
        self.assertEqual(7, len({case["id"] for case in cases}))
        self.assertTrue(all(case["initial_tree"] == str(fixture) for case in cases))
        self.assertTrue(all(case["category"] == "expensive" for case in cases))
        self.assertIn(
            "specspine/persistence/resource-dualwrite-lifecycle.md",
            cases[0]["handoff_judgments"]["required"],
        )
        self.assertIn(
            "specspine/operations/resource-provisioning-reconciliation.md",
            cases[0]["handoff_judgments"]["hard_negatives"],
        )
        for case in cases:
            self.assertEqual(
                case["handoff_judgments"]["relevant"],
                case["handoff_judgments"]["required"]
                + case["handoff_judgments"]["supporting"],
            )
        self.assertEqual(
            ["no-extract", "source-search", "accelerated"],
            [label for label, *_ in GRAFANA_BENCHMARK.ARMS],
        )

    def test_grafana_fixture_copies_only_bootstrap_and_spine(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "grafana"
            (source / "specspine").mkdir(parents=True)
            (source / "AGENTS.md").write_text("bootstrap", encoding="utf-8")
            (source / "specspine" / "README.md").write_text("index", encoding="utf-8")
            (source / "ignored.go").write_text("ignored", encoding="utf-8")
            target = GRAFANA_BENCHMARK.materialize_fixture(source, root / "fixture")
            self.assertTrue((target / "AGENTS.md").is_file())
            self.assertTrue((target / "specspine" / "README.md").is_file())
            self.assertFalse((target / "ignored.go").exists())

    def test_grafana_source_fixture_excludes_specspine_and_strips_bootstrap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "grafana"
            (source / "specspine").mkdir(parents=True)
            (source / "pkg").mkdir()
            (source / "AGENTS.md").write_text(
                "# Instructions\n"
                "<!-- specspine:begin -->\nUse SpecSpine.\n"
                "<!-- specspine:end -->\n",
                encoding="utf-8",
            )
            (source / "specspine" / "README.md").write_text(
                "index", encoding="utf-8"
            )
            (source / "pkg" / "service.go").write_text(
                "package pkg\n", encoding="utf-8"
            )
            listed = b"AGENTS.md\\0specspine/README.md\\0pkg/service.go\\0".replace(
                b"\\0", b"\0"
            )
            with mock.patch.object(
                GRAFANA_BENCHMARK.subprocess,
                "run",
                return_value=mock.Mock(stdout=listed),
            ):
                target = GRAFANA_BENCHMARK.materialize_source_fixture(
                    source, root / "source-fixture"
                )
            self.assertTrue((target / "pkg" / "service.go").is_file())
            self.assertFalse((target / "specspine").exists())
            self.assertNotIn(
                "SpecSpine",
                (target / "AGENTS.md").read_text(encoding="utf-8"),
            )

    def test_grafana_source_search_uses_alternative_source_path_groups(self):
        fixture = Path("/fixtures/grafana-source")
        case = GRAFANA_BENCHMARK.grafana_case(
            fixture,
            "source-search",
            GRAFANA_BENCHMARK.SCENARIOS[0],
        )
        judgments = case["handoff_judgments"]
        self.assertFalse(judgments["required"])
        self.assertTrue(judgments["required_groups"])
        self.assertNotIn("specspine/", " ".join(judgments["relevant"]))
        group_assertions = [
            item
            for item in case["assertions"]
            if item["type"] == "response_contains_any"
        ]
        self.assertEqual(
            len(judgments["required_groups"]),
            len(group_assertions),
        )

    def test_grafana_no_extract_adapter_does_not_enable_retrieval_telemetry(self):
        command = GRAFANA_BENCHMARK.adapter_command(
            "accelerated",
            "model",
            "medium",
            instrument_retrieval=False,
        )
        self.assertNotIn("--retrieval-telemetry", command)

    def test_grafana_run_arm_accepts_a_scenario_subset(self):
        selected = tuple(
            scenario
            for scenario in GRAFANA_BENCHMARK.SCENARIOS
            if scenario["id"] == "extract-grafana-frontend-api-boundary"
        )
        self.assertEqual(
            ["extract-grafana-frontend-api-boundary"],
            [scenario["id"] for scenario in selected],
        )

    def test_grow_grafana_ab_has_two_arms_and_three_fixed_scenarios(self):
        self.assertEqual(
            [("without-extract", False), ("with-extract", True)],
            list(GROW_GRAFANA_BENCHMARK.ARMS),
        )
        self.assertEqual(3, len(GROW_GRAFANA_BENCHMARK.SCENARIOS))
        self.assertEqual(
            3,
            len(
                {
                    scenario["target"]
                    for scenario in GROW_GRAFANA_BENCHMARK.SCENARIOS
                }
            ),
        )

    def test_grow_grafana_treatment_changes_only_extract_availability(self):
        fixture = Path("/fixtures/grafana")
        scenario = GROW_GRAFANA_BENCHMARK.SCENARIOS[0]
        baseline = GROW_GRAFANA_BENCHMARK.grow_case(fixture, False, scenario)
        treatment = GROW_GRAFANA_BENCHMARK.grow_case(fixture, True, scenario)
        self.assertEqual([], baseline["companion_skills"])
        self.assertEqual(
            ["skills/specspine-extract"], treatment["companion_skills"]
        )
        self.assertEqual(baseline["skill"], treatment["skill"])
        self.assertEqual(baseline["scenario"], treatment["scenario"])
        self.assertEqual([scenario["target"]], baseline["report_artifacts"])
        self.assertEqual("command_excludes", baseline["assertions"][-1]["type"])
        self.assertEqual("command_includes", treatment["assertions"][-2]["type"])

    def test_grow_grafana_blind_package_scores_hidden_arms(self):
        scenario = GROW_GRAFANA_BENCHMARK.SCENARIOS[0]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            grafana = root / "grafana"
            target = grafana / scenario["target"]
            target.parent.mkdir(parents=True)
            target.write_text("# Initial\n", encoding="utf-8")
            reports = {}
            for label, _ in GROW_GRAFANA_BENCHMARK.ARMS:
                reports[label] = {
                    "samples": [{
                        "case_id": scenario["id"],
                        "sample_number": 1,
                        "artifacts": {
                            scenario["target"]: f"# Final {label}\n"
                        },
                    }]
                }
            GROW_GRAFANA_BENCHMARK.write_blind_package(
                root,
                reports,
                grafana,
                (scenario,),
                "timestamp",
            )
            cases = json.loads(
                (root / "blind-review" / "cases.json").read_text(
                    encoding="utf-8"
                )
            )["cases"]
            candidates = list(cases[0]["candidates"])
            judgments = {
                "judgments": [{
                    "pair_id": cases[0]["pair_id"],
                    "scores": {
                        candidate: {
                            field: 4 if index == 0 else 3
                            for field in GROW_GRAFANA_BENCHMARK.RUBRIC_FIELDS
                        }
                        for index, candidate in enumerate(candidates)
                    },
                    "preferred_candidate": candidates[0],
                    "rationale": "candidate one is more complete",
                }]
            }
            judgment_path = root / "judgments.json"
            judgment_path.write_text(
                json.dumps(judgments), encoding="utf-8"
            )
            scores = GROW_GRAFANA_BENCHMARK.score_judgments(
                root, judgment_path
            )
            self.assertEqual(
                {20.0, 15.0},
                {
                    values["mean_blind_quality_0_20"]
                    for values in scores.values()
                },
            )
            self.assertEqual(1, sum(values["blind_wins"] for values in scores.values()))

    def test_three_fixed_arms_use_current_extract_cases(self):
        self.assertEqual(
            ["no-extract", "fallback", "accelerated"],
            [label for label, *_ in BENCHMARK.ARMS],
        )
        command, report = BENCHMARK.report_command(
            Path("/reports"),
            "fallback",
            "fallback",
            "fallback",
            samples=2,
            jobs=3,
            model="model",
            reasoning_effort="medium",
            timestamp="stamp",
        )
        rendered = " ".join(command)
        self.assertIn("--execution-profile fallback", rendered)
        self.assertIn("--retrieval-profile fallback", rendered)
        self.assertNotIn("--ranking", rendered)
        self.assertNotIn("--graph-limit", rendered)
        self.assertEqual(Path("/reports/fallback.json"), report)
        for case in BENCHMARK.CASES:
            self.assertIn(case, command)

    def test_no_extract_arm_does_not_instrument_missing_skill(self):
        command, _ = BENCHMARK.report_command(
            Path("/reports"),
            "no-extract",
            "no-extract",
            "accelerated",
            samples=1,
            jobs=1,
            model="model",
            reasoning_effort="medium",
            timestamp="stamp",
        )
        rendered = " ".join(command)
        self.assertNotIn("--retrieval-telemetry", rendered)

    def test_source_groups_use_group_recall_and_open_world_precision(self):
        report = {
            "cases": {
                "source-case": {
                    "handoff_judgments": {
                        "required": [],
                        "required_groups": [
                            ["pkg/a.go", "pkg/a_alt.go"],
                            ["pkg/b.go"],
                        ],
                        "supporting": [],
                        "relevant": ["pkg/a.go", "pkg/a_alt.go", "pkg/b.go"],
                        "hard_negatives": ["pkg/wrong.go"],
                        "open_world_relevance": True,
                    }
                }
            },
            "samples": [{
                "case_id": "source-case",
                "passed": True,
                "diagnostics": {
                    "response": "pkg/a_alt.go pkg/extra.go pkg/wrong.go"
                },
                "agent_runs": [],
            }],
        }
        summary = BENCHMARK.summarize(report)
        self.assertEqual(0.5, summary["mean_required_recall"])
        self.assertEqual(0.5, summary["mean_handoff_precision"])

    def test_comparison_contains_agent_cost_and_quality_metrics(self):
        sample = {
            "case_id": "case",
            "passed": True,
            "agent_duration_seconds": 1.0,
            "token_usage": {
                "input_tokens": 8,
                "cached_input_tokens": 3,
                "output_tokens": 2,
            },
            "agent_runs": [{
                "files_read": 2,
                "retrieval_attempt_count": 1,
                "unexpected_retry": False,
                "cost_ledger": {
                    "tool_cycles": 1,
                    "retrieval_output_utf8_bytes": 20,
                    "project_source_file_bytes": 30,
                },
                "retrieval_phase_metrics": {
                    "pre_retrieval_seconds": 0.5,
                    "production_retrieval_seconds": 0.1,
                    "post_retrieval_seconds": 0.4,
                    "post_retrieval_file_reads": 0,
                    "post_retrieval_returned_file_reads": 0,
                    "post_retrieval_unreturned_file_reads": 0,
                    "post_retrieval_returned_file_paths": [
                        "specspine/owner.md"
                    ],
                    "post_retrieval_unreturned_file_paths": [
                        "specspine/extra.md"
                    ],
                },
            }],
        }
        reports = {
            label: {
                "cases": {
                    "case": {
                        "handoff_judgments": {
                            "required": ["specspine/owner.md"],
                            "supporting": ["specspine/support.md"],
                            "relevant": [
                                "specspine/owner.md",
                                "specspine/support.md",
                            ],
                        }
                    }
                },
                "samples": [{
                    **json.loads(json.dumps(sample)),
                    "diagnostics": {
                        "response": "specspine/owner.md specspine/support.md"
                    },
                }],
            }
            for label, *_ in BENCHMARK.ARMS
        }
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "comparison.md"
            BENCHMARK.write_comparison(target, reports)
            text = target.read_text(encoding="utf-8")
        self.assertIn("No Extract", text)
        self.assertIn("Extract fallback", text)
        self.assertIn("Accelerated Extract", text)
        self.assertIn("mean_total_tokens", text)
        self.assertIn("mean_uncached_input_tokens", text)
        self.assertIn("quality_pass_rate", text)
        self.assertIn("mean_tool_cycles", text)
        self.assertIn("mean_required_recall", text)
        self.assertIn("mean_handoff_precision", text)
        self.assertIn("unexpected_retry_rate", text)
        self.assertIn("mean_production_retrieval_seconds", text)
        self.assertIn("mean_post_retrieval_file_reads", text)
        self.assertIn("mean_post_retrieval_returned_file_reads", text)
        self.assertIn("mean_post_retrieval_unreturned_file_reads", text)
        self.assertIn("`specspine/owner.md` (1)", text)
        self.assertIn("`specspine/extra.md` (1)", text)


if __name__ == "__main__":
    unittest.main()
