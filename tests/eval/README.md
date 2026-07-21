# SpecSpine evaluation harness

The harness runs an agent in a fresh temporary workspace and checks the result
with deterministic assertions. It has no third-party dependencies.

## Commands

```bash
python3 tests/eval/run.py --list
python3 tests/eval/run.py --validate --audit
python3 -m unittest discover -s tests/eval -p 'test_*.py'
SPECSPINE_RUN_NPX=1 python3 -m unittest discover -s tests/eval -p 'test_npx_install.py' -v
```

Run one or all executable cases with an agent adapter. The command receives the
evaluation prompt on standard input, runs with the isolated workspace as its
current directory, and must return zero on success:

```bash
python3 tests/eval/run.py \
  --case initialize-project \
  --agent-command "python3 $(pwd)/tests/eval/adapters/codex.py"
```

The adapter path must be absolute because each case runs with its temporary
workspace as the current directory.

Run the main behavioral set concurrently:

```bash
python3 tests/eval/run.py \
  --parallel \
  --case map-deepen-selected-area \
  --case add-cross-cutting-feature \
  --case grow-existing-spec \
  --case map-initial-survey \
  --case map-refresh-local-change \
  --case split-broad-spec \
  --case merge-rename-links \
  --agent-command "python3 $(pwd)/tests/eval/adapters/codex.py" \
  --keep-workspace
```

Omit `--case` to run every executable eval. This is a long, resource-intensive,
and potentially expensive operation; run it as infrequently as possible. Planned
cases are not executed. `--jobs` limits simultaneous agents while the remaining
cases wait in the executor queue (default: `4`):

```bash
python3 tests/eval/run.py \
  --parallel \
  --jobs 4 \
  --agent-command "python3 $(pwd)/tests/eval/adapters/codex.py" \
  --keep-workspace
```

The bundled Codex adapter defaults to `gpt-5.6-terra` with medium reasoning.
For cheaper eval runs, select `gpt-5.6-luna` and leave reasoning at the
adapter default by omitting `--reasoning-effort`:

```bash
python3 tests/eval/run.py \
  --parallel \
  --jobs 4 \
  --agent-command "python3 $(pwd)/tests/eval/adapters/codex.py --model gpt-5.6-luna"
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
- optional installed `companion_skills` copied into the isolated environment;
- an inline clean-room fixture;
- deterministic assertions;
- its migration status (`executable` or `planned`).

Assertions intentionally cover only objective invariants. Architectural
quality, minimality of context, and whether an inference is reasonable still
need a model judge or human rubric. The audit makes that missing coverage
visible rather than treating prose scenarios as passing tests.

Supported assertions:

- `path_exists`, `path_absent`, `glob_count`;
- `file_contains`, `file_not_contains`, `response_contains`, `response_not_contains`;
- `unchanged`, `changed_only`, `max_changed_files`;
- `read_only`, `read_includes`, `max_files_read` when an adapter emits a trace;
- `balanced_markers`, `no_template_placeholders`;
- `markdown_links_valid`, `semantic_ids_valid`.

Set manifest field `runs` above one to invoke the agent repeatedly in the same
workspace, for example to test connector idempotency. The bundled live Codex
adapter emits a conservative `.eval/trace.json` from command events; broad read
commands are treated as reading every candidate file.
