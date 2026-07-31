# Evaluation coverage

## Current inventory

The repository has thirty prose behavioral scenarios. Every scenario is
registered in `cases/`, so `run.py --audit` detects additions that have not been
classified.

Twenty-three scenarios are executable and seven remain planned. The audit
output is authoritative for category and agent-call counts.

`traceable-rule` is assigned to `specspine-map` because its expected result
includes repository-backed observations.

### Map coverage

Executable `specspine-map` coverage currently consists of five agent calls
across two cases:

- `lifecycle-survey-deepen`: a shallow initial survey that persists a frontier,
  followed by one bounded graph expansion without reopening unrelated source;
- `lifecycle-drift-refresh`: a narrow refresh that preserves accepted intent,
  records changed implementation as observation, and leaves disagreement open.

Remaining distinct behavioral gaps are:

- atomic Map returning no new document when the live Spine already answers the
  bounded question;
- custom `<spine-root>` handling;
- focused scope that ignores unrelated repository areas.

Keep broader parallel scenarios planned until they protect one of these
distinct gaps with observable assertions. Do not add another final-file-only
large-Map eval.

The executable set is divided by resource cost and necessity:

| Category | Manifests | Top-level agent calls | Purpose |
|---|---:|---:|---|
| `core` | 10 | 10 | Minimum behavioral regression set |
| `extended` | 13 | 22 | Lifecycle, root-first connection, language detection, terminal-depth refusal, idempotency, merge, removal, bounded growth, and multilingual Extract behavior |
| `planned` | 7 | 0 | Documentation and future redesign only |

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
- semantic-ID references and representative repository evidence across the
  remaining owner-focused lifecycle cases;
- semantic Doctor diagnosis and bounded mechanical repair without runtime companions;
- recursive Doctor link and marker-bounded semantic-ID validation across
  nested specification directories;
- staged lifecycle transitions covering survey, deepening, intentional split,
  downstream repository evolution, drift refresh, supersession, removal, and
  bounded Doctor repair.
- repeated Evolve deepening with per-document and whole-Spine word budgets while
  preserving addressable architectural meaning.
- Evolve refusal when a specification already has terminal architectural detail
  and the request asks only for implementation-manual content.

Planned cases include deterministic tooling already covered by unit tests,
redundant focused cases superseded by lifecycle coverage, and cases whose
assertions over-constrained architectural choices.

## Behavioral backlog

Items below are not automatic candidates for executable evals. Add one only
when it protects a distinct contract that cannot be covered by a deterministic
test or an existing behavioral case.

Potential gaps:

- agent navigation efficiency on larger-than-small documentation graphs;
- larger Map frontier growth beyond the controlled one-step expansion case;
- custom `<spine-root>` handling in `evolve` and `map`;
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
