# Evaluation coverage

## Current inventory

The repository has twenty-nine prose behavioral scenarios. Every scenario is
registered in `cases/`, so `run.py --audit` detects additions that have not been
classified.

| Area | Documented scenarios | Executable fixtures |
|---|---:|---:|
| `specspine-grow` | 9 | 7 |
| `specspine-map` | 7 | 3 |
| `specspine-map-large` | 2 | 0 |
| `specspine-connect` | 2 | 2 |
| `specspine-extract` | 5 | 5 |
| `specspine-doctor` | 3 | 2 |
| package generator tooling | 1 | 0 |
| Total | 29 | 19 |

`traceable-rule` is assigned to `specspine-map` because its expected result
includes repository-backed observations.

### Map coverage

Executable `specspine-map` coverage currently consists of four agent calls
across three cases:

- `lifecycle-survey-deepen`: a shallow initial survey followed by bounded
  deepening without reopening unrelated source;
- `lifecycle-drift-refresh`: a narrow refresh that preserves accepted intent,
  records changed implementation as observation, and leaves disagreement open;
- `traceable-rule`: evidence-backed semantic-ID ownership and cross-document
  references.

There is no executable `specspine-map-large` case. Its scheduling, isolated
staging, move-only publication, recovery, saturation, normalization, and
sequential fallback are currently protected only by deterministic contract
tests. The two registered large-Map scenarios remain planned because their
file-result assertions cannot observe subagent dispatch, concurrency, refill
ordering, or recovery and would therefore be expensive without accurately
testing the orchestration contract.

Distinct behavioral gaps worth considering are:

- atomic Map writing publish-ready candidates only to an explicitly supplied
  staging root while keeping the live Spine read-only;
- atomic Map returning no new document when the live Spine already answers the
  bounded question;
- custom `<spine-root>` handling;
- large-Map handoff of every bounded question to the companion
  `$specspine-map`;
- rolling replacement dispatch before candidate acceptance, isolated producer
  writes, report-driven backlog growth, retry/resume behavior, and move-only
  publication;
- a controlled no-subagent execution mode that proves the same protocol is
  retained sequentially;
- post-saturation normalization without source rereads and optional Doctor
  gating.

Do not make a large-Map scenario executable until the adapter records
subagent lifecycle and ordering or supplies a deterministic controlled
producer. Final-file assertions alone are insufficient. Prefer one small
staged-output Map case and, after that instrumentation exists, one two-producer
large-Map case that covers the orchestration path end to end.

The executable set is divided by resource cost and necessity:

| Category | Manifests | Agent calls | Purpose |
|---|---:|---:|---|
| `core` | 7 | 7 | Minimum behavioral regression set |
| `extended` | 12 | 15 | Lifecycle, terminal-depth refusal, idempotency, merge, removal, bounded growth, traceability, and multilingual Extract behavior |
| `planned` | 10 | 0 | Documentation and future redesign only |

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
- executable large-Map orchestration, recovery, and staged publication;
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
