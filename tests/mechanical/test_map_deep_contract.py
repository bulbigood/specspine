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

    def test_map_refuses_terminal_output_and_deep_uses_that_as_saturation(self):
        normalized_map = " ".join(self.mapper.split())
        normalized = " ".join((self.deep + self.protocol).split())
        self.assertIn("Create or change no document when", normalized_map)
        self.assertIn("Report that terminal reason explicitly", normalized_map)
        self.assertIn("Never manufacture output to keep the mapping branch alive", normalized)
        self.assertIn("Continue each branch after a successful document", normalized)
        self.assertIn("one terminal depth probe", normalized)
        self.assertIn("Close the branch only when this probe creates no document", normalized)
        self.assertIn("Do not repeat a terminal probe after that refusal", normalized)
        self.assertIn("no actionable question remains", normalized)
        self.assertIn("Do not stop at a predetermined number of documents", normalized)

    def test_producers_receive_complete_map_instructions_once(self):
        normalized = " ".join((self.deep + self.protocol).split())
        self.assertIn("bundle_skill.py --print", self.deep)
        self.assertIn("every UTF-8 file under Map `references/`", normalized)
        self.assertIn("Build the complete Map instruction bundle once", self.protocol)
        self.assertIn("complete-generated-map-instructions", self.protocol)
        self.assertIn("Do not load or invoke any skill", self.protocol)
        self.assertIn("Report a follow-up only when inspected evidence indicates", normalized)
        self.assertNotIn("$specspine-map", self.protocol)

    def test_parallel_producers_are_isolated_and_consumer_moves_results(self):
        normalized = " ".join(self.protocol.split())
        for statement in (
            "one private staging root per active producer",
            "Keep source, tests, configuration, the live Spine",
            "without rereading candidate prose",
            "--candidates <private-staging-root> --json",
            "Move every accepted candidate unchanged",
            "Never reconstruct a file by reading and rewriting it",
            "Defer index reachability",
        ):
            with self.subTest(statement=statement):
                self.assertIn(statement, normalized)

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
