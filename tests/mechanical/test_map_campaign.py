import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).parents[2]
CAMPAIGN = ROOT / "skills/specspine-map/scripts/campaign.py"
SYNTHESIS = ROOT / "skills/specspine-map/scripts/synthesis.py"
FINALIZE = ROOT / "skills/specspine-map/scripts/finalize_run.py"
CAMPAIGN_SPEC = importlib.util.spec_from_file_location("map_campaign", CAMPAIGN)
assert CAMPAIGN_SPEC is not None and CAMPAIGN_SPEC.loader is not None
CAMPAIGN_MODULE = importlib.util.module_from_spec(CAMPAIGN_SPEC)
CAMPAIGN_SPEC.loader.exec_module(CAMPAIGN_MODULE)


class MapCampaignTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repository = self.root / "repository"
        self.spine = self.repository / "specspine"
        self.spine.mkdir(parents=True)
        (self.spine / "_INDEX.md").write_text(
            "# Architecture\n\n"
            "**ID:** `project-architecture` · **Kind:** `index`\n\n"
            "Architecture fixture.\n\n"
            "## Contents\n\n"
            "- [Architecture](architecture.md)\n"
            "- [specspine.json](specspine.json)\n\n",
            encoding="utf-8",
        )
        (self.spine / "architecture.md").write_text(
            "# Architecture\n\n"
            "**ID:** `architecture-root` · **Kind:** `system`\n\n"
            "Broad system architecture owner.\n\n"
            "## Responsibility\n\n"
            "Owns the broad system boundary.\n\n"
            "<!-- specspine:evidence-baseline "
            "source=fixture; inspected=2026-07-28 -->\n"
            "<!-- specspine:semantic-ids:begin -->\n"
            "## Observed\n\n"
            "- **OBS-architecture-root** — Broad system owner. "
            "Evidence: `src/identity/session.py`, `pyproject.toml`.\n"
            "<!-- specspine:semantic-ids:end -->\n",
            encoding="utf-8",
        )
        (self.spine / "specspine.json").write_text(
            json.dumps(
                {
                    "specspine": 3,
                    "project": "fixture",
                    "implementation_freedom": "contract-equivalent",
                    "areas": [{
                        "owner": "architecture-root",
                        "facets": {
                            "architecture": "partial",
                            "behavior": "partial",
                            "interfaces": "not-applicable",
                            "data": "not-applicable",
                            "failure": "partial",
                            "quality": "not-applicable",
                            "verification": "partial",
                        },
                        "blockers": [],
                    }],
                    "assets": [],
                }
            ),
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
        self.run = self.repository / ".specspine" / "map" / "test-run"
        self.ledger = self.run / "campaign.json"
        self.staging = self.run / "staging"
        self.staging.mkdir(parents=True)
        self.checkpoint = self.run / "checkpoint.json"
        self.checker = self.root / "checker.py"
        self.checker.write_text(
            "import json\nprint(json.dumps([]))\n",
            encoding="utf-8",
        )
        self.operation = self.run / "operation.json"
        self.operation.parent.mkdir(parents=True, exist_ok=True)
        self.operation.write_text(
            json.dumps(
                {
                    "scope": {
                        "kind": "repository",
                        "title": "Whole repository",
                        "question": "Map the whole repository",
                        "inclusion_rule": "All repository architecture is in scope.",
                        "exclusion_rule": (
                            "Only mechanically excluded support is out of scope."
                        ),
                    },
                    "completion": {"kind": "exhaustive"},
                }
            ),
            encoding="utf-8",
        )
        self.cli(
            "init",
            str(self.ledger),
            str(self.operation),
            "--repository-root",
            str(self.repository),
        )
        self.integration_index = 0
        self.current_workspace = None

    def tearDown(self):
        self.temporary.cleanup()

    def cli(self, *arguments, expected=0, script=CAMPAIGN):
        arguments = list(arguments)
        if (
            script == CAMPAIGN
            and arguments
            and arguments[0] == "discovery-start"
            and "--initial-plan" not in arguments
        ):
            ledger = json.loads(Path(arguments[1]).read_text(encoding="utf-8"))
            if ledger["operation"]["scope"]["kind"] == "semantic":
                plan = Path(arguments[4]).parent / (
                    Path(arguments[4]).name + "-initial-plan.json"
                )
                plan.write_text(
                    json.dumps(
                        {
                            "discovery_plan_version": 1,
                            "rationale": "Focused fixture requires one scout.",
                            "leads": [
                                {
                                    "id": "scope-root",
                                    "title": "Sessions",
                                    "question": (
                                        "Map sessions and directly related services"
                                    ),
                                    "reason": (
                                        "The fixture has one semantic boundary."
                                    ),
                                }
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                arguments.extend(["--initial-plan", str(plan)])
        if script == CAMPAIGN and arguments and arguments[0] == "source-pass":
            option = arguments.index("--topic-plan")
            self.enrich_graph_mapping(Path(arguments[option + 1]))
        if script == SYNTHESIS and arguments and arguments[0] == "materialize":
            self.enrich_graph_mapping(Path(arguments[2]))
        result = subprocess.run(
            [sys.executable, str(script), *arguments],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(expected, result.returncode, result.stderr or result.stdout)
        return json.loads(result.stdout or result.stderr)

    @staticmethod
    def enrich_graph_value(value):
        semantic = [
            row
            for key in ("topics", "covered")
            for row in value.get(key, [])
            if isinstance(row, dict) and isinstance(row.get("id"), str)
        ]
        ids = [row["id"] for row in semantic]
        for index, row in enumerate(semantic):
            row.setdefault(
                "document",
                (
                    row.get("coverage", [{}])[0].get("document")
                    if row.get("coverage")
                    else f"topics/{row['id']}.md"
                ),
            )
            relationships = []
            if len(ids) > 1:
                target = ids[index + 1] if index + 1 < len(ids) else ids[index - 1]
                relationships = [
                    {
                        "type": "related-to",
                        "target": target,
                        "reason": "Fixture semantic graph connection.",
                    }
                ]
            if "relationships" not in row or (
                len(ids) > 1 and not row["relationships"]
            ):
                row["relationships"] = relationships

    @classmethod
    def enrich_graph_mapping(cls, path):
        if not path.is_file():
            return
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        if isinstance(value, dict):
            cls.enrich_graph_value(value)
            path.write_text(json.dumps(value), encoding="utf-8")

    def ledger_value(self):
        return json.loads(self.ledger.read_text(encoding="utf-8"))

    def inventory(self):
        return CAMPAIGN_MODULE.repository_inventory(
            self.repository,
            spine_root=self.spine,
        )

    def set_semantic_operation(self, *, completion="exhaustive", intent=None):
        ledger = self.ledger_value()
        ledger["operation"] = {
            "scope": {
                "kind": "semantic",
                "title": "Sessions",
                "question": "Map sessions and directly related services",
                "inclusion_rule": "Direct session lifecycle responsibilities.",
                "exclusion_rule": "Unrelated services.",
            },
            "completion": (
                {"kind": completion, "intent": intent}
                if completion == "increment"
                else {"kind": "exhaustive"}
            ),
        }
        self.ledger.write_text(json.dumps(ledger), encoding="utf-8")

    def copy_discovery_state(self, target):
        corpus = self.discovery_corpus_path()
        source = self.ledger_value()
        ledger = json.loads(target.read_text(encoding="utf-8"))
        ledger["discovery"] = source["discovery"]
        target.write_text(json.dumps(ledger), encoding="utf-8")
        return corpus

    def draft_evidence(self, task_id):
        marker = self.ledger_value()["tasks"][task_id]["evidence_baseline"]
        return f"\n{marker}\n"

    def add_spine_candidate(self, filename, document_id, evidence):
        (self.spine / filename).write_text(
            f"# {document_id}\n\n"
            f"**ID:** `{document_id}` · **Kind:** `concept`\n\n"
            "Candidate owner fixture.\n\n"
            "## Responsibility\n\n"
            "Owns the candidate boundary.\n\n"
            "<!-- specspine:evidence-baseline "
            "source=fixture; inspected=2026-07-28 -->\n"
            "<!-- specspine:semantic-ids:begin -->\n"
            "## Observed\n\n"
            f"- **OBS-{document_id}** — Candidate evidence exists. "
            f"Evidence: `{evidence}`.\n"
            "<!-- specspine:semantic-ids:end -->\n",
            encoding="utf-8",
        )
        manifest_path = self.spine / "specspine.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["areas"].append(
            {
                "owner": document_id,
                "facets": {
                    name: "missing"
                    for name in (
                        "architecture",
                        "behavior",
                        "interfaces",
                        "data",
                        "failure",
                        "quality",
                        "verification",
                    )
                },
                "blockers": [],
            }
        )
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "shared/scripts/rebuild_indexes.py"),
                str(self.spine),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    def topic_plan_path(self):
        inventory = self.inventory()
        grouped = {}
        for path in inventory["production_files"]:
            value = Path(path)
            unit = (
                "repository-root/manifests"
                if len(value.parts) == 1
                and value.name
                in {
                    "Makefile",
                    "go.mod",
                    "go.work",
                    "package.json",
                    "pyproject.toml",
                }
                else (
                    "repository-root/runtime"
                    if len(value.parts) == 1
                    else value.parent.as_posix()
                )
            )
            grouped.setdefault(unit, []).append(path)
        topics = []
        used = set()
        for index, (unit, files) in enumerate(sorted(grouped.items()), start=1):
            slug = re.sub(r"[^a-z0-9]+", "-", unit.lower()).strip("-")
            topic_id = slug
            if topic_id in used:
                topic_id = f"{slug}-{index}"
            used.add(topic_id)
            topics.append(
                {
                    "id": topic_id,
                    "document": f"topics/{topic_id}.md",
                    "title": unit,
                    "responsibility": f"Observed responsibility for {unit}",
                    "reason": f"Fixture semantic plan for {unit}",
                    "relationships": [],
                    "files": files,
                }
            )
        self.enrich_graph_value({"topics": topics, "covered": []})
        plan = self.run / "topic-plan.json"
        plan.write_text(
            json.dumps(
                {
                    "topics": topics,
                    "covered": [],
                    "supporting": [],
                    "open_leads": [],
                    "deferred_leads": [],
                }
            ),
            encoding="utf-8",
        )
        return plan

    def discovery_corpus_path(self):
        corpus = self.run / "discovery-corpus.json"
        if corpus.exists():
            return corpus
        discovery = self.run / "discovery"
        self.cli(
            "discovery-start",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            str(discovery),
            "--inventory-accelerator",
        )
        results = self.run / "discovery-results"
        for packet_path in sorted(discovery.rglob("lead-*.json")):
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
            lead = packet["lead"]
            result_path = results / packet_path.relative_to(discovery)
            result_path.parent.mkdir(parents=True, exist_ok=True)
            result_path.write_text(
                json.dumps(
                    {
                        "lead_id": lead["id"],
                        "status": "closed",
                        "reason": "Fixture discovery leaf.",
                        "inspected": {
                            "files": lead["seed_files"],
                            "queries": [],
                        },
                        "topics": [],
                        "supporting": (
                            [
                                {
                                    "reason": "Fixture disposition.",
                                    "files": lead["seed_files"],
                                }
                            ]
                            if lead["seed_files"]
                            else []
                        ),
                        "unresolved_leads": [],
                    }
                ),
                encoding="utf-8",
            )
        self.cli(
            "discovery-collect",
            str(self.ledger),
            str(discovery / "discovery-seed.json"),
            str(discovery),
            str(results),
            str(corpus),
        )
        return corpus

    def test_discovery_commands_are_idempotent_and_recover_missing_scouts(self):
        bulk = self.repository / "recovery"
        bulk.mkdir()
        for index in range(CAMPAIGN_MODULE.MAX_SCOUT_SEED_FILES + 1):
            (bulk / f"file_{index:03d}.py").write_text(
                f"VALUE = {index}\n",
                encoding="utf-8",
            )
        discovery = self.run / "resumable-discovery"
        first = self.cli(
            "discovery-start",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            str(discovery),
            "--inventory-accelerator",
        )
        second = self.cli(
            "discovery-start",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            str(discovery),
            "--inventory-accelerator",
        )
        self.assertEqual("written", first["status"])
        self.assertEqual("already_ready", second["status"])

        results = self.run / "resumable-results"
        packet = sorted(discovery.rglob("lead-*.json"))[0]
        relative = packet.relative_to(discovery)
        value = json.loads(packet.read_text(encoding="utf-8"))
        result = results / relative
        result.parent.mkdir(parents=True)
        result.write_text(
            json.dumps(
                {
                    "lead_id": value["lead"]["id"],
                    "status": "closed",
                    "reason": "Recovered fixture result.",
                    "inspected": {"files": value["lead"]["seed_files"], "queries": []},
                    "topics": [],
                    "supporting": (
                        [
                            {
                                "reason": "Recovered supporting evidence.",
                                "files": value["lead"]["seed_files"],
                            }
                        ]
                        if value["lead"]["seed_files"]
                        else []
                    ),
                    "unresolved_leads": [],
                }
            ),
            encoding="utf-8",
        )
        recovered = self.cli(
            "recover",
            str(self.ledger),
            "--discovery-results",
            str(results),
        )
        self.assertIn(relative.as_posix(), recovered["scouts"]["complete"])
        self.assertGreater(len(recovered["scouts"]["missing"]), 0)

    def test_discovery_rejects_state_outside_canonical_workspace_root(self):
        error = self.cli(
            "discovery-start",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            str(self.repository / ".map-campaign"),
            "--inventory-accelerator",
            expected=2,
        )
        self.assertIn(
            "workspace Map runtime root",
            error["error"],
        )

    def test_init_rejects_campaign_ledger_outside_canonical_workspace_root(self):
        error = self.cli(
            "init",
            str(self.repository / ".hidden-map" / "campaign.json"),
            str(self.operation),
            "--repository-root",
            str(self.repository),
            expected=2,
        )
        self.assertIn(
            "campaign ledger must be under the workspace Map runtime root",
            error["error"],
        )

    def test_init_creates_workspace_local_runtime_root_and_ignore(self):
        runtime_root = self.repository / ".specspine" / "map"
        self.assertTrue(self.ledger.is_relative_to(runtime_root))
        self.assertEqual(
            "*\n",
            (self.repository / ".specspine" / ".gitignore").read_text(
                encoding="utf-8"
            ),
        )

    def test_synthesis_prepare_is_idempotent_and_recorded(self):
        corpus = self.discovery_corpus_path()
        packet = self.run / "synthesis-packet.json"
        first = self.cli(
            "prepare",
            str(corpus),
            str(packet),
            "--ledger",
            str(self.ledger),
            script=SYNTHESIS,
        )
        second = self.cli(
            "prepare",
            str(corpus),
            str(packet),
            "--ledger",
            str(self.ledger),
            script=SYNTHESIS,
        )
        self.assertEqual("written", first["status"])
        self.assertEqual("already_ready", second["status"])
        self.assertEqual(
            str(packet.resolve()),
            self.ledger_value()["artifacts"]["synthesis"]["packet"]["path"],
        )

    def semantic_discovery_corpus_path(self):
        path = self.discovery_corpus_path()
        corpus = json.loads(path.read_text(encoding="utf-8"))
        evidence = "pyproject.toml"
        for group in list(corpus["supporting"]):
            if evidence not in group["files"]:
                continue
            group["files"].remove(evidence)
            if not group["files"]:
                corpus["supporting"].remove(group)
            break
        topic = {
            "id": "session-runtime",
            "title": "Session runtime",
            "responsibility": "Creates and validates application sessions.",
            "reason": "The project manifest selects the session runtime boundary.",
            "files": [evidence],
        }
        corpus["topics"].append(topic)
        corpus["leads"][0]["topics"].append(topic)
        corpus["digest"] = CAMPAIGN_MODULE.digest_json(
            {key: value for key, value in corpus.items() if key != "digest"}
        )
        path.write_text(json.dumps(corpus), encoding="utf-8")
        return path

    def source_pass(self, *, expected=0):
        plan = self.topic_plan_path()
        return self.cli(
            "source-pass",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            "--discovery-corpus",
            str(self.discovery_corpus_path()),
            "--topic-plan",
            str(plan),
            expected=expected,
        )

    def task_for_unit(self, unit):
        ledger = self.ledger_value()
        topics = [
            topic
            for topic in ledger["source_pass"]["topic_plan"]["topics"]
            if topic["title"] == unit
        ]
        self.assertEqual(1, len(topics), unit)
        task_id = ledger["source_pass"]["topic_tasks"][topics[0]["id"]]
        return task_id, ledger["tasks"][task_id]

    def assign(self, task_id, owner="/root/producer-1", handoffs=None):
        return self.cli(
            "assign",
            str(self.ledger),
            task_id,
            "--owner",
            owner,
            "--handoffs-root",
            str(handoffs or (self.run / "handoffs")),
        )

    def checkpoint_payload(
        self,
        *,
        outcome,
        evidence,
        directions=None,
        owner_document="architecture.md",
        owner_claim_ids=None,
    ):
        payload = {
            "outcome": outcome,
            "evidence": evidence,
            "summary": "The bounded unit and its responsibility were inspected",
            "directions": directions or [],
        }
        if outcome in {"covered", "answered"}:
            payload["owner"] = (
                {
                    "document": owner_document,
                    "claims": owner_claim_ids or ["OBS-architecture-root"],
                }
            )
        elif outcome == "retry":
            payload["need"] = ["src/identity/recovery.py"]
        elif outcome in {"blocked", "supporting", "unresolved"}:
            payload["reason"] = "External evidence is unavailable"
        return payload

    def accept(self, task_id, payload, *, owner="/root/producer-1", expected=0):
        self.checkpoint.write_text(json.dumps(payload), encoding="utf-8")
        task = self.ledger_value()["tasks"][task_id]
        attempt = task["attempts"]
        package = Path(task["handoff_package"])
        handoffs = package.parent
        package.mkdir(parents=True)
        shutil.copy2(self.checkpoint, package / "checkpoint.json")
        shutil.copytree(self.staging, package / "staging")
        harvest_root = self.run / f"harvest-{task_id}-{attempt}"
        settled = self.cli(
            "settle-wave",
            str(self.ledger),
            str(handoffs),
            str(self.spine),
            str(harvest_root),
        )
        if settled.get("rejected"):
            self.assertEqual(2, expected)
            return {"error": settled["rejected_tasks"][0]["error"]}
        if expected:
            return settled
        task = self.ledger_value()["tasks"][task_id]
        return {
            "status": "accepted",
            "task_state": settled["task_states"][task_id],
            "suggestions_pending_review": [
                value["id"] for value in task["producer_suggestions"]
            ],
        }

    def covered(self, task_id, evidence, *, owner="/root/producer-1"):
        self.assign(task_id, owner)
        return self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="covered",
                evidence=[evidence],
            ),
            owner=owner,
        )

    def unresolved_anchored_task(self, task_id="session-recovery"):
        self.source_pass()
        source_task, _ = self.task_for_unit("src/identity")
        self.covered(source_task, "src/identity/session.py")
        todo = {
            "id": task_id,
            "question": "Who owns failed session recovery?",
            "reason": "Recovery ownership remains unspecified",
            "evidence": ["src/identity/session.py"],
            "documents": ["architecture.md"],
            "excludes": [],
            "anchor": {
                "document": "architecture.md",
                "location": "Architecture map",
                "known": "Normal session ownership is documented",
            },
        }
        workspace = self.prepare_integration()
        self.integrate(
            self.integration_report(todo=[todo], workspace=workspace),
            workspace=workspace,
        )
        owner = "/root/producer-unresolved"
        self.assign(task_id, owner)
        self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="unresolved",
                evidence=["src/identity/session.py"],
            ),
            owner=owner,
        )
        return task_id

    def prepare_integration(self):
        self.integration_index += 1
        workspace = self.run / f"integration-workspace-{self.integration_index}"
        self.cli(
            "prepare-integration",
            str(self.ledger),
            str(self.spine),
            str(workspace),
        )
        self.current_workspace = workspace
        return workspace

    def integration_report(self, *, todo=None, omit_suggestions=False, workspace=None):
        workspace = workspace or self.current_workspace or self.prepare_integration()
        raw_todo = todo or []
        for value in raw_todo:
            value.setdefault("basis", "repository-observation")
            anchor = value.get("anchor")
            if anchor is None:
                continue
            anchor.setdefault("question", value["question"])
            document = workspace / anchor["document"]
            body = document.read_text(encoding="utf-8")
            if value["question"] not in body:
                document.write_text(
                    body + f"\n- {value['question']}\n",
                    encoding="utf-8",
                )
        ledger = self.ledger_value()
        before = ledger.get("spine_snapshot")
        if before is None:
            before = (ledger.get("integration_pass") or {}).get("documents")
        if before is None:
            before = (ledger.get("documentation_seed") or {}).get("documents", {})
        after = {
            path.relative_to(workspace).as_posix(): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in sorted(workspace.rglob("*.md"))
        }
        manifest = workspace / "specspine.json"
        if manifest.is_file():
            after["specspine.json"] = hashlib.sha256(
                manifest.read_bytes()
            ).hexdigest()
        changed_documents = [
            {
                "path": path,
                "operation": (
                    "created"
                    if path not in before
                    else "deleted"
                    if path not in after
                    else "changed"
                ),
            }
            for path in sorted(before.keys() | after.keys())
            if before.get(path) != after.get(path)
        ]
        settled = [
            task
            for task in ledger["tasks"].values()
            if task["state"] in {"published", "review"}
        ]
        reviews = [
            {
                "task": task["id"],
                "disposition": (
                    "confirmed_supporting"
                    if task.get("checkpoint_outcome") == "supporting"
                    else "answered_canonical"
                    if task.get("checkpoint_outcome") == "answered"
                    else "still_open"
                    if task.get("checkpoint_outcome") == "unresolved"
                    else "already_canonical"
                    if task["state"] == "review"
                    else "integrated"
                ),
                "reason": "Root integration confirmed the producer result",
                **(
                    {
                        "anchor_disposition": {
                            "status": (
                                "still-open"
                                if task.get("checkpoint_outcome") == "unresolved"
                                else "resolved"
                            ),
                            "reason": "Root reviewed the originating question",
                        }
                    }
                    if task.get("anchor") is not None
                    else {}
                ),
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
        return {
            "evidence_inspected": sorted(
                path.relative_to(workspace).as_posix()
                for path in workspace.rglob("*.md")
            ),
            "changed_documents": changed_documents,
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

    def integrate(self, report=None, *, workspace=None, expected=0):
        workspace = workspace or self.current_workspace or self.prepare_integration()
        path = self.run / "integration.json"
        path.write_text(
            json.dumps(report or self.integration_report(workspace=workspace)),
            encoding="utf-8",
        )
        result = self.cli(
            "integration-pass",
            str(self.ledger),
            str(self.spine),
            str(workspace),
            str(path),
            "--checker",
            str(self.checker),
            expected=expected,
        )
        self.current_workspace = None
        return result

    def verify_all_source_units(self):
        self.source_pass()
        ledger = self.ledger_value()
        queued = ledger["source_pass"]["todo"]
        for index, task_id in enumerate(queued):
            samples = ledger["tasks"][task_id]["evidence"]
            owner = f"/root/producer-{index}"
            self.assign(task_id, owner)
            self.accept(
                task_id,
                self.checkpoint_payload(outcome="covered", evidence=samples),
                owner=owner,
            )
        self.integrate()

    def verify_single_topic_operation(self):
        discovery = self.run / "single-topic-discovery"
        operation = self.ledger_value()["operation"]
        discovery_options = (
            ["--inventory-accelerator"]
            if operation["scope"]["kind"] == "repository"
            else []
        )
        self.cli(
            "discovery-start",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            str(discovery),
            *discovery_options,
        )
        packet_path = next(discovery.rglob("lead-*.json"))
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        seed_files = packet["lead"]["seed_files"]
        results = self.run / "single-topic-results"
        result_path = results / packet_path.relative_to(discovery)
        result_path.parent.mkdir(parents=True)
        topic = {
            "id": "session-lifecycle",
            "title": "Session lifecycle",
            "responsibility": "Owns the observed session lifecycle.",
            "reason": "The runtime exposes a durable session boundary.",
            "files": ["src/identity/session.py"],
        }
        result_path.write_text(
            json.dumps(
                {
                    "lead_id": packet["lead"]["id"],
                    "status": "closed",
                    "reason": "The directly exposed responsibility is classified.",
                    "inspected": {
                        "files": sorted(
                            set(seed_files) | {"src/identity/session.py"}
                        ),
                        "queries": ["session"],
                    },
                    "topics": [topic],
                    "supporting": (
                        [
                            {
                                "reason": "Fixture supporting evidence.",
                                "files": [
                                    path
                                    for path in seed_files
                                    if path != "src/identity/session.py"
                                ],
                            }
                        ]
                        if any(
                            path != "src/identity/session.py"
                            for path in seed_files
                        )
                        else []
                    ),
                    "unresolved_leads": [],
                }
            ),
            encoding="utf-8",
        )
        corpus = self.run / "single-topic-corpus.json"
        self.cli(
            "discovery-collect",
            str(self.ledger),
            str(discovery / "discovery-seed.json"),
            str(discovery),
            str(results),
            str(corpus),
        )
        plan = self.run / "single-topic-plan.json"
        plan.write_text(
            json.dumps(
                {
                    "topics": [topic],
                    "covered": [],
                    "supporting": [
                        {
                            "reason": "Fixture supporting evidence.",
                            "files": [
                                path
                                for path in seed_files
                                if path != "src/identity/session.py"
                            ],
                        }
                    ]
                    if any(
                        path != "src/identity/session.py" for path in seed_files
                    )
                    else [],
                    "open_leads": [],
                    "deferred_leads": [],
                }
            ),
            encoding="utf-8",
        )
        self.cli(
            "source-pass",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            "--discovery-corpus",
            str(corpus),
            "--topic-plan",
            str(plan),
        )
        task_id = self.ledger_value()["source_pass"]["todo"][0]
        self.covered(task_id, "src/identity/session.py")
        self.integrate()
        return self.cli("next-action", str(self.ledger))

    def test_init_uses_current_schema_and_private_ledger(self):
        ledger = self.ledger_value()
        self.assertEqual(CAMPAIGN_MODULE.SCHEMA_VERSION, ledger["schema_version"])
        contract = ROOT / "skills/specspine-map/references/producer-task.md"
        self.assertEqual(
            CAMPAIGN_MODULE.PRODUCER_CONTRACT_VERSION,
            ledger["producer_contract_version"],
        )
        self.assertEqual(
            hashlib.sha256(contract.read_bytes()).hexdigest(),
            ledger["producer_contract_digest"],
        )
        self.assertEqual({}, ledger["tasks"])
        self.assertEqual(0o600, self.ledger.stat().st_mode & 0o777)

    def test_empty_spine_bootstrap_is_idempotent(self):
        spine = self.run / "empty-spine"
        first = self.cli(
            "bootstrap-spine",
            str(self.ledger),
            str(spine),
            "--project",
            "grafana",
        )
        second = self.cli(
            "bootstrap-spine",
            str(self.ledger),
            str(spine),
            "--project",
            "grafana",
        )

        self.assertEqual("created", first["status"])
        self.assertEqual(["_INDEX.md", "specspine.json"], first["created"])
        self.assertEqual("already_ready", second["status"])
        self.assertEqual([], second["created"])

    def test_empty_spine_bootstrap_recovers_its_missing_manifest(self):
        spine = self.run / "partial-empty-spine"
        spine.mkdir()
        (spine / "_INDEX.md").write_text(
            CAMPAIGN_MODULE.bootstrap_index("grafana"),
            encoding="utf-8",
        )

        result = self.cli(
            "bootstrap-spine",
            str(self.ledger),
            str(spine),
            "--project",
            "grafana",
        )

        self.assertEqual("created", result["status"])
        self.assertEqual(["specspine.json"], result["created"])

    def test_repository_survey_increment_reaches_increment_verified(self):
        ledger = self.ledger_value()
        ledger["operation"]["completion"] = {
            "kind": "increment",
            "intent": "survey",
        }
        self.ledger.write_text(json.dumps(ledger), encoding="utf-8")

        next_action = self.verify_single_topic_operation()

        self.assertEqual("increment_verified", next_action["terminal"])
        self.assertEqual("finalize", next_action["action"])
        self.assertTrue(next_action["may_finish"])

    def test_semantic_exhaustive_reaches_scope_verified(self):
        self.set_semantic_operation()

        next_action = self.verify_single_topic_operation()

        self.assertEqual("scope_verified", next_action["terminal"])
        self.assertEqual("finalize", next_action["action"])
        self.assertTrue(next_action["may_finish"])

    def test_repository_non_survey_increment_is_rejected(self):
        for intent in ("deepen", "refresh", "drift"):
            with self.subTest(intent=intent):
                operation = self.run / f"invalid-{intent}-operation.json"
                operation.write_text(
                    json.dumps(
                        {
                            "scope": {
                                "kind": "repository",
                                "title": "Repository",
                                "question": "Update the repository",
                                "inclusion_rule": "All architecture.",
                                "exclusion_rule": "Generated files.",
                            },
                            "completion": {
                                "kind": "increment",
                                "intent": intent,
                            },
                        }
                    ),
                    encoding="utf-8",
                )
                error = self.cli(
                    "init",
                    str(self.run / f"invalid-{intent}-campaign.json"),
                    str(operation),
                    "--repository-root",
                    str(self.repository),
                    expected=2,
                )
                self.assertIn(
                    "repository increment supports only survey intent",
                    error["error"],
                )

    def test_increment_defers_unresolved_frontier_and_finishes_without_scope_claim(self):
        self.set_semantic_operation(completion="increment", intent="deepen")
        discovery = self.run / "increment-discovery"
        self.cli(
            "discovery-start",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            str(discovery),
        )
        packet_path = next(discovery.rglob("lead-*.json"))
        results = self.run / "increment-results"
        result_path = results / packet_path.relative_to(discovery)
        result_path.parent.mkdir(parents=True)
        result_path.write_text(
            json.dumps(
                {
                    "lead_id": "scope-root",
                    "status": "unresolved",
                    "reason": "Session storage is adjacent to the requested lifecycle.",
                    "inspected": {
                        "files": ["src/identity/session.py"],
                        "queries": ["session"],
                    },
                    "topics": [
                        {
                            "id": "session-lifecycle",
                            "title": "Session lifecycle",
                            "responsibility": "Owns session lifecycle.",
                            "reason": "The requested increment exposes this boundary.",
                            "files": ["src/identity/session.py"],
                        }
                    ],
                    "supporting": [],
                    "unresolved_leads": [
                        {
                            "id": "session-storage",
                            "title": "Session storage",
                            "question": "Who persists sessions?",
                            "reason": "Persistence is an adjacent responsibility.",
                            "fallback_kind": "increment_continuation",
                            "seed_files": ["src/identity/session.py"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        deferred = {
            "id": "session-storage",
            "title": "Session storage",
            "question": "Who persists sessions?",
            "reason": "Persistence is an adjacent responsibility.",
            "parent_ids": ["scope-root"],
            "seed_files": ["src/identity/session.py"],
            "deferral_reason": (
                "The increment records but does not expand adjacent ownership."
            ),
        }
        frontier = self.run / "increment-frontier.json"
        frontier.write_text(
            json.dumps(
                {
                    "decisions": [
                        {
                            "disposition": "defer",
                            "sources": ["scope-root/session-storage"],
                            "lead": {
                                key: value
                                for key, value in deferred.items()
                                if key != "deferral_reason"
                            },
                            "reason": deferred["deferral_reason"],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        receipt = self.cli(
            "discovery-packets",
            str(discovery / "discovery-seed.json"),
            str(frontier),
            str(discovery / "wave-0002"),
        )
        self.assertEqual([], receipt["packets"])
        self.assertEqual(1, receipt["deferred"])
        corpus = self.run / "increment-corpus.json"
        self.cli(
            "discovery-collect",
            str(self.ledger),
            str(discovery / "discovery-seed.json"),
            str(discovery),
            str(results),
            str(corpus),
        )
        plan = self.run / "increment-plan.json"
        plan.write_text(
            json.dumps(
                {
                    "topics": [
                        {
                            "id": "session-lifecycle",
                            "title": "Session lifecycle",
                            "responsibility": "Owns session lifecycle.",
                            "reason": "The requested increment exposes this boundary.",
                            "files": ["src/identity/session.py"],
                        }
                    ],
                    "covered": [],
                    "supporting": [],
                    "open_leads": [],
                    "deferred_leads": [deferred],
                }
            ),
            encoding="utf-8",
        )
        self.cli(
            "source-pass",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            "--discovery-corpus",
            str(corpus),
            "--topic-plan",
            str(plan),
        )
        task_id = self.ledger_value()["source_pass"]["todo"][0]
        self.covered(task_id, "src/identity/session.py")
        self.integrate()
        next_action = self.cli("next-action", str(self.ledger))
        self.assertEqual("increment_verified", next_action["terminal"])

    def test_inventory_returns_flat_production_files_and_exclusions(self):
        first = self.inventory()
        second = self.inventory()
        self.assertEqual(first["digest"], second["digest"])
        self.assertEqual(
            ["pyproject.toml", "src/identity/session.py"],
            first["production_files"],
        )
        self.assertEqual(
            ["tests/session_test.py"],
            first["excluded"]["test-only"],
        )

    def test_source_pass_queues_semantic_topics_over_discovery_scope(self):
        receipt = self.source_pass()
        self.assertEqual("repository", receipt["scope_kind"])
        self.assertEqual(2, receipt["evidence_files"])
        self.assertEqual(2, receipt["topics"])
        self.assertEqual(2, receipt["verification_todo"])
        self.assertEqual(2, receipt["added_todo_count"])
        self.assertNotIn("added_todo", receipt)
        ledger = self.ledger_value()
        self.assertEqual(
            "repository",
            ledger["source_pass"]["scope"]["kind"],
        )
        self.assertTrue(
            all(ledger["tasks"][task_id]["state"] == "todo"
                for task_id in ledger["source_pass"]["todo"])
        )

    def test_ready_can_limit_large_frontier_output(self):
        self.source_pass()

        ready = self.cli("ready", str(self.ledger), "--limit", "1")

        self.assertEqual(1, ready["returned"])
        self.assertEqual(2, ready["total"])
        self.assertEqual(1, len(ready["ready"]))

    def test_ready_rejects_oversized_producer_wave(self):
        error = self.cli(
            "ready",
            str(self.ledger),
            "--limit",
            str(CAMPAIGN_MODULE.MAX_PRODUCER_WAVE + 1),
            expected=2,
        )
        self.assertIn("producer wave limit exceeds 10", error["error"])

    def test_ready_prioritizes_system_breadth_before_leaf_detail(self):
        (self.repository / "main.go").write_text("package main\n", encoding="utf-8")
        for relative in (
            "cmd/server/main.go",
            "apps/advisor/app.go",
            "pkg/services/auth/service.go",
            "public/app/features/dashboard/index.ts",
        ):
            path = self.repository / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("production\n", encoding="utf-8")
        self.source_pass()
        by_unit = {
            unit: self.task_for_unit(unit)[0]
            for unit in (
                "repository-root/runtime",
                "repository-root/manifests",
                "cmd/server",
                "apps/advisor",
                "pkg/services/auth",
            )
        }
        ready = self.cli("ready", str(self.ledger), "--limit", "5")["ready"]
        self.assertEqual(
            [
                by_unit["repository-root/runtime"],
                by_unit["repository-root/manifests"],
                by_unit["cmd/server"],
                by_unit["apps/advisor"],
                by_unit["pkg/services/auth"],
            ],
            ready,
        )

    def test_repository_discovery_uses_flat_inventory_as_neutral_accelerator(self):
        for directory in ("alpha", "beta"):
            root = self.repository / "packages/big" / directory
            root.mkdir(parents=True)
            for index in range(70):
                (root / f"file_{index:03d}.ts").write_text(
                    f"export const value{index} = {index};\n",
                    encoding="utf-8",
                )
        discovery = self.run / "discovery"
        receipt = self.cli(
            "discovery-start",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            str(discovery),
            "--inventory-accelerator",
            "--page-size",
            str(CAMPAIGN_MODULE.MAX_SCOUT_SEED_FILES),
        )
        packets = [json.loads(Path(path).read_text()) for path in receipt["packets"]]
        inventory = self.inventory()
        paged = [
            path
            for packet in packets
            for path in packet["lead"]["seed_files"]
        ]
        self.assertEqual(inventory["production_files"], paged)
        self.assertFalse(receipt["inventory_truncated"])
        self.assertEqual(len(paged), receipt["inventory_total_files"])
        self.assertTrue(
            all(
                set(packet)
                == {
                    "discovery_contract_version",
                    "repository_root",
                    "spine_root",
                    "operation",
                    "lead",
                    "source_refs",
                }
                for packet in packets
            )
        )

    def test_repository_discovery_has_explicit_test_only_inventory_limit(self):
        test_limit = 1000
        bulk = self.repository / "bulk"
        bulk.mkdir()
        for index in range(test_limit + 5):
            (bulk / f"file_{index:04d}.ts").write_text(
                "export const value = 1;\n",
                encoding="utf-8",
            )
        discovery = self.run / "limited-discovery"
        receipt = self.cli(
            "discovery-start",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            str(discovery),
            "--inventory-accelerator",
            "--test-inventory-file-limit",
            str(test_limit),
        )
        seed = json.loads(
            (discovery / "discovery-seed.json").read_text(encoding="utf-8")
        )
        paged = [
            path
            for packet_path in receipt["packets"]
            for path in json.loads(Path(packet_path).read_text(encoding="utf-8"))[
                "lead"
            ]["seed_files"]
        ]

        self.assertEqual(
            test_limit,
            len(paged),
        )
        self.assertEqual(len(paged), receipt["seed_files"])
        self.assertGreater(receipt["inventory_total_files"], len(paged))
        self.assertTrue(receipt["inventory_truncated"])
        self.assertEqual(paged, seed["accelerator"]["production_files"])
        self.assertTrue(seed["accelerator"]["truncated"])
        self.assertEqual(test_limit, seed["accelerator"]["test_file_limit"])
        self.assertEqual(
            receipt["inventory_total_files"],
            seed["accelerator"]["total_production_files"],
        )
        self.assertFalse(
            self.cli("next-action", str(self.ledger))["terminal_gates"][
                "repository_boundary_complete"
            ]
        )

    def test_discovery_start_rejects_oversized_pages_before_writing(self):
        discovery = self.run / "oversized-discovery"
        error = self.cli(
            "discovery-start",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            str(discovery),
            "--inventory-accelerator",
            "--page-size",
            str(CAMPAIGN_MODULE.MAX_SCOUT_SEED_FILES + 1),
            expected=2,
        )

        self.assertIn(
            f"page size exceeds {CAMPAIGN_MODULE.MAX_SCOUT_SEED_FILES}",
            error["error"],
        )
        self.assertFalse(discovery.exists())
        self.assertIsNone(self.ledger_value()["discovery"])

    def test_discovery_validate_requires_exact_result_path(self):
        self.set_semantic_operation()
        discovery = self.run / "discovery"
        receipt = self.cli(
            "discovery-start",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            str(discovery),
        )
        packet = Path(receipt["packets"][0])
        results = self.run / "results"
        results.mkdir()
        wrong_result = results / packet.name
        wrong_result.write_text(
            json.dumps(
                {
                    "lead_id": "scope-root",
                    "status": "closed",
                    "reason": "The session responsibility is classified.",
                    "inspected": {
                        "files": ["src/identity/session.py"],
                        "queries": ["session"],
                    },
                    "topics": [
                        {
                            "id": "session-lifecycle",
                            "title": "Session lifecycle",
                            "responsibility": "Owns the session lifecycle.",
                            "reason": "The runtime exposes a session boundary.",
                            "files": ["src/identity/session.py"],
                        }
                    ],
                    "supporting": [],
                    "unresolved_leads": [],
                }
            ),
            encoding="utf-8",
        )
        error = self.cli(
            "discovery-validate",
            str(discovery / "discovery-seed.json"),
            str(discovery),
            str(results),
            str(packet),
            expected=2,
        )
        expected_result = results.resolve() / packet.resolve().relative_to(
            discovery.resolve()
        )
        self.assertIn(str(expected_result), error["error"])

        expected_result.parent.mkdir(parents=True)
        wrong_result.rename(expected_result)
        validated = self.cli(
            "discovery-validate",
            str(discovery / "discovery-seed.json"),
            str(discovery),
            str(results),
            str(packet),
        )
        self.assertEqual("valid", validated["status"])
        self.assertEqual(1, validated["count"])
        self.assertEqual(0, validated["unresolved_leads"])
        self.assertEqual("scope-root", validated["validated"][0]["lead_id"])

    def test_topic_discovery_starts_without_repository_inventory(self):
        self.set_semantic_operation()
        discovery = self.run / "discovery"
        receipt = self.cli(
            "discovery-start",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            str(discovery),
        )
        self.assertFalse(receipt["inventory_accelerator"])
        self.assertEqual(0, receipt["seed_files"])
        packet = json.loads(Path(receipt["packets"][0]).read_text())
        self.assertEqual("scope-root", packet["lead"]["id"])
        self.assertEqual([], packet["lead"]["seed_files"])

    def test_semantic_discovery_uses_adaptive_initial_fanout(self):
        self.set_semantic_operation()
        plan = self.run / "fanout.json"
        leads = [
            {
                "id": f"boundary-{index}",
                "title": f"Boundary {index}",
                "question": f"Which owner controls boundary {index}?",
                "reason": f"Boundary {index} is independently searchable.",
            }
            for index in range(1, 5)
        ]
        plan.write_text(
            json.dumps(
                {
                    "discovery_plan_version": 1,
                    "rationale": "The subsystem exposes four search boundaries.",
                    "leads": leads,
                }
            ),
            encoding="utf-8",
        )
        discovery = self.run / "fanout-discovery"
        receipt = self.cli(
            "discovery-start",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            str(discovery),
            "--initial-plan",
            str(plan),
        )
        self.assertEqual(4, len(receipt["packets"]))
        seed = json.loads(
            (discovery / "discovery-seed.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            [lead["id"] for lead in leads],
            seed["initial_leads"],
        )
        self.assertEqual(4, len(seed["initial_plan"]["leads"]))

    def test_semantic_discovery_rejects_more_than_ten_initial_scouts(self):
        self.set_semantic_operation()
        plan = self.run / "oversized-fanout.json"
        plan.write_text(
            json.dumps(
                {
                    "discovery_plan_version": 1,
                    "rationale": "Invalid oversized fanout.",
                    "leads": [
                        {
                            "id": f"boundary-{index}",
                            "title": f"Boundary {index}",
                            "question": f"Question {index}?",
                            "reason": f"Reason {index}.",
                        }
                        for index in range(1, 12)
                    ],
                }
            ),
            encoding="utf-8",
        )
        error = self.cli(
            "discovery-start",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            str(self.run / "oversized-fanout-discovery"),
            "--initial-plan",
            str(plan),
            expected=2,
        )
        self.assertIn("needs 1..10 leads", error["error"])

    def test_discovery_collect_requires_every_seed_result(self):
        self.discovery_corpus_path()
        discovery = self.run / "discovery"
        results = self.run / "discovery-results"
        first = sorted(results.rglob("lead-*.json"))[0]
        first.unlink()
        corpus = self.run / "second-corpus.json"
        error = self.cli(
            "discovery-collect",
            str(self.ledger),
            str(discovery / "discovery-seed.json"),
            str(discovery),
            str(results),
            str(corpus),
            expected=2,
        )
        self.assertIn("missing discovery result", error["error"])

    def test_discovery_collect_rejects_unclosed_unresolved_frontier(self):
        self.set_semantic_operation()
        discovery = self.run / "discovery"
        self.cli(
            "discovery-start",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            str(discovery),
        )
        packet_path = next(discovery.rglob("lead-*.json"))
        results = self.run / "results"
        result_path = results / packet_path.relative_to(discovery)
        result_path.parent.mkdir(parents=True)
        result_path.write_text(
            json.dumps(
                {
                    "lead_id": "scope-root",
                    "status": "unresolved",
                    "reason": "A child responsibility was exposed.",
                    "inspected": {
                        "files": ["src/identity/session.py"],
                        "queries": ["session"],
                    },
                    "topics": [
                        {
                            "id": "sessions",
                            "title": "Sessions",
                            "responsibility": "Owns session lifecycle.",
                            "reason": "Session evidence.",
                            "files": ["src/identity/session.py"],
                        }
                    ],
                    "supporting": [],
                    "unresolved_leads": [
                        {
                            "id": "session-storage",
                            "title": "Session storage",
                            "question": "Who stores sessions?",
                            "reason": "The lifecycle references durable state.",
                            "fallback_kind": "independent_investigation",
                            "seed_files": ["src/identity/session.py"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        error = self.cli(
            "discovery-collect",
            str(self.ledger),
            str(discovery / "discovery-seed.json"),
            str(discovery),
            str(results),
            str(self.run / "corpus.json"),
            expected=2,
        )
        self.assertIn("frontier is not closed", error["error"])

    def test_topic_discovery_closes_targeted_fallback_frontier(self):
        self.set_semantic_operation()
        discovery = self.run / "discovery"
        self.cli(
            "discovery-start",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            str(discovery),
        )
        root_packet = next(discovery.rglob("lead-*.json"))
        results = self.run / "results"
        root_result = results / root_packet.relative_to(discovery)
        root_result.parent.mkdir(parents=True)
        root_result.write_text(
            json.dumps(
                {
                    "lead_id": "scope-root",
                    "status": "unresolved",
                    "reason": "Session persistence needs one deeper pass.",
                    "inspected": {
                        "files": [
                            "pyproject.toml",
                            "src/identity/session.py",
                        ],
                        "queries": ["session"],
                    },
                    "topics": [
                        {
                            "id": "session-lifecycle",
                            "title": "Session lifecycle",
                            "responsibility": "Owns session lifecycle.",
                            "reason": "Runtime evidence.",
                            "files": ["src/identity/session.py"],
                        }
                    ],
                    "supporting": [],
                    "unresolved_leads": [
                        {
                            "id": "runtime-manifest",
                            "title": "Session runtime manifest",
                            "question": "How is the session runtime composed?",
                            "reason": "The runtime dependency remains unclassified.",
                            "fallback_kind": "separate_owner",
                            "seed_files": ["pyproject.toml"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        frontier = self.run / "frontier.json"
        frontier.write_text(
            json.dumps(
                {
                    "decisions": [
                        {
                            "disposition": "queue",
                            "sources": ["scope-root/runtime-manifest"],
                            "lead": {
                                "id": "session-runtime-manifest",
                                "title": "Session runtime manifest",
                                "question": "How is the session runtime composed?",
                                "reason": "The runtime dependency needs classification.",
                                "parent_ids": ["scope-root"],
                                "seed_files": ["pyproject.toml"],
                            },
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        wave = discovery / "wave-0002"
        receipt = self.cli(
            "discovery-packets",
            str(discovery / "discovery-seed.json"),
            str(frontier),
            str(wave),
        )
        unresolved_packet = Path(receipt["packets"][0])
        unresolved_result = results / unresolved_packet.relative_to(discovery.resolve())
        unresolved_result.parent.mkdir(parents=True)
        unresolved_result.write_text(
            json.dumps(
                {
                    "lead_id": "session-runtime-manifest",
                    "status": "closed",
                    "reason": "The manifest is supporting composition evidence.",
                    "inspected": {
                        "files": ["pyproject.toml"],
                        "queries": ["project"],
                    },
                    "topics": [],
                    "supporting": [
                        {
                            "reason": "Supporting runtime manifest.",
                            "files": ["pyproject.toml"],
                        }
                    ],
                    "unresolved_leads": [],
                }
            ),
            encoding="utf-8",
        )
        corpus = self.run / "topic-corpus.json"
        collected = self.cli(
            "discovery-collect",
            str(self.ledger),
            str(discovery / "discovery-seed.json"),
            str(discovery),
            str(results),
            str(corpus),
        )
        self.assertEqual("semantic", collected["scope_kind"])
        self.assertEqual(2, collected["leads"])
        self.assertEqual(2, collected["evidence_files"])

    def test_global_synthesis_uses_descriptions_and_materializes_files(self):
        corpus = self.semantic_discovery_corpus_path()
        packet_path = self.run / "synthesis-packet.json"
        receipt = self.cli(
            "prepare",
            str(corpus),
            str(packet_path),
            script=SYNTHESIS,
        )
        self.assertEqual(1, receipt["source_topics"])
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        self.assertEqual(
            sorted(CAMPAIGN_MODULE.CORE_RELATIONS),
            packet["allowed_relationship_types"],
        )
        source = packet["source_topics"][0]
        self.assertEqual("Session runtime", source["title"])
        self.assertEqual(
            "Creates and validates application sessions.",
            source["responsibility"],
        )
        self.assertIn("lead_id", source)
        self.assertIn(source["lead_id"], packet["leads"])
        self.assertNotIn("files", source)

        mapping = self.run / "semantic-mapping.json"
        mapping.write_text(
            json.dumps(
                {
                    "topics": [
                        {
                            "id": "session-runtime",
                            "document": "sessions/runtime.md",
                            "title": source["title"],
                            "responsibility": source["responsibility"],
                            "reason": source["reason"],
                            "relationships": [],
                            "source_topic_ids": [source["source_id"]],
                        }
                    ],
                    "covered": [],
                    "supporting": [],
                    "open_leads": [],
                    "deferred_leads": [],
                }
            ),
            encoding="utf-8",
        )
        plan = self.run / "materialized-topic-plan.json"
        plan.write_text("stale plan", encoding="utf-8")
        materialized = self.cli(
            "materialize",
            str(corpus),
            str(mapping),
            str(plan),
            script=SYNTHESIS,
        )
        self.assertEqual(1, materialized["final_topics"])
        value = json.loads(plan.read_text(encoding="utf-8"))
        self.assertEqual(["pyproject.toml"], value["topics"][0]["files"])
        self.assertEqual(
            [{"id": "semantic-source-01", "sample": "pyproject.toml"}],
            value["topics"][0]["evidence_strata"],
        )
        self.assertNotIn("source_topic_ids", value["topics"][0])

    def test_synthesis_packet_contains_all_sources_for_global_deduplication(self):
        corpus_path = self.semantic_discovery_corpus_path()
        corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
        original = corpus["leads"][0]["topics"][0]
        second = original | {
            "id": "session-renewal",
            "title": "Session renewal",
            "responsibility": "Renews active application sessions.",
            "reason": "The same owner extends the session lifecycle.",
        }
        corpus["leads"][0]["topics"].append(second)
        corpus["topics"].append(second)
        corpus["digest"] = CAMPAIGN_MODULE.digest_json(
            {key: value for key, value in corpus.items() if key != "digest"}
        )
        corpus_path.write_text(json.dumps(corpus), encoding="utf-8")

        packet_path = self.run / "global-packet.json"
        self.cli(
            "prepare",
            str(corpus_path),
            str(packet_path),
            script=SYNTHESIS,
        )
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        self.assertEqual(2, packet["source_topic_count"])
        self.assertEqual(2, len(packet["source_topics"]))
        self.assertEqual(
            {"session-runtime", "session-renewal"},
            {
                value["source_id"].split("/", 1)[1]
                for value in packet["source_topics"]
            },
        )

    def test_synthesis_materializer_rejects_undispositioned_source(self):
        corpus = self.semantic_discovery_corpus_path()
        mapping = self.run / "semantic-mapping.json"
        mapping.write_text(
            json.dumps(
                {
                    "topics": [],
                    "covered": [],
                    "supporting": [],
                    "open_leads": [],
                    "deferred_leads": [],
                }
            ),
            encoding="utf-8",
        )
        failed = self.cli(
            "materialize",
            str(corpus),
            str(mapping),
            str(self.run / "plan.json"),
            script=SYNTHESIS,
            expected=2,
        )
        self.assertIn("does not disposition every source topic", failed["error"])

    def test_synthesis_diagnostics_flag_suspicious_semantic_result(self):
        self.add_spine_candidate(
            "sessions.md",
            "sessions",
            "src/identity/session.py",
        )
        specification = importlib.util.spec_from_file_location(
            "map_synthesis_diagnostics",
            SYNTHESIS,
        )
        assert specification is not None and specification.loader is not None
        module = importlib.util.module_from_spec(specification)
        with mock.patch.dict(sys.modules, {"campaign": CAMPAIGN_MODULE}):
            specification.loader.exec_module(module)
        semantic_values = [
            {"source_topic_ids": [f"lead/topic-{index:02d}"]}
            for index in range(20)
        ]
        diagnostics = module.synthesis_diagnostics(
            corpus={"spine_root": str(self.spine)},
            source_count=20,
            semantic_values=semantic_values,
            covered_count=0,
        )
        self.assertEqual(
            {
                "zero-existing-coverage",
                "high-singleton-ratio",
                "low-semantic-reduction",
            },
            {value["code"] for value in diagnostics},
        )

    def test_synthesis_accepts_empty_semantic_frontier(self):
        corpus = self.discovery_corpus_path()
        packet = self.run / "empty-synthesis-packet.json"
        prepared = self.cli(
            "prepare",
            str(corpus),
            str(packet),
            script=SYNTHESIS,
        )
        self.assertEqual(0, prepared["source_topics"])
        self.assertEqual(
            [],
            json.loads(packet.read_text(encoding="utf-8"))["source_topics"],
        )

    def test_synthesis_open_leads_reopen_discovery_and_block_source_pass(self):
        plan = self.run / "open-topic-plan.json"
        plan.write_text(
            json.dumps(
                {
                    "topics": [],
                    "covered": [],
                    "supporting": [],
                    "open_leads": [
                        {
                            "id": "session-recovery",
                            "title": "Session recovery",
                            "question": "Who owns session recovery?",
                            "reason": "Discovery exposed an unexpanded failure boundary.",
                            "seed_files": ["src/identity/session.py"],
                        }
                    ],
                    "deferred_leads": [],
                }
            ),
            encoding="utf-8",
        )
        corpus = self.discovery_corpus_path()
        error = self.cli(
            "source-pass",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            "--discovery-corpus",
            str(corpus),
            "--topic-plan",
            str(plan),
            expected=2,
        )
        self.assertIn("open discovery leads", error["error"])
        reopened = self.cli(
            "discovery-reopen",
            str(self.ledger),
            str(self.run / "discovery/discovery-seed.json"),
            str(plan),
            str(self.run / "discovery/wave-0002"),
        )
        self.assertEqual(1, reopened["reopened"])

    def test_source_pass_rejects_incomplete_or_conflicting_topic_plan(self):
        incomplete = self.run / "incomplete-topic-plan.json"
        incomplete.write_text(
            json.dumps(
                {
                    "topics": [
                        {
                            "id": "sessions",
                            "title": "Sessions",
                            "responsibility": "Owns session lifecycle.",
                            "reason": "Session implementation evidence.",
                            "files": ["src/identity/session.py"],
                        }
                    ],
                    "covered": [],
                    "supporting": [],
                    "open_leads": [],
                    "deferred_leads": [],
                }
            ),
            encoding="utf-8",
        )
        error = self.cli(
            "source-pass",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            "--discovery-corpus",
            str(self.discovery_corpus_path()),
            "--topic-plan",
            str(incomplete),
            expected=2,
        )
        self.assertIn("leaves evidence files uncovered", error["error"])

        conflict = self.run / "conflicting-topic-plan.json"
        conflict.write_text(
            json.dumps(
                {
                    "topics": [
                        {
                            "id": "sessions",
                            "title": "Sessions",
                            "responsibility": "Owns session lifecycle.",
                            "reason": "Session implementation evidence.",
                            "files": ["src/identity/session.py"],
                        }
                    ],
                    "covered": [],
                    "supporting": [
                        {
                            "reason": "Manifest supporting context.",
                            "files": ["src/identity/session.py", "pyproject.toml"],
                        }
                    ],
                    "open_leads": [],
                    "deferred_leads": [],
                }
            ),
            encoding="utf-8",
        )
        error = self.cli(
            "source-pass",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            "--discovery-corpus",
            str(self.discovery_corpus_path()),
            "--topic-plan",
            str(conflict),
            expected=2,
        )
        self.assertIn("both topic-covered and supporting", error["error"])

    def test_source_pass_allows_file_in_multiple_semantic_topics(self):
        plan = self.run / "overlapping-topic-plan.json"
        plan.write_text(
            json.dumps(
                {
                    "topics": [
                        {
                            "id": "session-lifecycle",
                            "title": "Session lifecycle",
                            "responsibility": "Owns session lifecycle.",
                            "reason": "Session implementation evidence.",
                            "files": ["src/identity/session.py"],
                        },
                        {
                            "id": "runtime-composition",
                            "title": "Runtime composition",
                            "responsibility": "Composes runtime identity behavior.",
                            "reason": "Manifest and session module jointly configure runtime.",
                            "files": [
                                "pyproject.toml",
                                "src/identity/session.py",
                            ],
                        },
                    ],
                    "covered": [],
                    "supporting": [],
                    "open_leads": [],
                    "deferred_leads": [],
                }
            ),
            encoding="utf-8",
        )

        receipt = self.cli(
            "source-pass",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            "--discovery-corpus",
            str(self.discovery_corpus_path()),
            "--topic-plan",
            str(plan),
        )
        self.assertEqual(2, receipt["topics"])
        self.assertEqual(2, receipt["verification_todo"])

    def test_source_pass_skips_topics_covered_by_existing_spine_claims(self):
        plan = self.run / "covered-topic-plan.json"
        plan.write_text(
            json.dumps(
                {
                    "topics": [],
                    "covered": [
                        {
                            "id": "existing-architecture",
                            "title": "Existing architecture",
                            "responsibility": "Owns the fixture architecture.",
                            "reason": "The responsibility is architecturally durable.",
                            "files": [
                                "pyproject.toml",
                                "src/identity/session.py",
                            ],
                            "coverage_reason": (
                                "The canonical architecture observation already "
                                "describes this responsibility."
                            ),
                            "coverage": [
                                {
                                    "document": "architecture.md",
                                    "claims": ["OBS-architecture-root"],
                                }
                            ],
                        }
                    ],
                    "supporting": [],
                    "open_leads": [],
                    "deferred_leads": [],
                }
            ),
            encoding="utf-8",
        )

        receipt = self.cli(
            "source-pass",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            "--discovery-corpus",
            str(self.discovery_corpus_path()),
            "--topic-plan",
            str(plan),
        )

        self.assertEqual(0, receipt["topics"])
        self.assertEqual(1, receipt["covered_topics"])
        self.assertEqual(0, receipt["verification_todo"])
        ledger = self.ledger_value()
        self.assertEqual({}, ledger["source_pass"]["topic_tasks"])
        self.assertEqual([], ledger["source_pass"]["todo"])

    def test_source_pass_rejects_covered_topic_without_defined_claim(self):
        plan = self.run / "invalid-covered-topic-plan.json"
        plan.write_text(
            json.dumps(
                {
                    "topics": [],
                    "covered": [
                        {
                            "id": "existing-architecture",
                            "title": "Existing architecture",
                            "responsibility": "Owns the fixture architecture.",
                            "reason": "The responsibility is architecturally durable.",
                            "files": [
                                "pyproject.toml",
                                "src/identity/session.py",
                            ],
                            "coverage_reason": "An unsupported coverage decision.",
                            "coverage": [
                                {
                                    "document": "architecture.md",
                                    "claims": ["OBS-not-defined"],
                                }
                            ],
                        }
                    ],
                    "supporting": [],
                    "open_leads": [],
                    "deferred_leads": [],
                }
            ),
            encoding="utf-8",
        )

        error = self.cli(
            "source-pass",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            "--discovery-corpus",
            str(self.discovery_corpus_path()),
            "--topic-plan",
            str(plan),
            expected=2,
        )

        self.assertIn("claim is not defined", error["error"])

    def test_inventory_classifies_nonproduction_files(self):
        additions = {
            "src/identity/messages.pb.go": "package identity",
            "src/identity/service_mock.go": "package identity",
            "src/identity/testdata/case.json": "{}",
            "src/identity/test-data/case.json": "{}",
            "src/identity/generated/client.ts": "export {}",
            "src/identity/session_test.go": "package identity",
            "public/img/icon.svg": "<svg/>",
            "public/locales/en-US/messages.json": "{}",
            "go.sum": "checksum",
            ".github/workflows/build.yml": "name: build",
            ".vscode/settings.json": "{}",
            ".gitignore": "dist/",
            "packages/ui/LICENSE_APACHE2": "license",
            "packages/ui/src/Button.mdx": "# Button",
            "packages/ui/tsconfig.build.json": "{}",
        }
        for relative, body in additions.items():
            path = self.repository / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")

        inventory = self.inventory()

        generated = inventory["excluded"]["generated"]
        self.assertIn("src/identity/messages.pb.go", generated)
        self.assertIn("src/identity/service_mock.go", generated)
        terminal_members = {
            path for values in inventory["excluded"].values() for path in values
        }
        for relative in (
            "src/identity/testdata/case.json",
            "src/identity/test-data/case.json",
            "src/identity/generated/client.ts",
            "src/identity/session_test.go",
        ):
            self.assertIn(relative, terminal_members)
        self.assertIn("public/img/icon.svg", inventory["excluded"]["opaque-asset"])
        self.assertIn(
            "public/locales/en-US/messages.json",
            inventory["excluded"]["opaque-asset"],
        )
        self.assertIn("go.sum", inventory["excluded"]["dependency-lock"])
        self.assertIn(
            ".github/workflows/build.yml",
            inventory["excluded"]["repository-support"],
        )
        for relative in (
            ".gitignore",
            ".vscode/settings.json",
            "packages/ui/LICENSE_APACHE2",
            "packages/ui/src/Button.mdx",
            "packages/ui/tsconfig.build.json",
        ):
            self.assertIn(relative, inventory["excluded"]["repository-support"])
        self.assertEqual(
            ["pyproject.toml", "src/identity/session.py"],
            inventory["production_files"],
        )

    def test_candidate_owner_search_uses_every_member_not_only_samples(self):
        root = self.repository / "src/identity"
        for index in range(25):
            (root / f"module_{index:02d}.py").write_text(
                f"VALUE = {index}\n",
                encoding="utf-8",
            )
        self.add_spine_candidate(
            "late-owner.md",
            "late-owner",
            "src/identity/module_24.py",
        )
        self.source_pass()
        _, task = self.task_for_unit("src/identity")
        self.assertIn("late-owner.md", task["documents"])
        self.assertTrue(task["evidence_strata"])
        self.assertEqual(1, len(task["evidence_strata"]))
        self.assertIn(task["evidence_strata"][0]["sample"], task["evidence"])

    def test_candidate_owner_packet_is_bounded(self):
        for index in range(20):
            self.add_spine_candidate(
                f"candidate-{index:02d}.md",
                f"candidate-{index:02d}",
                "src/identity",
            )
        self.source_pass()
        _, task = self.task_for_unit("src/identity")
        self.assertGreaterEqual(len(task["documents"]), 1)
        self.assertLessEqual(len(task["documents"]), 12)

    def test_broad_existing_owner_cannot_eliminate_verification_todo(self):
        self.source_pass()
        task_id, task = self.task_for_unit("src/identity")
        self.assertIn("architecture.md", task["documents"])
        self.assertEqual("todo", task["state"])
        self.assertIn(task_id, self.cli("ready", str(self.ledger))["ready"])
        packet = self.cli("packet", str(self.ledger), task_id)
        self.assertEqual(task_id, packet["task"]["id"])
        self.assertEqual(
            CAMPAIGN_MODULE.PRODUCER_CONTRACT_VERSION,
            packet["producer_contract"]["version"],
        )
        self.assertEqual(
            self.ledger_value()["producer_contract_digest"],
            packet["producer_contract"]["digest"],
        )
        self.assertEqual(
            self.ledger_value()["operation"],
            packet["operation"],
        )
        self.assertEqual(
            {
                "document": task["planned_document"],
                "exists": False,
            },
            packet["current_owner"],
        )
        self.assertTrue(packet["task"]["evidence_strata"])
        packet_path = self.run / "packets" / f"{task_id}.json"
        receipt = self.cli(
            "packet",
            str(self.ledger),
            task_id,
            "--output",
            str(packet_path),
        )
        self.assertEqual("written", receipt["status"])
        self.assertEqual(task_id, json.loads(packet_path.read_text())["task"]["id"])

    def test_packet_reports_existing_planned_owner_facets(self):
        (self.spine / "topics").mkdir()
        self.add_spine_candidate(
            "topics/src-identity.md",
            "src-identity",
            "src/identity/session.py",
        )
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "shared/scripts/rebuild_indexes.py"),
                str(self.spine),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        self.source_pass()
        task_id, task = self.task_for_unit("src/identity")

        packet = self.cli("packet", str(self.ledger), task_id)

        self.assertEqual(task["planned_document"], "topics/src-identity.md")
        self.assertEqual(
            {
                "document": "topics/src-identity.md",
                "exists": True,
                "owner": "src-identity",
                "kind": "concept",
                "facets": {
                    name: "missing"
                    for name in (
                        "architecture",
                        "behavior",
                        "interfaces",
                        "data",
                        "failure",
                        "quality",
                        "verification",
                    )
                },
                "blockers": [],
            },
            packet["current_owner"],
        )

    def test_discover_recent_incomplete_campaign_recommends_operator_resume(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)

        result = self.cli(
            "discover",
            str(self.run.parent),
            str(self.repository),
        )

        self.assertTrue(result["requires_operator_choice"])
        self.assertEqual(1, len(result["campaigns"]))
        campaign = result["campaigns"][0]
        self.assertEqual(str(self.ledger.resolve()), campaign["ledger"])
        self.assertEqual("recent", campaign["recency"])
        self.assertTrue(campaign["source_current"])
        self.assertTrue(campaign["resume_allowed"])
        self.assertEqual("resume", campaign["recommendation"])
        self.assertTrue(campaign["requires_operator_choice"])
        self.assertEqual(1, campaign["states"]["assigned"])

    def test_discover_finds_campaign_interrupted_before_source_pass(self):
        early_ledger = self.run.parent / "early" / "campaign.json"
        self.cli(
            "init",
            str(early_ledger),
            str(self.operation),
            "--repository-root",
            str(self.repository),
            "--allow-duplicate-incomplete",
        )

        result = self.cli(
            "discover",
            str(self.run.parent),
            str(self.repository),
        )

        self.assertEqual(2, len(result["campaigns"]))
        campaign = next(
            value
            for value in result["campaigns"]
            if value["ledger"] == str(early_ledger.resolve())
        )
        self.assertEqual(str(early_ledger.resolve()), campaign["ledger"])
        self.assertEqual("source_pass_missing", campaign["incomplete_reason"])
        self.assertIsNone(campaign["source_current"])
        self.assertTrue(campaign["resume_allowed"])

    def test_init_rejects_duplicate_incomplete_operation_without_override(self):
        duplicate = self.run.parent / "duplicate" / "campaign.json"
        error = self.cli(
            "init",
            str(duplicate),
            str(self.operation),
            "--repository-root",
            str(self.repository),
            expected=2,
        )
        self.assertIn("resume it instead", error["error"])

        created = self.cli(
            "init",
            str(duplicate),
            str(self.operation),
            "--repository-root",
            str(self.repository),
            "--allow-duplicate-incomplete",
        )
        self.assertEqual(14, created["schema_version"])

    def test_discover_stale_campaign_recommends_new_but_requires_choice(self):
        self.source_pass()
        ledger = self.ledger_value()
        ledger["updated_at"] = "2000-01-01T00:00:00Z"
        self.ledger.write_text(json.dumps(ledger), encoding="utf-8")

        result = self.cli(
            "discover",
            str(self.run.parent),
            str(self.repository),
        )

        campaign = result["campaigns"][0]
        self.assertEqual("stale", campaign["recency"])
        self.assertEqual("new", campaign["recommendation"])
        self.assertTrue(campaign["requires_operator_choice"])

    def test_resume_session_retains_assigned_tasks_for_handoff_recovery(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)

        receipt = self.cli("resume-session", str(self.ledger))

        self.assertEqual("resumed", receipt["status"])
        self.assertEqual([task_id], receipt["retained_assigned_tasks"])
        ledger = self.ledger_value()
        self.assertEqual("assigned", ledger["tasks"][task_id]["state"])
        self.assertEqual("/root/producer-1", ledger["tasks"][task_id]["owner"])
        self.assertEqual(
            [task_id],
            ledger["resume_history"][-1]["retained_assigned_tasks"],
        )
        self.assertEqual(
            "wait",
            self.cli("next-action", str(self.ledger))["action"],
        )

    def test_resume_harvests_completed_handoff_without_new_producer(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        self.checkpoint.write_text(
            json.dumps(
                self.checkpoint_payload(
                    outcome="covered",
                    evidence=["src/identity/session.py"],
                )
            ),
            encoding="utf-8",
        )
        package = Path(self.ledger_value()["tasks"][task_id]["handoff_package"])
        handoffs = package.parent
        package.mkdir(parents=True)
        shutil.copy2(self.checkpoint, package / "checkpoint.json")
        shutil.copytree(self.staging, package / "staging")
        harvest_root = self.run / "resume-harvest"

        resumed = self.cli("resume-session", str(self.ledger))
        self.assertEqual([task_id], resumed["retained_assigned_tasks"])
        settled = self.cli(
            "settle-wave",
            str(self.ledger),
            str(handoffs),
            str(self.spine),
            str(harvest_root),
        )
        self.assertEqual([task_id], settled["harvest"]["harvested_tasks"])

        task = self.ledger_value()["tasks"][task_id]
        self.assertEqual("review", settled["task_states"][task_id])
        self.assertEqual(1, task["attempts"])
        self.assertEqual("dispatch", self.cli("next-action", str(self.ledger))["action"])

    def test_resume_releases_only_task_without_atomic_handoff(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)

        self.cli("resume-session", str(self.ledger))
        settled = self.cli(
            "settle-wave",
            str(self.ledger),
            str(self.run / "handoffs"),
            str(self.spine),
            str(self.run / "missing-harvest"),
        )
        self.assertEqual("waiting_for_handoffs", settled["status"])
        self.assertEqual([task_id], settled["pending_tasks"])
        self.cli("release", str(self.ledger), task_id)

        task = self.ledger_value()["tasks"][task_id]
        self.assertEqual("todo", task["state"])
        self.assertEqual(1, task["attempts"])
        self.assertIn(task_id, self.cli("ready", str(self.ledger))["ready"])

    def test_resume_session_rejects_missing_contract_metadata(self):
        ledger = self.ledger_value()
        del ledger["producer_contract_version"]
        del ledger["producer_contract_digest"]
        self.ledger.write_text(json.dumps(ledger), encoding="utf-8")

        error = self.cli("resume-session", str(self.ledger), expected=2)
        self.assertIn(
            "campaign does not use the current producer contract",
            error["error"],
        )

    def test_unsupported_campaign_schema_is_rejected(self):
        ledger = self.ledger_value()
        ledger["schema_version"] = 10
        self.ledger.write_text(json.dumps(ledger), encoding="utf-8")

        error = self.cli("next-action", str(self.ledger), expected=2)

        self.assertIn("unsupported campaign schema", error["error"])
        self.assertIn(
            f"expected {CAMPAIGN_MODULE.SCHEMA_VERSION}",
            error["error"],
        )

    def test_contract_change_requires_new_campaign(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        ledger = self.ledger_value()
        ledger["producer_contract_digest"] = "0" * 64
        self.ledger.write_text(json.dumps(ledger), encoding="utf-8")

        packet_error = self.cli(
            "packet",
            str(self.ledger),
            task_id,
            expected=2,
        )
        self.assertIn("start a new campaign", packet_error["error"])
        error = self.cli("resume-session", str(self.ledger), expected=2)
        self.assertIn("start a new campaign", error["error"])

    def test_changed_source_disables_and_refuses_resume(self):
        self.source_pass()
        (self.repository / "src/identity/session.py").write_text(
            "SESSION = False\n",
            encoding="utf-8",
        )

        result = self.cli(
            "discover",
            str(self.run.parent),
            str(self.repository),
        )
        campaign = result["campaigns"][0]
        self.assertFalse(campaign["source_current"])
        self.assertFalse(campaign["resume_allowed"])
        self.assertEqual("new", campaign["recommendation"])
        error = self.cli("resume-session", str(self.ledger), expected=2)
        self.assertIn("source snapshot changed", error["error"])

    def test_discover_excludes_unrelated_repository_campaign(self):
        self.source_pass()
        unrelated = self.root / "unrelated"
        unrelated.mkdir()

        result = self.cli(
            "discover",
            str(unrelated / ".specspine" / "map"),
            str(unrelated),
        )

        self.assertFalse(result["requires_operator_choice"])
        self.assertEqual([], result["campaigns"])

    def test_campaign_records_and_updates_activity_timestamps(self):
        before = self.ledger_value()
        self.assertIsNotNone(before["created_at"])
        self.assertEqual(before["created_at"], before["updated_at"])

        self.source_pass()

        after = self.ledger_value()
        self.assertEqual(before["created_at"], after["created_at"])
        self.assertGreaterEqual(after["updated_at"], before["updated_at"])

    def test_existing_spine_requires_documentation_seed(self):
        ledger = self.run / "existing.json"
        self.cli(
            "init",
            str(ledger),
            str(self.operation),
            "--spine-state",
            "existing",
            "--repository-root",
            str(self.repository),
            "--allow-duplicate-incomplete",
        )
        error = self.cli(
            "source-pass",
            str(ledger),
            str(self.repository),
            str(self.spine),
            "--discovery-corpus",
            str(self.discovery_corpus_path()),
            "--topic-plan",
            str(self.topic_plan_path()),
            expected=2,
        )
        self.assertIn("seed-from-spine", error["error"])

    def test_existing_spine_seed_records_baseline_without_granting_coverage(self):
        ledger = self.run / "existing-seeded.json"
        self.cli(
            "init",
            str(ledger),
            str(self.operation),
            "--spine-state",
            "existing",
            "--repository-root",
            str(self.repository),
            "--allow-duplicate-incomplete",
        )
        receipt = self.cli(
            "seed-from-spine",
            str(ledger),
            str(self.spine),
        )
        self.assertEqual(3, receipt["documents"])
        self.assertEqual([], receipt["added_todo"])
        self.assertEqual(
            [],
            json.loads(ledger.read_text(encoding="utf-8"))[
                "documentation_seed"
            ]["todo"],
        )
        corpus = self.copy_discovery_state(ledger)
        self.cli(
            "source-pass",
            str(ledger),
            str(self.repository),
            str(self.spine),
            "--discovery-corpus",
            str(corpus),
            "--topic-plan",
            str(self.topic_plan_path()),
        )

    def test_documentation_seed_rejects_non_v3_spine(self):
        ledger = self.run / "invalid-existing.json"
        self.cli(
            "init",
            str(ledger),
            str(self.operation),
            "--spine-state",
            "existing",
            "--repository-root",
            str(self.repository),
            "--allow-duplicate-incomplete",
        )
        manifest_path = self.spine / "specspine.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["specspine"] = 2
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        error = self.cli(
            "seed-from-spine",
            str(ledger),
            str(self.spine),
            expected=2,
        )

        self.assertIn("current SpecSpine v3", error["error"])
        self.assertIn("MANIFEST_VERSION", error["error"])

    def test_documentation_seed_records_current_v3_defects_as_baseline(self):
        ledger = self.run / "defective-v3.json"
        self.cli(
            "init",
            str(ledger),
            str(self.operation),
            "--spine-state",
            "existing",
            "--repository-root",
            str(self.repository),
            "--allow-duplicate-incomplete",
        )
        with (self.spine / "_INDEX.md").open("a", encoding="utf-8") as stream:
            stream.write("\n## Coverage\n\nNon-semantic status in a v3 document.\n")

        receipt = self.cli("seed-from-spine", str(ledger), str(self.spine))

        self.assertGreater(receipt["checker_baseline_findings"], 0)
        baseline = json.loads(ledger.read_text(encoding="utf-8"))
        self.assertIn(
            "COMPLETENESS_IN_MARKDOWN",
            {
                finding["code"]
                for finding in baseline["documentation_seed"]["checker_baseline"]
            },
        )
        corpus = self.copy_discovery_state(ledger)
        self.cli(
            "source-pass",
            str(ledger),
            str(self.repository),
            str(self.spine),
            "--discovery-corpus",
            str(corpus),
            "--topic-plan",
            str(self.topic_plan_path()),
        )

    def test_source_pass_rejects_checker_finding_added_after_seed(self):
        ledger = self.run / "new-defect-after-seed.json"
        self.cli(
            "init",
            str(ledger),
            str(self.operation),
            "--spine-state",
            "existing",
            "--repository-root",
            str(self.repository),
            "--allow-duplicate-incomplete",
        )
        self.cli("seed-from-spine", str(ledger), str(self.spine))
        with (self.spine / "_INDEX.md").open("a", encoding="utf-8") as stream:
            stream.write("\n## Coverage\n\nNew non-semantic status.\n")

        error = self.cli(
            "source-pass",
            str(ledger),
            str(self.repository),
            str(self.spine),
            "--discovery-corpus",
            str(self.discovery_corpus_path()),
            "--topic-plan",
            str(self.topic_plan_path()),
            expected=2,
        )

        self.assertIn("COMPLETENESS_IN_MARKDOWN", error["error"])

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
            "--handoffs-root",
            str(self.run / "handoffs"),
            expected=2,
        )
        self.assertIn("one producer may run only one task", error["error"])

    def test_assign_returns_and_records_exact_attempt_handoff_package(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        handoffs = self.run / "exact handoffs"

        assigned = self.assign(task_id, handoffs=handoffs)

        expected = str((handoffs / f"{task_id}-1").resolve())
        self.assertEqual(1, assigned["attempt"])
        self.assertEqual(expected, assigned["handoff_package"])
        self.assertEqual(
            expected,
            self.ledger_value()["tasks"][task_id]["handoff_package"],
        )

    def test_covered_by_owner_requires_existing_semantic_claim(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        error = self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="covered",
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
                outcome="covered",
                evidence=["pyproject.toml"],
            ),
            expected=2,
        )
        self.assertIn("every evidence stratum", error["error"])

    def test_covered_by_owner_waits_for_root_integration(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        receipt = self.covered(task_id, "src/identity/session.py")
        self.assertEqual("review", receipt["task_state"])
        next_action = self.cli("next-action", str(self.ledger))
        self.assertFalse(
            next_action["terminal_gates"]["publications_integrated"]
        )

    def test_settle_wave_derives_paths_without_shell_parsing(self):
        self.source_pass()
        ledger = self.ledger_value()
        handoffs = self.run / "handoffs with spaces"
        harvest = self.run / "harvest receipts"
        assigned = []
        for index, task in enumerate(ledger["tasks"].values()):
            owner = f"/root/producer-{index}"
            self.assign(task["id"], owner, handoffs)
            package = handoffs / f"{task['id']}-1"
            staging = package / "staging"
            staging.mkdir(parents=True)
            evidence = task["evidence"]
            (package / "checkpoint.json").write_text(
                json.dumps(
                    self.checkpoint_payload(
                        outcome="covered",
                        evidence=evidence,
                    )
                ),
                encoding="utf-8",
            )
            assigned.append(task["id"])

        settled = self.cli(
            "settle-wave",
            str(self.ledger),
            str(handoffs),
            str(self.spine),
            str(harvest),
        )
        self.assertEqual("settled_wave", settled["status"])
        self.assertEqual(2, settled["harvest"]["harvested"])
        self.assertEqual(2, settled["accepted"])
        self.assertEqual(
            {task_id: "review" for task_id in assigned},
            settled["task_states"],
        )

    def test_settle_wave_reports_invalid_handoff_without_hiding_valid_sibling(self):
        self.source_pass()
        ledger = self.ledger_value()
        handoffs = self.run / "handoffs"
        harvest = self.run / "harvest"
        tasks = list(ledger["tasks"].values())
        for index, task in enumerate(tasks):
            owner = f"/root/producer-{index}"
            self.assign(task["id"], owner, handoffs)
            package = handoffs / f"{task['id']}-1"
            (package / "staging").mkdir(parents=True)
            evidence = task["evidence"]
            outcome = "answered" if index == 0 else "covered"
            (package / "checkpoint.json").write_text(
                json.dumps(
                    self.checkpoint_payload(
                        outcome=outcome,
                        evidence=evidence,
                    )
                ),
                encoding="utf-8",
            )

        result = self.cli(
            "settle-wave",
            str(self.ledger),
            str(handoffs),
            str(self.spine),
            str(harvest),
        )

        self.assertEqual("needs_mechanical_repair", result["status"])
        self.assertEqual(1, result["harvested"])
        self.assertEqual(1, result["rejected"])
        self.assertIn(
            "integration-derived",
            result["rejected_tasks"][0]["error"],
        )

    def test_covered_requires_evidence_from_every_mechanical_stratum(self):
        root = self.repository / "src/identity"
        for index in range(40):
            (root / f"module_{index:02d}.py").write_text(
                f"VALUE = {index}\n",
                encoding="utf-8",
            )
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        error = self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="covered",
                evidence=["src/identity/session.py"],
            ),
            expected=2,
        )
        self.assertIn("every evidence stratum", error["error"])

    def test_producer_can_classify_unit_as_supporting(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        receipt = self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="supporting",
                evidence=["src/identity/session.py"],
            ),
        )
        self.assertEqual("review", receipt["task_state"])
        self.integrate()
        task = self.ledger_value()["tasks"][task_id]
        self.assertEqual("complete", task["state"])
        self.assertEqual("supporting", task["checkpoint_outcome"])

    def test_root_can_retry_weak_supporting_receipt(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="supporting",
                evidence=["src/identity/session.py"],
            ),
        )
        report = self.integration_report()
        report["task_reviews"][0]["disposition"] = "retry"
        self.integrate(report)
        self.assertEqual("todo", self.ledger_value()["tasks"][task_id]["state"])

    def test_draft_publication_records_suggestions_but_not_todo(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        (self.staging / "identity.md").write_text(
            "# Identity\n\n- **OBS-identity-owner** — owner.\n"
            + self.draft_evidence(task_id),
            encoding="utf-8",
        )
        direction = "Who owns failed refresh recovery?"
        receipt = self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="draft",
                evidence=["src/identity/session.py"],
                directions=[direction],
            ),
        )
        self.assertEqual("published", receipt["task_state"])
        self.assertEqual(1, len(receipt["suggestions_pending_review"]))
        self.assertNotIn(receipt["suggestions_pending_review"][0], self.ledger_value()["tasks"])

    def test_normative_suggestion_can_be_preserved_without_map_todo(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        (self.staging / "identity.md").write_text(
            "# Identity\n\n"
            "- **OBS-identity-owner** — `src/identity/session.py`.\n"
            + self.draft_evidence(task_id),
            encoding="utf-8",
        )
        question = "What recovery guarantee should the system provide?"
        self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="draft",
                evidence=["src/identity/session.py"],
                directions=[question],
            ),
        )
        workspace = self.prepare_integration()
        with (workspace / "architecture.md").open("a", encoding="utf-8") as stream:
            stream.write(f"\n- {question}\n")
        report = self.integration_report(workspace=workspace)
        suggestion = self.ledger_value()["tasks"][task_id]["producer_suggestions"][0]
        report["suggestion_reviews"] = [
            {
                "task": task_id,
                "suggestion": suggestion["id"],
                "disposition": "preserved",
                "document": "architecture.md",
                "reason": "Repository evidence cannot decide required policy",
            }
        ]

        self.integrate(report, workspace=workspace)

        review = self.ledger_value()["tasks"][task_id]["suggestion_reviews"][
            suggestion["id"]
        ]
        self.assertEqual("preserved", review["disposition"])
        self.assertNotIn(suggestion["id"], self.ledger_value()["tasks"])

    def test_accept_keeps_draft_private_until_checked_integration(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        (self.staging / "identity.md").write_text(
            "# Identity\n\n"
            "- **OBS-identity-owner** — `src/identity/session.py`.\n"
            + self.draft_evidence(task_id),
            encoding="utf-8",
        )
        self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="draft",
                evidence=["src/identity/session.py"],
            ),
        )
        self.assertFalse((self.spine / "identity.md").exists())
        workspace = self.prepare_integration()
        self.assertTrue((workspace / "identity.md").is_file())
        self.assertFalse((self.spine / "identity.md").exists())
        self.integrate(workspace=workspace)
        self.assertTrue((self.spine / "identity.md").is_file())

    def test_assembly_materializes_synthesized_graph_and_publishes_once(self):
        self.source_pass()
        ledger = self.ledger_value()
        topics = {
            topic["id"]: topic
            for topic in ledger["source_pass"]["topic_plan"]["topics"]
        }
        for index, (topic_id, task_id) in enumerate(
            sorted(ledger["source_pass"]["topic_tasks"].items())
        ):
            owner = f"/root/assembly-producer-{index}"
            self.assign(task_id, owner)
            shutil.rmtree(self.staging)
            self.staging.mkdir()
            document = self.staging / topics[topic_id]["document"]
            document.parent.mkdir(parents=True, exist_ok=True)
            evidence = self.ledger_value()["tasks"][task_id]["evidence"]
            document.write_text(
                f"# {topics[topic_id]['title']}\n\n"
                f"**ID:** `{topic_id}` · **Kind:** `component`\n\n"
                "Observed architectural owner for this fixture boundary.\n\n"
                "## Responsibility\n\n"
                f"{topics[topic_id]['responsibility']}\n\n"
                + self.draft_evidence(task_id)
                + "\n<!-- specspine:semantic-ids:begin -->\n"
                "## Observed\n\n"
                f"- **OBS-{topic_id}-owner** — Observed owner. "
                f"Evidence: `{evidence[0]}`.\n"
                "<!-- specspine:semantic-ids:end -->\n",
                encoding="utf-8",
            )
            self.accept(
                task_id,
                self.checkpoint_payload(
                    outcome="draft",
                    evidence=evidence,
                    directions=(
                        ["Should this synthesized dependency be refined later?"]
                        if index == 0
                        else []
                    ),
                ),
                owner=owner,
            )

        result = self.cli(
            "assemble-integration",
            str(self.ledger),
            str(self.spine),
            "--checker",
            str(ROOT / "skills/specspine-map/scripts/check_spine.py"),
        )

        self.assertEqual("assembled_and_integrated", result["status"])
        self.assertEqual(
            str((self.run / "integration-workspace").resolve()),
            result["workspace"],
        )
        self.assertEqual(
            str((self.run / "integration-report.json").resolve()),
            result["report"],
        )
        first_task = next(
            task
            for task in self.ledger_value()["tasks"].values()
            if task["producer_suggestions"]
        )
        suggestion_id = first_task["producer_suggestions"][0]["id"]
        self.assertEqual(
            "rejected",
            first_task["suggestion_reviews"][suggestion_id]["disposition"],
        )
        readme = (self.spine / "_INDEX.md").read_text(encoding="utf-8")
        self.assertIn("[topics/](topics/_INDEX.md)", readme)
        for topic in topics.values():
            body = (self.spine / topic["document"]).read_text(encoding="utf-8")
            self.assertIn("## Relationships", body)
            topic_index = (self.spine / Path(topic["document"]).parent / "_INDEX.md")
            self.assertIn(Path(topic["document"]).name, topic_index.read_text())
        second = self.cli(
            "assemble-integration",
            str(self.ledger),
            str(self.spine),
            "--checker",
            str(ROOT / "skills/specspine-map/scripts/check_spine.py"),
        )
        self.assertEqual("already_integrated", second["status"])

    def test_integration_derived_answer_uses_distinct_outcome(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.covered(task_id, "src/identity/session.py")
        question = {
            "id": "session-runtime-owner",
            "question": "Who owns the session runtime?",
            "reason": "The owner must be addressed explicitly",
            "evidence": ["src/identity/session.py"],
            "documents": ["architecture.md"],
            "excludes": [],
            "anchor": {
                "document": "architecture.md",
                "location": "Architecture map",
                "known": "The repository root cites the session source",
            },
        }
        first_workspace = self.prepare_integration()
        with (first_workspace / "architecture.md").open("a", encoding="utf-8") as stream:
            stream.write("\nWho owns the session runtime?\n")
        self.integrate(
            self.integration_report(todo=[question], workspace=first_workspace),
            workspace=first_workspace,
        )
        self.assign("session-runtime-owner", "/root/producer-answer")
        receipt = self.accept(
            "session-runtime-owner",
            self.checkpoint_payload(
                outcome="answered",
                evidence=["src/identity/session.py"],
            ),
            owner="/root/producer-answer",
        )
        self.assertEqual("review", receipt["task_state"])
        report = self.integration_report()
        self.assertEqual(
            "answered_canonical",
            report["task_reviews"][0]["disposition"],
        )
        error = self.integrate(report, expected=2)
        self.assertIn("resolved anchor question remains", error["error"])
        workspace = self.prepare_integration()
        readme = workspace / "architecture.md"
        readme.write_text(
            readme.read_text(encoding="utf-8").replace(
                "\nWho owns the session runtime?\n",
                "\n",
            ),
            encoding="utf-8",
        )
        self.integrate(
            self.integration_report(workspace=workspace),
            workspace=workspace,
        )
        self.assertEqual(
            "complete",
            self.ledger_value()["tasks"]["session-runtime-owner"]["state"],
        )

    def test_refined_anchor_requires_named_narrower_todo(self):
        task_id = self.unresolved_anchored_task()
        report = self.integration_report()
        report["task_reviews"][0]["anchor_disposition"] = {
            "status": "refined",
            "reason": "Recovery ownership is now narrowed to retry exhaustion",
            "todo": "session-retry-owner",
        }
        error = self.integrate(report, expected=2)
        self.assertIn("needs matching integration ToDo", error["error"])

        successor = {
            "id": "session-retry-owner",
            "question": "Who owns recovery after retries are exhausted?",
            "reason": "The broader recovery question was narrowed",
            "evidence": ["src/identity/session.py"],
            "documents": ["architecture.md"],
            "excludes": [],
            "anchor": {
                "document": "architecture.md",
                "location": "Architecture map",
                "known": "Normal and failed session ownership were separated",
            },
        }
        report = self.integration_report(todo=[successor])
        report["task_reviews"][0]["anchor_disposition"] = {
            "status": "refined",
            "reason": "Recovery ownership is now narrowed to retry exhaustion",
            "todo": successor["id"],
        }
        self.integrate(report)
        self.assertEqual(
            "todo",
            self.ledger_value()["tasks"][successor["id"]]["state"],
        )

    def test_blocking_anchor_requires_owner_oq_and_manifest_registration(self):
        self.unresolved_anchored_task()
        report = self.integration_report()
        workspace = self.current_workspace
        report["task_reviews"][0]["anchor_disposition"] = {
            "status": "blocking",
            "reason": "A reconstruction agent cannot choose recovery ownership",
            "blocker": "OQ-session-recovery-owner",
        }
        error = self.integrate(report, expected=2)
        self.assertIn("must define OQ-session-recovery-owner", error["error"])

        readme = workspace / "architecture.md"
        readme.write_text(
            readme.read_text(encoding="utf-8").replace(
                "<!-- specspine:semantic-ids:end -->",
                "- **OQ-session-recovery-owner** — Who owns failed session recovery?\n"
                "<!-- specspine:semantic-ids:end -->",
            ),
            encoding="utf-8",
        )
        manifest_path = workspace / "specspine.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["areas"][0]["blockers"] = ["OQ-session-recovery-owner"]
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        report = self.integration_report(workspace=workspace)
        report["task_reviews"][0]["anchor_disposition"] = {
            "status": "blocking",
            "reason": "A reconstruction agent cannot choose recovery ownership",
            "blocker": "OQ-session-recovery-owner",
        }
        self.integrate(report, workspace=workspace)

    def test_needs_more_evidence_returns_task_for_fresh_producer(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        receipt = self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="retry",
                evidence=["src/identity/session.py"],
            ),
        )
        self.assertEqual("todo", receipt["task_state"])
        self.assertIn(
            "src/identity/recovery.py",
            self.ledger_value()["tasks"][task_id]["evidence"],
        )

    def test_integration_checker_failure_preserves_live_spine(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        source = self.staging / "identity.md"
        source.write_text(
            "# Identity\n\n"
            "- **OBS-identity-owner** — `src/identity/session.py`.\n"
            + self.draft_evidence(task_id),
            encoding="utf-8",
        )
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
                outcome="draft",
                evidence=["src/identity/session.py"],
            ),
        )
        report = self.integration_report()
        error = self.integrate(report, expected=2)
        self.assertIn("checker rejected", error["error"])
        self.assertTrue(source.exists())
        self.assertFalse((self.spine / "identity.md").exists())
        self.assertEqual("published", self.ledger_value()["tasks"][task_id]["state"])

    def test_ledger_write_failure_rolls_back_published_spine(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.covered(task_id, "src/identity/session.py")
        workspace = self.prepare_integration()
        with (workspace / "architecture.md").open("a", encoding="utf-8") as stream:
            stream.write("\nRollback candidate content.\n")
        report = self.integration_report(workspace=workspace)
        report_path = self.run / "rollback-integration.json"
        report_path.write_text(json.dumps(report), encoding="utf-8")
        before_ledger = self.ledger.read_bytes()
        before_documents = CAMPAIGN_MODULE.document_hashes(self.spine)

        args = argparse.Namespace(
            ledger=self.ledger,
            spine_root=self.spine,
            workspace=workspace,
            report=report_path,
            checker=self.checker,
        )
        with mock.patch.object(
            CAMPAIGN_MODULE,
            "save_locked",
            side_effect=OSError("injected ledger write failure"),
        ):
            with self.assertRaisesRegex(OSError, "injected ledger write failure"):
                CAMPAIGN_MODULE.command_integration_pass(args)

        self.assertEqual(before_ledger, self.ledger.read_bytes())
        self.assertEqual(
            before_documents,
            CAMPAIGN_MODULE.document_hashes(self.spine),
        )
        self.assertEqual(
            [],
            list(self.spine.parent.glob(f".{self.spine.name}.map-*")),
        )

    def test_candidate_checker_receives_live_root_and_staging_path(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        (self.staging / "identity.md").write_text(
            "# Identity\n\n"
            "- **OBS-identity-owner** — `src/identity/session.py`.\n"
            + self.draft_evidence(task_id),
            encoding="utf-8",
        )
        self.checker.write_text(
            "import json, pathlib, sys\n"
            "if '--candidates' in sys.argv:\n"
            "    index = sys.argv.index('--candidates')\n"
            "    valid = pathlib.Path(sys.argv[1]).is_dir() and "
            "pathlib.Path(sys.argv[index + 1]).is_dir()\n"
            "else:\n"
            "    valid = pathlib.Path(sys.argv[1]).is_dir()\n"
            "print(json.dumps([] if valid else [{'code':'BAD_ARGS'}]))\n"
            "raise SystemExit(0 if valid else 1)\n",
            encoding="utf-8",
        )
        receipt = self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="draft",
                evidence=["src/identity/session.py"],
            ),
        )
        self.assertEqual("published", receipt["task_state"])

    def test_root_cannot_discard_source_publication_as_not_architectural(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        (self.staging / "identity.md").write_text(
            "# Identity\n\n"
            "- **OBS-identity-owner** — `src/identity/session.py`.\n"
            + self.draft_evidence(task_id),
            encoding="utf-8",
        )
        self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="draft",
                evidence=["src/identity/session.py"],
            ),
        )
        report = self.integration_report()
        report["task_reviews"][0]["disposition"] = "not_architectural"
        error = self.integrate(report, expected=2)
        self.assertIn("invalid integration disposition", error["error"])

    def test_root_cannot_mark_deleted_source_publication_integrated(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        (self.staging / "identity.md").write_text(
            "# Identity\n\n"
            "- **OBS-identity-owner** — `src/identity/session.py`.\n"
            + self.draft_evidence(task_id),
            encoding="utf-8",
        )
        self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="draft",
                evidence=["src/identity/session.py"],
            ),
        )
        workspace = self.prepare_integration()
        (workspace / "identity.md").unlink()
        report = self.integration_report(workspace=workspace)
        error = self.integrate(report, expected=2)
        self.assertIn("cannot discard producer publications", error["error"])

    def test_new_owner_requires_typed_graph_connection(self):
        neighbor_source = self.repository / "src/neighbor/service.py"
        neighbor_source.parent.mkdir(parents=True)
        neighbor_source.write_text("SERVICE = True\n", encoding="utf-8")
        self.add_spine_candidate(
            "neighbor.md",
            "neighbor",
            "src/neighbor/service.py",
        )
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        (self.staging / "identity.md").write_text(
            "# Identity\n\n"
            "**ID:** `identity` · **Kind:** `component`\n\n"
            "Observed identity boundary.\n\n"
            "## Responsibility\n\n"
            "Owns observed session handling.\n\n"
            f"{self.ledger_value()['tasks'][task_id]['evidence_baseline']}\n"
            "<!-- specspine:semantic-ids:begin -->\n"
            "## Observed\n\n"
            "- **OBS-identity-owner** — Session code exists. "
            "Evidence: `src/identity/session.py`.\n"
            "<!-- specspine:semantic-ids:end -->\n",
            encoding="utf-8",
        )
        self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="draft",
                evidence=["src/identity/session.py"],
            ),
        )
        workspace = self.prepare_integration()
        report = self.integration_report(workspace=workspace)

        error = self.integrate(report, workspace=workspace, expected=2)

        self.assertIn("typed relationship", error["error"])

    def test_integration_adds_document_derived_todo(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.covered(task_id, "src/identity/session.py")
        new_todo = {
            "id": "session-recovery",
            "question": "Who owns failed refresh recovery?",
            "reason": "Integration exposes unresolved recovery",
            "evidence": ["src/identity/session.py"],
            "documents": ["architecture.md"],
            "excludes": [],
            "anchor": {
                "document": "architecture.md",
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

    def test_integration_todo_must_match_visible_anchor_question(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.covered(task_id, "src/identity/session.py")
        workspace = self.prepare_integration()
        todo = {
            "id": "session-recovery",
            "question": "What recovery behavior is currently observed?",
            "reason": "Recovery evidence remains incomplete",
            "basis": "repository-observation",
            "evidence": ["src/identity/session.py"],
            "documents": ["architecture.md"],
            "excludes": [],
            "anchor": {
                "document": "architecture.md",
                "location": "Architecture map",
                "known": "Normal session ownership is documented",
                "question": "What recovery behavior should be guaranteed?",
            },
        }

        report = self.integration_report(todo=[todo], workspace=workspace)
        error = self.integrate(report, workspace=workspace, expected=2)

        self.assertIn("exactly match anchor question", error["error"])

    def test_integration_rejects_normative_map_todo_basis(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.covered(task_id, "src/identity/session.py")
        workspace = self.prepare_integration()
        todo = {
            "id": "session-policy",
            "question": "What recovery guarantee should be accepted?",
            "reason": "Policy remains undecided",
            "basis": "normative-policy",
            "evidence": ["src/identity/session.py"],
            "documents": ["architecture.md"],
            "excludes": [],
            "anchor": {
                "document": "architecture.md",
                "location": "Architecture map",
                "known": "Current behavior is observed",
                "question": "What recovery guarantee should be accepted?",
            },
        }

        report = self.integration_report(todo=[todo], workspace=workspace)
        error = self.integrate(report, workspace=workspace, expected=2)

        self.assertIn("basis must be repository-observation", error["error"])

    def test_integration_records_and_returns_exact_live_document_changes(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        (self.staging / "identity.md").write_text(
            "# Identity\n\n"
            "- **OBS-identity-owner** — `src/identity/session.py`.\n"
            + self.draft_evidence(task_id),
            encoding="utf-8",
        )
        self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="draft",
                evidence=["src/identity/session.py"],
            ),
        )
        workspace = self.prepare_integration()
        (workspace / "architecture.md").write_text(
            (workspace / "architecture.md").read_text(encoding="utf-8")
            + "\nSee [Identity](identity.md).\n",
            encoding="utf-8",
        )
        result = self.integrate(workspace=workspace)
        expected = [
            {"path": "architecture.md", "operation": "changed"},
            {"path": "identity.md", "operation": "created"},
        ]
        self.assertEqual(expected, result["changed_documents"])
        ledger = self.ledger_value()
        self.assertEqual(
            [
                {"publication_epoch": 1, **change}
                for change in expected
            ],
            ledger["document_change_history"],
        )

    def test_integration_rejects_incomplete_document_change_report(self):
        self.source_pass()
        workspace = self.prepare_integration()
        (workspace / "architecture.md").write_text(
            "# Architecture\n\nChanged by root.\n",
            encoding="utf-8",
        )
        report = self.integration_report(workspace=workspace)
        report["changed_documents"] = []
        error = self.integrate(report, expected=2)
        self.assertIn(
            "does not match workspace changes",
            error["error"],
        )

    def test_integration_rejects_missing_spine_snapshot(self):
        self.source_pass()
        self.integrate()
        ledger = self.ledger_value()
        ledger.pop("spine_snapshot")
        self.ledger.write_text(json.dumps(ledger), encoding="utf-8")
        error = self.cli(
            "prepare-integration",
            str(self.ledger),
            str(self.spine),
            str(self.run / "invalid-workspace"),
            expected=2,
        )
        self.assertIn("campaign Spine snapshot is invalid", error["error"])

    def test_prepare_integration_resumes_matching_edited_workspace(self):
        self.source_pass()
        workspace = self.prepare_integration()
        (workspace / "architecture.md").write_text(
            (workspace / "architecture.md").read_text(encoding="utf-8")
            + "\nRoot work in progress.\n",
            encoding="utf-8",
        )
        result = self.cli(
            "prepare-integration",
            str(self.ledger),
            str(self.spine),
            str(workspace),
        )
        self.assertEqual("already_ready", result["status"])
        self.assertIn(
            "Root work in progress.",
            (workspace / "architecture.md").read_text(encoding="utf-8"),
        )

    def test_integration_must_review_every_covered_task(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.covered(task_id, "src/identity/session.py")
        report = self.integration_report()
        report["task_reviews"] = []
        error = self.integrate(report, expected=2)
        self.assertIn("every settled producer task", error["error"])

    def test_scope_verified_requires_every_unit_and_empty_integration(self):
        self.verify_all_source_units()
        next_action = self.cli("next-action", str(self.ledger))
        self.assertEqual("scope_verified", next_action["terminal"])
        self.assertTrue(all(next_action["terminal_gates"].values()))
        self.assertTrue(next_action["may_finish"])
        self.assertEqual("finalize", next_action["action"])

    def test_unclean_v3_integration_requires_repair_before_finalize(self):
        self.verify_all_source_units()
        ledger = self.ledger_value()
        ledger["integration_pass"]["checker_clean"] = False
        self.ledger.write_text(json.dumps(ledger), encoding="utf-8")

        next_action = self.cli("next-action", str(self.ledger))

        self.assertFalse(next_action["terminal_gates"]["spine_v3_clean"])
        self.assertIsNone(next_action["terminal"])
        self.assertEqual("repair", next_action["action"])
        self.assertFalse(next_action["may_finish"])

    def test_next_action_for_active_campaign_forbids_finishing(self):
        self.source_pass()
        next_action = self.cli("next-action", str(self.ledger))
        self.assertFalse(next_action["may_finish"])
        self.assertEqual("dispatch", next_action["action"])
        self.assertEqual(
            "continue_in_same_turn_no_final_response",
            next_action["response_policy"],
        )
        self.assertGreater(next_action["counts"]["todo"], 0)

    def test_next_action_routes_every_preproduction_state(self):
        initial = self.cli("next-action", str(self.ledger))
        self.assertEqual("discover", initial["action"])
        self.assertFalse(initial["may_pause"])

        for status, action, may_pause in (
            ("discovering", "discover", False),
            ("synthesis", "synthesize", True),
            ("invalid", "repair", False),
        ):
            with self.subTest(status=status):
                ledger = self.ledger_value()
                ledger["discovery"] = {"status": status}
                self.ledger.write_text(json.dumps(ledger), encoding="utf-8")
                result = self.cli("next-action", str(self.ledger))
                self.assertEqual(action, result["action"])
                self.assertEqual(may_pause, result["may_pause"])
                self.assertFalse(result["may_finish"])

    def test_next_action_waits_then_integrates_settled_results(self):
        self.source_pass()
        task_id, task = self.task_for_unit("src/identity")
        self.assign(task_id)

        waiting = self.cli("next-action", str(self.ledger))
        self.assertEqual("wait", waiting["action"])
        self.assertEqual(1, waiting["counts"]["assigned"])

        self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="covered",
                evidence=task["evidence"],
            ),
        )
        integrating = self.cli("next-action", str(self.ledger))
        self.assertEqual("dispatch", integrating["action"])
        self.assertEqual(1, integrating["counts"]["review"])

    def test_blocked_producers_reach_report_blocked(self):
        self.source_pass()
        ledger = self.ledger_value()
        for index, task_id in enumerate(ledger["source_pass"]["todo"]):
            task = ledger["tasks"][task_id]
            owner = f"/root/blocked-producer-{index}"
            self.assign(task_id, owner)
            receipt = self.accept(
                task_id,
                self.checkpoint_payload(
                    outcome="blocked",
                    evidence=task["evidence"],
                ),
                owner=owner,
            )
            self.assertEqual("blocked", receipt["task_state"])

        result = self.cli("next-action", str(self.ledger))
        self.assertEqual("blocked", result["terminal"])
        self.assertEqual("report_blocked", result["action"])
        self.assertTrue(result["may_finish"])

    def test_retry_blocked_reopens_only_one_task_idempotently(self):
        self.source_pass()
        task_id, task = self.task_for_unit("src/identity")
        self.assign(task_id)
        self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="blocked",
                evidence=task["evidence"],
            ),
        )

        reopened = self.cli(
            "retry-blocked",
            str(self.ledger),
            task_id,
            "--reason",
            "Candidate checker treated an integration-owned index as missing",
        )
        self.assertEqual("retryable", reopened["status"])
        ledger = self.ledger_value()
        self.assertEqual("todo", ledger["tasks"][task_id]["state"])
        self.assertEqual(1, len(ledger["tasks"][task_id]["retry_history"]))

        repeated = self.cli(
            "retry-blocked",
            str(self.ledger),
            task_id,
            "--reason",
            "Candidate checker treated an integration-owned index as missing",
        )
        self.assertEqual("already_retryable", repeated["status"])
        self.assertEqual(
            1,
            len(self.ledger_value()["tasks"][task_id]["retry_history"]),
        )

    def test_integration_evidence_may_be_relevant_live_subset(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.covered(task_id, "src/identity/session.py")
        report = self.integration_report()
        report["evidence_inspected"] = ["_INDEX.md"]
        result = self.integrate(report)
        self.assertEqual("integrated", result["status"])

    def test_integration_evidence_rejects_unknown_document(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.covered(task_id, "src/identity/session.py")
        report = self.integration_report()
        report["evidence_inspected"] = ["missing.md"]
        error = self.integrate(report, expected=2)
        self.assertIn("only workspace Markdown documents", error["error"])

    def test_repository_content_change_invalidates_scope_snapshot(self):
        self.verify_all_source_units()
        (self.repository / "src/identity/session.py").write_text(
            "SESSION = False\nRECOVERY = True\n",
            encoding="utf-8",
        )
        next_action = self.cli("next-action", str(self.ledger))
        self.assertFalse(
            next_action["terminal_gates"]["operation_snapshot_current"]
        )
        self.assertIsNone(next_action["terminal"])

    def test_live_spine_change_invalidates_integration(self):
        self.verify_all_source_units()
        (self.spine / "_INDEX.md").write_text(
            "# Architecture\n\nChanged after integration.\n",
            encoding="utf-8",
        )
        next_action = self.cli("next-action", str(self.ledger))
        self.assertFalse(next_action["terminal_gates"]["integration_current"])
        self.assertIsNone(next_action["terminal"])

    def test_finalize_requires_scope_verified(self):
        self.verify_all_source_units()
        receipt = self.cli(
            str(self.ledger),
            str(self.spine),
            "--checker",
            str(self.checker),
            script=FINALIZE,
        )
        self.assertEqual("finalized", receipt["status"])
        self.assertEqual("scope_verified", receipt["terminal"])
        self.assertEqual(
            "selected observation scope completed",
            receipt["terminal_claim"],
        )
        self.assertEqual(
            {
                "status": "incomplete",
                "areas": {
                    "total": 1,
                    "ready": 0,
                    "incomplete": 1,
                    "blocked": 0,
                },
                "facets": {
                    "complete": 0,
                    "missing": 0,
                    "not-applicable": 3,
                    "partial": 4,
                },
            },
            receipt["reconstruction_readiness"],
        )
        self.assertEqual([], receipt["changed_documents"])
        self.assertEqual([], receipt["document_change_history"])

    def test_finalize_passes_recorded_repository_root_to_checker(self):
        self.verify_all_source_units()
        ledger = self.ledger_value()
        ledger["repository_root"] = str(self.repository.resolve())
        self.ledger.write_text(json.dumps(ledger), encoding="utf-8")
        checker = self.root / "repository-aware-checker.py"
        checker.write_text(
            "import json, pathlib, sys\n"
            "valid = '--repository-root' in sys.argv and "
            "pathlib.Path(sys.argv[sys.argv.index('--repository-root') + 1]).is_dir()\n"
            "print(json.dumps([] if valid else [{'code':'MISSING_REPOSITORY_ROOT'}]))\n"
            "raise SystemExit(0 if valid else 1)\n",
            encoding="utf-8",
        )

        receipt = self.cli(
            str(self.ledger),
            str(self.spine),
            "--checker",
            str(checker),
            script=FINALIZE,
        )

        self.assertEqual("finalized", receipt["status"])


if __name__ == "__main__":
    unittest.main()
