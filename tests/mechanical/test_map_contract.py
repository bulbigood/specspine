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

    def test_map_is_one_atomic_layer_pipeline(self):
        text = self.compact(self.entrypoint)
        self.assertIn(
            "scope → select frontier → inspect one layer → synthesize siblings",
            text,
        )
        self.assertIn("publish atomically", text)
        self.assertIn("depth advances by exactly one", text)

    def test_map_separates_action_from_inspection_mode(self):
        text = self.compact(self.entrypoint)
        for intent in ("`survey`", "`deepen`", "`refresh`", "`drift`"):
            self.assertIn(intent, text)
        self.assertIn("`refine`", text)
        self.assertIn("`decompose-layer`", text)
        self.assertIn("“deepen”", text)
        self.assertNotIn("exhaustive", text.casefold())
        self.assertNotIn("increment_verified", text)
        self.assertNotIn("scope_verified", text)

    def test_map_preserves_intent_and_retains_only_material_delta(self):
        text = self.compact(self.entrypoint + "\n" + self.method)
        self.assertIn("exception layer, not a code mirror", text)
        self.assertIn("`covered-by-intent`", text)
        self.assertIn("replacement test", text)
        self.assertIn("preserve title, ID, kind, summary, accepted prose", text)
        self.assertIn("publish repository-derived canonical `Relationships`", text)
        self.assertIn("register every completeness facet as `missing`", text)
        self.assertIn("no wording implies acceptance, conformance", text)

    def test_frontier_drives_a_complete_immediate_layer(self):
        text = self.compact(self.entrypoint + "\n" + self.method)
        self.assertIn("`mapping.frontier`", text)
        self.assertIn("proposed immediate child owners", text)
        self.assertIn("every selected parent", text)
        self.assertIn("complete immediate sibling set", text)
        self.assertIn("do not group peers because they share", text)
        self.assertIn("no grandchild was created", text)

    def test_observed_graph_is_obs_backed_and_non_normative(self):
        text = self.compact(self.entrypoint + "\n" + self.method)
        self.assertIn("`mapping.observed_edges`", text)
        self.assertIn("machine-traversable repository graph", text)
        self.assertIn("references one canonical `OBS`", text)
        self.assertIn("owned by one endpoint", text)
        self.assertIn("OBS-backed observed edges", text)
        self.assertIn("later promote an observed edge", text)

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
                "owner-operations.md",
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
        )
        schema_value = json.loads(schema.read_text(encoding="utf-8"))
        self.assertNotIn(
            "exhaustive",
            schema.read_text(encoding="utf-8"),
        )
        self.assertIn("mapping", schema_value["properties"])
        mapping = schema_value["$defs"]["mapping"]
        self.assertEqual(
            {"frontier", "observed_edges"},
            set(mapping["required"]),
        )
        self.assertEqual(
            {"frontier", "expanded", "terminal"},
            set(
                schema_value["$defs"]["decomposition"]["properties"]["status"]["enum"]
            ),
        )

    def test_result_contract_is_small_and_explicit(self):
        text = self.compact(self.entrypoint)
        for outcome in ("`mapped`", "`no-material-delta`", "`blocked`"):
            self.assertIn(outcome, text)
        self.assertIn("mandatory whole-Spine gate", text)
        self.assertIn("check_spine.py <spine-root>", text)


if __name__ == "__main__":
    unittest.main()
