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
- use temporary directories;
- avoid writing generated or cache artifacts into the repository;
- avoid changing skill wording merely to satisfy a test.

Performance benchmarks must keep correctness metrics separate from timings.
Use deterministic synthetic inputs and fixed ground truth; never turn host-time
measurements into CI thresholds. Production Extract accepts one structured
`query-json` request. Stdout contains one deterministic JSON object with the
architecture closure and complete selected documents within the token budget.

Run the production skill against the representative backend, CLI, Russian
mobile, and Chinese pipeline agent cases with:

```text
python3 tests/eval/run.py \
  --case extract-backend-multislice \
  --case extract-cli-multislice \
  --case extract-mobile-multislice-ru \
  --case extract-pipeline-multislice-zh-cn \
  --samples 3 \
  --agent-command 'python3 tests/eval/adapters/codex.py'
```

The raw report retains responses, retrieval attempts, deterministic byte/cycle
costs, tool-call counts, and model token counters.

Compare direct navigation, Extract fallback, and accelerated Extract:

```text
python3 tests/eval/benchmark_extract_agents.py \
  --output-dir /tmp/specspine-extract-agent-benchmark \
  --samples 3 --jobs 6
```

Codex currently reports cumulative tokens and wall time for the complete agent
tree. It does not expose exact orchestrator-only or per-subagent counters.

## Agent evals

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
python3 tests/eval/run.py --validate --audit
python3 tools/specspine-adapter-generator/scripts/generate_resources.py --check
```

All deterministic unit tests for the eval runner, adapter, assertions, doctor,
generator, and benchmarks live under `tests/mechanical`. The `tests/eval`
directory contains only agent-evaluation infrastructure and cases.

The npm installation test under `tests/mechanical` and live agent evals are
opt-in. Do not run them unless the task explicitly requires their external
dependencies or execution.
