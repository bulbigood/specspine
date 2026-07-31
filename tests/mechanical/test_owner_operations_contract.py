import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
PROTOCOL = ROOT / "docs/reference/owner-operations.md"
MAP = ROOT / "skills/specspine-map"
EVOLVE = ROOT / "skills/specspine-evolve"


class OwnerOperationsContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = " ".join(PROTOCOL.read_text(encoding="utf-8").split())
        cls.map_text = " ".join(
            (MAP / "SKILL.md").read_text(encoding="utf-8").split()
        )
        cls.evolve_text = " ".join(
            (EVOLVE / "SKILL.md").read_text(encoding="utf-8").split()
        )

    def test_protocol_is_shared_by_map_and_evolve(self):
        for skill in (MAP, EVOLVE):
            reference = skill / "references/owner-operations.md"
            self.assertTrue(reference.is_symlink())
            self.assertEqual(PROTOCOL.resolve(), reference.resolve())
            self.assertIn(
                "references/owner-operations.md",
                (skill / "SKILL.md").read_text(encoding="utf-8"),
            )

    def test_refine_and_expand_have_one_shared_meaning(self):
        self.assertIn("`refine` changes durable meaning or evidence", self.protocol)
        self.assertIn("`expand` creates exactly one", self.protocol)
        self.assertIn("Select exactly one write owner", self.protocol)
        self.assertIn("Create exactly one content document", self.protocol)
        for skill_text in (self.map_text, self.evolve_text):
            self.assertIn("`refine`", skill_text)
            self.assertIn("`expand`", skill_text)

    def test_authority_overlays_keep_observation_and_intent_distinct(self):
        self.assertIn(
            "Map authorizes `refine` and the `create` primitive of `expand`",
            self.map_text,
        )
        self.assertIn("observation-only owner", self.map_text)
        self.assertIn("canonical owner", self.evolve_text)
        self.assertIn("does not authorize expansion", self.evolve_text)
        self.assertIn("explicitly accepts", self.evolve_text)
        self.assertIn(
            "never select `expand` from `mapping.frontier` alone",
            self.evolve_text.casefold(),
        )

    def test_structural_primitives_are_shared_but_map_cannot_use_them(self):
        for primitive in (
            "`create`",
            "`split`",
            "`merge`",
            "`move`",
            "`rename`",
            "`link`",
            "`remove`",
        ):
            self.assertIn(primitive, self.protocol)
        self.assertIn(
            "does not authorize any other structural primitive",
            self.map_text,
        )
        self.assertIn(
            "`split`, `merge`, `move`, `rename`, `link`, and `remove`",
            self.evolve_text,
        )

    def test_protocol_owns_identity_reachability_indexes_and_gate(self):
        for phrase in (
            "Preserve stable document and statement IDs",
            "Preserve root reachability",
            "Rebuild all affected deterministic indexes",
            "Validate the whole Spine",
        ):
            self.assertIn(phrase, self.protocol)


if __name__ == "__main__":
    unittest.main()
