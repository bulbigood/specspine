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

    def test_reports_unresolved_template_guidance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                "# Architecture\n\nSummarize the concept in one or two sentences.\n",
                encoding="utf-8",
            )
            self.assertIn("TEMPLATE_TEXT", {finding.code for finding in CHECKER.check(root)})

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


if __name__ == "__main__":
    unittest.main()
