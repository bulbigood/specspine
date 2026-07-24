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

    def test_entrypoint_gates_parallel_reference_before_discovery(self):
        normalized = " ".join(self.deep.split())
        self.assertIn("Before reading any reference or starting discovery", normalized)
        self.assertIn("Do not probe capability by starting a subagent", normalized)
        self.assertIn("If a subagent-creation mechanism is exposed", normalized)
        self.assertIn("If no subagent-creation mechanism is exposed", normalized)
        self.assertIn("do not read that reference", normalized)
        self.assertLessEqual(len(self.deep.splitlines()), 70)
        for detail in (
            "private staging root",
            "`Current-branch continuation`",
            "--candidates",
            "Immediately dispatch ready work",
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
        self.assertIn(
            "Any checkpoint that created or replaced a file must be `continuing`",
            normalized,
        )
        self.assertIn(
            "A `locally saturated` checkpoint must be candidate-free",
            normalized,
        )
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
        self.assertIn("Prefix every new `spawn_agent` message", normalized)
        self.assertIn("isolated producers share no bundle", normalized)
        self.assertIn("Start each producer with a medium-strength model", normalized)
        self.assertIn('`agent_type="medium"`', normalized)
        self.assertIn('`fork_turns="none"`', normalized)
        self.assertIn("equivalent medium-capability role", normalized)
        self.assertIn("initial command is self-contained", normalized)
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
            "Give each initial assignment exactly one independent architectural branch question",
            "Never combine sibling responsibilities",
            "The producer may propose child branches but must never create producers",
            "A same-boundary continuation remains with its current producer",
            "never repurpose that session for an unrelated branch",
            "`Current-branch continuation`",
            "`Fork candidates`",
            "accept conflict-free reservation requests",
            "Treat any checkpoint that published a candidate as `continuing`",
            "regardless of its reported status or missing continuation",
            "only a later candidate-free `no useful node`",
            "Resume a continuing branch through the environment's native follow-up mechanism",
            "complete` only when it is locally saturated and every accepted child branch is complete",
        ):
            with self.subTest(statement=statement):
                self.assertIn(statement, normalized)

    def test_broad_surveys_cannot_vacuously_saturate(self):
        normalized = " ".join((self.deep + self.protocol).split())
        for statement in (
            "coverage frontier",
            "producer proposals never define the completeness",
            "A terminal Map refusal closes only the exact branch question",
            "A broad survey branch cannot become `locally saturated`",
            "Report every such boundary directly observed",
            "`Coverage frontier`",
            "reconcile every `Coverage frontier` item",
            "Treat `no useful node` as scoped to the exact assigned question",
            "audit the in-memory branch ToDo against the coverage frontiers",
        ):
            with self.subTest(statement=statement):
                self.assertIn(statement, normalized)
        self.assertIn(
            "The prohibition on mirroring source structure applies to published "
            "specifications, not to discovery or scheduling",
            normalized,
        )

    def test_unknown_and_partial_capacity_are_transactional(self):
        normalized = " ".join(self.protocol.split())
        for statement in (
            "Treat producer capacity as observed, not planned",
            "an exact limit need not be known in advance",
            "attempt to start producer subagents",
            "never choose local execution for convenience",
            "only after no usable producer handle can be obtained",
            "Keep a branch `queued` and unowned until the environment confirms",
            "Only then assign that handle, mark the branch `active`, and count its slot",
            "A failed start or missing handle leaves the branch queued",
            "Capacity exhaustion reduces concurrency",
            "retry ready branches only after capacity may have been released",
            "clear its ownership, and requeue the branch with fresh private staging",
            "Never count planned, attempted, failed, or terminated sessions as active",
            "Never interrupt a running producer",
            "Interrupt only for operator cancellation or a confirmed hang or failure",
        ):
            with self.subTest(statement=statement):
                self.assertIn(statement, normalized)

    def test_parallel_producers_are_isolated_and_consumer_moves_results(self):
        normalized = " ".join(self.protocol.split())
        for statement in (
            "one private staging root per active producer session",
            "Resolve one current evidence baseline once",
            "Keep source, tests, configuration, the live Spine",
            "Tool-level write access does not authorize live-Spine writes",
            "must begin with the private staging root",
            "Do not reread candidate prose",
            "<map-deep-skill-root>/scripts/check_spine.py",
            "--replace-existing",
            "Move every accepted candidate unchanged",
            "Never reconstruct a file by reading and rewriting it",
            "Defer index reachability",
        ):
            with self.subTest(statement=statement):
                self.assertIn(statement, normalized)

    def test_checker_has_one_shared_source_and_two_skill_symlinks(self):
        shared = ROOT / "shared/scripts/check_spine.py"
        self.assertTrue(shared.is_file())
        for consumer in (
            ROOT / "skills/specspine-map-deep/scripts/check_spine.py",
            ROOT / "skills/specspine-doctor/scripts/check_spine.py",
        ):
            with self.subTest(consumer=consumer):
                self.assertTrue(consumer.is_symlink())
                self.assertEqual(shared.resolve(), consumer.resolve())

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
            "exactly three producers",
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
            "producer",
            "shallowest",
            "orchestration",
        ):
            with self.subTest(leak=leak):
                self.assertNotIn(leak, request)

    def test_scheduler_refills_without_batches_and_cleans_safely(self):
        normalized = " ".join(self.protocol.split())
        self.assertIn("Immediately dispatch ready work into every free slot", normalized)
        self.assertIn("without waiting for siblings or forming pairs or waves", normalized)
        self.assertIn(
            "spawn one ready queued branch before calling `wait`",
            normalized,
        )
        self.assertIn(
            "Never wait for another active owner while that free slot has ready work",
            normalized,
        )
        self.assertIn("find <run-root> -depth -delete", normalized)
        self.assertNotIn("`rm -rf <run-root>`", normalized)

    def test_no_capability_uses_root_only_sequential_protocol(self):
        normalized_root = " ".join(self.deep.split())
        normalized_parallel = " ".join(self.protocol.split())
        for statement in (
            "Read the complete `specspine-map` skill and its required resources directly",
            "do not build an instruction bundle",
            "Perform one shallowest useful Map step at a time directly against the live Spine",
            "After every coherent write",
            "<map-deep-skill-root>/scripts/check_spine.py",
            "Do not create staging, a run root, producer reports, or recovery state",
            "When no actionable question remains",
        ):
            with self.subTest(statement=statement):
                self.assertIn(statement, normalized_root)
        self.assertIn("root capability gate", normalized_parallel)
        self.assertIn("actual start attempts all fail", normalized_parallel)
        self.assertIn("Never infer runtime failure without an attempted start", normalized_parallel)
        self.assertIn("orchestrator, producer, and consumer roles", normalized_parallel)
        self.assertIn("only concurrency changes", normalized_parallel)
        self.assertNotIn(
            "environment exposes no collaboration/subagent tool",
            normalized_parallel,
        )

    def test_normalization_stays_internal_and_doctor_is_a_new_session_handoff(self):
        normalized_root = " ".join(self.deep.split())
        normalized_parallel = " ".join(self.protocol.split())
        self.assertIn("SpecSpine Doctor is outside this run", normalized_parallel)
        self.assertIn("never invoke it from Map-Deep", normalized_parallel)
        self.assertIn("After saturation, perform one sequential navigation pass", normalized_parallel)
        self.assertIn("Add every new document to curated `README.md` navigation", normalized_parallel)
        self.assertIn("Run the full deterministic checker once", normalized_parallel)
        self.assertIn("final report must contain the literal phrase `no useful node`", normalized_parallel)
        self.assertIn("run `$specspine-doctor` in a new session", normalized_parallel)
        self.assertIn("Do not invoke Doctor in the current session", normalized_parallel)
        self.assertIn("recommend `$specspine-doctor` in a new session", normalized_root)
        self.assertIn("Never invoke Doctor during Map-Deep", normalized_root)
        self.assertNotIn("only when the operator explicitly requests", normalized_parallel)
        self.assertLessEqual(len(self.protocol.splitlines()), 310)


if __name__ == "__main__":
    unittest.main()
