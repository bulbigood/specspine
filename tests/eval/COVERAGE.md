# Evaluation coverage

## Current inventory

The repository has thirty-one prose behavioral scenarios. Every scenario is
registered in `cases/`, so `run.py --audit` detects additions that have not been
classified.

| Area | Documented scenarios | Executable fixtures |
|---|---:|---:|
| `specspine-grow` | 9 | 7 |
| `specspine-map` | 9 | 5 |
| `specspine-map-large` | 3 | 1 |
| `specspine-connect` | 2 | 2 |
| `specspine-extract` | 5 | 5 |
| `specspine-doctor` | 3 | 2 |
| package generator tooling | 1 | 0 |
| Total | 32 | 22 |

`traceable-rule` is assigned to `specspine-map` because its expected result
includes repository-backed observations.

### Map coverage

Executable `specspine-map` coverage currently consists of six agent calls
across five cases:

- `lifecycle-survey-deepen`: a shallow initial survey followed by bounded
  deepening without reopening unrelated source;
- `lifecycle-drift-refresh`: a narrow refresh that preserves accepted intent,
  records changed implementation as observation, and leaves disagreement open;
- `traceable-rule`: evidence-backed semantic-ID ownership and cross-document
  references;
- `map-staged-producer`: one bounded producer writes a publish-ready candidate
  to a private output root while the live Spine remains read-only.
- `map-direct-comparison-small`: maps the same controlled three-area repository
  used by `map-large-rolling-small`, enabling a paired quality/cost benchmark.

`map-large-rolling-small` provides one controlled executable orchestration
case. One top-level invocation must dispatch exactly three bounded mapper
producers using two initial worker slots. Codex JSONL collaboration events
verify initial saturation, mapper handoff, bounded dispatch count, and
replacement dispatch before staged candidate consumption.
Final assertions verify move-based publication, source protection, disposable
run-root cleanup, bounded output, and mechanical Spine validity. This case
costs one orchestrator plus three producer agents and belongs in the explicit
`expensive` category.

Remaining distinct behavioral gaps are:

- atomic Map returning no new document when the live Spine already answers the
  bounded question;
- custom `<spine-root>` handling;
- report-driven discovery of a question not present in the initial large-Map
  backlog;
- large-Map retry/resume, candidate rejection, path collision, and source-state
  change handling;
- a controlled no-subagent execution mode that proves the same protocol is
  retained sequentially;
- post-saturation normalization without source rereads and optional Doctor
  gating.

Keep broader parallel and no-subagent scenarios planned until they protect one
of these distinct gaps with observable assertions. Do not add another
final-file-only large-Map eval.

The executable set is divided by resource cost and necessity:

| Category | Manifests | Top-level agent calls | Purpose |
|---|---:|---:|---|
| `core` | 8 | 8 | Minimum behavioral regression set, including atomic staged Map output |
| `extended` | 12 | 15 | Lifecycle, terminal-depth refusal, idempotency, merge, removal, bounded growth, traceability, and multilingual Extract behavior |
| `expensive` | 2 | 2 | Paired direct Map and rolling Map Large benchmark; the latter has three nested producers |
| `planned` | 10 | 0 | Documentation and future redesign only |

The table counts harness invocations. `map-large-rolling-small` additionally
spawns exactly three producer agents, enforced by its trace assertions. Its
separate category prevents ordinary `core` or `extended` runs from selecting
it.

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
- large-Map recovery and report-discovered backlog growth beyond the controlled
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
