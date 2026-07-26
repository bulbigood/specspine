import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
CAMPAIGN = ROOT / "skills/specspine-map/scripts/campaign.py"
FINALIZE = ROOT / "skills/specspine-map/scripts/finalize_run.py"


class MapCampaignTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repository = self.root / "repository"
        self.spine = self.repository / "specspine"
        self.spine.mkdir(parents=True)
        (self.spine / "README.md").write_text(
            "# Architecture\n\n"
            "- **OBS-architecture-root** — broad system owner.\n"
            "- Candidate evidence: `src/identity`.\n"
            "- Build evidence: `pyproject.toml`.\n",
            encoding="utf-8",
        )
        (self.repository / "src/identity").mkdir(parents=True)
        (self.repository / "src/identity/session.py").write_text(
            "SESSION = True\n",
            encoding="utf-8",
        )
        (self.repository / "tests").mkdir()
        (self.repository / "tests/session_test.py").write_text(
            "def test_session(): pass\n",
            encoding="utf-8",
        )
        (self.repository / "pyproject.toml").write_text(
            "[project]\nname='fixture'\n",
            encoding="utf-8",
        )
        self.run = self.root / "run"
        self.ledger = self.run / "campaign.json"
        self.staging = self.run / "staging"
        self.staging.mkdir(parents=True)
        self.checkpoint = self.run / "checkpoint.json"
        self.checker = self.root / "checker.py"
        self.checker.write_text(
            "import json\nprint(json.dumps([]))\n",
            encoding="utf-8",
        )
        self.cli(
            "init",
            str(self.ledger),
            "--scope",
            "whole repository",
            "--root-question",
            "Map repository",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def cli(self, *arguments, expected=0, script=CAMPAIGN):
        result = subprocess.run(
            [sys.executable, str(script), *arguments],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(expected, result.returncode, result.stderr or result.stdout)
        return json.loads(result.stdout or result.stderr)

    def ledger_value(self):
        return json.loads(self.ledger.read_text(encoding="utf-8"))

    def source_pass(self, *, expected=0):
        return self.cli(
            "source-pass",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            expected=expected,
        )

    def task_for_unit(self, unit):
        ledger = self.ledger_value()
        task_id = ledger["source_pass"]["inventory"][unit]["task"]
        return task_id, ledger["tasks"][task_id]

    def assign(self, task_id, owner="/root/producer-1"):
        return self.cli(
            "assign",
            str(self.ledger),
            task_id,
            "--owner",
            owner,
        )

    def checkpoint_payload(
        self,
        *,
        status,
        evidence,
        candidate=None,
        suggestions=None,
        owner_document="README.md",
        owner_claim_ids=None,
    ):
        return {
            "status": status,
            "evidence_inspected": evidence,
            "findings": ["The bounded unit and its responsibility were inspected"],
            "candidates": (
                [{"path": candidate, "operation": "create"}] if candidate else []
            ),
            "coverage": (
                {
                    "owner_document": owner_document,
                    "owner_claim_ids": owner_claim_ids
                    or ["OBS-architecture-root"],
                    "boundary_summary": (
                        "The owner explicitly accounts for this bounded unit"
                    ),
                }
                if status == "covered_by_owner"
                else None
            ),
            "discovered_directions": suggestions or [],
            "required_evidence": (
                ["src/identity/recovery.py"]
                if status == "needs_more_evidence"
                else []
            ),
            "terminal_reason": (
                "External evidence is unavailable" if status == "blocked" else None
            ),
        }

    def accept(self, task_id, payload, *, owner="/root/producer-1", expected=0):
        self.checkpoint.write_text(json.dumps(payload), encoding="utf-8")
        return self.cli(
            "accept",
            str(self.ledger),
            task_id,
            str(self.checkpoint),
            str(self.staging),
            str(self.spine),
            "--owner",
            owner,
            "--checker",
            str(self.checker),
            expected=expected,
        )

    def covered(self, task_id, evidence, *, owner="/root/producer-1"):
        self.assign(task_id, owner)
        return self.accept(
            task_id,
            self.checkpoint_payload(
                status="covered_by_owner",
                evidence=[evidence],
            ),
            owner=owner,
        )

    def integration_report(self, *, todo=None, omit_suggestions=False):
        ledger = self.ledger_value()
        settled = [
            task
            for task in ledger["tasks"].values()
            if task["state"] in {"published", "review"}
        ]
        reviews = [
            {
                "task": task["id"],
                "disposition": (
                    "already_canonical"
                    if task["state"] == "review"
                    else "integrated"
                ),
                "reason": "Root integration confirmed the producer result",
            }
            for task in settled
        ]
        suggestion_reviews = []
        if not omit_suggestions:
            for task in settled:
                for suggestion in task["producer_suggestions"]:
                    suggestion_reviews.append(
                        {
                            "task": task["id"],
                            "suggestion": suggestion["id"],
                            "disposition": "queued",
                            "todo": suggestion["id"],
                            "reason": "The integrated result leaves this direction open",
                        }
                    )
        raw_todo = todo or []
        return {
            "evidence_inspected": sorted(
                path.relative_to(self.spine).as_posix()
                for path in self.spine.rglob("*.md")
            ),
            "task_reviews": reviews,
            "suggestion_reviews": suggestion_reviews,
            "todo": raw_todo,
            "organization": {
                "status": "flat_sufficient",
                "reason": "The fixture remains directly navigable",
            },
            "terminal_reason": (
                None
                if raw_todo
                else "no integration-derived ToDo: all settled results were reviewed"
            ),
        }

    def integrate(self, report=None, *, expected=0):
        path = self.run / "integration.json"
        path.write_text(
            json.dumps(report or self.integration_report()),
            encoding="utf-8",
        )
        return self.cli(
            "integration-pass",
            str(self.ledger),
            str(self.spine),
            str(path),
            "--checker",
            str(self.checker),
            expected=expected,
        )

    def verify_all_source_units(self):
        self.source_pass()
        ledger = self.ledger_value()
        queued = [
            (area, value["task"])
            for area, value in ledger["source_pass"]["inventory"].items()
            if value["classification"] == "queued"
        ]
        for index, (area, task_id) in enumerate(queued):
            sample = ledger["source_pass"]["inventory"][area]["samples"][0]
            self.covered(task_id, sample, owner=f"/root/producer-{index}")
        self.integrate()

    def test_init_uses_schema_three_and_private_ledger(self):
        ledger = self.ledger_value()
        self.assertEqual(3, ledger["schema_version"])
        self.assertEqual({}, ledger["tasks"])
        self.assertEqual(0o600, self.ledger.stat().st_mode & 0o777)

    def test_inventory_groups_root_manifests_and_excludes_spine(self):
        first = self.cli(
            "inventory",
            str(self.repository),
            "--spine-root",
            str(self.spine),
        )
        second = self.cli(
            "inventory",
            str(self.repository),
            "--spine-root",
            str(self.spine),
        )
        self.assertEqual(first["digest"], second["digest"])
        areas = {value["area"] for value in first["areas"]}
        self.assertEqual(
            {"repository-root/manifests", "src/identity", "tests"},
            areas,
        )

    def test_source_pass_mechanically_queues_every_production_unit(self):
        receipt = self.source_pass()
        self.assertEqual(3, receipt["areas"])
        self.assertEqual(2, receipt["verification_todo"])
        ledger = self.ledger_value()
        self.assertEqual(
            "test-only",
            ledger["source_pass"]["inventory"]["tests"]["classification"],
        )
        for area in ("src/identity", "repository-root/manifests"):
            row = ledger["source_pass"]["inventory"][area]
            self.assertEqual("queued", row["classification"])
            self.assertEqual("todo", ledger["tasks"][row["task"]]["state"])

    def test_broad_existing_owner_cannot_eliminate_verification_todo(self):
        self.source_pass()
        task_id, task = self.task_for_unit("src/identity")
        self.assertIn("README.md", task["documents"])
        self.assertEqual("todo", task["state"])
        self.assertIn(task_id, self.cli("ready", str(self.ledger))["ready"])

    def test_existing_spine_requires_documentation_seed(self):
        ledger = self.run / "existing.json"
        self.cli(
            "init",
            str(ledger),
            "--scope",
            "whole repository",
            "--root-question",
            "Map repository",
            "--spine-state",
            "existing",
        )
        error = self.cli(
            "source-pass",
            str(ledger),
            str(self.repository),
            str(self.spine),
            expected=2,
        )
        self.assertIn("seed-from-spine", error["error"])

    def test_source_pass_is_immutable(self):
        self.source_pass()
        error = self.source_pass(expected=2)
        self.assertIn("immutable", error["error"])

    def test_one_producer_can_run_only_one_task(self):
        self.source_pass()
        first, _ = self.task_for_unit("src/identity")
        second, _ = self.task_for_unit("repository-root/manifests")
        self.assign(first)
        self.cli("release", str(self.ledger), first)
        error = self.cli(
            "assign",
            str(self.ledger),
            second,
            "--owner",
            "/root/producer-1",
            expected=2,
        )
        self.assertIn("one producer may run only one task", error["error"])

    def test_covered_by_owner_requires_existing_semantic_claim(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        error = self.accept(
            task_id,
            self.checkpoint_payload(
                status="covered_by_owner",
                evidence=["src/identity/session.py"],
                owner_claim_ids=["OBS-does-not-exist"],
            ),
            expected=2,
        )
        self.assertIn("claim IDs do not exist", error["error"])

    def test_checkpoint_requires_concrete_evidence_from_task_unit(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        error = self.accept(
            task_id,
            self.checkpoint_payload(
                status="covered_by_owner",
                evidence=["pyproject.toml"],
            ),
            expected=2,
        )
        self.assertIn("every task unit", error["error"])

    def test_covered_by_owner_waits_for_root_integration(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        receipt = self.covered(task_id, "src/identity/session.py")
        self.assertEqual("review", receipt["task_state"])
        summary = self.cli("summary", str(self.ledger))
        self.assertFalse(summary["terminal_gates"]["publications_integrated"])

    def test_draft_publication_records_suggestions_but_not_todo(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        (self.staging / "identity.md").write_text(
            "# Identity\n\n- **OBS-identity-owner** — owner.\n",
            encoding="utf-8",
        )
        suggestion = {
            "id": "session-recovery",
            "question": "Who owns failed refresh recovery?",
            "reason": "Normal refresh does not explain recovery",
            "evidence": ["src/identity/session.py"],
            "documents": ["identity.md"],
            "excludes": [],
            "anchor": {
                "document": "identity.md",
                "location": "Lifecycle",
                "known": "Normal refresh is covered",
            },
        }
        receipt = self.accept(
            task_id,
            self.checkpoint_payload(
                status="draft_ready",
                evidence=["src/identity/session.py"],
                candidate="identity.md",
                suggestions=[suggestion],
            ),
        )
        self.assertEqual("published", receipt["task_state"])
        self.assertEqual(["session-recovery"], receipt["suggestions_pending_review"])
        self.assertNotIn("session-recovery", self.ledger_value()["tasks"])

    def test_needs_more_evidence_returns_task_for_fresh_producer(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        receipt = self.accept(
            task_id,
            self.checkpoint_payload(
                status="needs_more_evidence",
                evidence=["src/identity/session.py"],
            ),
        )
        self.assertEqual("todo", receipt["task_state"])
        self.assertIn(
            "src/identity/recovery.py",
            self.ledger_value()["tasks"][task_id]["evidence"],
        )

    def test_live_checker_failure_rolls_back_publication(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        source = self.staging / "identity.md"
        source.write_text("# Identity\n", encoding="utf-8")
        self.checker.write_text(
            "import json, sys\n"
            "findings = [] if '--candidates' in sys.argv else "
            "[{'severity':'error','code':'BROKEN'}]\n"
            "print(json.dumps(findings))\n"
            "raise SystemExit(1 if findings else 0)\n",
            encoding="utf-8",
        )
        self.accept(
            task_id,
            self.checkpoint_payload(
                status="draft_ready",
                evidence=["src/identity/session.py"],
                candidate="identity.md",
            ),
            expected=2,
        )
        self.assertTrue(source.exists())
        self.assertFalse((self.spine / "identity.md").exists())
        self.assertEqual("assigned", self.ledger_value()["tasks"][task_id]["state"])

    def test_integration_adds_document_derived_todo(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.covered(task_id, "src/identity/session.py")
        new_todo = {
            "id": "session-recovery",
            "question": "Who owns failed refresh recovery?",
            "reason": "Integration exposes unresolved recovery",
            "evidence": ["src/identity/session.py"],
            "documents": ["README.md"],
            "excludes": [],
            "anchor": {
                "document": "README.md",
                "location": "Architecture",
                "known": "Normal ownership is covered",
            },
        }
        report = self.integration_report(todo=[new_todo])
        self.integrate(report)
        self.assertEqual(
            "todo",
            self.ledger_value()["tasks"]["session-recovery"]["state"],
        )

    def test_integration_must_review_every_covered_task(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.covered(task_id, "src/identity/session.py")
        report = self.integration_report()
        report["task_reviews"] = []
        error = self.integrate(report, expected=2)
        self.assertIn("every settled producer task", error["error"])

    def test_inventory_verified_requires_every_unit_and_empty_integration(self):
        self.verify_all_source_units()
        summary = self.cli("summary", str(self.ledger))
        self.assertEqual("inventory_verified", summary["terminal"])
        self.assertTrue(all(summary["terminal_gates"].values()))
        coverage = self.cli("coverage-report", str(self.ledger))
        self.assertEqual("inventory_verified", coverage["coverage_claim"])

    def test_repository_content_change_invalidates_inventory(self):
        self.verify_all_source_units()
        (self.repository / "src/identity/session.py").write_text(
            "SESSION = False\nRECOVERY = True\n",
            encoding="utf-8",
        )
        summary = self.cli("summary", str(self.ledger))
        self.assertFalse(summary["terminal_gates"]["source_inventory_current"])
        self.assertIsNone(summary["terminal"])

    def test_live_spine_change_invalidates_integration(self):
        self.verify_all_source_units()
        (self.spine / "README.md").write_text(
            "# Architecture\n\nChanged after integration.\n",
            encoding="utf-8",
        )
        summary = self.cli("summary", str(self.ledger))
        self.assertFalse(summary["terminal_gates"]["integration_current"])
        self.assertIsNone(summary["terminal"])

    def test_finalize_requires_inventory_verified(self):
        self.verify_all_source_units()
        receipt = self.cli(
            str(self.ledger),
            str(self.spine),
            "--checker",
            str(self.checker),
            script=FINALIZE,
        )
        self.assertEqual("finalized", receipt["status"])
        self.assertEqual("inventory_verified", receipt["terminal"])


if __name__ == "__main__":
    unittest.main()
