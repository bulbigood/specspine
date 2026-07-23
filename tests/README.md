# Test rules

These rules apply to every test, fixture, scenario, and harness under `tests/`.
Keep tests reliable when skill prose changes without changing behavior.

## Choose the correct layer

- Use mechanical tests for deterministic code, parsers, schemas, file layout,
  graph behavior, cache behavior, CLI contracts, and harness data flow.
- Use eval cases for behavior that depends on an AI agent understanding and
  applying skill instructions.
- Do not turn an agent-behavior expectation into a mechanical approximation.

## Mechanical tests

Mechanical tests must not require particular natural-language words, phrases,
headings, or sentence structure in skills, references, templates, prompts,
model responses, explanations, or human-readable error messages.

Prefer assertions over observable structure and behavior:

- paths, file counts, links, exit codes, and machine-readable JSON fields;
- before/after state, idempotency, refresh, fallback, and isolation behavior;
- parsed structures, formal grammar, graph reachability, and query results;
- sentinel values for prompt composition, propagation, and leakage checks.

Exact values are appropriate only when they are machine contracts, such as
filenames, semantic IDs, managed markers, template variables, CLI flags, JSON
enums, finding codes, or formal regular expressions. Do not treat explanatory
text such as a search reason or error sentence as a machine contract.

When testing prompts, inject unique sentinel values and verify their placement
or exclusion. Never assert the wording of production instructions. When
testing skill packages, validate frontmatter, references, resource existence,
budgets, and dependency boundaries rather than prose.

Mechanical tests must:

- use the Python standard library unless a repository-wide decision says
  otherwise;
- be deterministic, hermetic, and independent of network access or live AI;
- use temporary directories and explicit disposable cache locations;
- avoid writing generated or cache artifacts into the repository;
- test optional accelerators as optional: failure must preserve the documented
  fallback rather than fail unrelated functionality;
- avoid changing skill wording merely to satisfy a test.

Performance benchmarks must keep correctness metrics separate from timings.
Use deterministic synthetic inputs and fixed ground truth; never turn host-time
measurements into CI thresholds. Run the Extract retrieval benchmark without an
agent using `python3 tests/mechanical/benchmark_extract_search.py`.

Compare the same structured workload under both Extract ranking systems with:

```text
python3 tests/mechanical/benchmark_extract_search.py --ranking legacy
python3 tests/mechanical/benchmark_extract_search.py --ranking faceted-bm25
python3 tests/mechanical/benchmark_extract_search.py --ranking faceted-normalized
```

The skill-facing `search_spine.py` remains unchanged. Experimental queries use
`search_spine_v2.py --ranking faceted-bm25 --queries-json '<json>'`, where each
slice contains an `id`, one or more `must` synonym groups, and optional
`should` synonym groups. Terms inside a group are alternatives; every `must`
group is required. V2 stdout is marked document text grouped by slice, not a
JSON list of paths. Slice blocks report `matched` or `no_match` and contain
marked hits with matching evidence. Document bodies follow the slice blocks
and are emitted once even when several slices select the same path. Use
`--max-output-bytes` to bound document output; whole documents are omitted and
marked instead of being cut mid-file.

The `faceted-normalized` arm uses derived schema v4. Normalized tokens and
English/Russian morphology candidates are routed through indexed token and
prefix tables; Chinese substring candidates use indexed 1–3-grams followed by
full-run verification. Incremental refresh updates these derived rows with the
document FTS index. This avoids scanning every document per normalized term
without changing the production `search_spine.py`.

Representative retrieval corpora live under `tests/retrieval-corpora/corpora`.
Each immutable corpus contains a natural project fixture, fixed ranker slices,
agent-level requests, graded relevance judgments, and a SHA-256 document
inventory. Validate and run the paired ranker benchmark with:

```text
python3 tools/specspine-extract/validate_corpus.py \
  tests/retrieval-corpora/corpora/*/manifest.json
python3 tests/retrieval-corpora/benchmark.py
```

The benchmark JSON includes global paired summaries plus breakdowns by
documentation language and project type.

The benchmark-only Extract skill is
`tests/eval/skills/specspine-extract-v2`; it is not a production or installable
skill. The eval adapter selects its ranking arm with
`--ranking legacy|faceted-bm25|faceted-normalized`.

Run the representative agent-level A/B across backend, CLI, Russian mobile,
and Chinese pipeline multi-slice tasks with:

```text
python3 tests/eval/run_extract_ranking_ab.py \
  --output-dir /tmp/specspine-extract-ranking-ab \
  --samples 3
```

The three arms run sequentially to avoid cross-arm service-load bias; cases and
samples within each arm use the configured parallel job limit. The generated
`comparison.md` reports canonical-owner and owner-plus-support recall, handoff
document precision, hard negatives, retrieval calls and repeats, final handoff
bytes, retrieval output bytes, and model tokens. Raw per-sample JSON remains
beside it.

## Eval tests

Use eval cases to verify whether an agent locates context, preserves semantics,
respects scope, and produces the intended architectural outcome. Prefer
observable artifacts and structural assertions. Use content assertions only
when behavior cannot be established structurally, and accept concise semantic
alternatives instead of one mandatory phrase.

Never expose hidden rubrics to the evaluated agent or edit a skill around an
eval assertion. See [eval/README.md](eval/README.md) for harness-specific rules.

## Execution speed

Run independent tests, cases, and eval samples concurrently, bounded by the
available CPU, memory, and external-service capacity. Prefer each harness's
parallel default; do not pass `--jobs 1` for routine runs or qualification.
Use sequential execution only for an unavoidable shared-state or ordering
constraint, or while isolating a diagnosed failure. State that reason and
restore parallel execution for final verification.

Design tests for safe parallel execution: use isolated temporary workspaces,
unique cache paths, no fixed shared mutable files, and no dependence on global
execution order. Independent deterministic gates may also run concurrently
after the focused test passes.

## Required checks

Run the relevant focused test first, then the complete deterministic gates:

```bash
python3 -m unittest discover -s tests/mechanical -p 'test_*.py'
python3 -m unittest discover -s tests/eval -p 'test_*.py'
python3 tests/eval/run.py --validate --audit
python3 tools/specspine-adapter-generator/scripts/generate_resources.py --check
```

The npm installation test and live agent evals are opt-in. Do not run them
unless the task explicitly requires their external dependencies or execution.
