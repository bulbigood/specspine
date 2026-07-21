import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("adapters") / "codex.py"
SPEC = importlib.util.spec_from_file_location("specspine_codex_adapter", MODULE_PATH)
assert SPEC and SPEC.loader
ADAPTER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ADAPTER
SPEC.loader.exec_module(ADAPTER)


class CodexAdapterTests(unittest.TestCase):
    def test_traces_explicit_file_reads(self):
        candidates = ["src/users/model.js", "src/billing/private.js"]
        self.assertEqual(
            {"src/users/model.js"},
            ADAPTER.traced_files("sed -n '1,80p' src/users/model.js", candidates),
        )

    def test_treats_repo_wide_content_search_as_reading_all_candidates(self):
        candidates = ["src/users/model.js", "src/billing/private.js"]
        self.assertEqual(set(candidates), ADAPTER.traced_files("rg TODO .", candidates))

    def test_does_not_treat_file_listing_as_content_read(self):
        candidates = ["src/users/model.js", "src/billing/private.js"]
        self.assertEqual(set(), ADAPTER.traced_files("find . -type f", candidates))

    def test_does_not_treat_rg_file_listing_glob_as_content_read(self):
        candidates = ["README.md", "specspine/README.md"]
        command = "sed -n '1,20p' .eval/skill/SKILL.md && rg --files -g 'README.md'"
        self.assertEqual(set(), ADAPTER.traced_files(command, candidates))

    def test_traces_files_read_through_shell_glob_loop(self):
        candidates = ["specspine/README.md", "specspine/payments.md", "README.md"]
        command = "for f in specspine/*.md; do sed -n '1,200p' \"$f\"; done"
        self.assertEqual(
            {"specspine/README.md", "specspine/payments.md"},
            ADAPTER.traced_files(command, candidates),
        )

    def test_traces_files_read_from_rg_listing_loop(self):
        candidates = ["src/api.ts", "src/payments/settlement.ts", "README.md"]
        command = "for f in $(rg --files src | sort); do sed -n '1,200p' \"$f\"; done"
        self.assertEqual(
            {"src/api.ts", "src/payments/settlement.ts"},
            ADAPTER.traced_files(command, candidates),
        )

    def test_traces_spine_read_by_doctor_checker(self):
        candidates = ["specspine/README.md", "specspine/payments.md", "src/payment.ts"]
        command = "python3 .eval/skill/scripts/check_spine.py specspine --json"
        self.assertEqual(
            {"specspine/README.md", "specspine/payments.md"},
            ADAPTER.traced_files(command, candidates),
        )

    def test_rg_pattern_and_glob_do_not_count_named_out_of_scope_files(self):
        candidates = ["README.md", "package.json", "specspine/README.md", "specspine/payment.md"]
        command = (
            "/bin/zsh -lc \"rg -n --glob '!README.md' "
            "'payment-webhook-retry|package.json' specspine\""
        )
        self.assertEqual(
            {"specspine/README.md", "specspine/payment.md"},
            ADAPTER.traced_files(command, candidates),
        )

    def test_does_not_treat_echoed_path_as_content_read(self):
        candidates = ["README.md", "specspine/README.md"]
        command = "sed -n '1,40p' specspine/README.md\necho 'README.md -> payments.md'"
        self.assertEqual(
            {"specspine/README.md"},
            ADAPTER.traced_files(command, candidates),
        )

    def test_parses_commands_reads_and_agent_messages(self):
        stdout = "\n".join(
            [
                '{"item":{"type":"command_execution","command":"sed -n 1,80p src/users/model.js"}}',
                '{"item":{"type":"agent_message","text":"Finished"}}',
            ]
        )
        reads, commands, messages = ADAPTER.parse_events(stdout, ["src/users/model.js", "src/billing.js"])
        self.assertEqual({"src/users/model.js"}, reads)
        self.assertEqual(["sed -n 1,80p src/users/model.js"], commands)
        self.assertEqual(["Finished"], messages)


if __name__ == "__main__":
    unittest.main()
