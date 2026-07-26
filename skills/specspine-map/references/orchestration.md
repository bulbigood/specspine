# SpecSpine Map exhaustive orchestration

Use this protocol only after the entrypoint selects exhaustive mode and confirms
that subagent creation is available. Exhaustive mode repeats the bounded Map
operation until every useful branch in the requested scope is complete.

## Invariants

- The root agent is the only scheduler and the only process that runs
  `campaign.py`.
- Use a strong root with `medium` or `high` reasoning for exhaustive control.
  If the active root has low reasoning, do not claim final saturation without
  an independent strong semantic audit.
- Each producer owns one branch and writes only to its private staging root.
- Keep producers evidence-affine. Reuse a producer for the same branch, or for
  a child that the same producer emitted in its accepted `coverage_frontier`
  with evidence and a semantic relation reason. Similar naming, a shared
  top-level domain, or a root-discovered adjacent document is not sufficient.
- Medium producers may draft ordinary branches. Use a strong producer or
  reviewer for security, authorization, ownership, migration, compatibility,
  and the final semantic breadth/depth audit.
- Producers never edit the live Spine, `README.md`, or campaign state.
- The root accepts a producer result only through `campaign.py accept`.
- Continue independent ready work after a branch failure. Stop only when
  `summary` reports `saturated` or `blocked`.
- A tool defect is not an operator decision. Preserve its evidence, continue
  unaffected branches, and report it only if no actionable work remains.

## Start or resume

Create one temporary run root outside the repository and Spine:

```text
mktemp -d
python3 <map-skill-root>/scripts/campaign.py init \
  <run-root>/campaign.json --scope <requested-scope> \
  --root-question <scope-question>
```

If the live Spine already has specification nodes, follow
`documentation-first-seeding.md`: initialize with `--spine-state existing`,
read the whole Spine, and record its gap-derived frontier with
`seed-from-spine` before source discovery or producer assignment.

If the operator supplies an existing campaign, inspect it and run:

```text
python3 <map-skill-root>/scripts/campaign.py resume <campaign>
```

`resume` releases stale non-root owners. Discard old staging because a staged
file is trusted only together with a checkpoint returned in the current
invocation.

Never replace an unfinished campaign by initializing a new ledger and seeding
its live documents. Repair the original ledger, or preserve its complete
frontier and identity with:

```text
python3 <map-skill-root>/scripts/campaign.py recover \
  <old-campaign> <new-campaign> --reason <tool-defect>
```

For an empty Spine, inspect architecture signals and seed every observed
independent branch before dispatch:

```text
python3 <map-skill-root>/scripts/campaign.py add <campaign> <branch-id> \
  --parent root --question <question> --origin <evidence> \
  [--namespace <name>] [--prerequisite <branch-id>]
```

Use `documented` instead of `add`, with `--document <path>`, only for an empty-
Spine campaign that encounters an already complete external owner. Existing-
Spine campaigns use documentation-first planned branches so owners can be
semantically tested rather than pre-closed.

Build the producer instructions once:

```text
python3 <map-skill-root>/scripts/bundle_skill.py \
  <map-skill-root> <run-root>/producer-instructions.md
```

## Dispatch

Use `campaign.py ready <campaign>` to select branches. Fill every safely
available slot. For each confirmed producer handle run:

```text
python3 <map-skill-root>/scripts/campaign.py assign \
  <campaign> <branch-id> --owner <agent-path>
```

Start a fresh producer handle for every branch not proven to originate in that
producer's accepted checkpoint. If all slots are occupied, continue root work
or wait for a slot; never send an unrelated branch through `followup_task` to
an existing producer merely to avoid waiting. `campaign.py assign` enforces
this provenance and also rejects assigning two active branches to one owner.

Give the producer:

- the complete producer instruction bundle inline;
- repository root, Spine root, evidence baseline and documentation language;
- its exact branch question and private staging root;
- permission to inspect only the repository and Spine evidence needed for that
  branch.

The producer performs one bounded Map step and returns exactly one JSON object:

```json
{
  "status": "continuing",
  "evidence_inspected": ["src/example"],
  "candidates": [{"path": "domains/example.md", "operation": "create"}],
  "mapped_responsibilities": ["Example boundary"],
  "relationships": [],
  "source_coverage": [
    {
      "area": "src/example",
      "classification": "summarized",
      "reason": "Owned by the example specification"
    }
  ],
  "quality_gate": {
    "ownership_coverage": {"status": "pass", "reason": "All production areas classified"},
    "orientation": {"status": "pass", "reason": "Purpose and boundaries are clear"},
    "information_gain": {"status": "pass", "reason": "Non-local behavior is captured"},
    "change_utility": {"status": "pass", "reason": "Owner and risks are navigable"},
    "non_duplication": {"status": "pass", "reason": "Local code is not reproduced"}
  },
  "continuation": "Check the same boundary for another useful node",
  "coverage_frontier": [
    {
      "id": "example-child",
      "question": "Map the child boundary",
      "evidence": ["src/example/child"],
      "namespace": "domains",
      "prerequisite": null,
      "classification": "fork_candidate",
      "document": null,
      "reason": "The inspected adapter document exposes an independent child boundary"
    }
  ],
  "unresolved": [],
  "terminal_reason": null
}
```

Candidate paths are final paths relative to the Spine. `create` requires a
missing destination; `replace` requires an existing destination. A
candidate-bearing checkpoint uses `continuing`.

When the candidate already passes every local quality gate and needs no second
parent-level step, use `publish_and_locally_saturate`, set `continuation` to
null, and give the normal `no useful node` terminal reason. Acceptance then
publishes and locally saturates atomically while retaining every child branch.

A terminal checkpoint has no candidates and uses either:

- `locally_saturated` with
  `terminal_reason: "no useful node: <evidence-based reason>"`; or
- `blocked` with the exact external input or authority required.

Before acceptance, confirm every fork candidate cites only paths present in
that producer's `evidence_inspected` and explains the semantic connection in
`reason`. Reject a checkpoint whose child is merely adjacent by name or was
introduced by the root; such work belongs to a fresh producer.

## Accept atomically

Save the exact producer JSON outside staging, then run one command:

```text
python3 <map-skill-root>/scripts/campaign.py accept \
  <campaign> <branch-id> <checkpoint.json> \
  <private-staging-root> <spine-root>
```

`accept` is one transaction. It:

1. locks and reloads campaign state;
2. validates branch ownership, checkpoint, paths and child branches;
3. hashes both checkpoint JSON and staged bytes;
4. runs the candidate checker;
5. moves candidates with rollback backups;
6. runs the live checker while deferring only navigation findings;
7. commits publications, children and terminal state in one atomic ledger
   write.

It also retains the producer's reported relationships for the root integration
pass. Acceptance validates edges already present in a candidate, but the root
must follow `integration-pass.md` to connect independently produced documents.

On any failure, live files and campaign state remain unchanged and staged files
remain available for correction. Ask the same producer for a corrected complete
checkpoint. Never manually move a staged file or partially import a report.

After a continuing candidate checkpoint, resume the same producer with its
reported continuation; this is still the same branch. A reported child may
reuse that producer only after its current branch reaches a terminal
checkpoint. After any terminal checkpoint, dispatch a ready queued branch to a
fresh producer unless the stored discovery provenance explicitly permits reuse.

If a producer terminates without an acceptable checkpoint, run `release` and
restart that branch with fresh staging. Use `block --reason <exact reason>` only
for missing authority, evidence, permission, or an unresolved ownership
decision—not for recoverable validation or tool errors.

If audit reports a prerequisite cycle, repair the original ledger with
`repair-prerequisite --clear|--set ... --reason ...`; do not reconstruct it.

## Reach saturation

Repeat `ready`, dispatch and `accept` until no producer is active and no branch
is ready. Close a locally saturated branch after all children are complete:

```text
python3 <map-skill-root>/scripts/campaign.py close <campaign> <branch-id>
```

When the queue drains, follow `integration-pass.md`: integrate shared
navigation, typed relationships, semantic-ID references and file organization,
then record `integration-pass`. Next reread every live Spine document and run
`documentation-pass` using the plan shape from
`documentation-first-seeding.md`. If it returns `gaps_found`, dispatch its new
branches and repeat from the queue-drain step. An initial problem is empty only
when its branch is `complete`; a final documentation list is empty only when
the current pass returns `no_gaps`.

Next repeat scope-level source discovery. In an existing-Spine campaign this
is the first broad code pass and only seeks blind spots without a credible
documented owner. For a whole repository revisit composition roots,
registries, public interfaces, persistence, integrations, configuration,
deployment, security, failure behavior and observability. Add newly exposed
branches and return to the queue-drain step. When a complete pass adds none,
record:

```text
python3 <map-skill-root>/scripts/campaign.py discovery-pass \
  <campaign> --evidence <signals-checked>
```

Run final `integration-pass` and `documentation-pass`. Continue if the latter
finds any direction. Before accepting the root checkpoint, inspect the
collaboration agent list: every assigned producer must have returned its
terminal result and no producer may still be running. Ledger completion is
necessary but does not replace this runtime check.

Before claiming coverage, inspect `campaign.py coverage-report <campaign>`.
An overview may be locally sufficient while useful children remain queued, but
the exhaustive campaign is not saturated until those children are inspected
and closed or given evidence-based terminal classifications.

The root producer must then return its own candidate-free `no useful node`
checkpoint. Accept it and close root after all descendants are complete.

Use:

```text
python3 <map-skill-root>/scripts/campaign.py summary <campaign>
```

A final response is permitted only when `terminal` is `saturated` or `blocked`.
If it is null, continue. Never stop merely to report progress, elapsed time, a
document count, or one failed branch.

## Finalize

After `terminal: saturated`, make no further documentation edits. Run the
checker, then:

```text
python3 <map-skill-root>/scripts/finalize_run.py \
  <campaign> <spine-root> --staging-root <staging-root>...
```

Only `status: finalized` permits deleting the exact run root with
`find <run-root> -depth -delete`. Otherwise preserve it.

Report scope, created/replaced/total document counts from the final receipt,
relationships, unresolved drift, exact `no useful node` reasons, normalization
and checks. Recommend
`$specspine-doctor` in a new session; never invoke it during exhaustive Map.
