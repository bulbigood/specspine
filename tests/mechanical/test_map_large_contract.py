import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]


class MapLargeContractTests(unittest.TestCase):
    def test_map_is_atomic_and_large_orchestration_is_explicit(self):
        mapper = (ROOT / "skills/specspine-map/SKILL.md").read_text(encoding="utf-8")
        large = (ROOT / "skills/specspine-map-large/SKILL.md").read_text(
            encoding="utf-8"
        )
        metadata = (ROOT / "skills/specspine-map-large/agents/openai.yaml").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("references/orchestration.md", mapper)
        self.assertNotIn("producer-consumer", mapper)
        self.assertNotIn("Normalize once after saturation", mapper)
        self.assertIn("one requested repository scope", mapper)
        self.assertIn("references/orchestration.md", large)
        self.assertIn("complete inline producer command", large)
        self.assertIn("must be passed as text", large)
        self.assertIn("Do not read another mapping skill", large)
        self.assertIn("allow_implicit_invocation: false", metadata)

    def test_parallel_workers_are_isolated_and_single_level(self):
        protocol = (
            ROOT / "skills/specspine-map-large/references/orchestration.md"
        ).read_text(encoding="utf-8")
        required = (
            "The orchestrator is the only agent allowed to spawn mapping workers.",
            "publish-ready Markdown specifications only",
            "must not modify the repository, the live Spine",
            "Schedule as producer-consumer",
            "As soon as each producer finishes",
            "Normalize once after saturation",
            "Do not use a requested or desired document count",
        )
        for statement in required:
            with self.subTest(statement=statement):
                self.assertIn(statement, protocol)

    def test_staged_publication_reads_once_then_moves_unchanged(self):
        protocol = (
            ROOT / "skills/specspine-map-large/references/orchestration.md"
        ).read_text(encoding="utf-8")
        publication = protocol.split("## Consume and publish results", 1)[1].split(
            "## Continue to saturation", 1
        )[0]
        doctor = (ROOT / "skills/specspine-doctor/SKILL.md").read_text(
            encoding="utf-8"
        )
        normalized_publication = " ".join(publication.split())
        self.assertIn("inspect every reported candidate file once", normalized_publication)
        self.assertIn("Do not inspect repository source", normalized_publication)
        self.assertIn("filesystem move/rename tool", normalized_publication)
        self.assertIn("never reconstruct the file", normalized_publication)
        self.assertIn("do not reread it after the move", normalized_publication)
        self.assertIn("Do not merge, semantically rewrite", normalized_publication)
        self.assertNotIn("parallel Map", doctor)
        self.assertNotIn("parallel mapping", doctor)

    def test_large_mapping_has_sequential_fallback_and_bounded_discovery(self):
        skill = (ROOT / "skills/specspine-map-large/SKILL.md").read_text(
            encoding="utf-8"
        )
        protocol = (
            ROOT / "skills/specspine-map-large/references/orchestration.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(protocol.split())
        self.assertIn(
            "current agent is orchestrator, producer, and consumer",
            " ".join(skill.split()),
        )
        self.assertIn("When subagents are unavailable", protocol)
        self.assertIn("one local producer", normalized)
        self.assertIn("Never attempt to hold the whole repository map", normalized)
        self.assertIn("Do not deeply explore the codebase", normalized)
        self.assertIn("capacity plus a small reserve", normalized)
        self.assertIn("primary discovery mechanism", normalized)
        self.assertIn("without rereading repository source", normalized)

    def test_large_mapping_checkpoints_and_recovers_simply(self):
        protocol = (
            ROOT / "skills/specspine-map-large/references/orchestration.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(protocol.split())
        self.assertIn("small durable append-only ledger", normalized)
        self.assertIn("append-only ledger", normalized)
        self.assertIn("without rereading or rewriting the ledger", normalized)
        self.assertIn("On resume, read the ledger, reconcile published paths", normalized)
        self.assertIn("return interrupted active questions to ready", normalized)
        self.assertIn("requeue the question once", normalized)
        self.assertIn("After a repeated confirmed failure", normalized)

    def test_continuously_refills_slots_without_wave_barriers(self):
        protocol = (
            ROOT / "skills/specspine-map-large/references/orchestration.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(protocol.split())
        refill = normalized.index(
            "Before reading or publishing any candidate file, immediately launch"
        )
        acceptance = normalized.index(
            "While the replacement producer runs, inspect and publish"
        )
        self.assertLess(refill, acceptance)
        self.assertIn("dependency-aware ready queue", normalized)
        self.assertIn(
            "Candidate acceptance and publication must not precede refilling a safe slot",
            normalized,
        )
        self.assertIn("Do not wait for all active workers to finish", normalized)
        self.assertIn("Keep active concurrency at the largest safe level", normalized)
        self.assertIn("barrier primitive as a transport limitation", normalized)
        self.assertIn("do not introduce conceptual waves", normalized)
        self.assertIn("Do not invoke SpecSpine Doctor during the mapping run", normalized)
        self.assertIn("agent or thread ID returned by the environment as opaque", normalized)
        self.assertIn("Never start a duplicate producer", normalized)
        self.assertIn("never grounds for retry", normalized)
        self.assertIn("explicit terminal `failed` state", normalized)
        self.assertIn("blocking completion notification", normalized)
        self.assertIn("Do not poll worker status", normalized)

    def test_parallel_handoff_is_minimal_and_reports_stay_compact(self):
        protocol = (
            ROOT / "skills/specspine-map-large/references/orchestration.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(protocol.split())
        self.assertIn("complete command below as plain text", normalized)
        self.assertIn("Do not mention, invoke, link to", normalized)
        self.assertIn("bounded SpecSpine mapping producer", protocol)
        self.assertIn("Do not load or invoke any skill", protocol)
        self.assertIn("Require a compact producer report", normalized)
        self.assertIn("does not repeat document prose", normalized)
        producer = (
            protocol.split("You are a bounded SpecSpine mapping producer.", 1)[1]
            .split("```", 1)[0]
        )
        self.assertNotIn("$specspine-map", producer)
        self.assertNotIn("SKILL.md", producer)
        self.assertNotIn("references/", producer)

    def test_normalizes_once_and_gates_post_map_doctor(self):
        protocol = (
            ROOT / "skills/specspine-map-large/references/orchestration.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(protocol.split())
        self.assertIn("do not inspect repository source", normalized)
        self.assertIn("Do not reread every published specification", normalized)
        self.assertIn("destination paths in the ledger as the new-node inventory", normalized)
        self.assertIn("only documents whose paths or links must change", normalized)
        self.assertIn("Update affected relative links", normalized)
        self.assertIn("Perform it once, not during continuous mapping", normalized)
        self.assertIn(
            "only when the current request explicitly includes a post-map semantic review",
            normalized,
        )
        self.assertIn("Apply semantic repairs only after operator approval", normalized)

    def test_doctor_progressively_audits_and_requires_approval_to_write(self):
        doctor = (ROOT / "skills/specspine-doctor/SKILL.md").read_text(
            encoding="utf-8"
        )
        method = (
            ROOT / "skills/specspine-doctor/references/review-method.md"
        ).read_text(encoding="utf-8")
        normalized_doctor = " ".join(doctor.split())
        normalized_method = " ".join(method.split())
        self.assertIn("inspect every specification progressively", doctor)
        self.assertIn("coverage while paths remain", normalized_doctor)
        self.assertIn("ask the operator to approve it", normalized_doctor)
        self.assertIn("clearly supported missing", normalized_doctor)
        self.assertIn("all Markdown", method)
        self.assertIn("write only after operator approval", normalized_method)


if __name__ == "__main__":
    unittest.main()
