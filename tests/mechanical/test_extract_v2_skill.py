import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[2]
SKILL_ROOT = PROJECT_ROOT / "tests/eval/skills/specspine-extract-v2"


class ExtractV2SkillTests(unittest.TestCase):
    def test_skill_is_benchmark_scoped_and_has_no_placeholders(self):
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertNotIn("TODO", text)
        self.assertIn("benchmark-only", text)
        self.assertIn("exactly once", text)
        self.assertIn("--queries-json", text)
        self.assertIn("SPECSPINE_EXTRACT_V2_RANKING", text)
        self.assertLess(
            text.index("<spine-root>/README.md"),
            text.index("python3 <skill-root>/scripts/search_spine_v2.py"),
        )

    def test_bundled_resources_match_canonical_v2_implementation(self):
        pairs = (
            (
                PROJECT_ROOT
                / "skills/specspine-extract/scripts/search_spine_v2.py",
                SKILL_ROOT / "scripts/search_spine_v2.py",
            ),
            (
                PROJECT_ROOT / "skills/specspine-extract/scripts/ranking_v2.py",
                SKILL_ROOT / "scripts/ranking_v2.py",
            ),
            (
                PROJECT_ROOT
                / "skills/specspine-extract/references/context-handoff.md",
                SKILL_ROOT / "references/context-handoff.md",
            ),
        )

        for source, bundled in pairs:
            self.assertEqual(
                source.read_bytes(),
                bundled.read_bytes(),
                f"stale benchmark resource: {bundled}",
            )

    def test_openai_metadata_names_v2_skill(self):
        metadata = (SKILL_ROOT / "agents/openai.yaml").read_text(
            encoding="utf-8"
        )

        self.assertIn('display_name: "SpecSpine Extract V2"', metadata)
        self.assertIn("$specspine-extract-v2", metadata)

    def test_manifest_schema_is_valid_json(self):
        schema = json.loads(
            (
                PROJECT_ROOT / "tests/retrieval-corpora/manifest.schema.json"
            ).read_text(encoding="utf-8")
        )

        self.assertEqual(
            "https://json-schema.org/draft/2020-12/schema",
            schema["$schema"],
        )


if __name__ == "__main__":
    unittest.main()
