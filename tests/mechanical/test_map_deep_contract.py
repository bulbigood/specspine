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

    def test_mode_dispatch_treats_whole_project_completion_as_exhaustive(self):
        normalized = " ".join(self.entrypoint.split())
        self.assertIn("Use **bounded mode** for an explicitly limited", normalized)
        self.assertIn("Use **exhaustive mode** for completion intent", normalized)
        self.assertIn("cover/document this whole project", normalized)
        self.assertIn(
            "A completion verb applied to the entire repository is explicit "
            "exhaustive intent",
            normalized,
        )

    def test_bounded_contract_has_no_orchestration_state(self):
        self.assertNotIn("campaign.py", self.mapper)
        self.assertNotIn("producer", self.mapper.lower())
        self.assertIn("one shallowest useful mapping step", self.mapper)

    def test_parallel_and_sequential_modes_share_one_campaign_protocol(self):
        normalized = " ".join(self.entrypoint.split())
        self.assertIn(
            "Read [references/orchestration.md](references/orchestration.md) "
            "completely",
            normalized,
        )
        self.assertIn("Use the same durable campaign state", normalized)
        self.assertIn("campaign.py accept", normalized)

    def test_only_one_transactional_campaign_script_is_exposed(self):
        scripts = ROOT / "skills/specspine-map/scripts"
        self.assertTrue((scripts / "campaign.py").is_file())
        self.assertFalse((scripts / "frontier.py").exists())
        self.assertFalse((scripts / "checkpoint.py").exists())
        self.assertFalse((scripts / "publish_candidates.py").exists())
        normalized = " ".join(self.protocol.split())
        self.assertIn("`accept` is one transaction", normalized)
        self.assertIn("hashes both checkpoint JSON and staged bytes", normalized)
        self.assertIn("commits publications, children and terminal state", normalized)

    def test_tool_failure_does_not_stop_independent_work(self):
        normalized = " ".join(self.protocol.split())
        self.assertIn(
            "Continue independent ready work after a branch failure", normalized
        )
        self.assertIn("A tool defect is not an operator decision", normalized)
        self.assertIn(
            "Stop only when `summary` reports `saturated` or `blocked`",
            normalized,
        )
        self.assertIn(
            "Never stop merely to report progress", normalized
        )
        self.assertIn("Never replace an unfinished campaign", normalized)
        self.assertIn("repair-prerequisite", normalized)
        self.assertIn("coverage-report", normalized)

    def test_model_routing_and_branch_affinity_are_explicit(self):
        normalized = " ".join(self.protocol.split())
        self.assertIn(
            "strong root with `medium` or `high` reasoning", normalized
        )
        self.assertIn("Keep producers evidence-affine", normalized)
        self.assertIn("independent strong semantic audit", normalized)
        self.assertIn("never send an unrelated branch through `followup_task`", normalized)
        self.assertIn("wait for a slot", normalized)
        self.assertIn("accepted `coverage_frontier`", normalized)

    def test_campaign_has_lock_atomic_write_and_rollback(self):
        self.assertIn("fcntl.flock", self.campaign)
        self.assertIn("os.replace(temporary_path, path)", self.campaign)
        self.assertIn("def rollback(", self.campaign)
        self.assertIn("checkpoint_digest", self.campaign)
        self.assertIn("DEFERRED_CODES", self.campaign)
        self.assertIn("validate_dependency_graph", self.campaign)
        self.assertIn("quality_gate", self.campaign)
        self.assertIn("publish_and_locally_saturate", self.campaign)
        self.assertIn("producer_affinity", self.campaign)
        self.assertIn("producer_assignments", self.campaign)
        self.assertIn("discovered_by_owner", self.campaign)
        self.assertIn("fresh producer required", self.campaign)

    def test_existing_spine_seeds_frontier_from_documentation_first(self):
        entrypoint = " ".join(self.entrypoint.split())
        protocol = " ".join(self.protocol.split())
        documentation_first = " ".join(self.documentation_first.split())
        self.assertIn("documentation-first-seeding.md", entrypoint)
        self.assertIn("before source discovery or producer assignment", protocol)
        self.assertIn("seed-from-spine", documentation_first)
        self.assertIn("documentation-pass", documentation_first)
        self.assertIn("records document digests", documentation_first)
        self.assertIn("strictly more precise", documentation_first)
        self.assertIn("recursive deepening mechanism", documentation_first)
        self.assertIn("documentation depth witness", self.campaign)
        self.assertIn("plan_depth", self.campaign)
        self.assertIn("first broad code pass", protocol)
        self.assertIn("missing_documentation_plan", self.campaign)
        self.assertIn("stale_documentation_pass", self.campaign)
        self.assertIn("stale_integration_pass", self.campaign)

    def test_saturation_requires_empty_frontier_and_finished_producers(self):
        normalized = " ".join(self.protocol.split())
        self.assertIn(
            "every assigned producer must have returned its terminal result",
            normalized,
        )
        self.assertIn("no producer may still be running", normalized)
        self.assertIn("current pass returns `no_gaps`", normalized)
        self.assertIn("make no further documentation edits", normalized)
        self.assertIn("typed relationships", normalized)
        self.assertIn("file organization", normalized)

    def test_graph_integration_owns_links_ids_and_directory_review(self):
        normalized = " ".join(self.integration.split())
        self.assertIn("canonical `Relationships` tables", normalized)
        self.assertIn("semantic ID as the complete link label", normalized)
        self.assertIn("do not manufacture reciprocal rows", normalized)
        self.assertIn("update every incoming and outgoing relative link", normalized)
        self.assertIn("flat layout while it remains easy to navigate", normalized)
        self.assertIn("integration-pass", normalized)

    def test_producers_cannot_write_shared_navigation(self):
        normalized = " ".join(self.protocol.split())
        self.assertIn(
            "Producers never edit the live Spine, `README.md`, or campaign state",
            normalized,
        )
        self.assertIn("producer must not publish README.md", self.campaign)
        self.assertIn("## Finalize", self.protocol)

    def test_prompt_size_is_bounded(self):
        self.assertLessEqual(len(self.entrypoint.splitlines()), 105)
        self.assertLessEqual(len(self.protocol.splitlines()), 290)
        self.assertLessEqual(len(self.documentation_first.splitlines()), 105)
        self.assertLessEqual(len(self.integration.splitlines()), 100)


if __name__ == "__main__":
    unittest.main()
