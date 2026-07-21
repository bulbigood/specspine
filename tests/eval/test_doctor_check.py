import importlib.util
import re
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[2] / "skills" / "specspine-doctor" / "scripts" / "check_spine.py"
SPEC = importlib.util.spec_from_file_location("specspine_doctor_check", MODULE_PATH)
assert SPEC and SPEC.loader
CHECKER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CHECKER
SPEC.loader.exec_module(CHECKER)


class DoctorCheckerTests(unittest.TestCase):
    def test_generated_rules_are_identical_in_all_consumers(self):
        project_root = Path(__file__).parents[2]
        for name in ("spec-format.md", "spec-semantics.md", "context-handoff.md"):
            grow = project_root / "skills" / "specspine-grow" / "references" / name
            for consumer in ("specspine-map", "specspine-doctor"):
                generated = project_root / "skills" / consumer / "references" / name
                self.assertEqual(grow.read_text(encoding="utf-8"), generated.read_text(encoding="utf-8"), name)

    def test_checker_id_grammar_matches_canonical_format(self):
        format_path = (
            Path(__file__).parents[2]
            / "tools"
            / "specspine-adapter-generator"
            / "assets"
            / "skill-sources"
            / "specspine-grow"
            / "references"
            / "spec-format.md"
        )
        text = format_path.read_text(encoding="utf-8")
        match = re.search(r"Use this identifier grammar:\n\n```text\n([^\n]+)\n```", text)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), CHECKER.ID_RE.pattern)

    def test_accepts_valid_graph_and_semantic_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("# Architecture\n\n[Jobs](jobs.md)\n", encoding="utf-8")
            (root / "jobs.md").write_text(
                "# Jobs\n\nOwns jobs.\n\n<!-- specspine:semantic-ids:begin -->\n"
                "## Constraints\n\n- **CON-retry-limit** — Retries are bounded.\n"
                "<!-- specspine:semantic-ids:end -->\n",
                encoding="utf-8",
            )
            self.assertEqual([], CHECKER.check(root))

    def test_reports_broken_link_unreachable_file_and_invalid_id_section(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("# Architecture\n\n[Missing](missing.md)\n", encoding="utf-8")
            (root / "orphan.md").write_text(
                "# Orphan\n\n## Decisions\n\n- **OBS-current-shape** — Current shape.\n",
                encoding="utf-8",
            )
            codes = {finding.code for finding in CHECKER.check(root)}
            self.assertTrue({"BROKEN_LINK", "UNREACHABLE_SPEC", "ID_SECTION"} <= codes)

    def test_reports_unresolved_semantic_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("# Architecture\n\n[Jobs](jobs.md)\n", encoding="utf-8")
            (root / "jobs.md").write_text(
                "# Jobs\n\nPreserve [CON-missing](owner.md).\n", encoding="utf-8"
            )
            (root / "owner.md").write_text("# Owner\n", encoding="utf-8")
            codes = {finding.code for finding in CHECKER.check(root)}
            self.assertIn("UNRESOLVED_ID", codes)

    def test_ignores_links_and_ids_in_fenced_examples(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                "# Architecture\n\n```markdown\n[Missing](missing.md)\n"
                "- **CON-example** — Example only.\n```\n",
                encoding="utf-8",
            )
            self.assertEqual([], CHECKER.check(root))

    def test_ignores_links_in_inline_code(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                "# Architecture\n\nUse `[label](not-a-link.md)` as an example.\n",
                encoding="utf-8",
            )
            self.assertEqual([], CHECKER.check(root))

    def test_does_not_treat_template_syntax_or_guidance_as_a_defect(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                "# Architecture\n\nSummarize the concept in one or two sentences.\n\n"
                "An external template uses `{{variable}}`.\n",
                encoding="utf-8",
            )
            self.assertEqual([], CHECKER.check(root))

    def test_accepts_kebab_case_directories_and_checks_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            area = root / "server" / "billing"
            area.mkdir(parents=True)
            (root / "README.md").write_text(
                "# Architecture\n\n[Billing](server/billing/payments.md)\n", encoding="utf-8"
            )
            (area / "payments.md").write_text(
                "# Payments\n\n## Observed\n\n"
                "<!-- specspine:evidence-baseline source=commit-abc; inspected=2026-07-21 -->\n"
                "- A worker consumes payment events.\n",
                encoding="utf-8",
            )
            self.assertEqual([], CHECKER.check(root))

    def test_traces_nested_links_and_path_scoped_semantic_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payments = root / "domains" / "payments"
            resilience = root / "platform" / "resilience"
            payments.mkdir(parents=True)
            resilience.mkdir(parents=True)
            (root / "README.md").write_text(
                "# Architecture\n\n[Payments](domains/payments/payment-processing.md)\n",
                encoding="utf-8",
            )
            (payments / "payment-processing.md").write_text(
                "# Payment processing\n\n"
                "Preserve [CON-retry-limit](../../platform/resilience/retry-policy.md).\n\n"
                "[Retry policy](../../platform/resilience/retry-policy.md)\n",
                encoding="utf-8",
            )
            (resilience / "retry-policy.md").write_text(
                "# Retry policy\n\n"
                "<!-- specspine:semantic-ids:begin -->\n"
                "## Constraints\n\n"
                "- **CON-retry-limit** — Retries stop after five attempts.\n"
                "<!-- specspine:semantic-ids:end -->\n",
                encoding="utf-8",
            )
            self.assertEqual([], CHECKER.check(root))

    def test_id_outside_marker_region_does_not_satisfy_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                "# Architecture\n\n[Consumer](consumer.md)\n[Owner](owner.md)\n",
                encoding="utf-8",
            )
            (root / "consumer.md").write_text(
                "# Consumer\n\nPreserve [CON-retry-limit](owner.md).\n",
                encoding="utf-8",
            )
            (root / "owner.md").write_text(
                "# Owner\n\n## Constraints\n\n- **CON-retry-limit** — Retries are bounded.\n",
                encoding="utf-8",
            )
            codes = {finding.code for finding in CHECKER.check(root)}
            self.assertTrue({"ID_OUTSIDE_REGION", "UNRESOLVED_ID"} <= codes)

    def test_supports_reference_links_and_ignores_images_and_long_code_spans(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                "# Architecture\n\n[Jobs][jobs]\n\n"
                "![CON-image](missing-image.md)\n\n"
                "Use ``[Missing](missing.md)`` as an example.\n\n"
                "[jobs]: jobs.md \"Job architecture\"\n",
                encoding="utf-8",
            )
            (root / "jobs.md").write_text("# Jobs\n", encoding="utf-8")
            self.assertEqual([], CHECKER.check(root))

    def test_supports_commonmark_headings_and_unordered_list_markers(self):
        for bullet in ("-", "*", "+"):
            with self.subTest(bullet=bullet), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "README.md").write_text("# Architecture\n\n[Policy](policy.md)\n", encoding="utf-8")
                (root / "policy.md").write_text(
                    "# Policy #\n\n<!-- specspine:semantic-ids:begin -->\n"
                    "## Constraints ##\n\n"
                    f"  {bullet} **CON-retry-limit** — Retries are bounded.\n"
                    "<!-- specspine:semantic-ids:end -->\n",
                    encoding="utf-8",
                )
                self.assertEqual([], CHECKER.check(root))

    def test_accepts_system_wide_sections_and_defers_translated_sections(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                "# Architecture\n\n<!-- specspine:semantic-ids:begin -->\n"
                "## System-wide decisions\n\n- **DEC-api-style** — APIs use JSON.\n"
                "## Решения\n\n- **DEC-session-style** — Сессии независимы.\n"
                "<!-- specspine:semantic-ids:end -->\n",
                encoding="utf-8",
            )
            findings = CHECKER.check(root)
            self.assertNotIn("ID_SECTION", {finding.code for finding in findings})
            self.assertEqual(
                ["ID_SECTION_UNVERIFIED"],
                [finding.code for finding in findings],
            )

    def test_reports_out_of_scope_link_without_checking_it_as_broken(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "specspine"
            root.mkdir()
            (root / "README.md").write_text(
                "# Architecture\n\n[Outside](../does-not-exist.md)\n",
                encoding="utf-8",
            )
            findings = CHECKER.check(root)
            self.assertIn("OUT_OF_SCOPE_LINK", {finding.code for finding in findings})
            self.assertNotIn("BROKEN_LINK", {finding.code for finding in findings})

    def test_skips_markdown_symlink_that_resolves_outside_root(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "specspine"
            root.mkdir()
            outside = base / "outside.md"
            outside.write_text("# Outside\n", encoding="utf-8")
            (root / "README.md").write_text("# Architecture\n", encoding="utf-8")
            (root / "linked.md").symlink_to(outside)
            findings = CHECKER.check(root)
            self.assertIn("OUT_OF_SCOPE_ENTRY", {finding.code for finding in findings})
            self.assertNotIn("UNREACHABLE_SPEC", {finding.code for finding in findings})

    def test_external_index_symlink_does_not_satisfy_required_index(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "specspine"
            root.mkdir()
            outside = base / "README.md"
            outside.write_text("# Outside\n", encoding="utf-8")
            (root / "README.md").symlink_to(outside)
            codes = {finding.code for finding in CHECKER.check(root)}
            self.assertTrue({"INDEX_MISSING", "OUT_OF_SCOPE_ENTRY"} <= codes)

    def test_unclosed_fence_and_html_comment_are_not_general_markdown_defects(self):
        cases = (
            "# Architecture\n\n```markdown\n[Missing](missing.md)\n",
            "# Architecture\n\n<!-- [Missing](missing.md)\n",
        )
        for content in cases:
            with self.subTest(content=content), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "README.md").write_text(content, encoding="utf-8")
                self.assertEqual([], CHECKER.check(root))

    def test_provenance_and_naming_findings_do_not_fail_preflight(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            area = root / "Server Area"
            area.mkdir()
            (root / "README.md").write_text("# Architecture\n\n[API](Server%20Area/API.md)\n", encoding="utf-8")
            (area / "API.md").write_text(
                "# API\n\n## Observed\n\n"
                "<!-- specspine:evidence-baseline source=x; inspected=2026-02-30 -->\n"
                "Observed behavior.\n",
                encoding="utf-8",
            )
            findings = CHECKER.check(root)
            by_code = {finding.code: finding.severity for finding in findings}
            self.assertEqual("note", by_code["INVALID_DIRECTORY"])
            self.assertEqual("warning", by_code["INVALID_FILENAME"])
            self.assertEqual("warning", by_code["INVALID_BASELINE_DATE"])
            self.assertFalse(any(finding.severity == "error" for finding in findings))

    def test_reports_invalid_utf8_as_read_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("# Architecture\n\n[Bad](bad.md)\n", encoding="utf-8")
            (root / "bad.md").write_bytes(b"# Bad\n\xff")
            findings = CHECKER.check(root)
            self.assertIn("READ_ERROR", {finding.code for finding in findings})

    def test_reports_root_and_index_preflight_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing = CHECKER.check(root / "missing")
            self.assertEqual(["ROOT_MISSING"], [finding.code for finding in missing])
            self.assertIn("INDEX_MISSING", {finding.code for finding in CHECKER.check(root)})

    def test_structural_and_provenance_finding_codes(self):
        cases = {
            "missing-h1": ("No heading.\n", "MISSING_H1"),
            "invalid-baseline": (
                "# A\n\n## Observed\n\n<!-- specspine:evidence-baseline bad -->\nFact.\n",
                "INVALID_BASELINE",
            ),
            "empty-section": ("# A\n\n## Responsibility\n", "EMPTY_SECTION"),
            "nested-region": (
                "# A\n\n<!-- specspine:semantic-ids:begin -->\n"
                "<!-- specspine:semantic-ids:begin -->\n"
                "<!-- specspine:semantic-ids:end -->\n<!-- specspine:semantic-ids:end -->\n",
                "ID_REGION_NESTED",
            ),
            "extra-region-end": ("# A\n\n<!-- specspine:semantic-ids:end -->\n", "ID_REGION_END"),
            "invalid-id": (
                "# A\n\n<!-- specspine:semantic-ids:begin -->\n## Constraints\n\n"
                "- **CON-bad_ID** — Invalid.\n<!-- specspine:semantic-ids:end -->\n",
                "INVALID_ID",
            ),
            "wrong-id-section": (
                "# A\n\n<!-- specspine:semantic-ids:begin -->\n## Decisions\n\n"
                "- **OBS-current** — Invalid.\n<!-- specspine:semantic-ids:end -->\n",
                "ID_SECTION",
            ),
            "unclosed-region": (
                "# A\n\n<!-- specspine:semantic-ids:begin -->\n## Decisions\n\n"
                "- **DEC-one** — One.\n",
                "ID_REGION_UNCLOSED",
            ),
            "multiple-regions": (
                "# A\n\n<!-- specspine:semantic-ids:begin -->\n## Decisions\n\n"
                "- **DEC-one** — One.\n<!-- specspine:semantic-ids:end -->\n"
                "<!-- specspine:semantic-ids:begin -->\n## Constraints\n\n"
                "- **CON-two** — Two.\n<!-- specspine:semantic-ids:end -->\n",
                "MULTIPLE_ID_REGIONS",
            ),
            "empty-region": (
                "# A\n\n<!-- specspine:semantic-ids:begin -->\n"
                "<!-- specspine:semantic-ids:end -->\n",
                "EMPTY_ID_REGION",
            ),
            "multiple-baselines": (
                "# A\n\n## Observed\n\n"
                "<!-- specspine:evidence-baseline source=a; inspected=2026-07-20 -->\n"
                "<!-- specspine:evidence-baseline source=b; inspected=2026-07-21 -->\nFact.\n",
                "MULTIPLE_BASELINES",
            ),
            "missing-baseline": ("# A\n\n## Observed\n\nFact.\n", "MISSING_BASELINE"),
            "duplicate-id": (
                "# A\n\n<!-- specspine:semantic-ids:begin -->\n## Decisions\n\n"
                "- **DEC-one** — One.\n- **DEC-one** — Again.\n"
                "<!-- specspine:semantic-ids:end -->\n",
                "DUPLICATE_ID",
            ),
        }
        for name, (content, expected) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "README.md").write_text(content, encoding="utf-8")
                self.assertIn(expected, {finding.code for finding in CHECKER.check(root)})

    def test_semantic_reference_finding_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                "# Architecture\n\n[Owner](owner.md)\n\n"
                "[CON-bad_ID](owner.md)\n\n[CON-missing](owner.md#fragment)\n",
                encoding="utf-8",
            )
            (root / "owner.md").write_text("# Owner\n", encoding="utf-8")
            codes = {finding.code for finding in CHECKER.check(root)}
            self.assertTrue({"INVALID_ID_REFERENCE", "ID_FRAGMENT", "UNRESOLVED_ID"} <= codes)


if __name__ == "__main__":
    unittest.main()
