import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]


class DirectoryLayoutContractTests(unittest.TestCase):
    def test_format_is_shared_authority_for_directory_density(self):
        format_text = (ROOT / "docs/reference/format.md").read_text(encoding="utf-8")
        map_text = (
            ROOT / "skills/specspine-map/references/topic-synthesis.md"
        ).read_text(encoding="utf-8")
        evolve_text = (
            ROOT / "skills/specspine-evolve/SKILL.md"
        ).read_text(encoding="utf-8")
        format_text = " ".join(format_text.split())
        map_text = " ".join(map_text.split())
        evolve_text = " ".join(evolve_text.split())

        self.assertIn("about 20 immediate index entries", format_text)
        self.assertIn("soft density threshold", format_text)
        self.assertIn("Map applies this rule only", format_text)
        self.assertIn("Evolve applies the same rule", format_text)
        self.assertIn("Preserve every existing owner path exactly", map_text)
        self.assertIn("Map may organize only new documents", map_text)
        self.assertIn("may redistribute existing documents", evolve_text)
        self.assertIn("preserve document IDs", evolve_text)


if __name__ == "__main__":
    unittest.main()
