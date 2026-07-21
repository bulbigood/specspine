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

Run an explicitly selected case with an agent adapter. The command receives the
evaluation prompt on standard input, runs with the isolated workspace as its
current directory, and must return zero on success:

```bash
python3 tests/eval/run.py \
  --case initialize-project \
  --agent-command "python3 $(pwd)/tests/eval/adapters/codex.py"
```

The adapter path must be absolute because each case runs with its temporary
workspace as the current directory.

## Categories

Every case belongs to exactly one resource category:

- `core` — the minimum PR behavioral set: 10 manifests and 12 agent calls;
- `extended` — rare restructuring and visualization behavior: 3 manifests and
  4 agent calls;
- `planned` — documented but intentionally non-executable coverage.

Run only the category needed for the change:

```bash
python3 tests/eval/run.py \
  --category core \
  --agent-command "python3 $(pwd)/tests/eval/adapters/codex.py" \
  --keep-workspace
```

`--case` and `--category` are repeatable and may be combined. Planned cases are
never executed. Agent execution without at least one explicit `--case` or
`--category` is rejected; there is deliberately no implicit "run everything"
mode.

Eval agents are slow and consume tokens. Prefer the smallest relevant set:

- run deterministic unit tests first;
- run named cases while developing a focused change;
- run `core` only when the change can affect several primary contracts;
- run `extended` only for its rare operations;
- do not run both a category and names already included in it.

The runner executes selected cases concurrently, up to eight by default.
`--jobs` changes that limit; use `--jobs 1` for sequential execution:

```bash
python3 tests/eval/run.py \
  --category extended \
  --agent-command "python3 $(pwd)/tests/eval/adapters/codex.py" \
  --jobs 1 \
  --keep-workspace
```

Pass a different limit when eight concurrent agents are too many, for example
`--jobs 4`.

The bundled Codex adapter defaults to `gpt-5.6-luna` with medium reasoning.
To select another model while keeping the same reasoning default, omit
`--reasoning-effort`:

```bash
python3 tests/eval/run.py \
  --case initialize-project \
  --agent-command "python3 $(pwd)/tests/eval/adapters/codex.py --model gpt-5.6-terra"
```

The runner also sets `SPECSPINE_EVAL_CASE` and `SPECSPINE_EVAL_WORKSPACE`.
Failed workspaces are deleted by default; use `--keep-workspace` to inspect one.
An adapter that can audit file reads should write `.eval/trace.json`:

```json
{
  "files_read": ["specspine/README.md", "specspine/billing.md"],
  "token_usage": {"input_tokens": 12000, "output_tokens": 900}
}
```

The bundled Codex adapter records token counters when the Codex event stream
provides them. Use the archived trace to compare category and case cost.

## Case manifests

Each `cases/*.json` manifest connects one prose scenario to:

- the skill under evaluation;
- its resource category (`core`, `extended`, or `planned`);
- optional installed `companion_skills` copied into the isolated environment;
- an inline clean-room fixture;
- deterministic assertions;
- its migration status (`executable` or `planned`).

For non-staged cases, the runner sends only the scenario's `User request`
section (or an explicit manifest `prompt`) to the agent. Expected behavior and
failure indicators remain a hidden maintainer rubric.

Assertions intentionally cover only objective invariants. Architectural
quality, minimality of context, and whether an inference is reasonable still
need a model judge or human rubric. The audit makes that missing coverage
visible rather than treating prose scenarios as passing tests.

Supported assertions:

- `path_exists`, `path_absent`, `glob_count`, `glob_contains`;
- `file_contains`, `file_not_contains`, `response_contains`, `response_not_contains`;
- `unchanged`, `changed_only`, `max_changed_files`;
- `read_only`, `read_includes`, `max_files_read` when an adapter emits a trace;
- `balanced_markers`, `no_template_placeholders`;
- `markdown_links_valid`, `semantic_ids_valid`, both implemented as scoped views
  of the bundled Doctor checker rather than independent Markdown parsers;
- `spine_mechanical_valid`, which fails on unallowed `error` findings and accepts
  optional `allowed_codes` and `forbidden_codes`. Warnings and notes are
  advisory unless explicitly forbidden by a scenario.

Glob assertions inspect project files only and exclude the harness-owned
`.eval/` directory.

Set manifest field `runs` above one to invoke the agent repeatedly in the same
workspace, for example to test connector idempotency. The bundled live Codex
adapter emits a conservative `.eval/trace.json` from command events; broad read
commands are treated as reading every candidate file.

## Staged lifecycle cases

A lifecycle manifest can replace the top-level `skill` and `assertions` with a
`stages` list. Agent stages select their own skill, receive only their local
prompt, and evaluate assertions against the snapshot immediately before that
stage. Fixture stages model downstream or external changes without invoking an
agent:

```json
{
  "id": "example-lifecycle",
  "scenario": "tests/scenarios/example-lifecycle.md",
  "status": "executable",
  "category": "core",
  "initial_files": {},
  "stages": [
    {
      "id": "map",
      "skill": "skills/specspine-map",
      "prompt": "Map the payment subsystem.",
      "assertions": [{"type": "path_exists", "path": "specspine/README.md"}]
    },
    {
      "id": "implementation",
      "fixture": {
        "write_files": {"src/payment.js": "export const mode = 'async';\n"},
        "remove_files": []
      }
    }
  ],
  "final_assertions": [{"type": "markdown_links_valid", "glob": "specspine/*.md"}]
}
```

Each agent stage is archived under `.eval/stages/<number>-<id>/` with its final
response, stderr when present, and trace. `SPECSPINE_EVAL_STAGE` contains the
current stage ID. A failing stage stops subsequent stages; final assertions run
against the state reached so far.
