import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "skills/specspine-map/scripts/frontier.py"


class MapExhaustiveFrontierTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.ledger = Path(self.temporary.name) / "frontier.json"
        self.cli(
            "init",
            str(self.ledger),
            "--scope",
            "whole repository",
            "--root-question",
            "Map the repository",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def cli(self, *arguments, expected=0):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(expected, result.returncode, result.stderr or result.stdout)
        stream = result.stdout or result.stderr
        return json.loads(stream)

    def add(self, branch_id="identity", parent="root"):
        return self.cli(
            "add",
            str(self.ledger),
            branch_id,
            "--parent",
            parent,
            "--question",
            f"Map {branch_id}",
            "--origin",
            "router registry",
            "--namespace",
            "architecture",
        )

    def saturate(self, branch_id):
        self.cli("assign", str(self.ledger), branch_id, "--owner", "producer-1")
        self.cli(
            "state",
            str(self.ledger),
            branch_id,
            "locally_saturated",
            "--terminal-reason",
            "no useful node: evidence exhausted",
        )

    def test_init_is_private_atomic_json(self):
        ledger = json.loads(self.ledger.read_text(encoding="utf-8"))
        self.assertEqual(2, ledger["schema_version"])
        self.assertEqual("active", ledger["branches"]["root"]["state"])
        self.assertEqual(0o600, self.ledger.stat().st_mode & 0o777)
        self.assertFalse(list(self.ledger.parent.glob("*.tmp")))

    def test_add_is_idempotent_but_conflicts_are_rejected(self):
        first = self.add()
        revision = first["revision"]
        second = self.add()
        self.assertEqual(revision, second["revision"])
        self.cli(
            "add",
            str(self.ledger),
            "identity",
            "--parent",
            "root",
            "--question",
            "Different question",
            "--origin",
            "router registry",
            expected=2,
        )

    def test_failed_start_and_resolved_blocker_return_to_queue(self):
        self.add()
        self.cli("assign", str(self.ledger), "identity", "--owner", "producer-1")
        ledger = self.cli("release", str(self.ledger), "identity")
        self.assertEqual("queued", ledger["branches"]["identity"]["state"])
        self.cli(
            "state",
            str(self.ledger),
            "identity",
            "blocked",
            "--terminal-reason",
            "needs operator authority",
        )
        ledger = self.cli("release", str(self.ledger), "identity")
        self.assertEqual("queued", ledger["branches"]["identity"]["state"])

    def test_publication_paths_and_replacement_reservations_are_durable(self):
        self.add()
        self.cli("assign", str(self.ledger), "identity", "--owner", "producer-1")
        ledger = self.cli(
            "reserve",
            str(self.ledger),
            "identity",
            "--path",
            "architecture/identity.md",
            "--path",
            "README.md",
            "--replace-existing",
            "README.md",
        )
        ledger = self.cli(
            "publish",
            str(self.ledger),
            "identity",
            "--path",
            "architecture/identity.md",
            "--path",
            "README.md",
        )
        identity = ledger["branches"]["identity"]
        self.assertEqual(
            ["README.md", "architecture/identity.md"], identity["published"]
        )
        self.assertEqual(
            ["README.md", "architecture/identity.md"], identity["reservations"]
        )
        self.assertEqual(["README.md"], identity["replacements"])
        self.assertEqual([], self.cli("audit", str(self.ledger)))

    def test_publication_rejects_unsafe_or_unpublished_reservations(self):
        self.add()
        self.cli("assign", str(self.ledger), "identity", "--owner", "producer-1")
        self.cli(
            "reserve",
            str(self.ledger),
            "identity",
            "--path",
            "../outside.md",
            expected=2,
        )
        self.cli(
            "reserve",
            str(self.ledger),
            "identity",
            "--path",
            "identity.md",
            "--replace-existing",
            "other.md",
            expected=2,
        )

    def test_reservations_are_globally_exclusive_and_releasable(self):
        self.add("identity")
        self.add("tokens")
        self.cli(
            "reserve",
            str(self.ledger),
            "identity",
            "--path",
            "identity.md",
        )
        self.cli(
            "reserve",
            str(self.ledger),
            "tokens",
            "--path",
            "identity.md",
            expected=2,
        )
        self.cli(
            "unreserve",
            str(self.ledger),
            "identity",
            "--path",
            "identity.md",
        )
        ledger = self.cli(
            "reserve",
            str(self.ledger),
            "tokens",
            "--path",
            "identity.md",
        )
        self.assertEqual(
            ["identity.md"], ledger["branches"]["tokens"]["reservations"]
        )

    def test_publish_requires_prior_branch_reservation(self):
        self.add()
        self.cli("assign", str(self.ledger), "identity", "--owner", "local")
        self.cli(
            "publish",
            str(self.ledger),
            "identity",
            "--path",
            "identity.md",
            expected=2,
        )

    def test_terminal_reason_and_children_gate_completion(self):
        self.add()
        self.add("identity-tokens", "identity")
        self.cli("assign", str(self.ledger), "identity", "--owner", "producer-1")
        self.cli(
            "state",
            str(self.ledger),
            "identity",
            "locally_saturated",
            expected=2,
        )
        self.cli(
            "state",
            str(self.ledger),
            "identity",
            "locally_saturated",
            "--terminal-reason",
            "no useful node",
            expected=2,
        )
        self.cli(
            "state",
            str(self.ledger),
            "identity",
            "locally_saturated",
            "--terminal-reason",
            "no useful node: inspected evidence is implementation detail",
        )
        self.cli(
            "state", str(self.ledger), "identity", "complete", expected=2
        )
        self.saturate("identity-tokens")
        self.cli("state", str(self.ledger), "identity-tokens", "complete")
        ledger = self.cli("state", str(self.ledger), "identity", "complete")
        self.assertEqual("complete", ledger["branches"]["identity"]["state"])

    def test_documented_branch_is_complete_with_exact_owner(self):
        ledger = self.cli(
            "documented",
            str(self.ledger),
            "runtime",
            "--parent",
            "root",
            "--question",
            "Map runtime composition",
            "--document",
            "architecture/runtime.md",
            "--origin",
            "Spine index",
        )
        runtime = ledger["branches"]["runtime"]
        self.assertEqual("complete", runtime["state"])
        self.assertEqual("already_documented", runtime["resolution"])
        self.assertEqual("architecture/runtime.md", runtime["document"])

    def test_final_audit_blocks_every_noncomplete_state(self):
        self.add()
        findings = self.cli(
            "audit", str(self.ledger), "--final", expected=1
        )
        self.assertEqual(
            {"active", "queued"},
            {
                finding["message"].removeprefix("state is ")
                for finding in findings
                if finding["code"] == "unfinished"
            },
        )
        self.saturate("identity")
        self.cli("state", str(self.ledger), "identity", "complete")
        self.cli(
            "discovery-pass",
            str(self.ledger),
            "--evidence",
            "composition roots and registries rechecked",
        )
        self.cli(
            "state",
            str(self.ledger),
            "root",
            "locally_saturated",
            "--terminal-reason",
            "no useful node: top-level signals exhausted",
        )
        self.cli("state", str(self.ledger), "root", "complete")
        self.assertEqual([], self.cli("audit", str(self.ledger), "--final"))

    def test_ready_respects_prerequisite(self):
        self.add("identity")
        self.cli(
            "add",
            str(self.ledger),
            "tokens",
            "--parent",
            "root",
            "--question",
            "Map tokens",
            "--origin",
            "identity API",
            "--prerequisite",
            "identity",
        )
        self.assertEqual(["identity"], [item["id"] for item in self.cli(
            "ready", str(self.ledger)
        )])
        self.saturate("identity")
        self.cli("state", str(self.ledger), "identity", "complete")
        self.assertEqual(["tokens"], [item["id"] for item in self.cli(
            "ready", str(self.ledger)
        )])

    def test_compact_mutation_receipt_and_summary_bound_output(self):
        receipt = self.cli(
            "add",
            "--compact",
            str(self.ledger),
            "identity",
            "--parent",
            "root",
            "--question",
            "Map identity",
            "--origin",
            "router registry",
        )
        self.assertEqual("ok", receipt["status"])
        self.assertEqual("add", receipt["command"])
        self.assertEqual("identity", receipt["branch"])
        self.assertNotIn("branches", receipt)

        summary = self.cli("summary", str(self.ledger))
        self.assertEqual(["identity"], summary["ready"])
        self.assertEqual([], summary["active"])
        self.assertIsNone(summary["terminal"])


if __name__ == "__main__":
    unittest.main()
