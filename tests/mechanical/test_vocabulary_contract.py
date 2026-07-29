import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
VOCABULARY_PATH = ROOT / "shared/references/vocabulary.json"
SCHEMA_PATH = ROOT / "shared/references/specspine.schema.json"


def load_contract():
    path = ROOT / "shared/scripts/spec_contract.py"
    specification = importlib.util.spec_from_file_location("spec_contract_test", path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


class VocabularyContractTests(unittest.TestCase):
    def setUp(self):
        self.vocabulary = json.loads(VOCABULARY_PATH.read_text(encoding="utf-8"))

    def test_contract_reads_canonical_vocabulary(self):
        contract = load_contract()
        self.assertEqual(
            set(self.vocabulary["document_kinds"]),
            set(contract.CORE_KINDS),
        )
        self.assertEqual(
            set(self.vocabulary["relations"]),
            set(contract.CORE_RELATIONS),
        )
        self.assertEqual(
            tuple(self.vocabulary["facets"]),
            contract.FACET_NAMES,
        )
        self.assertEqual(
            self.vocabulary["identifier_patterns"]["semantic"],
            contract.SEMANTIC_ID_PATTERN,
        )

    def test_manifest_schema_enums_match_vocabulary(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        definitions = schema["$defs"]
        self.assertEqual(
            set(self.vocabulary["implementation_freedom"]),
            set(schema["properties"]["implementation_freedom"]["enum"]),
        )
        self.assertEqual(
            set(self.vocabulary["facet_values"]),
            set(definitions["facet"]["enum"]),
        )
        self.assertEqual(
            set(self.vocabulary["inspection_facet_values"]),
            set(definitions["inspectionFacet"]["enum"]),
        )
        self.assertEqual(
            set(self.vocabulary["asset_roles"]),
            set(definitions["asset"]["properties"]["role"]["enum"]),
        )
        self.assertEqual(
            set(self.vocabulary["inspection_modes"]),
            set(
                definitions["area"]["properties"]["inspection"]["properties"]["mode"]["enum"]
            ),
        )
        presentation = definitions["presentation"]["properties"]
        self.assertEqual(
            set(self.vocabulary["headings"]),
            set(presentation["headings"]["properties"]),
        )
        self.assertEqual(
            set(self.vocabulary["headings"]),
            set(presentation["section_order"]["items"]["enum"]),
        )
        facets = definitions["facets"]
        self.assertEqual(set(self.vocabulary["facets"]), set(facets["required"]))
        self.assertEqual(set(self.vocabulary["facets"]), set(facets["properties"]))
        self.assertEqual(
            self.vocabulary["identifier_patterns"]["document"],
            definitions["area"]["properties"]["owner"]["pattern"],
        )
        self.assertEqual(
            "^OQ-" + self.vocabulary["identifier_patterns"]["document"][1:],
            definitions["area"]["properties"]["blockers"]["items"]["pattern"],
        )
        self.assertEqual(
            "^VER-" + self.vocabulary["identifier_patterns"]["document"][1:],
            definitions["asset"]["properties"]["verifies"]["items"]["pattern"],
        )

    def test_glossary_is_current(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "shared/scripts/render_vocabulary.py")],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_every_published_skill_exposes_vocabulary(self):
        for skill in sorted((ROOT / "skills").glob("specspine-*")):
            with self.subTest(skill=skill.name):
                glossary = skill / "references/spec-glossary.md"
                vocabulary = skill / "references/vocabulary.json"
                self.assertTrue(glossary.is_file())
                self.assertTrue(vocabulary.is_file())
                self.assertEqual(
                    VOCABULARY_PATH.read_bytes(),
                    vocabulary.read_bytes(),
                )

    def test_readme_template_is_compact_and_managed(self):
        template = (
            ROOT
            / "skills/specspine-doctor/assets/templates/readme-bootstrap.md"
        ).read_text(encoding="utf-8")
        self.assertEqual(1, template.count("<!-- specspine:readme:begin -->"))
        self.assertEqual(1, template.count("<!-- specspine:readme:end -->"))
        self.assertIn("{{SPINE_ROOT}}/_INDEX.md", template)
        self.assertNotIn("## Semantic identifier families", template)


if __name__ == "__main__":
    unittest.main()
