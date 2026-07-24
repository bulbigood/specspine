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

    def test_map_stays_atomic_and_deep_is_explicit(self):
        self.assertNotIn("references/orchestration.md", self.mapper)
        self.assertNotIn("producer", self.mapper.lower())
        self.assertNotIn("specspine-map-deep", self.mapper)
        self.assertIn("the requested repository scope", self.mapper)
        self.assertIn("references/orchestration.md", self.deep)
        self.assertIn("allow_implicit_invocation: false", self.metadata)

    def test_map_deep_accepts_the_same_user_scope_as_map(self):
        normalized = " ".join((self.deep + self.protocol).split())
        self.assertIn("Accept the same scope as `specspine-map`", normalized)
        self.assertIn("one focused concern, several areas, or the whole repository", normalized)
        self.assertIn("exact user-requested mapping scope", normalized)
        self.assertNotIn("Do not use for a focused survey", self.deep)
        self.assertNotIn("complete large-repository Map run", self.deep)

    def test_discovery_is_adaptive_and_has_no_recovery_protocol(self):
        normalized = " ".join((self.deep + self.protocol).split()).lower()
        self.assertIn("discover repository evidence adaptively", normalized)
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
        self.assertIn("Never manufacture output to keep the branch alive", normalized)
        self.assertIn("until it reports terminal `no useful node`", normalized)
        self.assertIn("do not create a fresh producer merely to probe the same branch", normalized)
        self.assertIn("no actionable branch remains", normalized)
        self.assertIn("Do not stop at a predetermined document count", normalized)

    def test_new_producers_receive_complete_map_instructions_once(self):
        normalized = " ".join((self.deep + self.protocol).split())
        self.assertIn("bundle_skill.py --print", self.deep)
        self.assertIn("every UTF-8 file under Map `references/`", normalized)
        self.assertIn("Build the complete Map instruction bundle once", self.protocol)
        self.assertIn("complete-generated-map-instructions", self.protocol)
        self.assertIn("Do not load or invoke any skill", self.protocol)
        self.assertIn("only in the initial command for each new producer session", normalized)
        self.assertIn("never resend the bundle or immutable shared context", normalized)
        self.assertNotIn("$specspine-map", self.protocol)

    def test_orchestrator_owns_forks_and_producers_keep_branch_affinity(self):
        normalized = " ".join((self.deep + self.protocol).split())
        for statement in (
            "The orchestrator is the sole scheduling authority",
            "The producer may propose child branches but must never create producers",
            "A same-boundary continuation remains with its current producer",
            "never repurpose that session for an unrelated branch",
            "`Current-branch continuation`",
            "`Fork candidates`",
            "Resume a continuing branch through the environment's native follow-up mechanism",
            "complete only when it is locally saturated and all accepted child branches are complete",
        ):
            with self.subTest(statement=statement):
                self.assertIn(statement, normalized)

    def test_parallel_producers_are_isolated_and_consumer_moves_results(self):
        normalized = " ".join(self.protocol.split())
        for statement in (
            "one private staging root per active producer session",
            "Every candidate must contain a `## Responsibility` section",
            "Resolve one current evidence baseline once",
            "never use a Markdown link for evidence",
            "never derive Decisions or Constraints without accepted intent",
            "Keep source, tests, configuration, the live Spine",
            "Do not reread candidate prose",
            "--candidates <private-staging-root> --json",
            "Move every accepted candidate unchanged",
            "Never reconstruct a file by reading and rewriting it",
            "Defer index reachability",
        ):
            with self.subTest(statement=statement):
                self.assertIn(statement, normalized)

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
