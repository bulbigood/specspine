import importlib.util
import json
import re
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
        semantic = re.compile(contract.SEMANTIC_ID_PATTERN)
        self.assertEqual(
            tuple(self.vocabulary["semantic_prefixes"]),
            contract.SEMANTIC_PREFIXES,
        )
        for prefix in self.vocabulary["semantic_prefixes"]:
            with self.subTest(prefix=prefix):
                self.assertIsNotNone(semantic.fullmatch(f"{prefix}-example"))
        self.assertIsNone(semantic.fullmatch("UNKNOWN-example"))

    def test_semantic_prefix_metadata_drives_contract_views(self):
        contract = load_contract()
        known_facets = set(self.vocabulary["facets"])
        known_sections = set(self.vocabulary["headings"])
        for prefix, definition in self.vocabulary["semantic_prefixes"].items():
            with self.subTest(prefix=prefix, metadata="shape"):
                self.assertIn(definition["section"], known_sections)
                self.assertIsInstance(definition["normative"], bool)
                self.assertLessEqual(
                    set(definition.get("supports_facets", ())),
                    known_facets,
                )
        expected_sections = {
            prefix: definition["section"]
            for prefix, definition in self.vocabulary["semantic_prefixes"].items()
        }
        self.assertEqual(expected_sections, contract.SEMANTIC_PREFIX_SECTIONS)
        for facet in self.vocabulary["facets"]:
            expected = {
                f"{prefix}-"
                for prefix, definition in self.vocabulary["semantic_prefixes"].items()
                if facet in definition.get("supports_facets", ())
            }
            with self.subTest(facet=facet):
                self.assertEqual(expected, contract.FACET_SUPPORT_PREFIXES[facet])

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

    def test_v4_excludes_private_implementation_contracts(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        semantics = (ROOT / "docs/reference/semantics.md").read_text(encoding="utf-8")
        format_reference = (ROOT / "docs/reference/format.md").read_text(
            encoding="utf-8"
        )

        self.assertEqual(4, self.vocabulary["format_major"])
        self.assertEqual(4, schema["properties"]["specspine"]["const"])
        self.assertNotIn("exact", self.vocabulary["implementation_freedom"])
        self.assertNotIn("execution-contract", self.vocabulary["asset_roles"])
        self.assertIn("“External” is relative to the canonical owner", semantics)
        self.assertIn("Apply the replacement test", semantics)
        self.assertIn("Do not canonize private algorithms", semantics)
        self.assertIn(
            "Typed owner relationships are accepted architectural intent",
            semantics,
        )
        self.assertIn("never a walkthrough", format_reference)
        self.assertIn(
            "MUST NOT publish those proposals as canonical",
            format_reference,
        )

    def test_glossary_is_current(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "shared/scripts/render_vocabulary.py")],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_default_root_index_glossary_covers_every_vocabulary_token(self):
        contract = load_contract()
        glossary = contract.DEFAULT_INDEX_TEXT["glossary"]
        groups = (
            "document_kinds",
            "semantic_prefixes",
            "relations",
            "facets",
            "facet_values",
            "inspection_modes",
            "inspection_facet_values",
            "implementation_freedom",
            "computed_statuses",
            "asset_roles",
            "headings",
            "manifest_fields",
            "markdown_keywords",
            "markers",
        )
        for group in groups:
            for token in self.vocabulary[group]:
                with self.subTest(group=group, token=token):
                    self.assertIn(f"`{token}`", glossary)
        for path in self.vocabulary["reserved_paths"].values():
            self.assertIn(f"`{path}`", glossary)

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
        self.assertIn("{{SPINE_ROOT}}/", template)
        self.assertNotIn("## Semantic identifier families", template)


if __name__ == "__main__":
    unittest.main()
