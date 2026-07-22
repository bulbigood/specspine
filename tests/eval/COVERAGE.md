# Evaluation coverage

## Current inventory

The repository has twenty-two prose behavioral scenarios. Every scenario is
registered in `cases/`, so `run.py --audit` detects additions that have not been
classified.

| Area | Documented scenarios | Executable fixtures |
|---|---:|---:|
| `specspine-grow` | 9 | 7 |
| `specspine-map` | 7 | 3 |
| `specspine-connect` | 4 | 3 |
| `specspine-doctor` | 3 | 2 |
| package generator tooling | 1 | 0 |
| Total | 24 | 15 |

`traceable-visual-spec` is assigned to `specspine-map` because its expected
result includes repository-backed observations.

The executable set is divided by resource cost and necessity:

| Category | Manifests | Agent calls | Purpose |
|---|---:|---:|---|
| `core` | 6 | 6 | Minimum behavioral regression set |
| `extended` | 9 | 13 | Lifecycle, terminal-depth refusal, idempotency, specialized integration, merge, removal, bounded growth, and visualization behavior |
| `planned` | 9 | 0 | Documentation and future redesign only |

Core and extended cases currently cover:

- greenfield initialization and source-file protection;
- creation of a brownfield map from runtime evidence;
- generic project-agent bootstrap boundaries;
- idempotent reconnect and specialized downstream SDD integration;
- semantic-ID references, evidence, and a Mermaid lifecycle view.
- semantic Doctor diagnosis and bounded mechanical repair without runtime companions;
- recursive Doctor link and marker-bounded semantic-ID validation across
  nested specification directories;
- staged lifecycle transitions covering survey, deepening, intentional split,
  downstream repository evolution, drift refresh, supersession, removal, and
  bounded Doctor repair.
- repeated Grow deepening with per-document and whole-Spine word budgets while
  preserving addressable architectural meaning.
- Grow refusal when a specification already has terminal architectural detail
  and the request asks only for implementation-manual content.

Deterministic runtime-skill generation and drift detection remain covered by
unit tests and do not consume an agent invocation.

Planned cases include unsupported native-SDD execution, deterministic tooling
already covered by unit tests, redundant focused cases superseded by lifecycle
coverage, and cases whose assertions over-constrained architectural choices.

## Planned fixture gap

- standalone use of a generated binding.

This needs a native downstream SDD fixture and executor.

## Behavioral backlog

Items below are not automatic candidates for executable evals. Add one only
when it protects a distinct contract that cannot be covered by a deterministic
test or an existing behavioral case.

Potential gaps:

- agent navigation efficiency on larger documentation graphs, including read
  and context-size budgets;
- custom `<spine-root>` handling in `grow` and `map`;
- broken links, unreachable specifications, duplicate IDs, and duplicate
  canonical ownership introduced by an agent.

Integration edge cases:

- ambiguous agent instruction or SDD framework selection;
- refresh after framework conventions change;
- generated binding with user edits or a missing ownership marker;
- explicit integration removal without deleting user-owned files;
- external project evidence supplied through MCP with and without
  authorization.

Scale and robustness:

- cyclic and highly connected specification graphs;
- large flat namespaces and similarly named concepts;
- stale repository documentation conflicting with code and ADRs;
- prompt-injection-like text in repository evidence;
- runs across multiple agent implementations and repeated stochastic samples.

## Semantic evaluation boundary

The mechanical runner does not judge architectural meaning. The comparative
model-judge layer scores:

- correct canonical owner selection;
- reasonableness of decomposition;
- `Observed` versus `Inferred` classification;
- minimality and sufficiency of context;
- invention of product or technology decisions;
- preservation of meaning without implementation-level duplication.

Implementation uses frozen task rubrics. Mechanical checks remain independent
objective gates, while overall comparative pass
requires both mechanical and semantic pass. Model name, version, prompt, sample
count, duration, and token usage are recorded for reproducibility.

Comparative downstream coverage under `comparisons/` uses a hash-pinned full
`node-express-boilerplate` repository. Four value tasks cover an
architecture-neutral utility change, cross-cutting authorization, an
intended-versus-observed token ownership conflict, and a blocking security
policy. Every task compares the native repository with the same repository plus
the complete Spine; the agent navigates the documentation graph itself.
See `HYPOTHESIS.md` for sampling budgets and interpretation.
