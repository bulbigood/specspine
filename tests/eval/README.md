# SpecSpine evaluation

Follow the repository-wide [test rules](../README.md). This file adds
eval-harness-specific guidance.

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

## Eval design rules

### Admit only distinct behavioral contracts

Add an executable eval only when an AI agent must interpret skill instructions
and the behavior is not already protected by a mechanical test or another eval.
Do not add a case merely because a prose scenario exists. Prefer extending an
existing lifecycle case when the new behavior is meaningful only as another
state transition; otherwise keep cases independent.

Before creating a case, state the distinct regression it must detect and why a
deterministic test cannot detect it. If those answers are unclear, leave the
scenario `planned`.

### Minimize fixtures and prompts

- Include only files required to make the architectural choice realistic.
- Keep every file short while preserving the ambiguity or boundary under test.
- Give the agent an explicit task and source boundary, not the expected answer.
- Do not repeat generic harness, skill, rubric, or safety instructions in the
  case prompt; the runner and installed skill already provide them.
- Never expose expected behavior, assertions, failure indicators, or hidden
  scenario prose to the evaluated agent.
- Use stable fictional data, paths, identifiers, and dates. Avoid wall-clock,
  network, mutable external service, or host-environment dependencies.

### Use the smallest sufficient assertion set

Assert externally observable behavior, not wording or one acceptable internal
approach. Prefer, in order:

1. paths and allowed change scope;
2. structural validity and executable downstream checks;
3. trace boundaries and read budgets;
4. semantic content in produced artifacts;
5. response text only when the response itself is the product contract.

Every mutation case should constrain unintended effects with `changed_only`,
`unchanged`, `max_changed_files`, `read_only`, or another appropriate boundary.
Use `markdown_links_valid`, `semantic_ids_valid`, or
`spine_mechanical_valid` instead of duplicating their rules with text checks.
Use `file_contains_any` or `response_contains_any` only when structural checks
cannot establish the behavior, and accept concise semantic alternatives.

Do not assert optional formatting, a particular document decomposition,
implementation detail, exact explanatory prose, or facts already guaranteed by
another assertion. A case should fail for a product regression, not for a
harmless rewrite.

### Control agent calls, latency, and tokens

- Use one agent call per case by default.
- Use fixture stages, not agent stages, to model external repository changes.
- Add another agent stage or `runs` only when persisted agent behavior across
  transitions is the contract under test.
- Keep authorized evidence narrow and enforce it with `read_includes`,
  `max_files_read`, and scope assertions when relevant.
- Use `word_budget` when uncontrolled artifact growth is a regression risk.
- During authoring, run only the focused case with one sample. Do not run a
  category merely to debug one manifest.
- Inspect reported wall time, files read, agent calls, and token usage. Reject
  unexplained cost growth even when behavioral assertions still pass.

Place a case in `core` only when it protects a critical, distinct contract with
a small fixture and normally one agent call. Put lifecycle, repeated, broader,
or more expensive coverage in `extended`. Keep redundant, speculative, or
currently uneconomical cases `planned`. Update [COVERAGE.md](COVERAGE.md) when
coverage or category costs change.

### Make stochastic results comparable

Use the same adapter, model, reasoning effort, fixture, and command when
comparing runs. Record these settings explicitly rather than relying on a
changing local default.

Use one sample for iteration. Before relying on a new or materially changed
case, choose a sample count and acceptable success threshold, then run fresh
independent samples with `--samples N`. Do not loosen assertions after one
failure. First classify the failure as:

- product behavior;
- invalid or over-constrained assertion;
- fixture or prompt ambiguity;
- harness defect;
- environment failure;
- expected model variance.

Fix the responsible layer. Retain a failed workspace with `--keep-workspace`
only when its trace or artifacts are needed for diagnosis.

### Completion checklist

A new executable eval is complete only when:

- its distinct behavioral contract and category are clear;
- its fixture, prompt, agent-call count, and assertions are minimal;
- hidden rubrics remain inaccessible;
- deterministic validation and unit tests pass;
- the focused live case passes the preselected stability threshold;
- token, read, and latency costs are proportionate to unique coverage;
- `COVERAGE.md` reflects the resulting inventory and cost.

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
disjoint: `core` has 8 executable cases, `extended` has 8, and `planned` has
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

### Compare extract retrieval cost

Do not create another eval case for performance comparison. Run the existing
`extract-accelerated-handoff` case against the same fixture and prompt in two
modes. The adapter's `fallback` mode makes only the disposable cache
unavailable, so the skill exercises its normal Markdown-link fallback.

Run both groups concurrently and save their per-sample reports:

```bash
report_dir=$(mktemp -d)
python3 tests/eval/run.py \
  --case extract-accelerated-handoff --samples 3 \
  --report-label forced-fallback --report-json "$report_dir/fallback.json" \
  --agent-command "python3 $(pwd)/tests/eval/adapters/codex.py --model gpt-5.6-luna --reasoning-effort medium --accelerator-mode fallback" &
fallback_pid=$!
python3 tests/eval/run.py \
  --case extract-accelerated-handoff --samples 3 \
  --report-label accelerated --report-json "$report_dir/accelerated.json" \
  --agent-command "python3 $(pwd)/tests/eval/adapters/codex.py --model gpt-5.6-luna --reasoning-effort medium --accelerator-mode enabled" &
accelerated_pid=$!
wait "$fallback_pid" "$accelerated_pid"
python3 tests/eval/compare_extract_metrics.py \
  --fallback "$report_dir/fallback.json" \
  --accelerated "$report_dir/accelerated.json"
```

The analyzer prints the absolute source-report directory and records it in the
generated Markdown, so every snapshot can be traced back to its JSON inputs.
It updates [EXTRACT_METRICS.md](EXTRACT_METRICS.md) by default; use `--output
PATH` for a disposable or alternate report. It performs no agent calls. It
rejects reports with different case
fingerprints, models, reasoning effort, sample identities, or parallelism. Its
paired averages include behavioral failures; environment-invalid samples are
reported and excluded. Agent time comes from adapter traces rather than fixture
setup or assertions. Token output separates total, cached, uncached input,
output, and reasoning tokens. Treat the result as a measurement, not a stable
CI pass/fail threshold.

Case manifests in `cases/*.json` define fixtures, prompts and deterministic
assertions. A manifest may instead define ordered `stages`; agent stages run a
prompt and assertions, while fixture stages model external changes.

Supported assertions:

- paths/content: `path_exists`, `path_absent`, `glob_count`, `glob_contains`,
  `file_contains`, `file_contains_any`, `file_not_contains`, `word_budget`;
- response: `response_contains`, `response_contains_any`,
  `response_not_contains`, `response_section_contains`,
  `response_sections_only`, `response_word_budget`;
- changes: `unchanged`, `changed_only`, `max_changed_files`;
- execution: `command_succeeds`;
- trace: `read_only`, `read_includes`, `max_files_read`;
- commands: `command_includes`, `command_excludes`;
- structure: `balanced_markers`, `no_template_placeholders`,
  `markdown_links_valid`, `semantic_ids_valid`, `spine_mechanical_valid`.

Trace assertions require `.eval/trace.json`. The Codex adapter conservatively
infers reads from completed command events; repository-wide content searches
may count every candidate file as read.

Any assertion may use `"when_trace": {"field": "value"}` for exact trace
conditions. A different trace value makes that assertion not applicable; a
missing trace is a failure. Use this only when the contract genuinely differs
between controlled adapter modes, not to hide ordinary eval failures.

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
