# SpecSpine evaluation

The directory contains a deterministic harness. `run.py` checks SpecSpine
skills against case manifests.

The Python harness uses only the standard library. Live runs require the Codex
CLI and Codex authentication.

## Validation

```bash
python3 tests/eval/run.py --validate --audit
python3 -m unittest discover -s tests/eval -p 'test_*.py'
```

The optional installed-package test requires npm execution:

```bash
SPECSPINE_RUN_NPX=1 python3 -m unittest discover -s tests/eval -p 'test_npx_install.py' -v
```

## Deterministic skill evaluation

List cases or run an explicitly selected case/category:

```bash
python3 tests/eval/run.py --list

python3 tests/eval/run.py \
  --category core \
  --agent-command "python3 $(pwd)/tests/eval/adapters/codex.py"
```

`run.py` does not select a model itself; it executes the command supplied by
`--agent-command`. The standard Codex adapter defaults to `gpt-5.6-luna` with
`medium` reasoning. Pass a model and reasoning effort through the quoted
adapter command. This example states the adapter defaults explicitly:

```bash
python3 tests/eval/run.py \
  --category core \
  --agent-command "python3 $(pwd)/tests/eval/adapters/codex.py --model gpt-5.6-luna --reasoning-effort medium"
```

`--case` and `--category` are repeatable and may be combined. There is no
implicit run-all mode. Planned cases are never executed. Categories are
disjoint: `core` has 6 executable cases, `extended` has 8, and `planned` has
8 documented non-executable cases.

Each case gets a clean temporary workspace. Cases run with concurrency 8 by
default; change it with `--jobs N`. Workspaces default to
`~/.cache/specspine-eval/workspaces`; override with
`SPECSPINE_EVAL_WORKSPACES_DIR`. Failed workspaces are retained only with
`--keep-workspace`.

Use `--samples N` to run each selected case independently in `N` fresh
workspaces and report its success rate. This differs from a manifest's `runs`:
those are sequential agent calls inside one workspace and test repeated or
lifecycle behavior.

Case manifests in `cases/*.json` define fixtures, prompts and deterministic
assertions. A manifest may instead define ordered `stages`; agent stages run a
prompt and assertions, while fixture stages model external changes.

Supported assertions:

- paths/content: `path_exists`, `path_absent`, `glob_count`, `glob_contains`,
  `file_contains`, `file_not_contains`, `word_budget`;
- response: `response_contains`, `response_contains_any`,
  `response_not_contains`;
- changes: `unchanged`, `changed_only`, `max_changed_files`;
- execution: `command_succeeds`;
- trace: `read_only`, `read_includes`, `max_files_read`;
- structure: `balanced_markers`, `no_template_placeholders`,
  `markdown_links_valid`, `semantic_ids_valid`, `spine_mechanical_valid`.

Trace assertions require `.eval/trace.json`. The Codex adapter conservatively
infers reads from completed command events; repository-wide content searches
may count every candidate file as read.

### Do not design skills around eval assertions

Never complicate a skill, prescribe extra response structure, or add mandatory
output phrases merely to make an eval pass. SpecSpine skills intentionally use
a relatively free response format so their instructions and validation remain
small, readable, and adaptable to the task.

Eval assertions must follow the behavioral contract rather than create a new
one. Prefer observable file, scope, and command outcomes. When response text is
necessary, accept concise semantically equivalent wording, for example with
`response_contains_any`, instead of forcing a schema, template, heading set, or
test-specific vocabulary into the skill. Change a skill only when an eval has
exposed a genuine product-behavior gap independent of the assertion wording.
