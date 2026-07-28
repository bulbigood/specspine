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

    def test_whole_project_completion_selects_exhaustive_mode(self):
        normalized = " ".join(self.entrypoint.split())
        self.assertIn("Use **bounded mode** for an explicitly limited", normalized)
        self.assertIn("Use **exhaustive mode** for completion intent", normalized)
        self.assertIn("cover/document this whole project", normalized)

    def test_bounded_contract_remains_free_of_campaign_state(self):
        self.assertNotIn("campaign.py", self.mapper)
        self.assertNotIn("producer", self.mapper.lower())
        self.assertIn("one shallowest useful mapping step", self.mapper)

    def test_exhaustive_requires_fresh_one_shot_producers(self):
        normalized = " ".join(self.entrypoint.split())
        self.assertIn("one producer per bounded ToDo", normalized)
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
        self.assertIn("Do not inspect or accept `producer-work`", protocol)
        self.assertIn("never trust the producer receipt", protocol)
        self.assertIn("def command_packet", self.campaign)

    def test_exhaustive_requires_medium_tier_producers(self):
        entrypoint = " ".join(self.entrypoint.split())
        protocol = " ".join(self.protocol.split())
        self.assertIn("medium-capability general-purpose agent tier", entrypoint)
        self.assertIn("`agent_type: medium`", self.entrypoint)
        self.assertIn("neither its weak/cheap tier nor its strongest/premium tier", entrypoint)
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

    def test_inventory_is_a_deterministic_completion_gate(self):
        normalized = " ".join(self.protocol.split())
        self.assertIn("mechanically generated repository frontier", normalized)
        self.assertIn(
            "creates one immutable verification ToDo for every remaining unit",
            normalized,
        )
        self.assertIn("Candidate owners do not close work", normalized)
        self.assertIn("inventory_verified", normalized)
        self.assertIn("never packs sibling subtrees", normalized)
        self.assertIn("over 80 files per file", normalized)
        self.assertIn("obligation for every production file", normalized)
        self.assertIn("classifies concrete files before grouping", normalized)
        self.assertIn("def repository_inventory", self.campaign)
        self.assertIn("verification_task_id", self.campaign)
        self.assertNotIn("OWNER_CLASSIFICATIONS", self.campaign)

    def test_turn_boundary_cannot_complete_an_active_campaign(self):
        entrypoint = " ".join(self.entrypoint.split())
        protocol = " ".join(self.protocol.split())
        self.assertIn("A turn boundary", entrypoint)
        self.assertIn("Before any final answer", entrypoint)
        self.assertIn("`may_finish: true`", entrypoint)
        self.assertIn("The durable campaign is the unit of completion", protocol)
        self.assertIn("`may_finish: false` forbids a final answer", protocol)
        self.assertIn("Do not phrase progress as a handoff", protocol)
        self.assertIn("The operator must not have to restart", protocol)
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
        self.assertIn("Give each producer only this minimal launch command", protocol)
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
        self.assertIn("todo --limit <n>", protocol)
        self.assertIn("create a unique new run", selection)
        self.assertNotIn("--adopt-producer-contract", selection)
        self.assertIn("PRODUCER_CONTRACT_VERSION", self.campaign)
        self.assertIn("require_current_producer_contract", self.campaign)

    def test_exhaustive_dispatch_uses_strict_wave_barriers(self):
        entrypoint = " ".join(self.entrypoint.split())
        protocol = " ".join(self.protocol.split())
        self.assertIn("Dispatch strict waves of at most five producers", entrypoint)
        self.assertIn(
            "smallest of ready ToDo, available producer slots, and five",
            protocol,
        )
        self.assertIn("emit all spawn calls back-to-back", protocol)
        self.assertIn("no reasoning, status checks, assignments, waits, or other tools", protocol)
        self.assertIn("harvest every available atomic handoff", protocol)
        self.assertIn("must not mutate the ledger or live Spine", protocol)
        self.assertIn("predeclared deadline", protocol)
        self.assertIn("never invent a timeout after launch", protocol)
        self.assertIn("after every wave member is completed, failed, or cancelled", protocol)
        self.assertIn("campaign.py harvest-wave", protocol)
        self.assertIn("campaign.py accept-wave", protocol)
        self.assertIn("never construct or parse shell-delimited task records", protocol)
        self.assertIn("without refill", protocol)
        self.assertIn("batch acceptance", protocol)
        self.assertNotIn("fill every available producer slot", protocol)

    def test_producers_cannot_write_shared_navigation(self):
        normalized = " ".join(self.producer.split())
        self.assertIn(
            "edit the live Spine, repository source, tests, README, or campaign state",
            normalized,
        )
        self.assertIn("producer must not publish README.md", self.campaign)

    def test_prompt_files_stay_bounded(self):
        self.assertLessEqual(len(self.entrypoint.splitlines()), 95)
        self.assertLessEqual(len(self.producer.splitlines()), 125)
        self.assertLessEqual(len(self.protocol.splitlines()), 240)
        self.assertLessEqual(len(self.documentation_first.splitlines()), 100)
        self.assertLessEqual(len(self.integration.splitlines()), 150)
        self.assertLessEqual(len(self.selection.splitlines()), 80)


if __name__ == "__main__":
    unittest.main()
