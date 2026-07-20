# Evaluation coverage

## Current inventory

The repository has sixteen prose behavioral scenarios. Every scenario is
registered in `cases/`, so `run.py --audit` detects additions that have not been
classified.

| Area | Documented scenarios | Executable fixtures |
|---|---:|---:|
| `specspine-grow` | 5 | 1 |
| `specspine-map` | 5 | 2 |
| `specspine-init` | 3 | 1 |
| `specspine-doctor` | 2 | 2 |
| `specspine-adapter-generator` | 1 | 1 |
| Total | 16 | 7 |

`traceable-visual-spec` is assigned to `specspine-map` because its expected
result includes repository-backed observations.

Executable cases currently cover:

- greenfield initialization and source-file protection;
- creation of a brownfield map from runtime evidence;
- generic project-agent bootstrap boundaries;
- semantic-ID references, evidence, and a Mermaid lifecycle view.
- mechanical and semantic Doctor diagnosis without runtime companions;
- deterministic runtime-skill generation and drift detection.

The remaining nine manifests are marked `planned`. Their prose remains useful
as a rubric, but they are not counted as automated tests.

## Missing fixtures for documented scenarios

- approval-gated cross-cutting impact proposal;
- approval-gated split of an existing specification;
- refinement of an existing specification without invented technology;
- strict source-of-truth read boundary and context handoff;
- initial brownfield survey breadth versus depth;
- selective deep mapping and file-read budget;
- local refresh without remapping unrelated areas;
- concrete SDD binding generation;
- standalone use of a generated binding.

These need multi-turn support or an adapter-provided file-read trace before
their important invariants can be tested honestly.

## Missing behavioral scenarios

High priority:

- longitudinal evolution: map, refine, split, handoff, drift, refresh, and
  supersede a decision in the same project;
- repeated invocation and idempotency, especially `specspine-init`;
- merge, rename, removal, incoming-link updates, and semantic-ID tombstones;
- intended-versus-observed conflict resolution after explicit user approval;
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
