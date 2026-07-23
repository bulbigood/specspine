# Evaluation coverage

## Current inventory

The repository has twenty-eight prose behavioral scenarios. Every scenario is
registered in `cases/`, so `run.py --audit` detects additions that have not been
classified.

| Area | Documented scenarios | Executable fixtures |
|---|---:|---:|
| `specspine-grow` | 9 | 7 |
| `specspine-map` | 8 | 3 |
| `specspine-connect` | 2 | 2 |
| `specspine-extract` | 5 | 5 |
| `specspine-doctor` | 3 | 2 |
| package generator tooling | 1 | 0 |
| Total | 28 | 19 |

`traceable-rule` is assigned to `specspine-map` because its expected result
includes repository-backed observations.

The executable set is divided by resource cost and necessity:

| Category | Manifests | Agent calls | Purpose |
|---|---:|---:|---|
| `core` | 7 | 7 | Minimum behavioral regression set |
| `extended` | 12 | 15 | Lifecycle, terminal-depth refusal, idempotency, merge, removal, bounded growth, traceability, and multilingual Extract behavior |
| `planned` | 9 | 0 | Documentation and future redesign only |

Core and extended cases currently cover:

- greenfield initialization and source-file protection;
- creation of a brownfield map from runtime evidence;
- generic project-agent bootstrap boundaries;
- idempotent reconnect of the project-agent bootstrap;
- production multi-slice Extract handoffs for backend and CLI projects
  in English, a mobile project in Russian, and a data pipeline in Chinese,
  with hidden owner/support/relevance judgments;
- native Markdown navigation when project configuration disables acceleration;
- semantic-ID references and representative repository evidence;
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

Planned cases include deterministic tooling already covered by unit tests,
redundant focused cases superseded by lifecycle coverage, and cases whose
assertions over-constrained architectural choices.

## Behavioral backlog

Items below are not automatic candidates for executable evals. Add one only
when it protects a distinct contract that cannot be covered by a deterministic
test or an existing behavioral case.

Potential gaps:

- agent navigation efficiency on larger-than-small documentation graphs;
- parallel Map orchestration and source-aware integration on a large repository;
- custom `<spine-root>` handling in `grow` and `map`;
- broken links, unreachable specifications, duplicate IDs, and duplicate
  canonical ownership introduced by an agent.

Bootstrap edge cases:

- ambiguous persistent agent-instruction selection;
- explicit bootstrap removal without deleting user-owned files;

Scale and robustness:

- cyclic and highly connected specification graphs;
- large flat namespaces and similarly named concepts;
- stale repository documentation conflicting with code and ADRs;
- prompt-injection-like text in repository evidence;
- runs across multiple agent implementations and repeated stochastic samples.
