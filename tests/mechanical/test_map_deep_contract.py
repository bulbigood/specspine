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
        self.assertIn("report `blocked`", normalized)
        self.assertNotIn("Sequential exhaustive protocol", self.entrypoint)

    def test_producer_has_one_checkpoint_and_no_coverage_authority(self):
        normalized = " ".join(self.producer.split())
        self.assertIn("exactly one bounded ToDo", normalized)
        self.assertIn("write one checkpoint, and terminate", normalized)
        self.assertIn(
            "title or broad neighboring owner is not proof",
            normalized,
        )
        self.assertIn('"outcome": "covered"', self.producer)
        self.assertIn('"outcome": "draft"', self.producer)
        self.assertIn('"outcome": "retry"', self.producer)
        self.assertIn("directions` are plain questions", normalized)

    def test_inventory_is_a_deterministic_completion_gate(self):
        normalized = " ".join(self.protocol.split())
        self.assertIn("mechanically generated repository frontier", normalized)
        self.assertIn(
            "creates one immutable verification ToDo for every remaining unit",
            normalized,
        )
        self.assertIn("Candidate owners do not close work", normalized)
        self.assertIn("inventory_verified", normalized)
        self.assertIn("at most 200 concrete files", normalized)
        self.assertIn("def repository_inventory", self.campaign)
        self.assertIn("verification_task_id", self.campaign)
        self.assertNotIn("OWNER_CLASSIFICATIONS", self.campaign)

    def test_campaign_has_atomic_publication_and_no_self_quality_gate(self):
        self.assertIn("fcntl.flock", self.campaign)
        self.assertIn("os.replace(temporary_path, path)", self.campaign)
        self.assertIn("def rollback_publication", self.campaign)
        self.assertIn("checkpoint_digest", self.campaign)
        self.assertIn("DEFERRED_CHECKER_CODES", self.campaign)
        self.assertNotIn("quality_gate", self.campaign)
        self.assertNotIn("locally_saturated", self.campaign)
        self.assertNotIn("producer_affinity", self.campaign)
        self.assertIn("one producer may run only one task", self.campaign)
        self.assertNotIn('"not_architectural"', self.campaign)

    def test_documentation_seed_creates_bounded_todo(self):
        normalized = " ".join(self.documentation_first.split())
        self.assertIn("Read `README.md` and every live Markdown node", normalized)
        self.assertIn("Anchor every task", normalized)
        self.assertIn("seed-from-spine", normalized)
        self.assertIn("additional documentation-derived ToDo", normalized)
        self.assertIn("cannot classify or remove", normalized)
        self.assertIn("validate_document_inventory", self.campaign)

    def test_root_integration_derives_and_persists_new_todo(self):
        normalized = " ".join(self.integration.split())
        self.assertIn("Inspect every producer-discovered direction", normalized)
        self.assertIn("Append every accepted refinement to persistent ToDo", normalized)
        self.assertIn("Every suggestion emitted", normalized)
        self.assertIn("queued`, with a matching `todo`", normalized)
        self.assertIn("integration-pass", normalized)
        self.assertIn("add_tasks(", self.campaign)

    def test_producers_cannot_write_shared_navigation(self):
        normalized = " ".join(self.producer.split())
        self.assertIn(
            "edit the live Spine, repository source, tests, README, or campaign state",
            normalized,
        )
        self.assertIn("producer must not publish README.md", self.campaign)

    def test_prompt_files_stay_bounded(self):
        self.assertLessEqual(len(self.entrypoint.splitlines()), 90)
        self.assertLessEqual(len(self.producer.splitlines()), 125)
        self.assertLessEqual(len(self.protocol.splitlines()), 240)
        self.assertLessEqual(len(self.documentation_first.splitlines()), 100)
        self.assertLessEqual(len(self.integration.splitlines()), 150)


if __name__ == "__main__":
    unittest.main()
