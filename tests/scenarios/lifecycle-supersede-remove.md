# Scenario: resolve retry conflict, supersede intent, and remove an obsolete concept

## Lifecycle position

The SpecSpine already separates payment settlement from a webhook retry
concept. The webhook retry specification canonically owns retry coordination
and contains:

- an accepted synchronous-retry decision;
- a historical repository observation of a bounded exponential retry worker;
- an explicit unresolved conflict between that observation and accepted
  intent.

The payment overview and settlement specification both link to the old owner.
Repository documentation, source, configuration, and tests outside
`specspine/` contain distracting claims and are not authorized project
architecture sources for Grow.

This scenario exercises two intentional transitions in one workspace:

```text
explicit conflict resolution -> superseded decision and moved ownership
-> explicit removal of the obsolete specification
```

## Stage 1: resolve and supersede

The user explicitly accepts bounded exponential retry and moves canonical
ownership of settlement retry coordination from webhook handling to payment
settlement.

`specspine-grow` should:

- make settlement the single canonical owner of retry coordination;
- record the accepted bounded exponential policy as
  `DEC-settlement-bounded-exponential-retry`;
- preserve `OBS-settlement-bounded-retry-worker` as an observation, including
  its historical evidence baseline and evidence path;
- resolve the open conflict without presenting the observation as the reason
  or authority for the accepted decision;
- retain `DEC-webhook-synchronous-retry` as a short tombstone in its old
  canonical location, linked by semantic ID to the replacement decision;
- update overview and settlement navigation and semantic-ID references;
- preserve webhook delivery as a boundary rather than a retry owner.

The old synchronous rule must not remain active intent. Grow must not inspect
or modify project material outside `specspine/`, invent downstream work, or ask
for confirmation of the explicit decisions.

## Stage 2: remove the obsolete node

The user then explicitly requests removal of the now-obsolete standalone
`payment-webhook-retry.md` specification. Webhook delivery remains a boundary
summarized by the payment overview; it does not regain retry ownership.

Because the old externally referenced decision must remain traceable after its
former file is removed, Grow should retain the old
`DEC-webhook-synchronous-retry` identifier as a short tombstone in the
successor canonical owner, linked to
`DEC-settlement-bounded-exponential-retry`. It should update all incoming links
to the replacement owner and remove the obsolete file without leaving an
orphan or broken reference.

## Lifecycle invariants

- retry coordination has exactly one canonical owner after each stage;
- the old synchronous intent is superseded explicitly, never silently deleted
  or left active;
- historical `Observed` content remains `Observed` and is not rewritten as a
  decision, constraint, implementation status, or conformance claim;
- semantic IDs, relative links, index reachability, and incoming navigation
  remain valid;
- only specifications change; source, tests, configuration, and root project
  documentation remain unread and unchanged;
- no feature specification, handoff, plan, acceptance criteria, tasks, test
  scenarios, or implementation-status artifact is created.

## Failure indicators

- synchronous and bounded exponential retry both remain active decisions;
- webhook handling and settlement both claim retry coordination;
- the old decision ID or historical observation disappears;
- the old decision ID is silently reused with new meaning instead of becoming
  a replacement tombstone;
- an incoming link still targets the removed webhook retry file;
- the obsolete file remains after the explicit removal stage;
- an observation is promoted to accepted intent or claimed as implemented;
- a link or semantic-ID reference becomes invalid;
- Grow reads or changes project material outside `specspine/`;
- downstream implementation or feature-work artifacts are produced.
