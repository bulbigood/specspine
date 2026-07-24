# Evaluation coverage

## Current inventory

The repository has thirty-three prose behavioral scenarios. Every scenario is
registered in `cases/`, so `run.py --audit` detects additions that have not been
classified.

| Area | Documented scenarios | Executable fixtures |
|---|---:|---:|
| `specspine-grow` | 9 | 7 |
| `specspine-map` | 9 | 5 |
| `specspine-map-deep` | 4 | 1 |
| `specspine-connect` | 2 | 2 |
| `specspine-extract` | 5 | 5 |
| `specspine-doctor` | 3 | 2 |
| package generator tooling | 1 | 0 |
| Total | 33 | 22 |

`traceable-rule` is assigned to `specspine-map` because its expected result
includes repository-backed observations.

### Map coverage

Executable `specspine-map` coverage currently consists of seven to fifteen
agent calls across five cases, depending on when the saturation benchmark
reaches its unchanged terminal invocation:

- `lifecycle-survey-deepen`: a shallow initial survey followed by bounded
  deepening without reopening unrelated source;
- `lifecycle-drift-refresh`: a narrow refresh that preserves accepted intent,
  records changed implementation as observation, and leaves disagreement open;
- `traceable-rule`: evidence-backed semantic-ID ownership and cross-document
  references;
- `map-staged-producer`: one bounded producer writes a publish-ready candidate
  to a private output root while the live Spine remains read-only.
- `map-sequential-saturation-small`: repeatedly performs one Map step on the same
  controlled six-area repository used by `map-deep-rolling-small` until an
  unchanged terminal invocation, enabling a paired saturation-quality/cost
  benchmark.

`map-deep-rolling-small` provides one controlled executable orchestration case.
One top-level invocation receives a production-like whole-repository request
and must keep two available producer slots working across more ready branches
than slots. Codex JSONL collaboration events verify spawning and same-session
continuation.
Both A/B arms copy the same 21-file
`map-modes-six-area` fixture tree, including six source/test/config evidence
slices, require the same terminal evidence coverage, and stop only after the
requested repository scope is saturated. Generated artifacts verify material
coverage through their evidence. The
runtime trace pins the orchestrator to Terra/medium and configures
producers as Luna/medium. Map is installed only so the orchestrator can obtain,
save, and emit in one script call a generated bundle containing the complete
Map body, every UTF-8 reference, and every UTF-8 Markdown template; producers
must not load those source files themselves. Collaboration assertions require
two initial producers, no more than two simultaneously active producers,
multiple total spawns and resumptions, and an encrypted-message size ratio that
rejects repeated bundles in continuations. Discovery is adaptive and keeps no
ledger or recovery manifest. Final assertions verify
move-based publication, source protection, disposable run-root cleanup, and
mechanical Spine validity. Document length is observed, not bounded. The paired
benchmark adds one blind holistic documentation-quality judgment per sample
pair. The judge is an independent bounded task and therefore defaults to
Luna/medium; its cost is excluded from both arms. This case normally costs one
Terra/medium orchestrator plus several Luna/medium producer sessions and belongs
in the explicit `expensive` category.

Remaining distinct behavioral gaps are:

- atomic Map returning no new document when the live Spine already answers the
  bounded question;
- custom `<spine-root>` handling;
- report-driven recursive discovery followed by a terminal no-output Map
  producer;
- large-Map candidate rejection and path-collision handling;
- a controlled no-subagent execution mode that proves the same protocol is
  retained sequentially;
- unknown partial producer capacity with rejected starts retained as queued
  work;
- focused large-Map scope that ignores unrelated repository areas;
- post-saturation normalization without candidate rereads and optional Doctor
  gating.

Keep broader parallel and no-subagent scenarios planned until they protect one
of these distinct gaps with observable assertions. Do not add another
final-file-only large-Map eval.

The executable set is divided by resource cost and necessity:

| Category | Manifests | Top-level agent calls | Purpose |
|---|---:|---:|---|
| `core` | 8 | 8 | Minimum behavioral regression set, including atomic staged Map output |
| `extended` | 12 | 15 | Lifecycle, terminal-depth refusal, idempotency, merge, removal, bounded growth, traceability, and multilingual Extract behavior |
| `expensive` | 2 | 3–11 per sample | Paired sequential Map saturation and Map Deep saturation benchmark with constrained producer capacity |
| `planned` | 11 | 0 | Documentation and future redesign only |

The table counts top-level agent invocations. The sequential Map arm uses 2–10
invocations, stopping at the first unchanged terminal result; Map Deep uses one
top-level orchestrator and additionally creates multiple producer sessions.
The separate category prevents ordinary `core` or `extended` runs from
selecting either expensive arm.

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
- large-Map report-discovered backlog growth beyond the controlled
  rolling-publication case;
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
