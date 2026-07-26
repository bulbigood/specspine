# Evaluation coverage

## Current inventory

The repository has thirty-five prose behavioral scenarios. Every scenario is
registered in `cases/`, so `run.py --audit` detects additions that have not been
classified.

| Area | Documented scenarios | Executable fixtures |
|---|---:|---:|
| `specspine-grow` | 9 | 7 |
| `specspine-map` | 13 | 7 |
| `specspine-extract` | 5 | 5 |
| `specspine-doctor` | 7 | 6 |
| package generator tooling | 1 | 0 |
| Total | 35 | 25 |

`traceable-rule` is assigned to `specspine-map` because its expected result
includes repository-backed observations.

### Map coverage

Executable `specspine-map` coverage currently consists of seven to fifteen
agent calls across five cases, depending on when the comparative benchmark
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

`map-deep-rolling-small` provides one controlled executable exhaustive-mode case.
One top-level invocation receives a production-like whole-repository request,
builds a deterministic source inventory, and keeps three producer slots working
across more ready ToDo entries than slots. Every ToDo receives a fresh producer;
Codex JSONL collaboration events verify spawning and reject producer
continuation or reuse.
Both benchmark arms copy the same 21-file
`map-modes-six-area` fixture tree, including six source/test/config evidence
slices, require the same terminal evidence coverage, and stop only after the
requested inventory is classified and all derived ToDo is resolved. Generated artifacts verify material
coverage through their evidence. The
runtime trace pins the orchestrator and producers to Terra/medium. Exhaustive
Map obtains, saves, and emits in one script call a generated bundle containing
the one-shot producer protocol, its UTF-8 references, and every UTF-8 Markdown
template; producers must not load those source files themselves.
Collaboration assertions require
three initial producers, no more than three simultaneously active producers,
multiple total spawns, zero resumptions, and an encrypted-message size ratio
that rejects repeated producer instructions. A persistent campaign ledger owns
the deterministic inventory, source classifications, ToDo, publications, and
root integration passes. Final assertions verify
move-based publication, source protection, disposable run-root cleanup, and
mechanical Spine validity. Document length is observed, not bounded. The
benchmark adds one blind holistic two-way documentation-quality judgment per
aligned sample. The judge is an independent bounded task and therefore defaults
to Terra/medium; its cost is excluded from all arms. This case normally costs one
Terra/medium orchestrator plus several Terra/medium producer sessions and belongs
in the explicit `expensive` category.

`map-deep-repository-no-subagents` runs the same six-area fixture with
`agents.enabled=false`. It verifies that root still inventories and classifies
the repository, persists unresolved work, leaves the live Spine unchanged, and
reports exhaustive mapping blocked because it cannot launch a fresh producer.
It must not silently replace the missing producer role with root-side mapping.

Remaining distinct behavioral gaps are:

- atomic Map returning no new document when the live Spine already answers the
  bounded question;
- custom `<spine-root>` handling;
- report-driven recursive discovery followed by a terminal no-output Map
  producer;
- large-Map candidate rejection and path-collision handling;
- unknown partial producer capacity with rejected starts retained as queued
  work;
- focused large-Map scope that ignores unrelated repository areas.

Keep broader parallel scenarios planned until they protect one of these
distinct gaps with observable assertions. Do not add another final-file-only
large-Map eval.

The executable set is divided by resource cost and necessity:

| Category | Manifests | Top-level agent calls | Purpose |
|---|---:|---:|---|
| `core` | 8 | 8 | Minimum behavioral regression set, including atomic staged Map output |
| `extended` | 14 | 21 | Lifecycle, root-first connection, language detection, terminal-depth refusal, idempotency, merge, removal, bounded growth, traceability, and multilingual Extract behavior |
| `expensive` | 3 | 4–12 per sample | Two-arm Map benchmark plus missing-producer failure behavior |
| `planned` | 10 | 0 | Documentation and future redesign only |

The table counts top-level agent invocations. The sequential Map arm uses 2–10
invocations, stopping at the first unchanged terminal result; each exhaustive arm
uses one top-level invocation, and only the producer-capable arm creates producer
sessions.
The separate category prevents ordinary `core` or `extended` runs from
selecting either expensive arm.

Core and extended cases currently cover:

- greenfield initialization and source-file protection;
- creation of a brownfield map from runtime evidence;
- root-first SpecSpine setup with explicit configuration confirmation;
- existing-root language detection without rewriting its documents;
- generic project-agent bootstrap boundaries;
- idempotent reconnect of the project-agent bootstrap;
- production multi-slice Extract handoffs for backend and CLI projects
  in English, a mobile project in Russian, and a data pipeline in Chinese,
  with hidden owner/support/relevance judgments;
- legacy repository accelerator configuration cannot suppress local retrieval;
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
