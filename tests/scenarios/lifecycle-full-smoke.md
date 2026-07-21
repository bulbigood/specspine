# Scenario: full payment SpecSpine lifecycle smoke

## Purpose

Exercise the critical SpecSpine lifecycle in one workspace without duplicating
the detailed assertions of the focused lifecycle evaluations:

```text
Map survey
-> Grow accepted split
-> Grow temporary handoff
-> downstream implementation mutation
-> Map targeted refresh
-> Grow explicit retry resolution
-> Doctor final check
```

The fixture is a small brownfield payment service. Checkout requests payment
authorization, settlement captures an authorized payment, and a provider
webhook records results. The initial implementation has neither settlement
idempotency propagation nor retry coordination.

## Lifecycle stages

### 1. Initial survey

Map creates the smallest useful SpecSpine and uses
`specspine/payment-processing.md` as the payment entry point. Repository-backed
claims remain Observed or Inferred and carry an evidence baseline. Map may
write only under `specspine/`.

### 2. Accepted split

The user accepts independently evolving authorization and settlement
responsibilities, settlement idempotency, and a concise payment overview that
retains webhook result handling as a boundary. Retry policy remains open.
Grow reads only the existing Spine, creates canonical authorization and
settlement owners, and does not alter repository evidence.

### 3. Temporary handoff

Grow returns a minimal settlement-idempotency handoff. It distinguishes
required and potentially affected specifications, carries the unresolved retry
question, and writes no persistent handoff or downstream work artifacts.

### 4. Downstream implementation mutation

The harness models work performed outside SpecSpine. It adds stable
idempotency-key propagation and a retry queue with exponential delay and five
attempts. This repository behavior is not architectural approval.

### 5. Targeted refresh

Map inspects only the settlement specification and the named local evidence.
It records idempotency propagation and the concrete retry behavior as
Observed, refreshes the evidence baseline, and preserves both accepted
idempotency intent and the still-open retry policy. It must not promote runtime
behavior to a Decision or claim conformance.

### 6. Explicit retry resolution

The user accepts bounded exponential retry with at most five attempts. Grow
records that decision in the settlement owner, resolves the old open question,
and preserves mapped observations as observations. It reads only the Spine.

### 7. Final Doctor check

Doctor runs the mechanical checker and traverses the reachable Spine in
spine-only check mode. It remains read-only, does not inspect repository
evidence, and does not claim code/spec conformance or completeness.

## Smoke invariants

- every agent respects its skill-specific read and write boundary;
- settlement is the sole canonical owner of settlement retry policy at the
  end;
- the temporary handoff never becomes a project file;
- only the harness fixture changes source, configuration, and tests;
- observations remain distinct from accepted decisions through refresh and
  resolution;
- relative Markdown links and semantic IDs remain valid;
- Doctor runs its bundled checker and leaves the workspace unchanged.

## Failure indicators

- Grow reads repository material outside `specspine/`;
- Map writes source or turns observed retry behavior into accepted intent;
- the handoff persists in the project;
- retry ownership or the accepted retry decision is duplicated outside the
  settlement owner;
- the open retry question remains active after explicit resolution;
- Doctor edits files, reads repository evidence, omits the checker, or claims
  conformance;
- links or semantic IDs become invalid.
