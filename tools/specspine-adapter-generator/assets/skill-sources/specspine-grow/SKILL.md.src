---
name: specspine-grow
description: Create and evolve intended architecture in a linked Markdown SpecSpine using explicit user intent and existing specifications. Use for greenfield initialization, accepted architectural changes, ownership or boundary restructuring, and architecture context handoffs. Do not use for repository discovery or drift analysis (use specspine-map), integrity diagnosis (use specspine-doctor), implementation, or code/spec conformance.
---

# SpecSpine Grow

Runtime contract: SpecSpine v1.

Maintain a lightweight, long-lived network of linked architectural
specifications. The network is the persistent artifact; a context handoff is a
temporary projection for downstream work.

## Resources

- Read [references/spec-semantics.md](references/spec-semantics.md) only when the
  operation adds, reclassifies, conflicts with, or resolves an architectural
  claim.
- Read [references/spec-format.md](references/spec-format.md) before creating,
  splitting, merging, renaming, or substantially restructuring specifications.
  For a focused prose or link edit, preserve the existing local format.
- Read [references/examples.md](references/examples.md) when deciding whether to
  split, merge, create, or reuse a specification.
- Read [references/context-handoff.md](references/context-handoff.md) before
  preparing a context handoff.
- When creating files, use
  [assets/templates/architecture-index.md](assets/templates/architecture-index.md)
  and [assets/templates/specification.md](assets/templates/specification.md) as
  starting points. Omit empty sections.

## Scope

Use this skill to:

- initialize a SpecSpine from an abstract project idea;
- evolve intended architecture and accepted decisions or constraints;
- identify architectural concepts affected by a requested change;
- split, merge, rename, or link specifications;
- maintain canonical ownership, boundaries, navigation, and uncertainty while
  applying an intended change;
- prepare a minimal architecture context handoff.

Do not use it to:

- modify source code or verify code/spec conformance;
- reverse-engineer undocumented code deeply;
- create feature specifications, acceptance criteria, plans, or tasks;
- track implementation, release, or review status;
- silently invent or resolve product and architectural decisions.

Preserve missing information according to `references/spec-semantics.md`.

## Source-of-truth boundary

By default, treat only these as authoritative sources of project architecture:

- the current user request;
- files inside the resolved `<spine-root>`.

Bundled files under this skill's `references/` and `assets/` define procedure
and format only; they are not project evidence.

This boundary governs project evidence, not tool use. Skills, MCP servers,
internet search, and external documentation may provide procedural guidance,
terminology, or general technical facts. Do not treat them as evidence of this
project's intended or observed architecture or let them override the SpecSpine.

Do not inspect or derive architecture from project-specific material outside
`<spine-root>` unless the user explicitly requests that source or authorizes
external project inspection. This includes source code, configuration, tests,
generated artifacts, repository documentation, issues, tickets, wikis, and
project data exposed through tools or MCP servers. Treat such material as
regenerable downstream artifacts, never as architectural authority.

When the user explicitly authorizes external project evidence:

- classify it only as `Observed` or `Inferred` unless the user separately
  accepts architectural intent;
- never let it silently override a `Decision` or `Constraint`;
- preserve conflicts as `Open questions`.

For an uninitialized project, use only the user request and bundled procedural
resources. Do not inspect the repository to fill missing architecture.

## Lifecycle role

Own intentional evolution of normative architecture. Preserve observations
already stored in SpecSpine or explicitly supplied by the user. When a request
primarily requires repository discovery, state that `specspine-map` is the
appropriate independently installable skill. Do not pretend mapping occurred.

Remain fully usable without any companion skill. Update the linked network and
produce context handoffs without proving conformance or implementing changes.

## Workflow

### 1. Read the spine

Resolve `<spine-root>` using `references/spec-format.md`. Start with
`<spine-root>/README.md`, then follow only links relevant to the request. If the
index does not exist, treat the project as uninitialized. Do not inspect other
project files to supplement the spine unless explicitly authorized.

### 2. Classify the request

Determine whether the user wants to initialize, refine, split, merge, link, or
prepare a context handoff. Route a general health audit to `specspine-doctor`.

### 3. Locate canonical owners

Identify the primary specification, directly affected specifications, required
context, and merely related context. Reuse an existing canonical home when it
already owns the responsibility.

### 4. Decide whether structure changes

Create or extract a specification only for an independent responsibility,
boundary, behavior, decision set, or independently evolving concept. Do not
create one file per feature or split by length alone.

### 5. Apply authority-aware approval

Treat an explicit operation or architectural decision in the current user
request as approval; do not ask for the same approval twice. Apply mechanical,
navigation, evidence-only, and clearly meaning-preserving changes directly.

Stop and request a decision only when the change would:

- create, change, or remove normative intent not explicitly decided by the
  user;
- resolve a conflict or blocking question;
- choose canonical ownership among plausible alternatives; or
- perform an agent-initiated restructuring whose meaning or ownership is not
  already clear.

When approval is still required, show:

```text
Affected specifications

Create:
- paths, or none

Modify:
- paths, or none

Rename:
- paths, or none

Remove:
- paths, or none

Reason:
- why this structure is appropriate

Open decisions:
- unresolved choices, or none
```

For an explicitly requested or otherwise safe change, apply it and include the
same impact information in the final report instead of pausing.

### 6. Apply the change

- Modify only specifications.
- Preserve unrelated and user-authored content.
- Maintain useful relative Markdown links and reachability from
  `<spine-root>/README.md`.
- Preserve optional directory organization without treating it as ownership;
  introduce broad directories only when a flat namespace impairs navigation.
- Keep one canonical home per concept; replace duplicates with summaries and
  links.
- When a document defines semantic IDs, keep every definition inside exactly
  one balanced `specspine:semantic-ids:begin` / `specspine:semantic-ids:end`
  region as required by `references/spec-format.md`; keep references as
  ordinary ID-labeled Markdown links.
- Before reporting, re-read every changed specification. If it defines IDs,
  place its only begin marker before the first ID-owning section and its end
  marker after the last. This must include `Observed` or `Inferred` definitions
  that precede an existing `Decisions` region. Verify that no definition remains
  outside the region. Keep `DEC`, `CON`, `OBS`, `INF`, and `OQ` definitions under
  the exact `Decisions`, `Constraints`, `Observed`, `Inferred`, and
  `Open questions` headings respectively; do not use alternate headings for
  addressable claims. Verify that ID-labeled links have no `#` fragment.
- Keep overview specifications concise after decomposition.
- Update `<spine-root>/README.md` only when top-level navigation or system-wide
  intent changes.

### 7. Report

Summarize changed files, structural decisions, unresolved questions, and
whether the area is ready for context handoff.

## Operation rules

### Initialize

Create `<spine-root>/README.md` and the smallest useful set of top-level concept
specifications using `references/spec-format.md`. Do not anticipate the full
project or inspect other project files for missing context. Once the missing
index establishes that the project is uninitialized, do not read root
documentation, source, configuration, tests, or other project material.

### Refine

Preserve the existing responsibility unless the user changes it. Add accepted
behavior or intent, link canonical neighbors, and extract a concept only when it
now evolves independently.

When the user explicitly adds a capability to an existing canonical owner,
record the smallest accepted statement of that capability. Keep unspecified
policies or implementation details as open questions; do not leave the explicit
change unapplied merely because those non-blocking details remain unresolved.

### Split or merge

For a split, identify the extracted responsibility, moved content, and changed
links; retain a concise overview when it remains a useful navigation point. For
a merge, preserve the clearest canonical filename and update incoming links.

### Prepare a context handoff

Follow `references/context-handoff.md`. Include the smallest useful set and
separate required, potentially affected, and merely related specifications.
Preserve claim semantics without adding downstream artifacts. Include only
observations already stored in the spine or explicitly supplied or authorized
by the user. By default, deliver the temporary handoff in the final response;
do not store it inside the persistent SpecSpine or another project file unless
the user explicitly requests a file and location.

## Readiness for context handoff

An area is ready when:

- a canonical owner is identified;
- its documents satisfy the applicable stopping rules in
  `references/spec-format.md`;
- potentially affected specifications are separated from related context;
- blocking architectural questions are explicit;
- claims follow `references/spec-semantics.md`.

This does not imply readiness for implementation. Product requirements, edge
cases, acceptance criteria, migrations, tests, and implementation readiness
belong downstream.

## Restrictions

Never:

- inspect or use project-specific material outside `<spine-root>` as
  architectural evidence without explicit user authorization;
- modify or create source-code files;
- invent repository structure;
- claim synchronization or conformance between specifications and code;
- claim that normative intent is implemented merely because it is documented;
- treat inference as fact or accepted intent;
- silently resolve blocking questions or intended-versus-observed conflicts;
- reproduce local implementation details in specifications;
- rewrite unrelated branches of the SpecSpine;
- create plans, tasks, acceptance criteria, or implementation status.

Be concise and architectural. Prefer concrete file operations and links. The
user owns product and architectural decisions; this skill owns organization,
refinement, navigation, and consistency of the specification network.
