import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]


class MapLargeContractTests(unittest.TestCase):
    def test_map_is_atomic_and_large_orchestration_is_explicit(self):
        mapper = (ROOT / "skills/specspine-map/SKILL.md").read_text(encoding="utf-8")
        large = (ROOT / "skills/specspine-map-large/SKILL.md").read_text(
            encoding="utf-8"
        )
        metadata = (ROOT / "skills/specspine-map-large/agents/openai.yaml").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("references/orchestration.md", mapper)
        self.assertNotIn("producer-consumer", mapper)
        self.assertNotIn("Normalize once after saturation", mapper)
        self.assertNotIn("specspine-map-large", mapper)
        self.assertIn("the requested repository scope", mapper)
        self.assertIn(
            "one or more selected areas or questions", " ".join(mapper.split())
        )
        self.assertIn("references/orchestration.md", large)
        self.assertIn("complete self-contained producer command", large)
        self.assertIn("bundle_skill.py", large)
        self.assertIn("bundle_skill.py --print", large)
        self.assertIn(
            "complete body with every UTF-8", " ".join(large.split())
        )
        self.assertIn("Do not read the generated file afterward", large)
        self.assertNotIn("specspine:map-core:", mapper)
        self.assertIn("allow_implicit_invocation: false", metadata)
        self.assertEqual(
            ["orchestration.md"],
            sorted(
                path.name
                for path in (
                    ROOT / "skills/specspine-map-large/references"
                ).iterdir()
            ),
        )
        self.assertFalse((ROOT / "skills/specspine-map-large/assets").exists())

    def test_parallel_producers_are_isolated(self):
        protocol = (
            ROOT / "skills/specspine-map-large/references/orchestration.md"
        ).read_text(encoding="utf-8")
        required = (
            "publish-ready Markdown only",
            "Keep source, tests,",
            "Schedule as producer-consumer",
            "Consume completed results",
            "Normalize once after saturation",
            "Do not use a requested or desired document count",
        )
        for statement in required:
            with self.subTest(statement=statement):
                self.assertIn(statement, protocol)

    def test_staged_publication_preflights_without_model_read_then_moves_unchanged(self):
        protocol = (
            ROOT / "skills/specspine-map-large/references/orchestration.md"
        ).read_text(encoding="utf-8")
        publication = protocol.split("## Consume and publish results", 1)[1].split(
            "## Continue to saturation", 1
        )[0]
        doctor = (ROOT / "skills/specspine-doctor/SKILL.md").read_text(
            encoding="utf-8"
        )
        normalized_publication = " ".join(publication.split())
        self.assertIn("without reading candidate prose or repository source", normalized_publication)
        self.assertIn("--candidates <private-staging-root> --json", normalized_publication)
        self.assertIn("private staging root mirrors the Spine", normalized_publication)
        self.assertIn("Publish only after a successful empty result", normalized_publication)
        self.assertIn("must not repeat that work", normalized_publication)
        self.assertIn("filesystem move/rename tool", normalized_publication)
        self.assertIn("never reconstruct the file", normalized_publication)
        self.assertIn("do not reread it after the move", normalized_publication)
        self.assertIn("Do not manually reread, merge, semantically rewrite", normalized_publication)
        self.assertNotIn("parallel Map", doctor)
        self.assertNotIn("parallel mapping", doctor)

    def test_large_mapping_has_sequential_fallback_and_bounded_discovery(self):
        skill = (ROOT / "skills/specspine-map-large/SKILL.md").read_text(
            encoding="utf-8"
        )
        protocol = (
            ROOT / "skills/specspine-map-large/references/orchestration.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(protocol.split())
        self.assertIn(
            "current agent is orchestrator, producer, and consumer",
            " ".join(skill.split()),
        )
        self.assertIn("When subagents are unavailable", protocol)
        self.assertIn("one local producer", normalized)
        self.assertIn("Never attempt to hold the whole repository map", normalized)
        self.assertIn(
            "initial survey with exactly this one path-only command", normalized
        )
        self.assertIn("find . -maxdepth 5", protocol)
        self.assertIn("do not substitute another discovery command", normalized)
        self.assertIn("-name node_modules", protocol)
        self.assertIn("-name .specspine-map-run", protocol)
        self.assertIn("-print | LC_ALL=C sort", protocol)
        self.assertIn("Use only directory and file names", normalized)
        self.assertIn("Do not read source, tests, configuration", normalized)
        self.assertIn("Do not make another discovery call before dispatching", normalized)
        self.assertIn("small bounded backlog", normalized)
        self.assertIn("primary discovery mechanism", normalized)
        self.assertIn("without rereading repository source", normalized)

    def test_large_mapping_checkpoints_and_recovers_simply(self):
        protocol = (
            ROOT / "skills/specspine-map-large/references/orchestration.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(protocol.split())
        self.assertIn("small durable append-only ledger", normalized)
        self.assertIn("append-only ledger", normalized)
        self.assertIn("without rereading or rewriting the ledger", normalized)
        self.assertIn("On resume, read the ledger, reconcile published paths", normalized)
        self.assertIn("return interrupted active questions to ready", normalized)
        self.assertIn("Retry once only when duplicate work cannot occur", normalized)
        self.assertIn("After a repeated failure", normalized)

    def test_continuous_pipeline_has_no_wave_barriers_or_tool_mechanics(self):
        protocol = (
            ROOT / "skills/specspine-map-large/references/orchestration.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(protocol.split())
        self.assertIn("dependency-aware ready queue", normalized)
        self.assertIn("without waiting for an entire batch", normalized)
        self.assertIn("Do not introduce conceptual waves", protocol)
        self.assertIn("Do not invoke SpecSpine Doctor during the mapping run", normalized)
        for implementation_detail in (
            "spawn metadata",
            "fork_turns",
            "agent or thread ID",
            "blocking completion notification",
            "poll worker status",
            "wait call",
        ):
            with self.subTest(implementation_detail=implementation_detail):
                self.assertNotIn(implementation_detail, protocol)

    def test_parallel_handoff_is_minimal_and_reports_stay_compact(self):
        protocol = (
            ROOT / "skills/specspine-map-large/references/orchestration.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(protocol.split())
        self.assertIn("complete command below as plain text", normalized)
        self.assertIn("Do not append instructions that send producers back", normalized)
        self.assertIn("SpecSpine mapping producer", protocol)
        self.assertIn("Do not load or invoke any skill", protocol)
        self.assertIn("Do not repeat the document prose", normalized)
        self.assertIn("Do not read the generated file", protocol)
        producer = (
            protocol.split("You are a SpecSpine mapping producer.", 1)[1]
            .split("```", 1)[0]
        )
        normalized_producer = " ".join(producer.split())
        self.assertIn("Do not run a checker", producer)
        self.assertIn(
            "consumer owns all post-production validation", normalized_producer
        )
        self.assertNotIn("Verify that every candidate", producer)
        self.assertNotIn("$specspine-map", producer)
        self.assertNotIn("SKILL.md", producer)
        self.assertNotIn("references/", producer)
        self.assertIn("<complete-generated-map-instructions>", producer)
        self.assertIn("All Map instructions and references", producer)
        self.assertIn("Capture that stdout directly", protocol)
        self.assertIn("Do not read the generated file", protocol)
        self.assertIn("--print", protocol)
        self.assertIn("exact final path relative to the writable root", normalized_producer)
        self.assertIn("<private-staging-root>/jobs/runner.md", producer)
        self.assertLess(producer.index("Do not load or invoke"), producer.index("Assignment:"))
        self.assertLess(producer.index("Shared repository topology:"), producer.index("Assignment:"))
        self.assertLess(
            producer.index("Assignment:"),
            producer.index("Writable output root mirroring the Spine:"),
        )

    def test_each_producer_receives_one_architectural_zone(self):
        protocol = (
            ROOT / "skills/specspine-map-large/references/orchestration.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(protocol.split())
        self.assertIn("exactly one coherent architectural zone", normalized)
        self.assertIn("never combine independent zones", normalized)
        self.assertIn("one zone-specific coverage probe", normalized)
        self.assertNotIn("small bundle of independent", normalized)
        self.assertLessEqual(len(protocol.splitlines()), 320)

    def test_live_eval_prompt_keeps_model_routing_out_of_producer_commands(self):
        scenario = (
            ROOT / "tests/scenarios/map-large-rolling-small.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(scenario.split())
        self.assertIn("harness configures producer models outside their commands", normalized)
        self.assertNotIn("fork_turns", normalized)

    def test_normalizes_once_and_gates_post_map_doctor(self):
        protocol = (
            ROOT / "skills/specspine-map-large/references/orchestration.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(protocol.split())
        self.assertIn("do not inspect repository source", normalized)
        self.assertIn("Do not reread every published specification", normalized)
        self.assertIn("destination paths in the ledger as the new-node inventory", normalized)
        self.assertIn("only documents whose paths or links must change", normalized)
        self.assertIn("Update affected relative links", normalized)
        self.assertIn("Perform it once, not during continuous mapping", normalized)
        self.assertIn(
            "only when the current request explicitly includes a post-map semantic review",
            normalized,
        )
        self.assertIn("Apply semantic repairs only after operator approval", normalized)
        self.assertIn("full deterministic checker exactly once", normalized)
        self.assertIn("batch that check", normalized)
        self.assertIn("concise descriptions to curated `README.md` navigation", normalized)

    def test_doctor_progressively_audits_and_requires_approval_to_write(self):
        doctor = (ROOT / "skills/specspine-doctor/SKILL.md").read_text(
            encoding="utf-8"
        )
        method = (
            ROOT / "skills/specspine-doctor/references/review-method.md"
        ).read_text(encoding="utf-8")
        normalized_doctor = " ".join(doctor.split())
        normalized_method = " ".join(method.split())
        self.assertIn("inspect every specification progressively", doctor)
        self.assertIn("coverage while paths remain", normalized_doctor)
        self.assertIn("ask the operator to approve it", normalized_doctor)
        self.assertIn("clearly supported missing", normalized_doctor)
        self.assertIn("all Markdown", method)
        self.assertIn("write only after operator approval", normalized_method)


if __name__ == "__main__":
    unittest.main()
