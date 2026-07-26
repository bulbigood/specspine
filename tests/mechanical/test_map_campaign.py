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
        (self.spine / "README.md").write_text("# Architecture\n", encoding="utf-8")
        (self.repository / "src/identity").mkdir(parents=True)
        (self.repository / "src/identity/session.py").write_text(
            "SESSION = True\n", encoding="utf-8"
        )
        (self.repository / "tests").mkdir()
        (self.repository / "tests/session_test.py").write_text(
            "def test_session(): pass\n", encoding="utf-8"
        )
        (self.repository / "pyproject.toml").write_text(
            "[project]\nname='fixture'\n", encoding="utf-8"
        )
        self.run = self.root / "run"
        self.ledger = self.run / "campaign.json"
        self.staging = self.run / "staging/identity"
        self.staging.mkdir(parents=True)
        self.checkpoint = self.run / "identity.json"
        self.checker = self.root / "checker.py"
        self.checker.write_text(
            "import json\nprint(json.dumps([]))\n", encoding="utf-8"
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

    def add_identity(self):
        return self.cli(
            "todo-add",
            str(self.ledger),
            "identity",
            "--question",
            "Map identity sessions",
            "--reason",
            "Session runtime has durable state",
            "--origin",
            "test",
            "--evidence",
            "src/identity",
            "--document",
            "README.md",
        )

    def assign_identity(self, owner="/root/producer-1"):
        return self.cli(
            "assign",
            str(self.ledger),
            "identity",
            "--owner",
            owner,
        )

    def payload(self, *, status="draft_ready", suggestions=True):
        candidates = (
            [{"path": "identity.md", "operation": "create"}]
            if status == "draft_ready"
            else []
        )
        return {
            "status": status,
            "evidence_inspected": ["src/identity/session.py"],
            "findings": ["Session state has an independent lifecycle"],
            "candidates": candidates,
            "discovered_directions": (
                [
                    {
                        "id": "session-recovery",
                        "question": "Who owns failed refresh recovery?",
                        "reason": "Normal session expiry does not explain recovery",
                        "evidence": ["src/identity/session.py"],
                        "documents": ["identity.md"],
                        "excludes": ["login"],
                        "anchor": {
                            "document": "identity.md",
                            "location": "Lifecycle / refresh",
                            "known": "Normal refresh is documented",
                        },
                    }
                ]
                if suggestions
                else []
            ),
            "required_evidence": (
                ["tests/session_recovery_test.py"]
                if status == "needs_more_evidence"
                else []
            ),
            "terminal_reason": (
                "no architectural value: generated compatibility veneer"
                if status == "no_architectural_value"
                else "External ownership decision is required"
                if status == "blocked"
                else None
            ),
        }

    def write_candidate(self, body="# Identity\n"):
        path = self.staging / "identity.md"
        path.write_text(body, encoding="utf-8")
        return path

    def accept(self, payload=None, *, owner="/root/producer-1", expected=0):
        self.checkpoint.write_text(
            json.dumps(payload or self.payload()),
            encoding="utf-8",
        )
        return self.cli(
            "accept",
            str(self.ledger),
            "identity",
            str(self.checkpoint),
            str(self.staging),
            str(self.spine),
            "--owner",
            owner,
            "--checker",
            str(self.checker),
            expected=expected,
        )

    def inventory(self):
        return self.cli(
            "inventory",
            str(self.repository),
            "--spine-root",
            str(self.spine),
        )

    def source_report(self, *, queued=False):
        inventory = self.inventory()
        rows = []
        todo = []
        for value in inventory["areas"]:
            area = value["area"]
            if queued and area == "src/identity":
                rows.append(
                    {
                        "area": area,
                        "classification": "queued",
                        "task": "identity",
                        "reason": "Session state requires mapping",
                    }
                )
                todo.append(
                    {
                        "id": "identity",
                        "question": "Map identity sessions",
                        "reason": "Session state has durable lifecycle",
                        "evidence": ["src/identity"],
                        "documents": ["README.md"],
                        "excludes": [],
                        "anchor": None,
                    }
                )
            elif area == "tests":
                rows.append(
                    {
                        "area": area,
                        "classification": "test-only",
                        "reason": "Test evidence only",
                    }
                )
            else:
                rows.append(
                    {
                        "area": area,
                        "classification": "no-architecture-value",
                        "reason": "Fixture support without durable boundary",
                    }
                )
        return {
            "inventory": rows,
            "todo": todo,
            "terminal_reason": (
                None
                if todo
                else "no source-derived ToDo: all fixture areas classified"
            ),
        }

    def record_source(self, *, queued=False, expected=0):
        report = self.run / "source.json"
        report.write_text(
            json.dumps(self.source_report(queued=queued)),
            encoding="utf-8",
        )
        return self.cli(
            "source-pass",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            str(report),
            expected=expected,
        )

    def test_init_is_private_and_schema_has_explicit_todo(self):
        ledger = json.loads(self.ledger.read_text())
        self.assertEqual(2, ledger["schema_version"])
        self.assertEqual({}, ledger["tasks"])
        self.assertEqual(0o600, self.ledger.stat().st_mode & 0o777)

    def test_inventory_is_deterministic_and_excludes_spine(self):
        first = self.inventory()
        second = self.inventory()
        self.assertEqual(first["digest"], second["digest"])
        areas = {value["area"] for value in first["areas"]}
        self.assertIn("src/identity", areas)
        self.assertIn("tests", areas)
        self.assertIn("pyproject.toml", areas)
        self.assertNotIn("specspine", areas)

    def test_source_pass_rejects_an_unclassified_area(self):
        report = self.source_report()
        report["inventory"].pop()
        path = self.run / "incomplete-source.json"
        path.write_text(json.dumps(report), encoding="utf-8")

        error = self.cli(
            "source-pass",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            str(path),
            expected=2,
        )

        self.assertIn("classify every deterministic inventory area", error["error"])

    def test_source_pass_adds_persistent_todo(self):
        receipt = self.record_source(queued=True)
        self.assertEqual(["identity"], receipt["added_todo"])
        ready = self.cli("ready", str(self.ledger))
        self.assertEqual(["identity"], ready["ready"])

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
        report = self.run / "source-existing.json"
        report.write_text(json.dumps(self.source_report()), encoding="utf-8")

        error = self.cli(
            "source-pass",
            str(ledger),
            str(self.repository),
            str(self.spine),
            str(report),
            expected=2,
        )

        self.assertIn("seed-from-spine", error["error"])

    def test_documentation_seed_requires_complete_markdown_inventory(self):
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
        plan = self.run / "plan.json"
        plan.write_text(
            json.dumps(
                {
                    "evidence_inspected": ["README.md"],
                    "todo": [],
                    "terminal_reason": (
                        "no documentation-derived ToDo: index has no deeper nodes"
                    ),
                }
            ),
            encoding="utf-8",
        )

        receipt = self.cli(
            "seed-from-spine",
            str(ledger),
            str(self.spine),
            str(plan),
        )

        self.assertEqual("seeded", receipt["status"])
        self.assertEqual(1, receipt["documents"])

    def test_one_producer_can_run_only_one_task(self):
        self.add_identity()
        self.assign_identity()
        self.cli("release", str(self.ledger), "identity")

        error = self.cli(
            "assign",
            str(self.ledger),
            "identity",
            "--owner",
            "/root/producer-1",
            expected=2,
        )

        self.assertIn("one producer may run only one task", error["error"])

    def test_draft_publication_records_suggestions_but_not_todo(self):
        self.add_identity()
        self.assign_identity()
        source = self.write_candidate()

        receipt = self.accept()

        self.assertEqual("published", receipt["task_state"])
        self.assertEqual(["session-recovery"], receipt["suggestions_pending_review"])
        self.assertFalse(source.exists())
        self.assertTrue((self.spine / "identity.md").is_file())
        ready = self.cli("ready", str(self.ledger))
        self.assertEqual([], ready["ready"])
        ledger = json.loads(self.ledger.read_text())
        self.assertNotIn("session-recovery", ledger["tasks"])

    def test_non_draft_status_cannot_publish(self):
        self.add_identity()
        self.assign_identity()
        self.write_candidate()
        payload = self.payload(status="no_architectural_value")
        payload["candidates"] = [{"path": "identity.md", "operation": "create"}]

        error = self.accept(payload, expected=2)

        self.assertIn("must not publish candidates", error["error"])

    def test_no_architectural_value_completes_task(self):
        self.add_identity()
        self.assign_identity()

        receipt = self.accept(
            self.payload(status="no_architectural_value", suggestions=False)
        )

        self.assertEqual("complete", receipt["task_state"])

    def test_needs_more_evidence_returns_task_to_todo_for_fresh_producer(self):
        self.add_identity()
        self.assign_identity()

        receipt = self.accept(
            self.payload(status="needs_more_evidence", suggestions=False)
        )

        self.assertEqual("todo", receipt["task_state"])
        task = self.cli("todo", str(self.ledger))["todo"][0]
        self.assertIn("tests/session_recovery_test.py", task["evidence"])

    def test_live_checker_failure_rolls_back_publication(self):
        self.add_identity()
        self.assign_identity()
        source = self.write_candidate()
        self.checker.write_text(
            "import json, sys\n"
            "findings = [] if '--candidates' in sys.argv else "
            "[{'severity':'error','code':'BROKEN'}]\n"
            "print(json.dumps(findings))\n"
            "raise SystemExit(1 if findings else 0)\n",
            encoding="utf-8",
        )

        self.accept(expected=2)

        self.assertTrue(source.exists())
        self.assertFalse((self.spine / "identity.md").exists())
        ledger = json.loads(self.ledger.read_text())
        self.assertEqual("assigned", ledger["tasks"]["identity"]["state"])

    def publish_identity(self, *, suggestions=True):
        self.add_identity()
        self.assign_identity()
        self.write_candidate()
        return self.accept(self.payload(suggestions=suggestions))

    def integration_report(self, *, suggestions=True, todo=True):
        evidence = sorted(
            path.relative_to(self.spine).as_posix()
            for path in self.spine.rglob("*.md")
        )
        raw_todo = (
            [
                {
                    "id": "session-recovery",
                    "question": "Who owns failed refresh recovery?",
                    "reason": "Integrated lifecycle leaves recovery unresolved",
                    "evidence": ["src/identity/session.py"],
                    "documents": ["identity.md"],
                    "excludes": ["login"],
                    "anchor": {
                        "document": "identity.md",
                        "location": "Lifecycle / refresh",
                        "known": "Normal refresh is documented",
                    },
                }
            ]
            if suggestions and todo
            else []
        )
        return {
            "evidence_inspected": evidence,
            "task_reviews": [
                {
                    "task": "identity",
                    "disposition": "integrated",
                    "reason": "Canonical owner and relationships are coherent",
                }
            ],
            "suggestion_reviews": (
                [
                    {
                        "task": "identity",
                        "suggestion": "session-recovery",
                        "disposition": "queued" if todo else "covered",
                        "todo": "session-recovery" if todo else None,
                        "reason": (
                            "Recovery remains unresolved"
                            if todo
                            else "Integrated failure section answers it"
                        ),
                    }
                ]
                if suggestions
                else []
            ),
            "todo": raw_todo,
            "organization": {
                "status": "flat_sufficient",
                "reason": "Two documents remain directly navigable",
            },
            "terminal_reason": (
                None
                if raw_todo
                else "no integration-derived ToDo: integrated graph is sufficient"
            ),
        }

    def integrate(self, report, expected=0):
        path = self.run / "integration.json"
        path.write_text(json.dumps(report), encoding="utf-8")
        return self.cli(
            "integration-pass",
            str(self.ledger),
            str(self.spine),
            str(path),
            "--checker",
            str(self.checker),
            expected=expected,
        )

    def test_integration_adds_document_derived_todo_atomically(self):
        self.publish_identity()

        receipt = self.integrate(self.integration_report())

        self.assertEqual(["identity"], receipt["reviewed_tasks"])
        self.assertEqual(["session-recovery"], receipt["added_todo"])
        ledger = json.loads(self.ledger.read_text())
        self.assertEqual("complete", ledger["tasks"]["identity"]["state"])
        self.assertEqual("todo", ledger["tasks"]["session-recovery"]["state"])

    def test_integration_must_disposition_every_producer_suggestion(self):
        self.publish_identity()
        report = self.integration_report()
        report["suggestion_reviews"] = []

        error = self.integrate(report, expected=2)

        self.assertIn("disposition every producer suggestion", error["error"])

    def test_empty_ready_list_does_not_hide_unintegrated_publication(self):
        self.publish_identity(suggestions=False)

        summary = self.cli("summary", str(self.ledger))

        self.assertEqual([], summary["ready"])
        self.assertFalse(summary["terminal_gates"]["publications_integrated"])
        self.assertIsNone(summary["terminal"])

    def test_inventory_closed_requires_source_and_empty_integration(self):
        self.record_source()
        report = {
            "evidence_inspected": ["README.md"],
            "task_reviews": [],
            "suggestion_reviews": [],
            "todo": [],
            "organization": {
                "status": "flat_sufficient",
                "reason": "Single index is sufficient for the fixture",
            },
            "terminal_reason": (
                "no integration-derived ToDo: no published or unresolved nodes"
            ),
        }
        self.integrate(report)

        summary = self.cli("summary", str(self.ledger))

        self.assertEqual("inventory_closed", summary["terminal"])
        self.assertTrue(all(summary["terminal_gates"].values()))
        coverage = self.cli("coverage-report", str(self.ledger))
        self.assertEqual("inventory_closed", coverage["coverage_claim"])

    def test_live_spine_change_invalidates_integration_pass(self):
        self.record_source()
        report = {
            "evidence_inspected": ["README.md"],
            "task_reviews": [],
            "suggestion_reviews": [],
            "todo": [],
            "organization": {
                "status": "flat_sufficient",
                "reason": "Single index is sufficient for the fixture",
            },
            "terminal_reason": "no integration-derived ToDo: no unresolved nodes",
        }
        self.integrate(report)
        (self.spine / "README.md").write_text(
            "# Architecture\n\nChanged after integration.\n",
            encoding="utf-8",
        )

        summary = self.cli("summary", str(self.ledger))

        self.assertFalse(summary["terminal_gates"]["integration_current"])
        self.assertIsNone(summary["terminal"])

    def test_repository_change_invalidates_source_inventory(self):
        self.record_source()
        (self.repository / "src/new-area").mkdir()
        (self.repository / "src/new-area/new.py").write_text(
            "NEW = True\n", encoding="utf-8"
        )

        summary = self.cli("summary", str(self.ledger))

        self.assertFalse(summary["terminal_gates"]["source_inventory_current"])

    def test_repository_content_change_invalidates_source_inventory(self):
        self.record_source()
        (self.repository / "src/identity/session.py").write_text(
            "SESSION = False\nRECOVERY = True\n",
            encoding="utf-8",
        )

        summary = self.cli("summary", str(self.ledger))

        self.assertFalse(summary["terminal_gates"]["source_inventory_current"])

    def test_finalize_requires_inventory_closed_and_clean_staging(self):
        self.record_source()
        report = {
            "evidence_inspected": ["README.md"],
            "task_reviews": [],
            "suggestion_reviews": [],
            "todo": [],
            "organization": {
                "status": "flat_sufficient",
                "reason": "Single index is sufficient",
            },
            "terminal_reason": "no integration-derived ToDo: no open depth",
        }
        self.integrate(report)

        receipt = self.cli(
            str(self.ledger),
            str(self.spine),
            "--checker",
            str(self.checker),
            script=FINALIZE,
        )

        self.assertEqual("finalized", receipt["status"])
        self.assertEqual("inventory_closed", receipt["terminal"])


if __name__ == "__main__":
    unittest.main()
