import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[2]
MODULE_PATH = PROJECT_ROOT / "tools/specspine-extract/validate_corpus.py"
SPEC = importlib.util.spec_from_file_location(
    "specspine_extract_corpus_validator", MODULE_PATH
)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class ExtractCorpusValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "backend-service-en-01"
        self.project = self.root / "project"
        self.spine = self.project / "specspine"
        self.spine.mkdir(parents=True)
        (self.project / "AGENTS.md").write_text(
            "<!-- specspine:begin -->\n"
            "## Architecture\n\n"
            "- SpecSpine index: `specspine/README.md`\n"
            "- Documentation language: `en`\n"
            "- Retrieval accelerator: `auto`\n"
            "<!-- specspine:end -->\n",
            encoding="utf-8",
        )
        documents = {
            "README.md": "# Index\n\n[Owner](owner.md)\n",
            "owner.md": "# Retry owner\n\nOwns provider retry timeouts.\n",
            "support.md": "# Provider support\n\nDefines provider boundaries.\n",
            "hard-negative.md": "# Client retries\n\nRetries local requests.\n",
        }
        documents.update({
            f"decoy-{index}.md": f"# Decoy {index}\n\nGeneric architecture.\n"
            for index in range(6)
        })
        documents["README.md"] = "# Index\n\n" + "\n".join(
            f"- [{Path(relative).stem}]({relative})"
            for relative in sorted(documents)
            if relative != "README.md"
        ) + "\n"
        for relative, content in documents.items():
            (self.spine / relative).write_text(content, encoding="utf-8")
        self.manifest = {
            "schema_version": 1,
            "corpus": {
                "id": "backend-service-en-01",
                "project_type": "backend-service",
                "documentation_language": "en",
                "size_tier": "small",
                "seed": 101,
                "axes": {
                    "boilerplate": "medium",
                    "lexical_overlap": "high",
                    "ownership": "single",
                    "graph_density": "low",
                },
            },
            "documents": {
                relative: "sha256:" + hashlib.sha256(
                    (self.spine / relative).read_bytes()
                ).hexdigest()
                for relative in sorted(documents)
            },
            "scenarios": [{
                "id": "retry-ownership",
                "tags": ["synonym", "partial-match-decoys"],
                "request": {
                    "language": "en",
                    "text": "Find the provider retry owner.",
                },
                "search": {
                    "limit": 5,
                    "graph_depth": 1,
                    "graph_limit": 2,
                },
                "slices": [{
                    "id": "retry-owner",
                    "must": [
                        ["provider"],
                        ["retry", "retries"],
                        ["timeout", "timeouts"],
                    ],
                    "should": [["ownership", "owner"]],
                    "evaluation": "ranking",
                    "expected_status": "matched",
                    "judgments": [
                        {"path": "owner.md", "grade": 3, "origin": "direct"},
                        {"path": "support.md", "grade": 2, "origin": "either"},
                        {
                            "path": "hard-negative.md",
                            "grade": 0,
                            "origin": "either",
                            "hard_negative": True,
                        },
                    ],
                }],
            }],
        }
        self.path = self.root / "manifest.json"
        self.write_manifest()

    def tearDown(self):
        self.temporary.cleanup()

    def write_manifest(self):
        self.path.write_text(
            json.dumps(self.manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_valid_manifest_and_schema_parse(self):
        payload = VALIDATOR.validate_manifest(self.path)
        schema = json.loads(
            (
                PROJECT_ROOT / "tests/retrieval-corpora/manifest.schema.json"
            ).read_text(encoding="utf-8")
        )

        self.assertEqual(1, payload["schema_version"])
        self.assertEqual(
            "SpecSpine retrieval benchmark corpus", schema["title"]
        )

    def test_inventory_hash_drift_is_rejected(self):
        (self.spine / "owner.md").write_text(
            "# Changed\n", encoding="utf-8"
        )

        with self.assertRaisesRegex(
            VALIDATOR.CorpusValidationError, "hash mismatch"
        ):
            VALIDATOR.validate_manifest(self.path)

    def test_multiple_canonical_owners_are_rejected(self):
        judgments = self.manifest["scenarios"][0]["slices"][0]["judgments"]
        judgments[1]["grade"] = 3
        judgments[1]["origin"] = "direct"
        self.write_manifest()

        with self.assertRaisesRegex(
            VALIDATOR.CorpusValidationError, "at most one canonical owner"
        ):
            VALIDATOR.validate_manifest(self.path)

    def test_structured_query_limits_are_reused_from_ranking_v2(self):
        self.manifest["scenarios"][0]["slices"][0]["must"] = []
        self.write_manifest()

        with self.assertRaisesRegex(
            VALIDATOR.CorpusValidationError, "must contain 1 to 8 groups"
        ):
            VALIDATOR.validate_manifest(self.path)

    def test_protocol_no_match_may_retain_one_semantic_owner(self):
        item = self.manifest["scenarios"][0]["slices"][0]
        item["evaluation"] = "protocol"
        item["expected_status"] = "no_match"
        item["must"] = [["term-not-present"]]
        self.manifest["scenarios"][0]["tags"] = ["no-match", "wrong-must"]
        self.write_manifest()

        VALIDATOR.validate_manifest(self.path)

    def test_unknown_fields_are_rejected(self):
        invalid = copy.deepcopy(self.manifest)
        invalid["corpus"]["generator_note"] = "not part of v1"
        self.manifest = invalid
        self.write_manifest()

        with self.assertRaisesRegex(
            VALIDATOR.CorpusValidationError, "unknown fields"
        ):
            VALIDATOR.validate_manifest(self.path)

    def test_unreachable_documents_are_rejected(self):
        readme = self.spine / "README.md"
        readme.write_text("# Index\n\n[Owner](owner.md)\n", encoding="utf-8")
        self.manifest["documents"]["README.md"] = (
            "sha256:" + hashlib.sha256(readme.read_bytes()).hexdigest()
        )
        self.write_manifest()

        with self.assertRaisesRegex(
            VALIDATOR.CorpusValidationError, "not reachable from README.md"
        ):
            VALIDATOR.validate_manifest(self.path)


if __name__ == "__main__":
    unittest.main()
