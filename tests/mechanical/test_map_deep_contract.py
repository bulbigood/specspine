import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]


class MapDeepContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapper = (ROOT / "skills/specspine-map/SKILL.md").read_text(
            encoding="utf-8"
        )
        cls.deep = (ROOT / "skills/specspine-map-deep/SKILL.md").read_text(
            encoding="utf-8"
        )
        cls.protocol = (
            ROOT / "skills/specspine-map-deep/references/orchestration.md"
        ).read_text(encoding="utf-8")
        cls.metadata = (
            ROOT / "skills/specspine-map-deep/agents/openai.yaml"
        ).read_text(encoding="utf-8")
        cls.eval_scenario = (
            ROOT / "tests/scenarios/map-deep-rolling-small.md"
        ).read_text(encoding="utf-8")

    def test_map_stays_atomic_and_deep_is_explicit(self):
        self.assertNotIn("references/orchestration.md", self.mapper)
        self.assertNotIn("producer", self.mapper.lower())
        self.assertNotIn("specspine-map-deep", self.mapper)
        self.assertIn("the requested repository scope", self.mapper)
        self.assertIn("one shallowest useful mapping step", self.mapper)
        self.assertIn("instead of pursuing them recursively", self.mapper)
        self.assertIn("references/orchestration.md", self.deep)
        self.assertIn("allow_implicit_invocation: false", self.metadata)

    def test_map_deep_accepts_the_same_user_scope_as_map(self):
        normalized = " ".join((self.deep + self.protocol).split())
        self.assertIn("Accept the same scope as `specspine-map`", normalized)
        self.assertIn("one focused concern, several areas, or the whole repository", normalized)
        self.assertIn("Map exactly the scope requested by the operator", normalized)
        self.assertNotIn("Do not use for a focused survey", self.deep)
        self.assertNotIn("complete large-repository Map run", self.deep)

    def test_entrypoint_routes_without_repeating_orchestration(self):
        self.assertIn("sole Map-Deep execution protocol", self.deep)
        self.assertLessEqual(len(self.deep.splitlines()), 30)
        for detail in (
            "private staging root",
            "`Current-branch continuation`",
            "--candidates",
            "Immediately dispatch ready work",
            "When subagents are unavailable",
        ):
            with self.subTest(detail=detail):
                self.assertNotIn(detail, self.deep)

    def test_discovery_is_adaptive_and_has_no_recovery_protocol(self):
        normalized = " ".join((self.deep + self.protocol).split()).lower()
        self.assertIn("discover evidence adaptively", normalized)
        self.assertIn("do not prescribe a universal listing command", normalized)
        self.assertIn("do not create a ledger", normalized)
        self.assertIn("current spine", normalized)
        for obsolete in (
            "survey_repository.py",
            "ledger.ndjson",
            "run_started",
            "producer_completed",
            "recovery.status",
            "source_drift",
            "project_inventory_sha256",
        ):
            with self.subTest(obsolete=obsolete):
                self.assertNotIn(obsolete, normalized)
        self.assertFalse(
            (ROOT / "skills/specspine-map-deep/scripts/survey_repository.py").exists()
        )

    def test_map_refuses_terminal_output_and_branch_owner_reaches_saturation(self):
        normalized_map = " ".join(self.mapper.split())
        normalized = " ".join((self.deep + self.protocol).split())
        self.assertIn("Create or change no document when", normalized_map)
        self.assertIn("Report that terminal reason explicitly", normalized_map)
        self.assertIn("never manufacture output to keep the branch alive", normalized)
        self.assertIn("until it reports terminal `no useful node`", normalized)
        self.assertIn("do not create a fresh producer merely to probe the same branch", normalized)
        self.assertIn("no actionable branch remains", normalized)
        self.assertIn("Do not stop at a predetermined document count", normalized)

    def test_new_producers_receive_complete_map_instructions_once(self):
        normalized = " ".join((self.deep + self.protocol).split())
        self.assertIn("bundle_skill.py", self.protocol)
        self.assertIn("every UTF-8 file under Map `references/`", normalized)
        self.assertIn("every UTF-8 Markdown file", normalized)
        self.assertIn("Build the complete Map instruction bundle once", self.protocol)
        self.assertIn("complete-generated-map-instructions", self.protocol)
        self.assertIn("Do not load or invoke any skill", self.protocol)
        self.assertIn("only in the initial command for each new producer session", normalized)
        self.assertIn("never resend the bundle or immutable shared context", normalized)
        self.assertNotIn("$specspine-map", self.protocol)

    def test_each_producer_turn_is_one_map_step_until_refusal(self):
        normalized = " ".join((self.deep + self.protocol).split())
        for statement in (
            "Perform exactly one Map step in this turn",
            "Do not execute the reported continuation in the same turn",
            "one Map step per checkpoint",
        ):
            with self.subTest(statement=statement):
                self.assertIn(statement, normalized)

    def test_orchestrator_owns_forks_and_producers_keep_branch_affinity(self):
        normalized = " ".join((self.deep + self.protocol).split())
        for statement in (
            "The orchestrator is the sole scheduling authority",
            "The producer may propose child branches but must never create producers",
            "A same-boundary continuation remains with its current producer",
            "never repurpose that session for an unrelated branch",
            "`Current-branch continuation`",
            "`Fork candidates`",
            "accept conflict-free reservation requests",
            "Resume a continuing branch through the environment's native follow-up mechanism",
            "complete` only when it is locally saturated and every accepted child branch is complete",
        ):
            with self.subTest(statement=statement):
                self.assertIn(statement, normalized)

    def test_parallel_producers_are_isolated_and_consumer_moves_results(self):
        normalized = " ".join(self.protocol.split())
        for statement in (
            "one private staging root per active producer session",
            "Resolve one current evidence baseline once",
            "Keep source, tests, configuration, the live Spine",
            "Do not reread candidate prose",
            "--replace-existing",
            "Move every accepted candidate unchanged",
            "Never reconstruct a file by reading and rewriting it",
            "Defer index reachability",
        ):
            with self.subTest(statement=statement):
                self.assertIn(statement, normalized)

    def test_map_owns_mapping_rules_and_override_only_adapts_execution(self):
        normalized_map = " ".join(self.mapper.split())
        normalized_protocol = " ".join(self.protocol.split())
        self.assertIn(
            "Source code, tests, configuration, and other repository behavior",
            normalized_map,
        )
        self.assertIn(
            "complete replacements of explicitly assigned existing specifications",
            normalized_map,
        )
        for duplicate in (
            "Put a short summary below each H1",
            "Write repository paths only as inline code",
            "Code supports only Observed or Inferred claims",
            "Every candidate must contain a `## Responsibility` section",
        ):
            with self.subTest(duplicate=duplicate):
                self.assertNotIn(duplicate, normalized_protocol)

    def test_production_contract_has_no_eval_or_model_specific_rules(self):
        normalized = (self.deep + self.protocol).lower()
        for marker in (
            ".eval/",
            "benchmark",
            "fixture",
            "sample",
            "gpt-",
            "luna",
            "terra",
            "exactly two producers",
            "exactly six",
        ):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, normalized)

    def test_executable_eval_request_does_not_leak_expected_orchestration(self):
        request = self.eval_scenario.split("## User request", 1)[1].split(
            "## Expected behavior",
            1,
        )[0]
        for leak in (
            ".eval/",
            "bundle_skill.py",
            "check_spine.py",
            ".specspine-map-run",
            "exactly six",
            "resume that same producer",
            "no useful node",
            "identity-sessions.md",
            "webhook-ingestion.md",
        ):
            with self.subTest(leak=leak):
                self.assertNotIn(leak, request)

    def test_scheduler_refills_without_batches_and_cleans_safely(self):
        normalized = " ".join(self.protocol.split())
        self.assertIn("Immediately dispatch ready work into every free slot", normalized)
        self.assertIn("without waiting for siblings or forming pairs or waves", normalized)
        self.assertIn("find <run-root> -depth -delete", normalized)
        self.assertNotIn("`rm -rf <run-root>`", normalized)

    def test_sequential_fallback_changes_only_concurrency(self):
        normalized = " ".join((self.deep + self.protocol).split())
        self.assertIn("When subagents are unavailable", normalized)
        self.assertIn("orchestrator, producer, and consumer roles", normalized)
        self.assertIn("only concurrency changes", normalized)

    def test_normalization_and_doctor_happen_only_after_saturation(self):
        normalized = " ".join(self.protocol.split())
        self.assertIn("Do not invoke SpecSpine Doctor", normalized)
        self.assertIn("After saturation, perform one sequential navigation pass", normalized)
        self.assertIn("Add every new document to curated `README.md` navigation", normalized)
        self.assertIn("Run the full deterministic checker once", normalized)
        self.assertIn("only when the operator explicitly requests", normalized)
        self.assertLessEqual(len(self.protocol.splitlines()), 220)


if __name__ == "__main__":
    unittest.main()
