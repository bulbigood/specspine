---
name: specspine-evolve
description: Create or evolve accepted architecture and durable system specifications in a linked SpecSpine from explicit user intent and existing specifications. Use for greenfield initialization, accepted requirements and contracts, architectural changes, SDD promotion, impact analysis, and specification restructuring. Do not use for repository discovery, implementation, or code/spec conformance.
---

# SpecSpine Evolve

Maintain a linked network of architecture and durable system specifications.
Record stable responsibilities, requirements, guarantees, invariants,
interfaces, quality constraints, verification contracts, and uncertainty
without turning the Spine into a delivery or implementation workflow. This file
owns Evolve's authority and editing procedure; the linked format and semantics
references own document structure and claim meaning.

## Resources

- Read [references/spec-format.md](references/spec-format.md) before creating,
  editing, or restructuring specifications. It is the canonical owner of
  document content, organization, identity, relationships, decomposition, and
  terminal detail.
- Read [references/spec-semantics.md](references/spec-semantics.md) before
  adding, reclassifying, conflicting, or resolving an architectural claim. It
  is the canonical owner of claim kinds, authority, and conflict handling.
- Read [references/evolve-examples.md](references/evolve-examples.md) when the right
  specification boundary is unclear.
- When creating files, start from the templates under `assets/templates/` and
  omit empty sections. Create and maintain mandatory `specspine.json` from its
  template in the same write batch.
- Run `scripts/check_spine.py <spine-root>` after every write batch. It is the
  mandatory whole-Spine mechanical gate.

## Authority and scope

Use the current user request and files inside the resolved `<spine-root>` as the
only project architecture sources. Bundled resources define procedure and
format, not project facts.

Do not inspect project-specific code, configuration, tests, documentation, or
external systems unless the user explicitly authorizes them. Authorized
external evidence must be classified according to
`references/spec-semantics.md` and must not change accepted intent without
explicit approval.
For an uninitialized Spine, do not list, search, or read any existing project
file outside `<spine-root>`, including a repository README, even to seek context.
Derive only the smallest useful starting structure from the request.

Evolve owns organization and intentional evolution of the specification network.
It does not:

- discover repository architecture or verify code/spec conformance;
- implement source changes;
- create temporary feature scope, delivery acceptance, plans, tasks, or status;
- manufacture normative behavior from observations or unaccepted drafts;
- decide product or architecture choices for the user.

Evolve may promote explicitly accepted SDD meaning into canonical owners,
including durable `REQ`, `GUA`, `INV`, `QLT`, and `VER` claims and owned
machine-readable contracts. Keep implementation-specific tests and source out
of the Spine.

Use `specspine-map` for repository discovery and drift, `specspine-doctor` for
health review, and `specspine-extract` for a downstream context handoff. Evolve
must remain usable without those skills.

When the request explicitly composes Extract with Evolve, treat Extract's
machine-selected complete files as the project-source reads required below.
When that request requires Extract and its companion is available, invoke its
search exactly once before directly reading project specifications; do not
silently substitute manual navigation.
If `task_context.complete` is true and the result is not truncated, do not
re-read the returned index or specifications before editing. If the capsule is
incomplete, follow Extract's reported gaps and suggested paths rather than
starting a second navigation pass.

## Workflow

1. Resolve `<spine-root>` as defined by `references/spec-format.md`; absent an
   explicit user or project configuration, this is exactly `specspine`
   relative to the current working directory, never the repository root.
   Test for its `_INDEX.md` without listing the project. If present, read it
   and follow only relevant links, unless a non-truncated Extract result
   already supplied it as described above. If absent, immediately initialize
   `_INDEX.md` and `specspine.json` together from the request; do not run any
   other project discovery or read any other project path.
2. Classify the operation: initialize, refine, promote, split, merge, rename,
   or link. Identify the canonical owner, specifications whose normative or
   architectural meaning changes, and context needed only for understanding.
   For refinement, perform the terminal-depth check immediately after reading
   the index and relevant specification. Compare the requested material with
   the terminal-detail boundary in `references/spec-format.md`. If the request
   adds no durable normative or architectural meaning within Evolve's scope and
   only asks for implementation mechanics, stop without editing or seeking
   implementation evidence.
3. Choose owners and decomposition using `references/spec-format.md`. Reuse an
   existing owner when possible; do not create a specification merely because a
   file is long or a feature is new.
4. Treat an explicit in-scope operation or architectural decision as approval.
   Approval does not override Evolve's scope or terminal-detail boundary. Apply
   navigation, evidence-only, and clearly meaning-preserving edits directly.
   Ask the user only before introducing unapproved normative intent, resolving
   a conflict or blocking question, choosing among plausible owners, or making
   an ambiguous agent-initiated restructure. State the affected files, reason,
   and unresolved choice without prescribing a rigid response format.
5. Apply the smallest coherent change. Follow `references/spec-format.md` for
   canonical ownership, identity, relationships, navigation, and reachability.
   Preserve unrelated content. Never edit an index manually; after changing
   paths or files, run `scripts/rebuild_indexes.py <spine-root>`.
   Store newly accepted but implementation-unverified behavior under its
   normative claim kind. Do not restate it as current observed behavior unless
   the request supplies evidence that establishes it.
6. After every write batch, run the bundled checker against the whole resolved
   Spine. If it reports an error, correct only defects caused by the approved
   operation and rerun it. If an error is pre-existing or needs new
   architectural authority, stop and report it; never claim the Evolve operation
   succeeded while the checker fails.
7. Report changed files, structural choices, checker outcome, and unresolved
   architectural questions concisely.

## Operation guidance

### Initialize

Create the root pair through the bootstrap script, create the smallest useful
set of top-level concept specifications, then rebuild indexes mechanically.
Do not anticipate the full system or invent repository
structure. Represent uncertainty and addressability only as defined by the
canonical format and semantics references.

### Refine

Preserve an existing responsibility unless the user changes it. Record the
smallest accepted architectural meaning and modify only owners whose behavior
or boundaries change. Treat related specifications needed only for context as
read-only. A dependency's participation, session use, or configuration need
does not by itself change its specification. Modify a related owner only when
the request supplies new durable architectural intent belonging there; report
implementation prerequisites and speculative questions instead.

### Promote

Promote only durable accepted meaning from an SDD or explicit user decision.
Move requirements, guarantees, invariants, quality constraints, and reusable
verification into their canonical owners. Leave temporary scope, tasks,
delivery acceptance, status, and implementation-specific tests downstream.
Update manifest facets and blockers only when every change is supported.

### Split, merge, rename, or link

Apply the canonical ownership, identity-preservation, replacement, and
relationship rules from `references/spec-format.md`. Use
`references/spec-semantics.md` only when the operation changes claim meaning,
authority, uncertainty, or conflict state. For a link operation, first classify
the link as navigation, a statement reference, or a typed relationship; do not
create a reciprocal typed edge unless it expresses a distinct approved
relationship.

## Invariants

- Modify only files inside `<spine-root>`.
- Apply claim kinds, authority, and conflicts exclusively as defined by
  `references/spec-semantics.md`.
- Apply document identity, statement addressability, relationships,
  decomposition, and terminal detail exclusively as defined by
  `references/spec-format.md`.
- Never imply that documented intent is implemented or conformant.
- Never silently resolve uncertainty, conflicts, or ownership ambiguity.
- Keep specifications linked, source-independent, and concise at their chosen
  reconstruction profile. Exact durable contracts may use the machine-readable
  assets allowed by the canonical format.
- Never omit the final mechanical gate after a write, including initialization,
  rename, merge, split, and deletion.
