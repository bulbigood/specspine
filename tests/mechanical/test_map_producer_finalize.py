import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
FINALIZE = ROOT / "skills/specspine-map/scripts/producer_finalize.py"


class ProducerFinalizeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.spine = self.root / "specspine"
        self.spine.mkdir()
        (self.spine / "README.md").write_text("# Architecture\n", encoding="utf-8")
        self.repository = self.root / "repository"
        (self.repository / "src/identity").mkdir(parents=True)
        (self.repository / "src/identity/session.py").write_text(
            "SESSION = True\n",
            encoding="utf-8",
        )
        runtime = self.repository / ".specspine" / "map" / "test-run"
        self.work = runtime / "work" / "task-1"
        (self.work / "staging").mkdir(parents=True)
        self.handoff = runtime / "handoffs" / "task-1"
        self.packet = runtime / "packet.json"
        self.packet.write_text(
            json.dumps(
                {
                    "campaign_id": "campaign",
                    "task": {
                        "id": "verify-identity",
                        "origin": "source-pass",
                        "units": ["src/identity"],
                        "planned_document": "identity.md",
                        "planned_relationships": [],
                        "anchor": None,
                        "evidence_strata": [
                            {
                                "id": "entrypoint",
                                "sample": "src/identity/session.py",
                            }
                        ],
                    },
                }
            ),
            encoding="utf-8",
        )
        self.checker = self.root / "checker.py"
        self.checker.write_text(
            "import json\nprint(json.dumps([]))\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def checkpoint(self, **overrides):
        value = {
            "outcome": "draft",
            "evidence": ["src/identity/session.py"],
            "summary": "Identity owns the session lifecycle.",
            "directions": [],
        }
        value.update(overrides)
        (self.work / "checkpoint.json").write_text(
            json.dumps(value),
            encoding="utf-8",
        )

    def candidate(self):
        (self.work / "staging" / "identity.md").write_text(
            "# Identity\n\n"
            "<!-- specspine:evidence-baseline "
            "source=fixture; inspected=2026-07-28 -->\n"
            "- **OBS-identity-session** — `src/identity/session.py`.\n",
            encoding="utf-8",
        )

    def execute(self, *, expected=0):
        completed = subprocess.run(
            [
                sys.executable,
                str(FINALIZE),
                str(self.packet),
                str(self.work),
                str(self.handoff),
                str(self.repository),
                str(self.spine),
                "--checker",
                str(self.checker),
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

    def test_clean_draft_moves_whole_package_atomically(self):
        self.candidate()
        self.checkpoint()

        receipt = self.execute()

        self.assertEqual("ready", receipt["status"])
        self.assertEqual("clean", receipt["mechanical_preflight"])
        self.assertFalse(self.work.exists())
        self.assertTrue((self.handoff / "checkpoint.json").is_file())
        self.assertTrue((self.handoff / "staging" / "identity.md").is_file())

    def test_rejects_work_outside_workspace_map_root(self):
        outside = self.root / "outside" / "task-1"
        shutil.copytree(self.work, outside)
        self.work = outside
        self.candidate()
        self.checkpoint()

        error = self.execute(expected=2)

        self.assertIn("workspace Map runtime root", error["error"])

    def test_checker_failure_keeps_private_work_and_exposes_no_handoff(self):
        self.candidate()
        self.checkpoint()
        self.checker.write_text(
            "import json\n"
            "print(json.dumps([{'severity':'error','code':'BROKEN'}]))\n"
            "raise SystemExit(1)\n",
            encoding="utf-8",
        )

        error = self.execute(expected=2)

        self.assertIn("candidate preflight failed", error["error"])
        self.assertTrue(self.work.is_dir())
        self.assertFalse(self.handoff.exists())

    def test_missing_evidence_sample_keeps_result_private(self):
        self.candidate()
        self.checkpoint(evidence=["src/identity/other.py"])

        error = self.execute(expected=2)

        self.assertIn("every packet evidence sample", error["error"])
        self.assertTrue(self.work.is_dir())
        self.assertFalse(self.handoff.exists())

    def test_non_draft_checkpoint_requires_empty_staging(self):
        self.candidate()
        self.checkpoint(
            outcome="retry",
            need=["src/identity/recovery.py"],
            directions=[],
        )

        error = self.execute(expected=2)

        self.assertIn("retry must not publish staged files", error["error"])
        self.assertTrue(self.work.is_dir())
        self.assertFalse(self.handoff.exists())

    def test_covered_checkpoint_is_atomically_handed_off_without_checker(self):
        self.checker.write_text("raise SystemExit(99)\n", encoding="utf-8")
        (self.spine / "identity.md").write_text(
            "# Identity\n\n"
            "- **OBS-identity-session** — `src/identity/session.py`.\n",
            encoding="utf-8",
        )
        self.checkpoint(
            outcome="covered",
            owner={
                "document": "identity.md",
                "claims": ["OBS-identity-session"],
            },
        )

        receipt = self.execute()

        self.assertEqual("not_applicable", receipt["mechanical_preflight"])
        self.assertFalse(self.work.exists())
        self.assertTrue((self.handoff / "checkpoint.json").is_file())

    def test_invalid_covered_owner_stays_private(self):
        self.checkpoint(
            outcome="covered",
            owner={
                "document": "missing.md",
                "claims": ["OBS-identity-session"],
            },
        )

        error = self.execute(expected=2)

        self.assertIn("owner document does not exist", error["error"])
        self.assertTrue(self.work.is_dir())
        self.assertFalse(self.handoff.exists())

    def test_integration_task_rejects_scope_covered_outcome(self):
        packet = json.loads(self.packet.read_text(encoding="utf-8"))
        packet["task"]["origin"] = "integration-1"
        packet["task"]["units"] = []
        packet["task"]["anchor"] = {
            "document": "identity.md",
            "location": "Open questions",
            "known": "The runtime owner is unknown",
        }
        self.packet.write_text(json.dumps(packet), encoding="utf-8")
        (self.spine / "identity.md").write_text(
            "# Identity\n\n"
            "- **OBS-identity-session** — `src/identity/session.py`.\n",
            encoding="utf-8",
        )
        self.checkpoint(
            outcome="covered",
            owner={
                "document": "identity.md",
                "claims": ["OBS-identity-session"],
            },
        )

        error = self.execute(expected=2)

        self.assertIn("covered is valid only for scope verification", error["error"])
        self.assertTrue(self.work.is_dir())

    def test_integration_task_accepts_answered_outcome(self):
        packet = json.loads(self.packet.read_text(encoding="utf-8"))
        packet["task"]["origin"] = "integration-1"
        packet["task"]["units"] = []
        packet["task"]["anchor"] = {
            "document": "identity.md",
            "location": "Open questions",
            "known": "The runtime owner is unknown",
        }
        self.packet.write_text(json.dumps(packet), encoding="utf-8")
        (self.spine / "identity.md").write_text(
            "# Identity\n\n"
            "- **OBS-identity-session** — `src/identity/session.py`.\n",
            encoding="utf-8",
        )
        self.checkpoint(
            outcome="answered",
            owner={
                "document": "identity.md",
                "claims": ["OBS-identity-session"],
            },
        )

        receipt = self.execute()

        self.assertEqual("answered", receipt["outcome"])
        self.assertFalse(self.work.exists())

    def test_real_checker_accepts_publish_ready_candidate(self):
        shutil.rmtree(self.spine)
        shutil.copytree(
            ROOT / "tests/eval/fixtures/map-modes-six-area/specspine",
            self.spine,
        )
        self.checker = ROOT / "skills/specspine-map/scripts/check_spine.py"
        (self.work / "staging" / "identity.md").write_text(
            "# Identity\n\n"
            "**ID:** `identity` · **Kind:** `concept`\n\n"
            "Documents the observed identity session boundary.\n\n"
            "## Responsibility\n\n"
            "Owns the observed session lifecycle evidenced by "
            "`src/identity/session.py`.\n\n"
            "<!-- specspine:evidence-baseline "
            "source=fixture; inspected=2026-07-28 -->\n"
            "<!-- specspine:semantic-ids:begin -->\n"
            "## Observed\n\n"
            "- **OBS-identity-session** — A session implementation exists. "
            "Evidence: `src/identity/session.py`.\n"
            "<!-- specspine:semantic-ids:end -->\n",
            encoding="utf-8",
        )
        self.checkpoint()

        receipt = self.execute()

        self.assertEqual("clean", receipt["mechanical_preflight"])
        self.assertTrue((self.handoff / "staging" / "identity.md").is_file())

    def test_real_checker_rejects_shortened_candidate_evidence_path(self):
        shutil.rmtree(self.spine)
        shutil.copytree(
            ROOT / "tests/eval/fixtures/map-modes-six-area/specspine",
            self.spine,
        )
        self.checker = ROOT / "skills/specspine-map/scripts/check_spine.py"
        (self.work / "staging" / "identity.md").write_text(
            "# Identity\n\n"
            "**ID:** `identity` · **Kind:** `concept`\n\n"
            "Documents the observed identity session boundary.\n\n"
            "## Responsibility\n\n"
            "Owns the observed session lifecycle.\n\n"
            "<!-- specspine:evidence-baseline "
            "source=fixture; inspected=2026-07-28 -->\n"
            "<!-- specspine:semantic-ids:begin -->\n"
            "## Observed\n\n"
            "- **OBS-identity-session** — A session implementation exists. "
            "Evidence: `session.py`.\n"
            "<!-- specspine:semantic-ids:end -->\n",
            encoding="utf-8",
        )
        self.checkpoint()

        error = self.execute(expected=2)

        self.assertIn("EVIDENCE_PATH_MISSING", error["error"])
        self.assertTrue(self.work.is_dir())
        self.assertFalse(self.handoff.exists())

    def test_draft_requires_semantic_observation_and_baseline(self):
        (self.work / "staging" / "identity.md").write_text(
            "# Identity\n\n"
            "<!-- specspine:evidence-baseline "
            "source=fixture; inspected=2026-07-28 -->\n"
            "Observed session implementation.\n",
            encoding="utf-8",
        )
        self.checkpoint()

        error = self.execute(expected=2)

        self.assertIn("semantic OBS definition", error["error"])
        self.assertTrue(self.work.is_dir())

    def test_answered_rejects_normative_owner_claim(self):
        packet = json.loads(self.packet.read_text(encoding="utf-8"))
        packet["task"]["origin"] = "integration-1"
        packet["task"]["units"] = []
        packet["task"]["anchor"] = {
            "document": "identity.md",
            "location": "Open questions",
            "known": "The runtime owner is unknown",
        }
        self.packet.write_text(json.dumps(packet), encoding="utf-8")
        (self.spine / "identity.md").write_text(
            "# Identity\n\n"
            "- **GUA-identity-session** — Sessions remain available.\n",
            encoding="utf-8",
        )
        self.checkpoint(
            outcome="answered",
            owner={
                "document": "identity.md",
                "claims": ["GUA-identity-session"],
            },
        )

        error = self.execute(expected=2)

        self.assertIn("repository observations", error["error"])


if __name__ == "__main__":
    unittest.main()
