# Semantics and evidence

## Statement authority

Semantic IDs make statements addressable; they do not change authority or
confidence.

- A **Decision** is an accepted architectural choice.
- A **Constraint** restricts acceptable architecture or implementation.
- A **Requirement** is an accepted durable system outcome.
- A **Guarantee** is an accepted externally observable promise.
- An **Invariant** must hold across valid states or transitions.
- A **Quality constraint** is an accepted measurable non-functional limit.
- **Verification** defines durable implementation-independent conformance.
- **Observed** records a fact directly supported by repository evidence.
- **Inferred** records an unconfirmed interpretation of evidence.
- An **Open question** preserves unresolved uncertainty.

Putting text under a normative section records acceptance but MUST NOT be used
by an agent to manufacture acceptance. An explicit user decision, an already
accepted Spine claim, or an authorized external workflow establishes intent.

An observation describes what currently exists; it does not establish what
should exist. An inference MUST NOT be presented as a decision, constraint, or
observed fact. A blocking open question MUST explain what is unknown, why it
matters, and what downstream work must not decide silently.

An observation belongs in SpecSpine only when it is architecture-significant,
repository-backed, and not already fully represented by accepted intent. It
MUST either expose a material intent gap, support a confirmed divergence,
affect an unresolved architectural question, or provide necessary navigation
to a surprising owner or boundary. Map MUST NOT retain observations merely to
confirm accepted intent, inventory implementation, or restate source detail.
Compatible implementation detail remains in code.

When repository evidence is already fully represented by accepted intent, Map
records inspection coverage without creating a duplicate observation.
Inspection coverage does not prove conformance.

## Evidence baseline

Repository observations SHOULD cite representative, repository-relative paths:

```markdown
## Observed

- **OBS-provider-event-not-deduplicated** — Provider events reach the state
  transition without a durable deduplication check.
  Evidence: `src/payments/provider-events.ts`,
  `tests/payments/provider-events.test.ts`.
```

Evidence paths support provenance and navigation. They do not prove complete
code/spec conformance. Current code, tests, and runtime evidence remain the
authorities for implementation reality and observed behavior.

## Conflict semantics

- Normative claims describe accepted intent.
- Observations describe current evidence.
- Inferences remain unconfirmed.
- Observations do not override normative claims.
- Normative claims do not prove implementation.
- An agent MUST NOT silently choose intent or implementation when they differ.

A confirmed, architecture-significant conflict is stored once:

```markdown
## Known divergences

| Intended | Observed | Consequence |
|---|---|---|
| [CON-payment-idempotency](payment-invariants.md) | [OBS-provider-event-not-deduplicated](payment-processing.md) | A duplicate transition is possible |
```

Each row MUST reference an existing normative statement, reference an existing
repository-backed `OBS`, and state a non-empty architectural consequence.

The canonical row belongs either to the owner of the affected responsibility or
to the root index for a system-wide divergence. The same intended/observed pair
MUST NOT be authored in several documents.

A divergence:

- does not cancel intent;
- does not resolve drift;
- is not an implementation task;
- remains until the observation is rechecked;
- is updated or removed only after confirmed resolution;
- SHOULD be included when a task touches either side.

The absence of a divergence is not evidence of conformance unless the area was
explicitly checked. A suspected but unconfirmed conflict belongs in `Inferred`.
Even an explicit inspection without retained observations is only a bounded
comparison at its recorded evidence baseline, not a conformance result.

## Change and drift lifecycle

Before changing code, an architecture-aware agent MUST:

1. identify the primary owner and document ID;
2. obtain applicable normative claims and contracts;
3. inspect Boundaries and typed relationships;
4. inspect manifest facets and blockers for the affected area;
5. obtain applicable Known divergences;
6. preserve blocking Open questions;
7. distinguish existing intent, an accepted change delta, and implementation
   reality.

The agent MUST NOT expand scope to repair unrelated drift. If drift repair is
in scope, code may be brought into conformance. If authority or scope is
unclear, the agent must request a decision.

An accepted SDD may supersede existing intent. Its durable requirements,
guarantees, invariants, verification, and relationships MUST be transferred
into SpecSpine before or together with implementation. Implementation-only
changes do not require artificial documentation growth.

An `Observed` statement changes only after evidence is checked again. A Known
divergence is removed only after its resolution is confirmed.

When accepted intent later represents a previously observed fact, remove the
redundant active observation if nothing references its ID. If its ID is
externally referenced, preserve a short supersession tombstone without
presenting historical evidence as current implementation reality. Version
control remains the history of unreferenced observations. When implementation
changes, recheck affected observations: update current facts, remove facts that
no longer exist, and resolve linked divergences only after confirmation.

Existing Spines migrate incrementally. Map need not rewrite every historical
observation in one operation; when it touches an owner, it should remove
unreferenced observations that merely duplicate accepted intent, preserve
material gaps and divergences, and add or refresh that owner's optional
inspection record. Areas without inspection remain valid and make no bounded
comparison claim.
