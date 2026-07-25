# SpecSpine Map exhaustive orchestration

Use this protocol only after the entrypoint selects exhaustive mode and confirms
that subagent creation is available. Exhaustive mode repeats the bounded Map
operation until every useful branch in the requested scope is complete.

## Invariants

- The root agent is the only scheduler and the only process that runs
  `campaign.py`.
- Each producer owns one branch and writes only to its private staging root.
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

If the operator supplies an existing campaign, inspect it and run:

```text
python3 <map-skill-root>/scripts/campaign.py resume <campaign>
```

`resume` releases stale non-root owners. Discard old staging because a staged
file is trusted only together with a checkpoint returned in the current
invocation.

Inspect architecture signals and seed every observed independent branch before
dispatch:

```text
python3 <map-skill-root>/scripts/campaign.py add <campaign> <branch-id> \
  --parent root --question <question> --origin <evidence> \
  [--namespace <name>] [--prerequisite <branch-id>]
```

Use `documented` instead of `add`, with `--document <path>`, when an existing
Spine document already owns the branch.

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
  "source_coverage": [],
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
      "reason": null
    }
  ],
  "unresolved": [],
  "terminal_reason": null
}
```

Candidate paths are final paths relative to the Spine. `create` requires a
missing destination; `replace` requires an existing destination. A
candidate-bearing checkpoint uses `continuing`.

A terminal checkpoint has no candidates and uses either:

- `locally_saturated` with
  `terminal_reason: "no useful node: <evidence-based reason>"`; or
- `blocked` with the exact external input or authority required.

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

On any failure, live files and campaign state remain unchanged and staged files
remain available for correction. Ask the same producer for a corrected complete
checkpoint. Never manually move a staged file or partially import a report.

After a successful candidate-bearing checkpoint, resume the same producer with
its reported continuation. After a terminal checkpoint, immediately dispatch a
ready queued branch before waiting.

If a producer terminates without an acceptable checkpoint, run `release` and
restart that branch with fresh staging. Use `block --reason <exact reason>` only
for missing authority, evidence, permission, or an unresolved ownership
decision—not for recoverable validation or tool errors.

## Reach saturation

Repeat `ready`, dispatch and `accept` until no producer is active and no branch
is ready. Close a locally saturated branch after all children are complete:

```text
python3 <map-skill-root>/scripts/campaign.py close <campaign> <branch-id>
```

When the queue first drains, repeat scope-level discovery. For a whole
repository revisit composition roots, registries, public interfaces,
persistence, integrations, configuration, deployment, security, failure
behavior and observability. Add newly exposed branches and drain them. When a
complete repeat pass adds none, record:

```text
python3 <map-skill-root>/scripts/campaign.py discovery-pass \
  <campaign> --evidence <signals-checked>
```

The root producer must then return its own candidate-free `no useful node`
checkpoint. Accept it and close root after all descendants are complete.

Use:

```text
python3 <map-skill-root>/scripts/campaign.py summary <campaign>
```

A final response is permitted only when `terminal` is `saturated` or `blocked`.
If it is null, continue. Never stop merely to report progress, elapsed time, a
document count, or one failed branch.

## Normalize and finalize

After `terminal: saturated`, update `README.md` navigation and evidence-backed
reciprocal overview links once. Run the checker, then:

```text
python3 <map-skill-root>/scripts/finalize_run.py \
  <campaign> <spine-root> --staging-root <staging-root>...
```

Only `status: finalized` permits deleting the exact run root with
`find <run-root> -depth -delete`. Otherwise preserve it.

Report scope, published documents, relationships, unresolved drift, exact
`no useful node` reasons, normalization and checks. Recommend
`$specspine-doctor` in a new session; never invoke it during exhaustive Map.
