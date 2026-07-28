import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]


class MapExhaustiveContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entrypoint = (ROOT / "skills/specspine-map/SKILL.md").read_text(
            encoding="utf-8"
        )
        cls.mapper = (
            ROOT / "skills/specspine-map/references/bounded-mode.md"
        ).read_text(encoding="utf-8")
        cls.producer = (
            ROOT / "skills/specspine-map/references/producer-task.md"
        ).read_text(encoding="utf-8")
        cls.discovery = (
            ROOT / "skills/specspine-map/references/discovery-task.md"
        ).read_text(encoding="utf-8")
        cls.curator = (
            ROOT / "skills/specspine-map/references/frontier-curation.md"
        ).read_text(encoding="utf-8")
        cls.synthesis = (
            ROOT / "skills/specspine-map/references/topic-synthesis.md"
        ).read_text(encoding="utf-8")
        cls.protocol = (
            ROOT / "skills/specspine-map/references/orchestration.md"
        ).read_text(encoding="utf-8")
        cls.documentation_first = (
            ROOT
            / "skills/specspine-map/references/documentation-first-seeding.md"
        ).read_text(encoding="utf-8")
        cls.integration = (
            ROOT / "skills/specspine-map/references/integration-pass.md"
        ).read_text(encoding="utf-8")
        cls.selection = (
            ROOT / "skills/specspine-map/references/campaign-selection.md"
        ).read_text(encoding="utf-8")
        cls.campaign = (
            ROOT / "skills/specspine-map/scripts/campaign.py"
        ).read_text(encoding="utf-8")

    def test_completion_selects_one_exhaustive_campaign_for_any_scope(self):
        normalized = " ".join(self.entrypoint.split())
        self.assertIn("Use **bounded-step mode** for an explicitly limited", normalized)
        self.assertIn("Use an **exhaustive campaign** for completion intent", normalized)
        self.assertIn("fully document Kafka and related services", normalized)
        self.assertIn(
            "whole repository is one exhaustive scope, not a separate campaign type",
            normalized,
        )

    def test_bounded_contract_remains_free_of_campaign_state(self):
        self.assertNotIn("campaign.py", self.mapper)
        self.assertNotIn("producer", self.mapper.lower())
        self.assertIn("one shallowest useful mapping step", self.mapper)

    def test_exhaustive_requires_fresh_one_shot_producers(self):
        normalized = " ".join(self.entrypoint.split())
        self.assertIn(
            "one fresh producer per remaining bounded semantic ToDo",
            normalized,
        )
        self.assertIn("Never reuse a producer", normalized)
        self.assertIn("`fork_turns: none`", self.entrypoint)
        self.assertIn("fresh isolated context", normalized)
        self.assertIn("another agent platform", normalized)
        self.assertIn("report `blocked`", normalized)
        self.assertNotIn("Sequential exhaustive protocol", self.entrypoint)
        self.assertIn("`producer_finalize.py` preflight", normalized)
        self.assertIn("Do not invoke Doctor inside producers", normalized)

    def test_producer_self_checks_before_atomic_handoff(self):
        producer = " ".join(self.producer.split())
        protocol = " ".join(self.protocol.split())
        self.assertIn("Mandatory preflight and handoff", self.producer)
        self.assertIn("atomically renames the entire work package", producer)
        self.assertIn("fix every candidate-caused finding", producer)
        self.assertIn("Root independently repeats all acceptance checks", producer)
        self.assertIn("campaign.py packet", protocol)
        self.assertIn("Never inspect or accept `producer-work`", protocol)
        self.assertIn("Root reruns every acceptance check", protocol)
        self.assertIn("def command_packet", self.campaign)

    def test_exhaustive_requires_medium_tier_producers(self):
        entrypoint = " ".join(self.entrypoint.split())
        protocol = " ".join(self.protocol.split())
        self.assertIn("medium-capability general-purpose tier", entrypoint)
        self.assertIn("`agent_type: medium`", self.entrypoint)
        self.assertIn("neither weak/cheap nor strongest/premium", entrypoint)
        self.assertIn("Never fall back to a weak or strongest tier", protocol)

    def test_producer_has_one_checkpoint_and_no_coverage_authority(self):
        normalized = " ".join(self.producer.split())
        self.assertIn("exactly one bounded ToDo", normalized)
        self.assertIn("write one checkpoint, and terminate", normalized)
        self.assertIn(
            "broad neighboring owner is not proof",
            normalized,
        )
        self.assertIn('"outcome": "covered"', self.producer)
        self.assertIn('"outcome": "draft"', self.producer)
        self.assertIn('"outcome": "retry"', self.producer)
        self.assertIn('"outcome": "supporting"', self.producer)
        self.assertIn('"outcome": "answered"', self.producer)
        self.assertIn('"unresolved"` with', normalized)
        self.assertIn("every evidence stratum", normalized)
        self.assertIn("directions` are plain questions", normalized)
        self.assertIn("evidence baseline and at least one v3 semantic", normalized)
        self.assertIn("all `OBS-*`", normalized)

    def test_discovery_scope_is_the_completion_gate(self):
        normalized = " ".join(self.protocol.split())
        self.assertIn("closes one operator-defined semantic scope", normalized)
        self.assertIn(
            "creates one immutable producer ToDo per uncovered semantic topic",
            normalized,
        )
        self.assertIn("Candidate owners never close work", normalized)
        self.assertIn("scope_verified", normalized)
        self.assertIn("flat production-file inventory", normalized)
        self.assertIn("only a repository-scope accelerator", normalized)
        self.assertIn("discovery-collect", normalized)
        self.assertIn("discovery-reopen", normalized)
        self.assertIn("topic-plan.json", normalized)
        discovery = " ".join(self.discovery.split())
        self.assertIn("one semantic expansion step", discovery)
        self.assertIn("Read `<spine-root>/README.md`", self.discovery)
        self.assertIn("Every seed file", discovery)
        curator = " ".join(self.curator.split())
        self.assertIn("compare every child-lead proposal", curator)
        self.assertIn("Disposition every proposal exactly once", curator)
        synthesis = " ".join(self.synthesis.split())
        self.assertIn("process every semantic topic one at a time", synthesis)
        self.assertIn("existing `<spine-root>`", synthesis)
        self.assertIn("semantic discovery/extraction workflow", synthesis)
        self.assertIn("Only `topics` becomes the producer", synthesis)
        self.assertIn("`open_leads`", self.synthesis)
        self.assertIn("def repository_inventory", self.campaign)
        self.assertIn("def command_discovery_start", self.campaign)
        self.assertIn("def command_discovery_collect", self.campaign)
        self.assertIn("verification_task_id", self.campaign)
        self.assertNotIn("OWNER_CLASSIFICATIONS", self.campaign)

    def test_turn_boundary_cannot_complete_an_active_campaign(self):
        entrypoint = " ".join(self.entrypoint.split())
        protocol = " ".join(self.protocol.split())
        self.assertIn("before any final answer", entrypoint)
        self.assertIn("`may_finish: true`", entrypoint)
        self.assertIn("`may_pause: true`", entrypoint)
        self.assertIn("The durable campaign is the unit of completion", protocol)
        self.assertIn("`may_finish: false` forbids a final answer", protocol)
        self.assertIn("`may_pause: true`", protocol)
        self.assertIn("continue_in_same_turn_no_final_response", self.campaign)
        self.assertIn("def command_next_action", self.campaign)
        self.assertIn('"next-action": command_next_action', self.campaign)

    def test_new_session_requires_operator_campaign_choice(self):
        entrypoint = " ".join(self.entrypoint.split())
        selection = " ".join(self.selection.split())
        self.assertIn("campaign-selection.md", entrypoint)
        self.assertIn("Before `init` in a new session", selection)
        self.assertIn("Always require this choice", selection)
        self.assertIn("activity is at most 24 hours old", selection)
        self.assertIn("campaign.py discover", selection)
        self.assertIn("campaign.py resume-session", selection)
        self.assertIn("Never silently choose the newest directory", selection)
        self.assertIn("def command_discover", self.campaign)
        self.assertIn("def command_resume_session", self.campaign)

    def test_campaign_has_atomic_publication_and_no_self_quality_gate(self):
        self.assertIn("fcntl.flock", self.campaign)
        self.assertIn("os.replace(temporary_path, path)", self.campaign)
        self.assertIn("def rollback_integration_publication", self.campaign)
        self.assertIn("def command_prepare_integration", self.campaign)
        self.assertIn("checkpoint_digest", self.campaign)
        self.assertIn("DEFERRED_CHECKER_CODES", self.campaign)
        self.assertNotIn("quality_gate", self.campaign)
        self.assertNotIn("locally_saturated", self.campaign)
        self.assertNotIn("producer_affinity", self.campaign)
        self.assertIn("one producer may run only one task", self.campaign)
        self.assertNotIn('"not_architectural"', self.campaign)

    def test_documentation_seed_is_mechanical(self):
        normalized = " ".join(self.documentation_first.split())
        self.assertIn("complete Markdown inventory mechanically", normalized)
        self.assertIn("seed-from-spine", normalized)
        self.assertIn("adds no ToDo and grants no coverage", normalized)
        self.assertIn("document_hashes", self.campaign)

    def test_root_integration_derives_and_persists_new_todo(self):
        normalized = " ".join(self.integration.split())
        self.assertIn("Inspect every producer direction", normalized)
        self.assertIn("Append every accepted refinement to persistent ToDo", normalized)
        self.assertIn("Every suggestion emitted", normalized)
        self.assertIn("queued`, with a matching `todo`", normalized)
        self.assertIn("`preserved`", normalized)
        self.assertIn("exactly matches visible `anchor.question`", normalized)
        self.assertIn("integration-pass", normalized)
        self.assertIn("add_tasks(", self.campaign)

    def test_root_reports_only_after_atomic_integration_succeeds(self):
        integration = " ".join(self.integration.split())
        protocol = " ".join(self.protocol.split())
        self.assertIn(
            "After the whole integration transaction and its checks succeed",
            integration,
        )
        self.assertIn("immediate commentary update", integration)
        self.assertIn("Spine-relative Markdown path", integration)
        self.assertIn(
            "label it `created`, `changed`, or `deleted`",
            integration,
        )
        self.assertIn("Never announce a write before publication succeeds", integration)
        self.assertIn(
            "Repeat cumulative document history",
            protocol,
        )
        self.assertIn("`changed_documents` is the exact workspace delta", self.integration)
        self.assertIn("rejects missing, extra, or mislabeled paths", integration)
        self.assertIn("returns the published delta", integration)

    def test_producer_uses_minimal_contract_without_other_skill_context(self):
        producer = " ".join(self.producer.split())
        protocol = " ".join(self.protocol.split())
        self.assertIn("complete producer instruction set", producer)
        self.assertIn("do not load the Map `SKILL.md`", producer)
        self.assertIn("Do not message root or any other agent", producer)
        self.assertIn("Give each fresh producer only", protocol)
        self.assertIn(
            "references/producer-task.md completely; it is your sole Map contract",
            protocol,
        )
        self.assertIn("Do not read SKILL.md or any other Map reference", protocol)
        self.assertIn("targeted `rg` and narrow excerpts", producer)
        self.assertIn("at most 10,000 output tokens per call", producer)

    def test_dispatch_and_resume_keep_context_bounded_and_versioned(self):
        protocol = " ".join(self.protocol.split())
        selection = " ".join(self.selection.split())
        self.assertIn("ready <campaign> --limit <wave-size>", protocol)
        self.assertIn("create a unique new run", selection)
        self.assertNotIn("--adopt-producer-contract", selection)
        self.assertIn("PRODUCER_CONTRACT_VERSION", self.campaign)
        self.assertIn("require_current_producer_contract", self.campaign)

    def test_exhaustive_dispatch_uses_strict_wave_barriers(self):
        entrypoint = " ".join(self.entrypoint.split())
        protocol = " ".join(self.protocol.split())
        self.assertIn("Dispatch strict waves of at most five producers", entrypoint)
        self.assertIn(
            "Precompute the entire wave and emit spawn calls back-to-back",
            protocol,
        )
        self.assertIn("After every wave member is completed, failed, or cancelled", protocol)
        self.assertIn("campaign.py harvest-wave", protocol)
        self.assertIn("campaign.py accept-wave", protocol)
        self.assertIn("without refill", protocol)
        self.assertNotIn("fill every available producer slot", protocol)

    def test_producers_cannot_write_shared_navigation(self):
        normalized = " ".join(self.producer.split())
        self.assertIn(
            "edit the live Spine, repository source, tests, README, or campaign state",
            normalized,
        )
        self.assertIn("producer must not publish README.md", self.campaign)

    def test_prompt_files_stay_bounded(self):
        self.assertLessEqual(len(self.entrypoint.splitlines()), 110)
        self.assertLessEqual(len(self.producer.splitlines()), 135)
        self.assertLessEqual(len(self.discovery.splitlines()), 90)
        self.assertLessEqual(len(self.curator.splitlines()), 80)
        self.assertLessEqual(len(self.synthesis.splitlines()), 100)
        self.assertLessEqual(len(self.protocol.splitlines()), 315)
        self.assertLessEqual(len(self.documentation_first.splitlines()), 100)
        self.assertLessEqual(len(self.integration.splitlines()), 175)
        self.assertLessEqual(len(self.selection.splitlines()), 80)


if __name__ == "__main__":
    unittest.main()
