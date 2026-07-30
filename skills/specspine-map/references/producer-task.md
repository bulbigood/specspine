# SpecSpine Map one-shot producer contract

Handle exactly one bounded ToDo, write one checkpoint, and terminate only after
revising it to a checked atomic handoff. Inspect every packet `sample`, then read
only enough evidence to establish responsibility, boundary inputs and outputs,
consumers, data authority, controls, observable lifecycle, failures, and
relationships. This file is the complete producer
instruction set: do not load the Map `SKILL.md` or any other Map reference.
Start with targeted `rg` and narrow excerpts, target at most 10,000 output tokens per call, and never dump complete large files; exceed the target only for a concrete unresolved boundary.

`architecture_unit`, `planned_document`, and `planned_relationships` come from
the synthesized semantic graph. Verify the responsibility against every evidence
stratum. If `current_owner.exists` is false, create exactly `planned_document`;
if true, refine that document in place. A draft defines exactly the owner ID
named by the `topics/<owner-id>` architecture unit; preflight rejects any
different identity before the handoff becomes visible.
Do not add, remove, or render graph edges: deterministic assembly
owns `Relationships`. If an edge or part of the proposed boundary is weak,
publish the coherent evidence-backed core and record the doubt as a concise
`directions` question. Do not reject an otherwise useful document because the
semantic graph may need later Doctor or Evolve refinement. Copy
`evidence_baseline` exactly.

## SpecSpine authority and format

SpecSpine separates accepted intent from repository reality. Accepted prose in
`Responsibility`, `Boundaries`, `Behavior`, `Interfaces`, information/data,
lifecycle, failure, configuration, and compatibility sections is authoritative
architectural intent. `DEC`, `CON`, `REQ`, `GUA`, `INV`, `QLT`, and `VER` are
normative; code cannot create them. `OBS` is a directly evidenced repository
fact, `INF` an unconfirmed interpretation, and `OQ` unresolved uncertainty.
Every bullet in `Open questions` must be a semantic definition with a stable
`OQ-*` ID; never emit an anonymous question bullet.
Only accepted intent may use normative `MUST`, `SHOULD`, or `MAY`.

For a new Map owner with no accepted intent, keep `Summary` observational and
make required `Responsibility` state that the document records evidence about
one observed candidate boundary. Retain only boundary-significant facts under
`Observed`; do not distribute code-derived facts through authoritative prose sections. For an
existing owner, preserve authoritative prose and add only material repository
delta under `Observed`, `Inferred`, `Open questions`, or `Known divergences`.
Semantic definitions are bold bullets inside the marker region; each `OBS`
uses complete repository-relative `Evidence:` paths and the exact baseline.

Evidence may include neighboring owners to prove a boundary. Do not turn those
files into observations owned by this document and do not restate behavior of
`planned_relationships` targets. Keep accepted narrative and claims unchanged unless the existing Spine or an explicit user decision supplies accepted intent.
Code, tests, schemas, and runtime evidence establish only repository observations; place material deltas in `OBS`, and never rewrite matching code behavior into accepted prose.
Preflight rejects changed normative claims and any `OBS` without non-test evidence; tests alone establish repository expectations, so preserve the question for later verification.

Read packet `operation`, `current_owner`, `related_existing_owners`, and
`related_planned_owners` first. Existing owners resolve accepted graph targets;
planned owners supply the title, responsibility, and incoming or outgoing
interaction of parallel documents. Use both only to keep this owner narrow;
do not restate a neighbor. In every operation, make one targeted pass across
boundary inputs, outputs, consumers, controls, data authority, observable
lifecycle, failure, and recovery. Check registrations and consumers plus
relevant schemas, configuration, and tests when they establish those surfaces.
A private algorithm, helper, hook, framework state, internal call order, or
file layout is `implementation-detail`, even when stable or complex.

For `completion.intent: deepen`, update the existing `current_owner.document`
instead of creating a parallel owner. Preserve all accepted normative claims
and unrelated observations. Concentrate on its `partial` and `missing`
boundary facets, but write only facts supported by repository evidence.
Code cannot establish normative guarantees, quality targets, or
implementation-independent verification; leave those incomplete rather than
manufacturing them.
Map never reorganizes the existing Spine. Preserve an existing owner's ID, path, kind, accepted claims, boundary, and content ownership. Never split, merge, move, rename, replace, decompose, or transfer it; preserve suggested topology changes as uncertainty because only Evolve may perform the reorganization.

Choose the narrowest accurate v4 `Kind`. Use `component` for a runtime,
renderer, plugin, adapter, or other independently evolving owner only when it
has a distinct boundary contract; `capability` for a responsibility coordinated across components;
`behavior` for a durable process or lifecycle; and `interface` or `data` when
that is the actual ownership. Use `concept` only for shared vocabulary or a
domain model without operational ownership. Never use it as a generic fallback.

Write Markdown only in staging; write checkpoint to `<work-package>/checkpoint.json`.
Do not edit the live Spine, repository source, tests, README, or campaign state;
do not write to handoff, continue to another unit, or integrate navigation.

## Mandatory preflight and handoff
Before handoff, reread every candidate as a coherent architectural
specification and verify:

- one canonical responsibility without duplicated neighboring ownership;
- observations remain `OBS`; every `Evidence:` span is a complete
  repository-relative path, never prefix-inherited shorthand;
- a new observation-only owner has no code-derived accepted prose outside
  `Observed`;
- every staged owner containing `OBS` has the exact task-packet evidence
  baseline; a source draft exists only for a material retained delta;
- supported relevant inputs, outputs, consumers, controls, data authority,
  observable lifecycle, and boundary failures are present;
- each applicable boundary facet was either documented from evidence or
  deliberately left incomplete because the inspected repository cannot
  establish it;
- section headings follow the canonical concerns in `spec-format`; never merge
  concerns into custom headings such as `Interfaces and lifecycle` or
  `Lifecycle and state`; use separate canonical sections;
- follow configured order: `Known divergences` before evidence/uncertainty;
  never hide canonical content in `<details>`;
- render those canonical sections using `specspine.json.presentation`
  headings and order when the profile is present;
- semantic IDs are stable and links use the required complete labels;
- source walkthroughs, private implementation detail, and unsupported intent
  are absent;
- every direction is a genuine unanswered question; keep required policy
  distinct from observable repository behavior and never rewrite one as the
  other.

Revise the private result until this review is clean. Then run exactly:

```text
python3 <producer-finalize-script> \
  <task-packet.json> <work-package> <handoff-package> \
  <repository-root> <spine-root>
```

The helper validates checkpoint shape and evidence samples, checks candidates
against the live Spine overlay, and atomically renames the entire work package.
If it reports findings, fix every candidate-caused finding and rerun it. Never
ask root to accept private work. Do not message root or any other agent; after
atomic handoff, report only in the producer's final response and terminate.

Use `retry` only when unavailable or inaccessible evidence prevents any
coherent evidence-backed document, and name the missing evidence. Use
`blocked` only for a concrete external dependency, not a semantic doubt or
draft defect. Root repeats mechanical acceptance checks; preflight never
grants publication authority.

## Result

Write one small JSON object. Use only the fields shown below. `evidence` and
staged `OBS` paths are complete repository-relative concrete paths.
`directions` are plain questions; the campaign assigns their IDs and root
decides whether they become ToDo.
Existing owner:

```json
{
  "outcome": "covered",
  "evidence": ["pkg/services/caching/cache.go", "pkg/services/caching/service.go"],
  "summary": "The existing claims cover ownership, invalidation and fallback.",
  "owner": {
    "document": "caching.md",
    "claims": ["DEC-cache-lifecycle", "CON-cache-failure-fallback"]
  },
  "directions": []
}
```

Use `covered` only for a source-pass scope task. The cited accepted claims and
architectural owner must cover the assigned semantic topic. The owner need not
cite inspected source paths: code remains the evidence authority and inspection
coverage records the bounded comparison without manufacturing `OBS`.

For an integration-derived task, use `"outcome": "answered"` with the same
`evidence`, `summary`, `owner`, and `directions` fields only when cited claims
are all `OBS-*` and answer the exact observable anchored question. Repository
evidence cannot answer what the system should guarantee. Use `"outcome":
"unresolved"` with `evidence`, `summary`, `reason`, and empty `directions` when
evidence confirms the anchor must remain uncertain.

Missing observation:

```json
{
  "outcome": "draft",
  "evidence": ["pkg/services/caching/cache.go"],
  "summary": "No existing owner describes this cache lifecycle.",
  "directions": ["Who owns recovery after persistent invalidation failure?"]
}
```

For `draft`, place one or more publish-ready Markdown files under the work
package's `staging/` directory. Do not describe their paths or create/replace
operations in JSON; the preflight and `campaign.py` derive both from staging
and the live Spine.

Use `"outcome": "supporting"` with `evidence`, `summary`, `reason`, and empty
`directions` only after every stratum proves the scope unit has no durable
responsibility. Use `"outcome": "retry"` with `evidence`, `summary`, and
nonempty `need` only when required evidence is unavailable or inaccessible.
Use `"outcome": "blocked"` with
`evidence`, `summary`, and `reason` only for a concrete external dependency.
An integration-owned index, relationship, manifest update, or navigation entry
is not external and never justifies `blocked`.

`draft`, `covered`, `answered`, `unresolved`, and `supporting` must cite at
least one concrete member from every evidence stratum. `covered` is valid only
for scope tasks; `answered` and `unresolved` are valid only for anchored
integration-derived tasks. For `covered` or `answered`, the owner document must
exist, every claim must be a semantic ID in it, the document must reference the
unit or inspected evidence, and the summary must explain the exact boundary or
answer. A title, unknown-owner observation, or broad neighboring owner is not
proof.
