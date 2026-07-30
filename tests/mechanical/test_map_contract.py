import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
MAP = ROOT / "skills/specspine-map"


class MapOperationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entrypoint = (MAP / "SKILL.md").read_text(encoding="utf-8")
        cls.method = (MAP / "references/mapping-method.md").read_text(
            encoding="utf-8"
        )

    @staticmethod
    def compact(value):
        return " ".join(value.split())

    def test_map_is_one_direct_bounded_pipeline(self):
        text = self.compact(self.entrypoint)
        self.assertIn(
            "scope → context → inspect → classify → write → verify",
            text,
        )
        self.assertIn("current agent", text)
        self.assertIn("at most one non-index content owner", text)
        self.assertIn("one owner-relative semantic frontier", text)
        self.assertIn("Do not create campaign state", text)
        self.assertIn("Do not promise whole-repository coverage", text)

    def test_map_has_one_workflow_and_four_inspection_intents(self):
        text = self.compact(self.entrypoint)
        for intent in ("`survey`", "`deepen`", "`refresh`", "`drift`"):
            self.assertIn(intent, text)
        self.assertIn(
            "do not create different workflows or completion claims",
            text,
        )
        self.assertNotIn("exhaustive", text.casefold())
        self.assertNotIn("increment_verified", text)
        self.assertNotIn("scope_verified", text)

    def test_map_preserves_intent_and_retains_only_material_delta(self):
        text = self.compact(self.entrypoint + "\n" + self.method)
        self.assertIn("exception layer, not a code mirror", text)
        self.assertIn("`covered-by-intent`", text)
        self.assertIn("replacement test", text)
        self.assertIn("preserve title, ID, kind, summary, accepted prose", text)
        self.assertIn("publish repository-derived `Relationships`", text)
        self.assertIn("Inspection never raises completeness", text)
        self.assertIn("no wording implies conformance", text)

    def test_adjacent_responsibilities_are_reported_not_pursued(self):
        text = self.compact(self.entrypoint + "\n" + self.method)
        self.assertIn("deferred lead", text)
        self.assertIn("Do not begin mapping that neighbor", text)
        self.assertIn("must not be pursued in the same invocation", text)
        self.assertIn("not persistent delivery work", text)

    def test_only_shared_deterministic_scripts_remain(self):
        scripts = {
            path.name
            for path in (MAP / "scripts").iterdir()
            if path.name != "__pycache__"
        }
        self.assertEqual(
            {
                "bootstrap_spine.py",
                "check_spine.py",
                "rebuild_indexes.py",
                "spec_contract.py",
            },
            scripts,
        )
        for name in scripts:
            self.assertTrue((MAP / "scripts" / name).is_symlink())

    def test_only_canonical_and_mapping_references_remain(self):
        references = {path.name for path in (MAP / "references").iterdir()}
        self.assertEqual(
            {
                "mapping-method.md",
                "spec-format.md",
                "spec-glossary.md",
                "spec-semantics.md",
                "specspine.schema.json",
                "vocabulary.json",
            },
            references,
        )

    def test_manifest_vocabulary_has_no_recursive_completion_mode(self):
        vocabulary = json.loads(
            (ROOT / "shared/references/vocabulary.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            {"survey", "deepen", "refresh", "drift"},
            set(vocabulary["inspection_modes"]),
        )
        schema = (
            ROOT / "shared/references/specspine.schema.json"
        ).read_text(encoding="utf-8")
        self.assertNotIn('"exhaustive"', schema)

    def test_result_contract_is_small_and_explicit(self):
        text = self.compact(self.entrypoint)
        for outcome in ("`mapped`", "`no-material-delta`", "`blocked`"):
            self.assertIn(outcome, text)
        self.assertIn("mandatory whole-Spine gate", text)
        self.assertIn("check_spine.py <spine-root>", text)


if __name__ == "__main__":
    unittest.main()
