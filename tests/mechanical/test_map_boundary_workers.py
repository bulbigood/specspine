import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
SCRIPTS = ROOT / "skills/specspine-map/scripts"
sys.path.insert(0, str(SCRIPTS))


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PLANNING = load_module("planning")
COVERAGE = load_module("coverage")


class MapBoundaryWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.repository = Path(self.temporary.name)
        self.runtime = self.repository / ".specspine/map/run"
        self.runtime.mkdir(parents=True)
        self.spine = self.repository / "specspine"
        self.spine.mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, name, value):
        path = self.runtime / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def test_planner_finalizes_only_a_bounded_semantic_plan(self):
        packet = self.write(
            "planner-packet.json",
            {
                "planner_contract_version": 1,
                "operation": {},
                "repository_root": str(self.repository),
                "spine_root": str(self.spine),
            },
        )
        draft = self.write(
            "planner-draft.json",
            {
                "discovery_plan_version": 1,
                "rationale": "One independently searchable boundary.",
                "leads": [
                    {
                        "id": "runtime",
                        "title": "Runtime",
                        "question": "Who owns runtime composition?",
                        "reason": "Composition exposes the subsystem boundary.",
                    }
                ],
            },
        )
        output = self.runtime / "initial-plan.json"
        receipt = PLANNING.command_finalize(
            type("Args", (), {"packet": packet, "draft": draft, "output": output})
        )
        self.assertEqual(1, receipt["leads"])
        self.assertEqual([], json.loads(output.read_text())["leads"][0]["seed_files"])

    def test_coverage_finalizer_rejects_clear_review_with_gaps(self):
        source = self.repository / "src.py"
        source.write_text("pass\n", encoding="utf-8")
        packet = self.write(
            "coverage-packet.json",
            {
                "coverage_contract_version": 1,
                "topic_plan_digest": "0" * 64,
                "repository_root": str(self.repository),
            },
        )
        draft = self.write(
            "coverage-draft.json",
            {
                "status": "clear",
                "reason": "Contradictory fixture.",
                "inspected_roots": ["runtime entries"],
                "open_leads": [
                    {
                        "id": "missing-runtime",
                        "title": "Missing runtime",
                        "question": "Who owns it?",
                        "reason": "It is absent from the plan.",
                        "seed_files": ["src.py"],
                    }
                ],
            },
        )
        with self.assertRaisesRegex(
            COVERAGE.CoverageError,
            "clear coverage review cannot contain open leads",
        ):
            COVERAGE.command_finalize(
                type(
                    "Args",
                    (),
                    {
                        "packet": packet,
                        "draft": draft,
                        "output": self.runtime / "coverage-review.json",
                    },
                )
            )


if __name__ == "__main__":
    unittest.main()
