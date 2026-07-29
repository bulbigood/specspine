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
        cls.planner = read("references/discovery-planner.md")
        cls.discovery = read("references/discovery-task.md")
        cls.curator = read("references/frontier-curation.md")
        cls.synthesis = read("references/topic-synthesis.md")
        cls.coverage = read("references/repository-coverage.md")
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
        self.assertIn("paths, and filenames never define", text)
        self.assertIn("Root does not inspect production code", text)

    def test_map_retains_only_material_repository_delta(self):
        entrypoint = self.compact(self.entrypoint)
        method = self.compact(self.method)
        producer = self.compact(self.producer)
        integration = self.compact(self.integration)
        self.assertIn("exception layer, not a code mirror", entrypoint)
        self.assertIn("`covered-by-intent`", method)
        self.assertIn("omit the duplicate fact", method)
        self.assertIn("never rewrite matching code behavior", producer)
        self.assertIn("inspection", integration)
        self.assertIn("never claims conformance", integration)
        self.assertIn("never hide canonical content in `<details>`", producer)

    def test_operation_is_durable_and_atomic(self):
        protocol = self.compact(self.protocol)
        self.assertIn("campaign.py next-action", protocol)
        self.assertIn("`may_finish: false`", protocol)
        self.assertIn("`may_pause: true`", protocol)
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
            "status",
            "init",
            "seed-from-spine",
            "discovery-start",
            "discovery-defer",
            "discovery-packets",
            "discovery-validate",
            "discovery_finalize.py",
            "discovery-collect",
            "discovery-reopen",
            "coverage-reopen",
            "synthesis.py prepare",
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
        self.assertIn("missing data/control-flow edges", synthesis)
        self.assertIn("every `source_topic`", synthesis)
        self.assertIn("source_topic_ids", synthesis)
        self.assertIn("source_topics(corpus", self.synthesis_script)
        self.assertIn("publish_validated_plan", self.synthesis_script)
        self.assertIn("zero-existing-coverage", self.synthesis_script)
        self.assertIn("fresh strong-tier synthesizer", protocol)
        self.assertIn("do not split either pass across isolated workers", protocol)
        self.assertIn("do not block production", protocol)
        self.assertIn("may remain isolated only after this explicit audit", synthesis)

    def test_scout_parallelism_is_adaptive_and_wave_checked(self):
        protocol = self.compact(self.protocol)
        self.assertIn("smaller of ten and the runtime's available subagent slots", protocol)
        self.assertIn("isolated semantic planner", protocol)
        self.assertIn("same pipeline; never partition it into mandatory file pages", protocol)
        self.assertIn("Dispatch every initial packet", protocol)
        self.assertIn("Never start frontier curation", protocol)
        self.assertIn("--initial-plan", protocol)
        self.assertIn("at most 40 seed files", protocol)
        self.assertIn("reserve one slot", protocol)
        self.assertIn("fresh weak-tier scouts", protocol)
        self.assertIn("fresh weak-tier curator", protocol)
        self.assertIn("discovery_finalize.py", protocol)
        self.assertIn("discovery-validate", protocol)
        self.assertIn("exact result path", protocol)
        self.assertIn("Do not write topic IDs, search-query logs", self.discovery)
        self.assertIn("Never write or edit the result directly", self.discovery)
        self.assertIn("MAX_PRODUCER_WAVE = 10", self.campaign)
        self.assertIn("MAX_SCOUT_SEED_FILES = 40", self.campaign)
        self.assertIn("MAX_INITIAL_SCOUTS = 10", self.campaign)
        self.assertIn("MAX_UNIT_FILES = 80", self.campaign)

    def test_repository_exhaustive_has_a_topology_backstop(self):
        protocol = self.compact(self.protocol)
        coverage = self.compact(self.coverage)
        self.assertIn("whole-repository exhaustive work only", protocol)
        self.assertIn("coverage.py prepare", protocol)
        self.assertNotIn("coverage-record", protocol)
        self.assertIn("coverage-reopen", protocol)
        self.assertIn("missing architectural roots", coverage)
        self.assertIn("Do not require every directory or production file", coverage)

    def test_mapping_method_prefers_responsibility_over_source_shape(self):
        text = self.compact(self.method)
        self.assertIn("independently evolving responsibilities", text)
        self.assertIn("generic layers, utilities, individual classes/endpoints", text)
        self.assertIn("A path match, navigation entry, or broad neighboring owner is not coverage", text)
        self.assertIn("repository evidence cannot answer what the system should guarantee", text)

    def test_synthesis_uses_directional_relationship_semantics(self):
        synthesis = self.compact(self.synthesis)
        self.assertIn("`publishes` makes an event, intent, or result available", synthesis)
        self.assertIn("`writes-to` directly mutates", synthesis)
        self.assertIn("`migrates-from` points from the successor", synthesis)
        self.assertIn("Every reason names the concrete event", synthesis)
        self.assertIn("Reciprocal edges require two distinct directed interactions", synthesis)
        self.assertIn("omit a doubtful edge or preserve a question", synthesis)

    def test_producer_is_one_shot_private_and_checked(self):
        producer = self.compact(self.producer)
        protocol = self.compact(self.protocol)
        self.assertIn("exactly one bounded ToDo", producer)
        self.assertIn("complete producer instruction set", producer)
        self.assertIn("atomically renames the entire work package", producer)
        self.assertIn("Root repeats mechanical acceptance checks", producer)
        self.assertIn("Wait for the whole wave without refill", protocol)
        self.assertIn("fresh medium-tier producers", protocol)
        self.assertIn("Use `concept` only for shared vocabulary", producer)
        self.assertIn("never merge concerns into custom headings", producer)
        self.assertIn("make one targeted facet pass", producer)
        self.assertIn("For `completion.intent: deepen`", producer)
        self.assertIn("only Evolve may perform the reorganization", producer)
        self.assertIn("related_existing_owners", producer)
        self.assertIn("current_owner", self.campaign)

    def test_receipts_preserve_atomic_handoffs_before_redispatch(self):
        protocol = self.compact(self.protocol)
        self.assertIn("valid `_receipt.json`", protocol)
        self.assertIn("Repair only `rejected_tasks`", protocol)
        self.assertIn("Never read or accept an unfinished producer work directory", protocol)
        self.assertIn("<workspace>/.specspine/map", protocol)
        self.assertIn("Never place Map state elsewhere", protocol)
        self.assertIn(
            "ledger file `<run>/campaign.json`, never the run directory",
            protocol,
        )
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
                "status",
                "seed-from-spine",
                "bootstrap-spine",
                "discovery-start",
                "discovery-defer",
                "discovery-packets",
                "discovery-reopen",
                "coverage-reopen",
                "discovery-validate",
                "discovery-collect",
                "source-pass",
                "ready",
                "packet",
                "assign",
                "release",
                "retry-blocked",
                "settle-wave",
                "prepare-integration",
                "integration-pass",
                "assemble-integration",
                "next-action",
            },
            commands,
        )
        self.assertNotIn("OWNER_CLASSIFICATIONS", self.campaign)
        self.assertNotIn("quality_gate", self.campaign)
        self.assertNotIn("locally_saturated", self.campaign)

    def test_prompt_files_stay_small(self):
        limits = {
            "entrypoint": (self.entrypoint, 118),
            "protocol": (self.protocol, 390),
            "method": (self.method, 110),
            "planner": (self.planner, 55),
            "discovery": (self.discovery, 105),
            "curator": (self.curator, 85),
            "synthesis": (self.synthesis, 116),
            "coverage": (self.coverage, 40),
            "producer": (self.producer, 165),
            "integration": (self.integration, 175),
        }
        for name, (value, maximum) in limits.items():
            with self.subTest(name=name):
                self.assertLessEqual(len(value.splitlines()), maximum)


if __name__ == "__main__":
    unittest.main()
