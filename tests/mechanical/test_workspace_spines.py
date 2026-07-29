import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


INDEXER = load("test_indexer", ROOT / "shared/scripts/rebuild_indexes.py")
CHECKER = load("test_workspace_checker", ROOT / "shared/scripts/check_spine.py")
WORKSPACE = load(
    "test_workspace_spines_module",
    ROOT / "skills/specspine-doctor/scripts/workspace_spines.py",
)


def manifest(project):
    return {
        "specspine": 3,
        "project": project,
        "implementation_freedom": "contract-equivalent",
        "areas": [],
        "assets": [],
    }


class WorkspaceSpinesTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def root(self, relative, project):
        root = self.workspace / relative
        root.mkdir(parents=True)
        (root / "specspine.json").write_text(json.dumps(manifest(project)))
        (root / "_INDEX.md").write_text(
            f"# {project}\n\n"
            "**ID:** `project-architecture` · **Kind:** `index`\n\n"
            "Bootstrap.\n"
        )
        INDEXER.rebuild(root)
        return root

    def test_rebuild_creates_one_index_per_directory_idempotently(self):
        root = self.root("specspine", "demo")
        contracts = root / "contracts"
        contracts.mkdir()
        (contracts / "api.yaml").write_text("openapi: 3.1.0\n")
        first = INDEXER.rebuild(root)
        second = INDEXER.rebuild(root)
        self.assertIn("contracts/_INDEX.md", first["changed"])
        self.assertEqual([], second["changed"])
        self.assertIn("[api.yaml](api.yaml)", (contracts / "_INDEX.md").read_text())

    def test_checker_rejects_stale_directory_index(self):
        root = self.root("specspine", "demo")
        (root / "owner.md").write_text("unindexed\n")
        codes = {finding.code for finding in CHECKER.check(root)}
        self.assertIn("INDEX_ENTRY_MISSING", codes)

    def test_workspace_graph_connects_nested_roots_and_keeps_siblings(self):
        parent = self.root("docs/specspine", "parent")
        child = self.root("docs/specspine/services/payments/specspine", "child")
        sibling = self.root("mobile/specspine", "mobile")
        INDEXER.rebuild(parent)
        roots = WORKSPACE.discover(self.workspace)
        value = WORKSPACE.graph(self.workspace, roots)
        rows = {row["root"]: row for row in value["roots"]}
        self.assertEqual("docs/specspine", rows[
            "docs/specspine/services/payments/specspine"
        ]["parent"])
        self.assertIsNone(rows["docs/specspine"]["parent"])
        self.assertIsNone(rows["mobile/specspine"]["parent"])
        self.assertIn(
            "services/payments/specspine/_INDEX.md",
            (parent / "_INDEX.md").read_text(),
        )
        self.assertEqual([], [
            finding for finding in CHECKER.check(child)
            if finding.severity == "error"
        ])
        self.assertEqual([], [
            finding for finding in CHECKER.check(sibling)
            if finding.severity == "error"
        ])


if __name__ == "__main__":
    unittest.main()
