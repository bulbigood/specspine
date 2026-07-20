# SpecSpine evaluation harness

The harness runs an agent in a fresh temporary workspace and checks the result
with deterministic assertions. It has no third-party dependencies.

## Commands

```bash
python3 tests/eval/run.py --list
python3 tests/eval/run.py --validate --audit
python3 -m unittest discover -s tests/eval -p 'test_*.py'
```

Run one or all executable cases with an agent adapter. The command receives the
evaluation prompt on standard input, runs with the isolated workspace as its
current directory, and must return zero on success:

```bash
python3 tests/eval/run.py \
  --case initialize-project \
  --agent-command './path/to/agent-adapter'
```

The runner also sets `SPECSPINE_EVAL_CASE` and `SPECSPINE_EVAL_WORKSPACE`.
Failed workspaces are deleted by default; use `--keep-workspace` to inspect one.
An adapter that can audit file reads should write `.eval/trace.json`:

```json
{"files_read": ["specspine/README.md", "specspine/billing.md"]}
```

## Case manifests

Each `cases/*.json` manifest connects one prose scenario to:

- the skill under evaluation;
- an inline clean-room fixture;
- deterministic assertions;
- its migration status (`executable` or `planned`).

Assertions intentionally cover only objective invariants. Architectural
quality, minimality of context, and whether an inference is reasonable still
need a model judge or human rubric. The audit makes that missing coverage
visible rather than treating prose scenarios as passing tests.

Supported assertions:

- `path_exists`, `path_absent`, `glob_count`;
- `file_contains`, `file_not_contains`, `response_contains`;
- `unchanged`, `changed_only`, `max_changed_files`;
- `read_only`, `read_includes`, `max_files_read` when an adapter emits a trace;
- `balanced_markers`, `no_template_placeholders`;
- `markdown_links_valid`, `semantic_ids_valid`.
