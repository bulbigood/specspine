# Semantics and evidence

## Statement authority

Semantic IDs make statements addressable; they do not change authority or
confidence.

- A **Decision** is an accepted architectural choice.
- A **Constraint** restricts acceptable architecture or implementation.
- **Observed** records a fact directly supported by repository evidence.
- **Inferred** records an unconfirmed interpretation of evidence.
- An **Open question** preserves unresolved uncertainty.

Putting text under `Decisions` or `Constraints` records acceptance but MUST NOT
be used by an agent to manufacture acceptance. An explicit user decision, an
already accepted Spine claim, or an authorized external workflow establishes
intent.

An observation describes what currently exists; it does not establish what
should exist. An inference MUST NOT be presented as a decision, constraint, or
observed fact. A blocking open question MUST explain what is unknown, why it
matters, and what downstream work must not decide silently.

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

- Decisions and constraints describe accepted intent.
- Observations describe current evidence.
- Inferences remain unconfirmed.
- Observations do not override decisions or constraints.
- Decisions and constraints do not prove implementation.
- An agent MUST NOT silently choose intent or implementation when they differ.

A confirmed, architecture-significant conflict is stored once:

```markdown
## Known divergences

| Intended | Observed | Consequence |
|---|---|---|
| [CON-payment-idempotency](payment-invariants.md) | [OBS-provider-event-not-deduplicated](payment-processing.md) | A duplicate transition is possible |
```

Each row MUST reference an existing `DEC` or `CON`, reference an existing
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

## Change and drift lifecycle

Before changing code, an architecture-aware agent MUST:

1. identify the primary owner and document ID;
2. obtain applicable Decisions and Constraints;
3. inspect Boundaries and typed relationships;
4. determine coverage of the affected area;
5. obtain applicable Known divergences;
6. preserve blocking Open questions;
7. distinguish existing intent, an accepted change delta, and implementation
   reality.

The agent MUST NOT expand scope to repair unrelated drift. If drift repair is
in scope, code may be brought into conformance. If authority or scope is
unclear, the agent must request a decision.

An accepted SDD may supersede existing intent. Its durable claims and
relationships MUST be transferred into SpecSpine before or together with
implementation. Implementation-only changes do not require artificial
documentation growth. Architecture-significant accepted changes do.

An `Observed` statement changes only after evidence is checked again. A Known
divergence is removed only after its resolution is confirmed.
