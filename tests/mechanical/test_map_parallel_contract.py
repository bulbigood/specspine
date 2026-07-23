import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]


class MapParallelContractTests(unittest.TestCase):
    def test_map_routes_large_repository_parallelism_to_reference(self):
        skill = (ROOT / "skills/specspine-map/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("references/parallel-mapping.md", skill)
        self.assertIn("parallel mapping run", skill)

    def test_parallel_workers_are_isolated_and_single_level(self):
        protocol = (
            ROOT / "skills/specspine-map/references/parallel-mapping.md"
        ).read_text(encoding="utf-8")
        required = (
            "The orchestrator is the only agent allowed to spawn mapping workers.",
            "private staging root as the only writable documentation location",
            "must not modify the repository, the live Spine",
            "Schedule as producer-consumer",
            "As soon as each worker finishes",
            "Worker output is the published output",
            "Normalize once after saturation",
            "Do not use a requested or desired document count",
        )
        for statement in required:
            with self.subTest(statement=statement):
                self.assertIn(statement, protocol)

    def test_parallel_publication_skips_integration_and_doctor(self):
        protocol = (
            ROOT / "skills/specspine-map/references/parallel-mapping.md"
        ).read_text(encoding="utf-8")
        publication = protocol.split("## Consume and publish results", 1)[1].split(
            "## Continue to saturation", 1
        )[0]
        doctor = (ROOT / "skills/specspine-doctor/SKILL.md").read_text(
            encoding="utf-8"
        )
        normalized_publication = " ".join(publication.split())
        self.assertIn("Do not read or review file contents", normalized_publication)
        self.assertIn("run SpecSpine Doctor", normalized_publication)
        self.assertIn("semantic integration", normalized_publication)
        self.assertNotIn("parallel Map", doctor)
        self.assertNotIn("parallel mapping", doctor)

    def test_continuously_refills_slots_without_wave_barriers(self):
        protocol = (
            ROOT / "skills/specspine-map/references/parallel-mapping.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(protocol.split())
        self.assertIn("dependency-aware ready queue", normalized)
        self.assertIn("Immediately launch the next ready question", normalized)
        self.assertIn("Do not wait for all active workers to finish", normalized)
        self.assertIn("Keep active concurrency at the largest safe level", normalized)
        self.assertIn("barrier primitive as a transport limitation", normalized)
        self.assertIn("do not introduce conceptual waves", normalized)
        self.assertIn("Do not invoke SpecSpine Doctor during the mapping run", normalized)

    def test_normalizes_once_and_gates_post_map_doctor(self):
        protocol = (
            ROOT / "skills/specspine-map/references/parallel-mapping.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(protocol.split())
        self.assertIn("do not inspect repository source", normalized)
        self.assertIn("move specifications into a few broad", normalized)
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
