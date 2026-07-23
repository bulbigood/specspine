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
`extract-accelerated-handoff` case against the same fixture and scenario in four
profiles: no Extract skill, forced fallback, isolated cold, and prewarmed. The
no-Extract profile does not stage a skill or retrieval instructions; it measures
direct project-documentation search. Profile-specific assertions remove only
the Extract response schema, retrieval command, and accelerator read budget.
The required documents, semantic constraint, exclusions, read-only behavior,
and response budget remain checked. The adapter's
`fallback` mode makes only the disposable cache
unavailable, so the skill exercises its normal Markdown-link fallback.
Every benchmark corpus root must include an `AGENTS.md` rendered from the
`specspine-connect` bootstrap with its real Spine path and documentation
language. Codex loads this project instruction in every profile. The no-Extract
profile therefore has the same persistent discovery route as the Extract
profiles, while only the staged skill and its prompt scaffolding differ. The
runner validates the managed markers, resolved index path, and absence of
template placeholders. The deterministic ledger reports `AGENTS.md` bytes
separately from skill context bytes.

Run all groups concurrently and save their per-sample reports:

```bash
report_dir=$(mktemp -d -t specspine-extract-eval.XXXXXX)
run_id="extract-ab-$(date -u +%Y%m%dT%H%M%SZ)"
python3 tests/eval/run.py \
  --case extract-accelerated-handoff --samples 5 \
  --execution-profile no-extract \
  --run-id "$run_id-no-extract" \
  --report-label no-extract --report-json "$report_dir/no-extract.json" \
  --agent-command "python3 $(pwd)/tests/eval/adapters/codex.py --model gpt-5.6-luna --reasoning-effort medium --accelerator-mode enabled" &
no_extract_pid=$!
python3 tests/eval/run.py \
  --case extract-accelerated-handoff --samples 5 \
  --run-id "$run_id-fallback" \
  --report-label forced-fallback --report-json "$report_dir/fallback.json" \
  --agent-command "python3 $(pwd)/tests/eval/adapters/codex.py --model gpt-5.6-luna --reasoning-effort medium --accelerator-mode fallback" &
fallback_pid=$!
python3 tests/eval/run.py \
  --case extract-accelerated-handoff --samples 5 \
  --run-id "$run_id-cold" \
  --report-label accelerated-cold --report-json "$report_dir/cold.json" \
  --agent-command "python3 $(pwd)/tests/eval/adapters/codex.py --model gpt-5.6-luna --reasoning-effort medium --accelerator-mode enabled" &
cold_pid=$!
python3 tests/eval/run.py \
  --case extract-accelerated-handoff --samples 5 \
  --run-id "$run_id-warm" \
  --report-label accelerated-prewarmed --report-json "$report_dir/warm.json" \
  --agent-command "python3 $(pwd)/tests/eval/adapters/codex.py --model gpt-5.6-luna --reasoning-effort medium --accelerator-mode enabled --cache-profile prewarmed" &
warm_pid=$!
fallback_status=0
cold_status=0
warm_status=0
no_extract_status=0
wait "$no_extract_pid" || no_extract_status=$?
wait "$fallback_pid" || fallback_status=$?
wait "$cold_pid" || cold_status=$?
wait "$warm_pid" || warm_status=$?
python3 tests/eval/compare_extract_metrics.py \
  --no-extract "$report_dir/no-extract.json" \
  --fallback "$report_dir/fallback.json" \
  --accelerated "$report_dir/cold.json" \
  --warm "$report_dir/warm.json"
test "$no_extract_status" -eq 0 -a "$fallback_status" -eq 0 -a "$cold_status" -eq 0 -a "$warm_status" -eq 0
```

Each adapter invocation uses a private disposable runtime and cache. The cold
group leaves that cache empty; the prewarmed group builds the exact workspace
index before starting the agent. Sharing one cache directory between samples
would not create a warm index because production cache keys include each
workspace's absolute Spine path. The report records both profiles explicitly.
Prewarm setup is excluded from agent duration and shown separately per sample.
Cold and prewarmed samples are also compared directly, independently of their
comparisons against fallback.
The report compares no Extract separately with forced fallback and the cold
accelerator. This distinguishes the value and cost of Extract's navigation
instructions from the additional effect of SQLite routing. The no-Extract
profile must record zero retrieval attempts; otherwise the comparator rejects
the reports.
Use the prewarmed group when cache lifecycle, locking, refresh, or index startup
changes. For routine retrieval-quality A/B runs, omit that group and `--warm`;
warm state should not change agent tokens when routing output is identical.

The analyzer prints the absolute source-report directory and records it in the
generated Markdown, so every snapshot can be traced back to its JSON inputs.
By default it creates a timestamped, never-overwritten report under
`tests/eval/reports/`. `--output PATH` selects a preferred location, but if that
path exists the analyzer adds a numeric suffix instead of replacing it. Raw JSON
reports stay in the unique system temporary directory created by `mktemp`; the
runner and analyzer do not remove them, leaving eventual cleanup to the
operating system. It performs no agent calls. It
rejects reports with incompatible case/skill or adapter fingerprints, models,
reasoning effort, Codex CLI versions, sample identities, or configured
parallelism. Pairwise cold comparisons also require identical cache profiles;
the explicit prewarmed comparison permits only that intentional difference.
Sample numbers verify completeness but independent
stochastic calls are not treated as statistical pairs. Environment-invalid
samples are reported and excluded. Agent time comes from adapter traces rather
than fixture setup or assertions. The Markdown is a compact median-first
summary; means stay beside medians to expose outlier influence, and bootstrap
intervals apply to median differences. It retains concise sample outcomes,
routing/usefulness aggregates, failures, byte/cycle proxies, agent-message
events, and observed concurrency. Agent-message events are a better proxy for
repeated model interaction than parallel shell-command count. Detailed attempts
and commands remain in the raw JSON. Normal A/B
runs omit retrieval telemetry and therefore execute the exact compact
production command. For an instrumented A/B, add `--retrieval-telemetry
minimal` to every adapter command. The adapter stages a repository-only tool
that transparently observes the disposable production script without changing
the staged `SKILL.md` command. It writes compact cache state and timings to a
sidecar while preserving production stdout byte-for-byte; telemetry does not
enter model context. Use
`tools/specspine-extract/search_spine_diagnostics.py --telemetry full` only in
mechanical tests or direct investigations that need ranking signals, candidate
details, runtime versions, and failure reasons.
It also keeps a deterministic byte/cycle cost ledger and relates returned
direct/graph candidates to conservatively inferred subsequent document reads.
These proxies explain context growth but are not model tokens.
Ledger rows overlap and must not be summed into a synthetic total.
Raw JSON also retains bounded response/stderr diagnostics after workspaces are
removed. Token counters come only from the final top-level
`turn.completed.usage` event; nested counters in tool payloads are ignored.
Treat the result as a measurement, not a stable CI pass/fail threshold.

### Compare Extract v2 ranking systems

The four `extract-v2-*-multislice` cases reuse the immutable retrieval corpora
and exercise two English project types plus Russian and Chinese documentation.
Their hidden `handoff_judgments` distinguish canonical owners, grade-2
supporting specifications, the broader relevant set, and hard negatives. The
runner copies this gold metadata into JSON reports but never exposes it to the
evaluated workspace or prompt.

Run all three ranking arms:

```bash
report_dir=$(mktemp -d -t specspine-extract-ranking-ab.XXXXXX)
python3 tests/eval/run_extract_ranking_ab.py \
  --output-dir "$report_dir" \
  --samples 3 \
  --jobs 4 \
  --model gpt-5.6-luna \
  --reasoning-effort medium
```

Each arm receives identical cases, prompts, benchmark-only skill, model
settings, and sample identities. Arms are intentionally sequential so service
load from one ranker cannot distort another; independent cases and samples
inside an arm remain parallel. `comparison.md` contains macro agent-level
quality and cost metrics, while `legacy.json`, `faceted-bm25.json`, and
`faceted-normalized.json` preserve bounded responses, retrieval attempts, and
deterministic byte ledgers.

For an existing subset of two or three compatible reports:

```bash
python3 tests/eval/compare_extract_rankings.py \
  legacy.json faceted-bm25.json faceted-normalized.json \
  --output comparison.md
```

The comparator rejects different case/skill fingerprints, adapter files,
runtime metadata, commands beyond `--ranking`, or sample identities.

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
