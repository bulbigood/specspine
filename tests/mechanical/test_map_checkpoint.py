import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
FRONTIER = ROOT / "skills/specspine-map/scripts/frontier.py"
CHECKPOINT = ROOT / "skills/specspine-map/scripts/checkpoint.py"
FINALIZE = ROOT / "skills/specspine-map/scripts/finalize_run.py"


class MapCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.ledger = self.root / "run/frontier.json"
        self.checkpoint = self.root / "run/checkpoint.json"
        self.cli(
            FRONTIER,
            "init",
            str(self.ledger),
            "--scope",
            "whole repository",
            "--root-question",
            "Map repository",
        )
        self.cli(
            FRONTIER,
            "add",
            str(self.ledger),
            "identity",
            "--parent",
            "root",
            "--question",
            "Map identity",
            "--origin",
            "identity registry",
        )
        self.cli(
            FRONTIER,
            "assign",
            str(self.ledger),
            "identity",
            "--owner",
            "producer-1",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def cli(self, script, *arguments, expected=0):
        result = subprocess.run(
            [sys.executable, str(script), *arguments],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(expected, result.returncode, result.stderr or result.stdout)
        return json.loads(result.stdout or result.stderr)

    def payload(self):
        return {
            "status": "continuing",
            "evidence_inspected": ["src/identity/session.py"],
            "candidates": [
                {"path": "identity/session.md", "operation": "create"}
            ],
            "mapped_responsibilities": ["Application session ownership"],
            "relationships": ["Authentication creates sessions"],
            "source_coverage": [
                {
                    "paths": ["src/identity/session.py"],
                    "classification": "mapped_here",
                    "owner": None,
                    "branch_id": None,
                    "reason": None,
                },
                {
                    "paths": ["src/identity/tokens.py"],
                    "classification": "child_branch",
                    "owner": None,
                    "branch_id": "identity-tokens",
                    "reason": None,
                },
            ],
            "continuation": "Inspect session invalidation",
            "coverage_frontier": [
                {
                    "id": "identity-tokens",
                    "question": "Map identity tokens",
                    "evidence": ["src/identity/tokens.py"],
                    "prerequisite": None,
                    "namespace": "identity",
                    "classification": "fork_candidate",
                    "document": None,
                    "reason": None,
                }
            ],
            "unresolved": [],
            "terminal_reason": None,
        }

    def import_payload(self, payload, expected=0):
        self.checkpoint.write_text(json.dumps(payload), encoding="utf-8")
        return self.cli(
            CHECKPOINT,
            str(self.ledger),
            "identity",
            str(self.checkpoint),
            expected=expected,
        )

    def test_import_is_atomic_and_records_every_frontier_item(self):
        receipt = self.import_payload(self.payload())
        ledger = json.loads(self.ledger.read_text(encoding="utf-8"))

        self.assertEqual(["identity-tokens"], receipt["added_branches"])
        self.assertEqual(
            receipt["digest"],
            ledger["branches"]["identity"]["pending_checkpoint"]["digest"],
        )
        self.assertEqual(
            "queued", ledger["branches"]["identity-tokens"]["state"]
        )
        self.assertEqual(2, ledger["frontier_epoch"])

        repeated = self.import_payload(self.payload())
        self.assertEqual("already_imported", repeated["status"])

    def test_schema_rejects_missing_fields_and_unledgered_child_coverage(self):
        payload = self.payload()
        del payload["relationships"]
        self.import_payload(payload, expected=2)
        ledger = json.loads(self.ledger.read_text(encoding="utf-8"))
        self.assertNotIn("identity-tokens", ledger["branches"])

        payload = self.payload()
        payload["coverage_frontier"] = []
        error = self.import_payload(payload, expected=2)
        self.assertIn("absent from coverage_frontier", error["error"])

    def test_terminal_checkpoint_changes_state_without_publication(self):
        payload = self.payload()
        payload.update(
            status="locally_saturated",
            candidates=[],
            continuation=None,
            source_coverage=[payload["source_coverage"][0]],
            coverage_frontier=[],
            terminal_reason="no useful node: remaining detail is local implementation",
        )
        self.import_payload(payload)
        ledger = json.loads(self.ledger.read_text(encoding="utf-8"))
        self.assertEqual(
            "locally_saturated", ledger["branches"]["identity"]["state"]
        )
        self.assertIsNone(
            ledger["branches"]["identity"].get("pending_checkpoint")
        )

    def test_pending_checkpoint_blocks_state_change_and_resume_discards_it(self):
        self.import_payload(self.payload())
        self.cli(
            FRONTIER,
            "release",
            str(self.ledger),
            "identity",
            expected=2,
        )
        receipt = self.cli(
            FRONTIER, "resume", "--compact", str(self.ledger)
        )
        self.assertEqual(["identity"], receipt["discarded_checkpoints"])
        ledger = json.loads(self.ledger.read_text(encoding="utf-8"))
        self.assertEqual("queued", ledger["branches"]["identity"]["state"])
        self.assertIsNone(
            ledger["branches"]["identity"].get("pending_checkpoint")
        )

    def test_pending_checkpoint_can_be_discarded_for_corrected_report(self):
        receipt = self.import_payload(self.payload())
        self.cli(
            FRONTIER,
            "reserve",
            str(self.ledger),
            "identity",
            "--path",
            "identity/session.md",
        )
        self.cli(
            FRONTIER,
            "discard-checkpoint",
            "--compact",
            str(self.ledger),
            "identity",
        )
        ledger = json.loads(self.ledger.read_text(encoding="utf-8"))
        identity = ledger["branches"]["identity"]
        self.assertIsNone(identity.get("pending_checkpoint"))
        self.assertEqual([], identity["reservations"])
        self.assertEqual(
            receipt["digest"], identity["discarded_checkpoint_digest"]
        )

    def test_new_frontier_invalidates_scope_discovery(self):
        terminal = self.payload()
        terminal.update(
            status="locally_saturated",
            candidates=[],
            continuation=None,
            source_coverage=[terminal["source_coverage"][0]],
            coverage_frontier=[],
            terminal_reason="no useful node: evidence exhausted",
        )
        self.import_payload(terminal)
        self.cli(
            FRONTIER,
            "state",
            str(self.ledger),
            "identity",
            "complete",
        )
        self.cli(
            FRONTIER,
            "discovery-pass",
            str(self.ledger),
            "--evidence",
            "composition roots and registries",
        )
        self.cli(
            FRONTIER,
            "add",
            str(self.ledger),
            "runtime",
            "--parent",
            "root",
            "--question",
            "Map runtime",
            "--origin",
            "main entry point",
        )
        self.cli(
            FRONTIER,
            "state",
            str(self.ledger),
            "root",
            "locally_saturated",
            "--terminal-reason",
            "no useful node: scope signals exhausted",
            expected=2,
        )


class MapFinalizeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.ledger = self.root / "run/frontier.json"
        self.spine = self.root / "specspine"
        self.staging = self.root / "run/staging"
        self.spine.mkdir(parents=True)
        self.staging.mkdir(parents=True)
        (self.spine / "README.md").write_text(
            "# Architecture\n\nProject architecture.\n", encoding="utf-8"
        )
        self.cli(
            FRONTIER,
            "init",
            str(self.ledger),
            "--scope",
            "whole repository",
            "--root-question",
            "Map repository",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def cli(self, script, *arguments, expected=0):
        result = subprocess.run(
            [sys.executable, str(script), *arguments],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(expected, result.returncode, result.stderr or result.stdout)
        return json.loads(result.stdout or result.stderr)

    def finish_root(self):
        self.cli(
            FRONTIER,
            "discovery-pass",
            str(self.ledger),
            "--evidence",
            "all architecture signal classes",
        )
        self.cli(
            FRONTIER,
            "state",
            str(self.ledger),
            "root",
            "locally_saturated",
            "--terminal-reason",
            "no useful node: scope is saturated",
        )
        self.cli(
            FRONTIER, "state", str(self.ledger), "root", "complete"
        )

    def test_finalize_requires_complete_frontier_and_empty_staging(self):
        self.cli(
            FINALIZE,
            str(self.ledger),
            str(self.spine),
            "--staging-root",
            str(self.staging),
            expected=2,
        )
        self.finish_root()
        receipt = self.cli(
            FINALIZE,
            str(self.ledger),
            str(self.spine),
            "--staging-root",
            str(self.staging),
        )
        self.assertEqual("finalized", receipt["status"])

        (self.staging / "leftover.md").write_text("draft", encoding="utf-8")
        self.cli(
            FINALIZE,
            str(self.ledger),
            str(self.spine),
            "--staging-root",
            str(self.staging),
            expected=2,
        )


if __name__ == "__main__":
    unittest.main()
