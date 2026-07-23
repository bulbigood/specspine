import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]


class MapParallelContractTests(unittest.TestCase):
    def test_map_routes_large_repository_parallelism_to_reference(self):
        skill = (ROOT / "skills/specspine-map/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("references/parallel-mapping.md", skill)
        self.assertIn("parallel mapping wave", skill)

    def test_parallel_workers_are_isolated_and_single_level(self):
        protocol = (
            ROOT / "skills/specspine-map/references/parallel-mapping.md"
        ).read_text(encoding="utf-8")
        required = (
            "The orchestrator is the only agent allowed to spawn mapping workers.",
            "private staging root as the only writable documentation location",
            "must not modify the repository, the live Spine",
            "source-aware Map",
            "invoke SpecSpine Doctor",
            "Do not use a requested or desired document count",
        )
        for statement in required:
            with self.subTest(statement=statement):
                self.assertIn(statement, protocol)

    def test_parallel_protocol_preserves_map_doctor_boundary(self):
        protocol = (
            ROOT / "skills/specspine-map/references/parallel-mapping.md"
        ).read_text(encoding="utf-8")
        doctor = (ROOT / "skills/specspine-doctor/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Doctor does not inspect repository code", protocol)
        self.assertIn("Pass the integrated `<spine-root>`", protocol)
        self.assertNotIn("parallel Map", doctor)
        self.assertNotIn("parallel mapping", doctor)

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
