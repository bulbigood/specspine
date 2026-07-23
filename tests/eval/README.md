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
```

The harness's deterministic unit tests live in `tests/mechanical` and run with
the repository's mechanical suite. The optional installed-package test requires
npm execution:

```bash
SPECSPINE_RUN_NPX=1 python3 -m unittest discover \
  -s tests/mechanical -p 'test_npx_install.py' -v
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
- Use `word_budget` only when uncontrolled artifact growth is itself a product
  regression. Do not use it as a proxy for documentation quality; record word
  counts and judge whether the added text improves architectural meaning.
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
`--agent-command`. The standard Codex adapter defaults the top-level agent
(the Map Large orchestrator) to `gpt-5.6-terra` with `medium` reasoning and
spawned agents to `gpt-5.6-luna` with `medium` reasoning. Pass overrides
through the quoted adapter command. This example states all defaults explicitly:

```bash
python3 tests/eval/run.py \
  --category core \
  --agent-command "python3 $(pwd)/tests/eval/adapters/codex.py --model gpt-5.6-terra --reasoning-effort medium --subagent-model gpt-5.6-luna --subagent-reasoning-effort medium"
```

`--case` and `--category` are repeatable and may be combined. There is no
implicit run-all mode. Planned cases are never executed. Categories are
disjoint: `core` has 8 executable cases, `extended` has 12, `expensive` has 2,
and `planned` has 10 documented non-executable cases.

`map-large-rolling-small` makes one top-level call and normally three nested
producer calls; one retry is tolerated. It is isolated in `expensive`, so ordinary `core` and
`extended` runs never select it. Run it with one sample during ordinary
iteration; use repeated samples only for release calibration.

The Codex adapter defaults the top-level agent to `gpt-5.6-terra` with medium
reasoning and nested agents to `gpt-5.6-luna` with medium reasoning. The
Map-Large case asserts all four values from the runtime trace.

```bash
python3 tests/eval/run.py \
  --case map-large-rolling-small --samples 1 --jobs 1 \
  --agent-command "python3 $(pwd)/tests/eval/adapters/codex.py"
```

To compare direct Map with orchestrated Map Large on the same controlled
three-area repository:

```bash
report_dir=$(mktemp -d -t specspine-map-modes.XXXXXX)
python3 tests/eval/benchmark_map_modes.py \
  --output-dir "$report_dir" --samples 1
```

Both arms use the same top-level model and reasoning effort: Terra/medium by
default. Only Map Large creates producers; those use Luna/medium by default.
Model overrides apply symmetrically to both top-level arms.

The arms use identical project files and common mechanical assertions. For each
paired sample, one additional blind judge compares the complete generated
Spines using architectural fidelity, evidence and epistemic discipline,
responsibility and boundary clarity, material coverage, coherence/navigation,
signal-to-noise/usefulness, and holistic overall quality. Length is reported but
is not a failure or quality penalty by itself. Use `--skip-quality-judge` only
for mechanical harness debugging.

The report compares documentation-quality scores and preference, pass rate,
word counts, case and complete-agent-tree wall time, cumulative tree
input/cache-read/cache-write/uncached/output/reasoning tokens, project reads,
tool cycles, spawned agents, and sanitized collaboration lifecycle counts
(spawn/wait/close outcomes and latest producer statuses). Judge time and tokens
are reported separately and excluded from both arms. Current Codex JSONL exposes only cumulative token usage for the
orchestrator plus nested producers; it does not expose exact orchestrator-only
or per-producer token/time breakdowns. The report states this limitation and
does not estimate missing counters. Keep one sample for routine calibration;
repeated samples are release-level evidence. Successful reports include only
the explicitly requested `specspine/**/*.md` snapshots needed by the blind
judge.

Each case gets a clean temporary workspace. Cases run with concurrency 8 by
default; change it with `--jobs N`. Workspaces default to
`~/.cache/specspine-eval/workspaces`; override with
`SPECSPINE_EVAL_WORKSPACES_DIR`. Failed workspaces are retained only with
`--keep-workspace`.

Use `--samples N` to run each selected case independently in `N` fresh
workspaces and report its success rate. This differs from a manifest's `runs`:
those are sequential agent calls inside one workspace and test repeated or
lifecycle behavior.

### Evaluate production Extract

The four `extract-*-multislice` cases reuse the immutable retrieval corpora and
exercise two English project types plus Russian and Chinese documentation.
Their hidden `handoff_judgments` distinguish canonical owners, grade-2
supporting specifications, the broader relevant set, and hard negatives. The
runner copies this gold metadata into JSON reports but never exposes it to the
evaluated workspace or prompt.

Run the single production policy:

```bash
report=$(mktemp -t specspine-extract.XXXXXX.json)
python3 tests/eval/run.py \
  --case extract-backend-multislice \
  --case extract-cli-multislice \
  --case extract-mobile-multislice-ru \
  --case extract-pipeline-multislice-zh-cn \
  --samples 3 \
  --jobs 4 \
  --report-json "$report" \
  --agent-command 'python3 tests/eval/adapters/codex.py'
```

The report preserves bounded responses, retrieval attempts, effective fixed
ranking/graph policy, deterministic byte ledgers, tool cycles, and token
counters.

To compare the complete agent workflow—not ranking variants—run the three fixed
arms against the same EN/RU/ZH cases:

```bash
report_dir=$(mktemp -d -t specspine-extract-agents.XXXXXX)
python3 tests/eval/benchmark_extract_agents.py \
  --output-dir "$report_dir" --samples 3 --jobs 4
```

The arms are direct documentation navigation without Extract, Extract with an
intentionally unavailable disposable accelerator, and production accelerated
Extract. The benchmark writes one raw JSON report per arm and `comparison.md`
with behavioral success, duration, tokens, project reads, tool cycles, and
retrieval bytes. `--retrieval-profile` is evaluator-only and is never exposed
by the production skill or search CLI.

Case manifests in `cases/*.json` define fixtures, prompts and deterministic
assertions. A manifest may instead define ordered `stages`; agent stages run a
prompt and assertions, while fixture stages model external changes.

Keep small fixtures inline in `initial_files`. Put large reusable repository
fixtures under `context-bundles/` and reference them with `initial_tree`; the
runner copies the tree into each clean workspace and includes its contents in
the case fingerprint. Use exactly one fixture source per case so the benchmark
corpus remains a single source of truth.

Supported assertions:

- paths/content: `path_exists`, `path_absent`, `glob_count`, `glob_contains`,
  `file_contains`, `file_contains_any`, `file_not_contains`, `word_budget`;
- response: `response_contains`, `response_contains_any`,
  `response_not_contains`, `response_section_contains`,
  `response_sections_only`, `response_word_budget`;
- changes: `unchanged`, `changed_only`, `max_changed_files`;
- execution: `command_succeeds`;
- trace: `read_only`, `read_includes`, `max_files_read`, `trace_equals`;
- commands: `command_includes`, `command_excludes`;
- collaboration: `collab_spawn_count`, `collab_initial_spawn_count`,
  `collab_spawn_prompts`, `collab_targets_spawned_agents`,
  `collab_refill_before_staging_consume`;
- structure: `balanced_markers`, `no_template_placeholders`,
  `markdown_links_valid`, `semantic_ids_valid`, `spine_mechanical_valid`.

Trace assertions require `.eval/trace.json`. The Codex adapter conservatively
infers reads from completed command events; repository-wide content searches
may count every candidate file as read. Reports therefore call this metric
`inferred distinct files read`; it is a conservative scope/read-budget signal,
not proof that every counted file contributed its full content to model
context.

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
