# SpecSpine semantics

SpecSpine is a long-lived graph of canonical owners and their durable boundary
contracts. Each owner is described from outside its boundary: what
responsibility it owns, what crosses the boundary, which controls constrain
it, which information it owns, how peers depend on it, and what a conforming
implementation must make observable. A sufficiently specified area can be
reconstructed independently without reproducing its current internals.

SpecSpine is the source of truth for accepted durable system intent:
architecture, requirements, guarantees, invariants, quality constraints, and
verification contracts. An SDD owns a proposed change delta until acceptance;
its durable accepted meaning is then promoted into canonical SpecSpine owners.
Source code owns implementation reality; tests and runtime evidence establish
observed behavior and may verify conformance; an external workflow owns backlog
and delivery state. Drafts, inferences, existing code, and passing tests cannot
create or rewrite normative claims without acceptance.

Accepted intent includes only durable boundary meaning and the minimum
architecture needed to assign it: owner identity and responsibility, boundary
inputs and outputs, controls, data authority, observable lifecycle and failure
behavior, relationships, and explicit architecture constraints. Addressable
normative sections make accepted claims. Evidence, uncertainty, divergences,
implementation navigation, risks, terminology, and rationale retain their
narrower non-intent semantics.

## Contents

- [Statement kinds](#statement-kinds)
- [Boundary-contract rule](#boundary-contract-rule)
- [Conflict semantics](#conflict-semantics)
- [Reconstruction semantics](#reconstruction-semantics)
- [Statement identity](#statement-identity)
- [Architecture versus feature artifacts](#architecture-versus-feature-artifacts)

## Boundary-contract rule

“External” is relative to the canonical owner. A contract between two internal
components is external to both component boundaries and belongs in SpecSpine
when it is durable. A private interaction inside one owner does not.

A statement belongs in a canonical owner only when at least one is true:

- a consumer, neighboring owner, operator, or implementation-independent
  verifier can observe its violation;
- it assigns responsibility, data authority, trust, or policy across a
  boundary;
- it fixes a topology, technology, or mechanism as an explicitly accepted
  architecture constraint.

Apply the replacement test: if the owner were reimplemented behind the same
boundary, the statement must still constrain the replacement. Otherwise leave
it in code, tests, or implementation documentation.

Inputs include calls, commands, events, data, and stimuli. Outputs include
responses, events, state effects, and failures. Controls include policy,
configuration, compatibility, security, and quality constraints. Mechanisms
are normally implementation freedom; name one only when it is another
canonical owner or an explicit architecture constraint.

Do not canonize private algorithms, helper structure, class or function
decomposition, framework state, internal call order, incidental file layout,
or a source walkthrough. Shared implementation machinery does not make peer
responsibilities one owner. Conversely, do not split one responsibility into
documents for its private stages or implementation facets.

## Statement kinds

SpecSpine consumes accepted architectural intent but does not implement its
approval process. An explicit user decision or an already accepted Spine claim
may establish intent; an external ADR or SDD workflow may own approval and
carry its provenance. Putting text under `Decisions` or `Constraints` records
that acceptance but must not be used by an agent to manufacture it.

### Decision

An accepted architectural choice. A decision describes intended architecture
and should be supported by explicit documentation or confirmed by the user.

Example:

```text
Application sessions are independent of identity providers.
```

### Constraint

A restriction on acceptable architecture or implementation. A constraint also
describes intended architecture, but expresses what downstream work must
preserve or avoid.

Example:

```text
External provider credentials must not be used as application session tokens.
```

### Requirement

An accepted durable capability or behavior the system must provide.
Requirements state externally meaningful outcomes, not implementation tasks.

### Guarantee

An accepted observable promise made to a user, caller, consumer, or neighboring
component, including success, failure, ordering, compatibility, and recovery.

### Invariant

A truth that must hold across valid states or transitions, commonly protecting
identity, data ownership, security, lifecycle, or consistency.

### Quality constraint

An accepted and verifiable restriction on qualities such as availability,
latency, privacy, accessibility, resource use, or portability.

### Verification

A durable black-box check or conformance criterion that distinguishes a
satisfying implementation from a violating one. It does not own temporary
delivery acceptance criteria or implementation-specific unit tests.

### Observed

A fact directly supported by current repository evidence. Observations describe
what is present, not necessarily what is intended or required. Evidence paths
support provenance and navigation; they do not prove complete code/spec
conformance.

Retain an observation only when it is boundary-significant, not already
fully represented by accepted intent, and exposes a material intent gap,
supports a confirmed divergence, affects an unresolved architectural question,
or navigates to a surprising owner or boundary. Do not retain an observation
merely to confirm intent, inventory implementation, or restate source detail.
When accepted intent already represents the evidence, record bounded inspection
coverage without creating a duplicate observation. Inspection coverage never
proves conformance.

### Inferred

An unconfirmed interpretation of repository evidence. Never present an
inference as a decision, constraint, or observed fact.

### Open question

Unresolved uncertainty that may affect architecture or downstream work. Make a
question explicitly blocking when a downstream workflow must not answer it
silently.

## Conflict semantics

- Decisions, constraints, requirements, guarantees, invariants, quality
  constraints, and verification claims describe accepted normative intent.
- Observations describe current repository evidence.
- Inferences describe interpretations that remain unconfirmed.
- Observations do not override normative claims.
- Normative claims do not imply that code currently implements them.
- Preserve disagreements between intended and observed architecture explicitly
  until the user or a downstream workflow resolves them.
- SpecSpine does not prove or guarantee conformance between specifications and
  code.
- Absence of an observation or divergence is not evidence of conformance.

A confirmed conflict is stored once under `Known divergences`:

```markdown
| Intended | Observed | Consequence |
|---|---|---|
| [CON-idempotency](payments.md) | [OBS-no-deduplication](payments.md) | Duplicate transition is possible |
```

The first side references a normative statement (`DEC`, `CON`, `REQ`, `GUA`,
`INV`, `QLT`, or `VER`), and the second references repository-backed `OBS`.
Preserve the row until evidence is rechecked; never silently resolve it by
preferring code or intent.

The canonical row belongs to the non-index owner of the affected
responsibility. For a cross-cutting conflict, use the applicable system owner
or create a justified non-index owner; `_INDEX.md` never owns project claims.
Do not author the same intended/observed pair in several documents.

When accepted intent later represents an observation, remove an unreferenced
redundant `OBS`. Preserve an externally referenced ID as a short supersession
tombstone without presenting historical evidence as current reality. Existing
Spines migrate owner by owner; absence of an inspection record remains valid
and makes no repository-comparison claim.

## Reconstruction semantics

Reconstruction means creating an independent implementation that satisfies the
selected normative closure and its machine-readable contracts. It never means
reproducing original source text, private identifiers, incidental file layout,
or unrecorded implementation choices.

An area is reconstructable only when:

- responsibility and neighboring ownership are closed;
- applicable normative claims and public contracts are retrievable;
- significant interfaces, data/state invariants, failure behavior, quality
  constraints, configuration, and external dependencies are specified where
  relevant;
- durable verification can detect violations of important guarantees; and
- no applicable blocking open question requires the implementation agent to
  invent product, security, compatibility, or operational policy.

Repository observations may orient a reconstruction but are not requirements.
When behavior must be preserved, accept it explicitly as a normative claim.
Machine-readable contracts, scenarios, and fixtures may live inside the
SpecSpine bundle; implementation source, delivery plans, and implementation-
specific tests do not.

## Statement identity

A semantic identifier makes a statement addressable but does not change its
kind, authority, or confidence. Use identifiers selectively, keep externally
referenced identifiers stable, and resolve their meaning through the canonical
specification that owns them.

## Architecture versus feature artifacts

Keep an artifact in SpecSpine when it:

- defines a stable responsibility or ownership boundary;
- describes a relationship between architectural concepts;
- records a long-lived decision, requirement, guarantee, invariant, constraint,
  or verification contract;
- defines a durable owner-relative boundary contract;
- supplies a machine-readable schema, conformance scenario, or fixture needed
  to implement and verify that durable contract;
- is expected to remain useful across multiple changes;
- helps a future agent determine where to look.

Leave an artifact to a downstream feature or implementation workflow when it:

- describes a specific delta or temporary scope;
- defines acceptance criteria or test scenarios useful only for one change;
- decomposes implementation tasks;
- tracks implementation, release, or review status;
- exists primarily for one feature, release, or pull request.
- describes private algorithms, call sequences, helpers, framework state, or
  source layout without an explicit architecture constraint.

After a change is accepted, promote only its durable normative meaning and
implementation-independent verification into canonical SpecSpine owners.

Examples:

```text
SpecSpine:
Webhook processing must be idempotent.

Downstream workflow:
Given the same webhook event twice, the second request returns 200 without
creating another transaction.
```

```text
SpecSpine:
Application sessions are independent of authentication providers.

Downstream workflow:
Add POST /auth/google/callback and create a session after validating the Google
authorization code.
```
