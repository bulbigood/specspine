import json
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
FINALIZE = ROOT / "skills/specspine-map/scripts/discovery_finalize.py"
CAMPAIGN = ROOT / "skills/specspine-map/scripts/campaign.py"
SPEC = importlib.util.spec_from_file_location("map_campaign_finalize_tests", CAMPAIGN)
assert SPEC and SPEC.loader
CAMPAIGN_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CAMPAIGN_MODULE)


class DiscoveryFinalizeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repository = self.root / "repository"
        (self.repository / "src/identity").mkdir(parents=True)
        (self.repository / "src/identity/session.py").write_text(
            "SESSION = True\n",
            encoding="utf-8",
        )
        (self.repository / "src/identity/recovery.py").write_text(
            "RECOVERY = True\n",
            encoding="utf-8",
        )
        (self.repository / "pyproject.toml").write_text(
            "[project]\nname = 'fixture'\n",
            encoding="utf-8",
        )
        self.spine = self.root / "specspine"
        self.spine.mkdir()
        self.packet = self.root / "packet.json"
        self.packet.write_text(
            json.dumps(
                {
                    "discovery_contract_version": (
                        CAMPAIGN_MODULE.DISCOVERY_CONTRACT_VERSION
                    ),
                    "repository_root": str(self.repository),
                    "spine_root": str(self.spine),
                    "operation": {
                        "scope": {
                            "kind": "repository",
                            "title": "Repository",
                            "question": "Map repository architecture",
                            "inclusion_rule": "Production architecture.",
                            "exclusion_rule": "Generated files.",
                        },
                        "completion": {"kind": "exhaustive"},
                    },
                    "lead": {
                        "id": "identity-runtime",
                        "title": "Identity runtime",
                        "question": "How are sessions managed?",
                        "reason": "The runtime owns sessions.",
                        "parent_ids": [],
                        "seed_files": [
                            "pyproject.toml",
                            "src/identity/session.py",
                        ],
                    },
                    "source_refs": [],
                }
            ),
            encoding="utf-8",
        )
        self.draft = self.root / "draft.json"
        self.result = self.root / "results/lead-identity-runtime.json"

    def tearDown(self):
        self.temporary.cleanup()

    def draft_value(self):
        return {
            "disposition": "mapped",
            "reason": "The session runtime exposes persistence and recovery.",
            "topics": [
                {
                    "title": "Session lifecycle",
                    "responsibility": "Owns session creation and recovery.",
                    "reason": "Session code exposes a durable boundary.",
                    "files": [
                        "src/identity/session.py",
                        "src/identity/session.py",
                    ],
                }
            ],
            "supporting": [
                {
                    "reason": "Runtime composition metadata.",
                    "files": [
                        "src/identity/session.py",
                        "src/identity/session.py",
                        "pyproject.toml",
                        "pyproject.toml",
                    ],
                },
                {
                    "reason": "Repeated composition evidence.",
                    "files": ["pyproject.toml"],
                },
            ],
            "unresolved_leads": [
                {
                    "id": "session-recovery",
                    "title": "Session recovery",
                    "question": "Who recovers failed sessions?",
                    "reason": "Recovery crosses the inspected boundary.",
                    "fallback_kind": "separate_owner",
                    "seed_files": [
                        "src/identity/session.py",
                        "src/identity/session.py",
                        "src/identity/recovery.py",
                        "src/identity/recovery.py",
                    ],
                }
            ],
        }

    def execute(self, *, expected=0):
        completed = subprocess.run(
            [
                sys.executable,
                str(FINALIZE),
                str(self.packet),
                str(self.draft),
                str(self.result),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(
            expected,
            completed.returncode,
            completed.stderr or completed.stdout,
        )
        return json.loads(completed.stdout or completed.stderr)

    def test_finalize_derives_and_normalizes_canonical_result(self):
        self.draft.write_text(
            json.dumps(self.draft_value()),
            encoding="utf-8",
        )

        receipt = self.execute()

        result = json.loads(self.result.read_text(encoding="utf-8"))
        self.assertEqual("ready", receipt["status"])
        self.assertEqual("identity-runtime", result["lead_id"])
        self.assertEqual("unresolved", result["status"])
        self.assertEqual([], result["inspected"]["queries"])
        self.assertEqual("session-lifecycle", result["topics"][0]["id"])
        self.assertEqual(
            [
                "pyproject.toml",
                "src/identity/recovery.py",
                "src/identity/session.py",
            ],
            result["inspected"]["files"],
        )
        self.assertEqual(
            ["src/identity/session.py"],
            result["topics"][0]["files"],
        )
        self.assertEqual(
            ["pyproject.toml"],
            result["supporting"][0]["files"],
        )
        self.assertEqual(
            [
                "src/identity/recovery.py",
                "src/identity/session.py",
            ],
            result["unresolved_leads"][0]["seed_files"],
        )
        self.assertEqual(
            {
                "duplicate_topic_files": 1,
                "duplicate_supporting_files": 3,
                "duplicate_unresolved_seed_files": 2,
                "topic_supporting_overlaps": 1,
            },
            receipt["normalization"],
        )
        self.assertEqual(0o600, self.result.stat().st_mode & 0o777)

    def test_unclassified_packet_seed_is_not_auto_downgraded(self):
        value = self.draft_value()
        value["supporting"] = []
        self.draft.write_text(json.dumps(value), encoding="utf-8")

        error = self.execute(expected=2)

        self.assertIn("leaves seed files unclassified", error["error"])
        self.assertFalse(self.result.exists())

    def test_nonexistent_evidence_is_not_published(self):
        value = self.draft_value()
        value["topics"][0]["files"] = ["src/identity/missing.py"]
        self.draft.write_text(json.dumps(value), encoding="utf-8")

        error = self.execute(expected=2)

        self.assertIn("does not exist", error["error"])
        self.assertFalse(self.result.exists())

    def test_exhaustive_rejects_increment_continuation_fallback(self):
        value = self.draft_value()
        value["unresolved_leads"][0][
            "fallback_kind"
        ] = "increment_continuation"
        self.draft.write_text(json.dumps(value), encoding="utf-8")

        error = self.execute(expected=2)

        self.assertIn(
            "cannot use fallback_kind increment_continuation",
            error["error"],
        )
        self.assertFalse(self.result.exists())

    def test_terminal_refusal_cannot_hide_classification(self):
        value = self.draft_value()
        value["disposition"] = "out_of_scope"
        self.draft.write_text(json.dumps(value), encoding="utf-8")

        error = self.execute(expected=2)

        self.assertIn("cannot publish topics", error["error"])
        self.assertFalse(self.result.exists())


if __name__ == "__main__":
    unittest.main()
