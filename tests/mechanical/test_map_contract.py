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
        cls.reduction = read("references/topic-reduction.md")
        cls.producer = read("references/producer-task.md")
        cls.integration = read("references/integration-pass.md")
        cls.campaign = read("scripts/campaign.py")
        cls.synthesis_script = read("scripts/synthesis.py")

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
        self.assertIn("synthesis defines topics, canonical documents", text)
        self.assertIn("producers verify one topic", text)
        self.assertIn("deterministic assembly publishes clean results", text)
        self.assertIn("inventory pages, paths, and filenames never define", text)

    def test_operation_is_durable_and_atomic(self):
        entrypoint = self.compact(self.entrypoint)
        protocol = self.compact(self.protocol)
        self.assertIn("campaign.py next-action", entrypoint)
        self.assertIn("`may_finish: false`", entrypoint)
        self.assertIn("`may_pause: true`", entrypoint)
        self.assertIn(
            "checks and publishes atomically",
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
            "discovery-validate",
            "discovery_finalize.py",
            "discovery-collect",
            "discovery-reopen",
            "synthesis.py prepare",
            "synthesis.py merge",
            "synthesis.py materialize",
            "source-pass",
            "ready",
            "packet",
            "assign",
            "settle-wave",
            "prepare-integration",
            "integration-pass",
            "next-action",
            "finalize_run.py",
        ):
            self.assertIn(command, text)

    def test_discovery_and_synthesis_close_the_selected_frontier(self):
        entrypoint = self.compact(self.entrypoint)
        protocol = self.compact(self.protocol)
        discovery = self.compact(self.discovery)
        curator = self.compact(self.curator)
        synthesis = self.compact(self.synthesis)
        self.assertIn("Every packet seed file", discovery)
        self.assertIn("private queue", discovery)
        self.assertIn("until it is empty", discovery)
        self.assertIn("Use `unresolved_leads` only as fallback", discovery)
        self.assertIn("fallback_kind", discovery)
        self.assertIn("targeted fallback", self.compact(self.method))
        self.assertIn("Never create mandatory breadth-first", protocol)
        self.assertIn("Disposition every proposal exactly once", curator)
        self.assertIn("Increment", protocol)
        self.assertIn("Exhaustive", protocol)
        self.assertIn("classify every canonical topic", synthesis)
        self.assertIn("SpecSpine semantic extraction", synthesis)
        self.assertIn("`open_leads`", synthesis)
        self.assertIn("`deferred_leads`", synthesis)
        self.assertIn("Disposition every input `source_id` exactly once", self.reduction)
        self.assertIn("`passthrough`", self.reduction)
        self.assertIn("`merged`", self.reduction)
        self.assertIn("source_topic_ids", synthesis)
        self.assertIn("merged_source_topics", synthesis)
        self.assertIn("source_topics(corpus", self.synthesis_script)
        self.assertIn("publish_validated_plan", self.synthesis_script)
        self.assertIn("zero-existing-coverage", self.synthesis_script)
        self.assertIn("fresh strong-tier synthesizer", protocol)
        self.assertIn("strong-tier global synthesizer", entrypoint)
        self.assertIn("medium-tier topic reducers", protocol)
        self.assertIn("do not block production", protocol)
        self.assertIn("may remain temporarily isolated", synthesis)

    def test_scout_parallelism_is_adaptive_and_wave_checked(self):
        protocol = self.compact(self.protocol)
        entrypoint = self.compact(self.entrypoint)
        self.assertIn("smaller of ten and the runtime's available subagent slots", protocol)
        self.assertIn("Choose one to ten independent semantic search boundaries", protocol)
        self.assertIn("Dispatch every initial packet", protocol)
        self.assertIn("Never start frontier curation", protocol)
        self.assertIn("--initial-plan", protocol)
        self.assertIn("default page size of 40 seed files", protocol)
        self.assertIn("reserve one slot", protocol)
        self.assertIn("fresh weak-tier scouts", protocol)
        self.assertIn("discovery_finalize.py", protocol)
        self.assertIn("discovery-validate", protocol)
        self.assertIn("exact result path", protocol)
        self.assertIn("Do not write topic IDs, search-query logs", self.discovery)
        self.assertIn("Never write or edit the result directly", self.discovery)
        self.assertIn("discovery_finalize.py", self.entrypoint)
        self.assertIn("weak-tier scouts", entrypoint)
        self.assertIn("at most ten", entrypoint)
        self.assertIn("Producer waves contain at most ten", entrypoint)
        self.assertIn("MAX_PRODUCER_WAVE = 10", self.campaign)
        self.assertIn("MAX_SCOUT_SEED_FILES = 40", self.campaign)
        self.assertIn("MAX_INITIAL_SCOUTS = 10", self.campaign)
        self.assertIn("MAX_UNIT_FILES = 80", self.campaign)

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
        self.assertIn("Root repeats mechanical acceptance checks", producer)
        self.assertIn("Wait for the whole wave without refill", protocol)
        self.assertIn("fresh strong-tier producers", protocol)
        self.assertIn("one-shot producers", self.entrypoint)
        self.assertIn("strong-tier one-shot producers", self.entrypoint)

    def test_resume_recovers_atomic_handoffs_before_redispatch(self):
        protocol = self.compact(self.protocol)
        entrypoint = self.compact(self.entrypoint)
        self.assertIn("Resume preserves every `assigned` task", protocol)
        self.assertIn("Repair only `rejected_tasks`", protocol)
        self.assertIn("Never read or accept an unfinished producer work directory", protocol)
        self.assertIn("harvest retained assigned tasks", entrypoint)
        self.assertIn("never restart accepted or harvestable work", entrypoint)
        self.assertIn("<workspace>/.specspine/map", protocol)
        self.assertIn("Never place Map state elsewhere", protocol)
        self.assertIn('".specspine"', self.campaign)
        self.assertIn("ensure_map_runtime_root", self.campaign)

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
                "bootstrap-spine",
                "discovery-start",
                "discovery-packets",
                "discovery-reopen",
                "discovery-validate",
                "discovery-collect",
                "source-pass",
                "ready",
                "packet",
                "assign",
                "release",
                "settle-wave",
                "prepare-integration",
                "integration-pass",
                "assemble-integration",
                "next-action",
                "recover",
            },
            commands,
        )
        self.assertNotIn("OWNER_CLASSIFICATIONS", self.campaign)
        self.assertNotIn("quality_gate", self.campaign)
        self.assertNotIn("locally_saturated", self.campaign)

    def test_prompt_files_stay_small(self):
        limits = {
            "entrypoint": (self.entrypoint, 115),
            "protocol": (self.protocol, 340),
            "method": (self.method, 110),
            "discovery": (self.discovery, 105),
            "curator": (self.curator, 85),
            "synthesis": (self.synthesis, 100),
            "reduction": (self.reduction, 50),
            "producer": (self.producer, 135),
            "integration": (self.integration, 175),
        }
        for name, (value, maximum) in limits.items():
            with self.subTest(name=name):
                self.assertLessEqual(len(value.splitlines()), maximum)


if __name__ == "__main__":
    unittest.main()
