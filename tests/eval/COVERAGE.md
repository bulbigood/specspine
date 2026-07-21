# Evaluation coverage

## Current inventory

The repository has twenty-four prose behavioral scenarios. Every scenario is
registered in `cases/`, so `run.py --audit` detects additions that have not been
classified.

| Area | Documented scenarios | Executable fixtures |
|---|---:|---:|
| `specspine-grow` | 9 | 9 |
| `specspine-map` | 7 | 7 |
| `specspine-connect` | 3 | 2 |
| `specspine-doctor` | 3 | 3 |
| cross-skill lifecycle | 1 | 1 |
| package generator tooling | 1 | 1 |
| Total | 24 | 23 |

`traceable-visual-spec` is assigned to `specspine-map` because its expected
result includes repository-backed observations.

Executable cases currently cover:

- greenfield initialization and source-file protection;
- creation of a brownfield map from runtime evidence;
- generic project-agent bootstrap boundaries;
- semantic-ID references, evidence, and a Mermaid lifecycle view.
- mechanical and semantic Doctor diagnosis without runtime companions;
- recursive Doctor link and marker-bounded semantic-ID validation across
  nested specification directories;
- deterministic runtime-skill generation and drift detection.
- staged lifecycle transitions covering survey, deepening, intentional split,
  temporary handoff, downstream repository evolution, drift refresh,
  supersession, removal, and bounded Doctor repair.

Only the downstream binding-without-connector scenario remains `planned`; it
requires a separate native SDD executor rather than a SpecSpine skill.

## Missing fixtures for documented scenarios

- standalone use of a generated binding.

This needs a native downstream SDD fixture and executor.

## Missing behavioral scenarios

High priority:

- minimal handoff selection on a larger graph, including read and context-size
  budgets;
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

## Missing evaluation capabilities

The deterministic runner cannot judge architectural quality by itself. A later
model-judge layer should score:

- correct canonical owner selection;
- reasonableness of decomposition;
- `Observed` versus `Inferred` classification;
- minimality and sufficiency of context;
- invention of product or technology decisions;
- preservation of meaning without implementation-level duplication.

Judge output should be advisory and stored separately from deterministic
pass/fail assertions. Model name, version, prompt, sample count, duration, and
token usage should be recorded for reproducibility.
