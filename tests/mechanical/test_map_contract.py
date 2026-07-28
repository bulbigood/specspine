import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
MAP = ROOT / "skills/specspine-map"


class MapOperationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def read(relative):
            return (MAP / relative).read_text(encoding="utf-8")

        cls.entrypoint = read("SKILL.md")
        cls.protocol = read("references/orchestration.md")
        cls.method = read("references/mapping-method.md")
        cls.discovery = read("references/discovery-task.md")
        cls.curator = read("references/frontier-curation.md")
        cls.synthesis = read("references/topic-synthesis.md")
        cls.producer = read("references/producer-task.md")
        cls.integration = read("references/integration-pass.md")
        cls.campaign = read("scripts/campaign.py")

    @staticmethod
    def compact(value):
        return " ".join(value.split())

    def test_entrypoint_defines_one_pipeline_and_two_axes(self):
        text = self.compact(self.entrypoint)
        self.assertIn(
            "scope → discovery → synthesis → production → integration → verification",
            text,
        )
        self.assertIn("scope.kind: semantic", text)
        self.assertIn("completion.kind: increment", text)
        self.assertIn("Repository increment supports only `survey`", text)
        self.assertIn("increment_verified", text)
        self.assertIn("scope_verified", text)

    def test_authority_is_split_without_duplicate_coverage_claims(self):
        text = self.compact(self.entrypoint)
        self.assertIn("Discovery finds evidence", text)
        self.assertIn("synthesis alone defines semantic topics", text)
        self.assertIn("producers verify one topic", text)
        self.assertIn("root alone chooses canonical ownership", text)
        self.assertIn("inventory pages, paths, and filenames never define", text)

    def test_operation_is_durable_and_atomic(self):
        entrypoint = self.compact(self.entrypoint)
        protocol = self.compact(self.protocol)
        self.assertIn("campaign.py next-action", entrypoint)
        self.assertIn("`may_finish: false`", entrypoint)
        self.assertIn("`may_pause: true`", entrypoint)
        self.assertIn(
            "publishes the workspace plus ledger transition atomically",
            protocol,
        )
        self.assertIn("continue_in_same_turn_no_final_response", self.campaign)
        self.assertIn("rollback_integration_publication", self.campaign)

    def test_orchestration_contains_only_the_live_lifecycle(self):
        text = self.compact(self.protocol)
        for command in (
            "discover",
            "resume-session",
            "init",
            "seed-from-spine",
            "discovery-start",
            "discovery-packets",
            "discovery-collect",
            "discovery-reopen",
            "source-pass",
            "ready",
            "packet",
            "assign",
            "harvest-wave",
            "accept-wave",
            "prepare-integration",
            "integration-pass",
            "next-action",
            "finalize_run.py",
        ):
            self.assertIn(command, text)

    def test_discovery_and_synthesis_close_the_selected_frontier(self):
        protocol = self.compact(self.protocol)
        discovery = self.compact(self.discovery)
        curator = self.compact(self.curator)
        synthesis = self.compact(self.synthesis)
        self.assertIn("Every seed file", discovery)
        self.assertIn("Disposition every proposal exactly once", curator)
        self.assertIn("Increment", protocol)
        self.assertIn("Exhaustive", protocol)
        self.assertIn("process every semantic topic one at a time", synthesis)
        self.assertIn("semantic discovery/extraction workflow", synthesis)
        self.assertIn("Only `topics` becomes the producer", synthesis)
        self.assertIn("`open_leads`", synthesis)
        self.assertIn("`deferred_leads`", synthesis)

    def test_mapping_method_prefers_responsibility_over_source_shape(self):
        text = self.compact(self.method)
        self.assertIn("independently evolving responsibilities", text)
        self.assertIn("generic layers, utilities, individual classes/endpoints", text)
        self.assertIn("A path match, navigation entry, or broad neighboring owner is not coverage", text)
        self.assertIn("repository evidence cannot answer what the system should guarantee", text)

    def test_producer_is_one_shot_private_and_checked(self):
        producer = self.compact(self.producer)
        protocol = self.compact(self.protocol)
        self.assertIn("exactly one bounded ToDo", producer)
        self.assertIn("complete producer instruction set", producer)
        self.assertIn("atomically renames the entire work package", producer)
        self.assertIn("Root independently repeats all acceptance checks", producer)
        self.assertIn("Wait for the whole wave without refill", protocol)
        self.assertIn("one-shot producers", self.entrypoint)

    def test_integration_owns_canonical_publication_and_derived_todo(self):
        text = self.compact(self.integration)
        self.assertIn("Confirm or correct ownership", text)
        self.assertIn("Every suggestion emitted", text)
        self.assertIn("Increment completion forbids `queued`", text)
        self.assertIn("changed_documents", text)
        self.assertIn("integration-pass", text)
        self.assertIn("add_tasks(", self.campaign)

    def test_campaign_exposes_only_the_operation_lifecycle(self):
        commands = set(re.findall(r'add_parser\("([^"]+)"\)', self.campaign))
        self.assertEqual(
            {
                "init",
                "discover",
                "resume-session",
                "seed-from-spine",
                "discovery-start",
                "discovery-packets",
                "discovery-reopen",
                "discovery-collect",
                "source-pass",
                "ready",
                "packet",
                "assign",
                "release",
                "harvest-wave",
                "accept-wave",
                "prepare-integration",
                "integration-pass",
                "next-action",
            },
            commands,
        )
        self.assertNotIn("OWNER_CLASSIFICATIONS", self.campaign)
        self.assertNotIn("quality_gate", self.campaign)
        self.assertNotIn("locally_saturated", self.campaign)

    def test_prompt_files_stay_small(self):
        limits = {
            "entrypoint": (self.entrypoint, 90),
            "protocol": (self.protocol, 220),
            "method": (self.method, 110),
            "discovery": (self.discovery, 90),
            "curator": (self.curator, 80),
            "synthesis": (self.synthesis, 100),
            "producer": (self.producer, 135),
            "integration": (self.integration, 175),
        }
        for name, (value, maximum) in limits.items():
            with self.subTest(name=name):
                self.assertLessEqual(len(value.splitlines()), maximum)


if __name__ == "__main__":
    unittest.main()
