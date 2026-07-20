---
name: specspine-init
description: Bootstrap or refresh project-local integration between an existing SpecSpine, the current AI-agent environment, and an optional SDD framework. Use this skill to advertise the SpecSpine architectural source of truth in persistent project instructions, generate a thin project-specific integration skill, map SpecSpine context into native downstream specification workflows, or repair and remove a previous SpecSpine integration. It adapts project-local instructions without rewriting SpecSpine documents, source code, or third-party skills.
---

# SpecSpine Init

Install a small discovery bridge and a detailed project-local integration skill.
Treat this as build-time adaptation: generated artifacts must remain usable
without this skill.

## Resources

- Read [references/integration-contract.md](references/integration-contract.md)
  before proposing or applying an integration.
- Use [assets/templates/agent-bootstrap.md](assets/templates/agent-bootstrap.md)
  for the persistent project-instruction block.
- Use
  [assets/templates/project-integration-skill.md](assets/templates/project-integration-skill.md)
  when the environment supports project-local skills.
- Use [assets/templates/project-openai.yaml](assets/templates/project-openai.yaml)
  only when that metadata file is supported by the target environment.

## Scope

Use this skill to:

- declare the SpecSpine entry point in persistent project instructions;
- generate or refresh a thin project-specific consumer skill;
- map SpecSpine claims and context handoffs into a detected SDD workflow;
- fall back to native project instructions when local skills are unsupported;
- remove only integration artifacts previously owned by this skill when the
  user explicitly requests removal.

Do not use it to:

- initialize or edit architectural specifications;
- copy, fuse, patch, or replace third-party skills;
- alter source code, tests, feature specifications, plans, or tasks;
- claim compatibility or code/spec conformance;
- install a project-specific skill globally without explicit approval.

## Discovery boundary

Inspect only what is needed to adapt the environment: applicable persistent
agent instructions, local skill conventions, and SDD configuration,
instructions, templates, or manifests. Do not inspect implementation files,
tests, feature contents, or unrelated repository documentation unless the user
explicitly authorizes them.

Treat discovered framework files as integration metadata, not project
architecture. Do not execute framework commands during discovery.

## Workflow

### 1. Resolve the spine

Resolve `<spine-root>` in this order:

1. an explicit path from the user;
2. an applicable project instruction;
3. an existing configured root;
4. `specspine`.

Require `<spine-root>/README.md` before installing the bridge. If it is absent,
report that SpecSpine must first be created or mapped; do not create
architectural documents.

### 2. Discover the target environment

Identify:

- the persistent instruction surface applicable to the project root;
- a supported project-local skill location and format, if any;
- the SDD framework and exact native workflow entry, if present;
- the downstream stage, artifact paths, work-item naming rule, format source,
  context insertion point, traceability rule, and conflict destination.

Prefer existing project conventions and documented environment behavior. Do
not invent a skill directory merely because another agent supports it. If
several instruction surfaces or frameworks are plausible and the active target
is unclear, ask the user which one to adapt.

### 3. Derive the adapter

Keep SpecSpine framework-neutral. Map its context into the downstream workflow
without changing canonical specification names or format. Generate a thin
consumer skill; do not reproduce the full upstream SDD skill.

Resolve every runtime binding field from inspected evidence. Use explicit
`not applicable` values for a generic integration; never leave a field implied
or unresolved. If no SDD framework is present, generate a generic coding-agent
integration.

### 4. Propose changes

Before writing, show:

```text
SpecSpine integration plan

Spine root:
- path

Agent environment:
- detected target and evidence

SDD framework:
- detected framework and evidence, or none

Create:
- paths, or none

Modify:
- paths, or none

Runtime binding:
- framework
- native workflow entry
- downstream stage
- artifact paths
- work-item naming rule
- format source
- context insertion point
- traceability rule
- conflict destination

Open decisions:
- unresolved choices, or none
```

Wait for approval unless the user explicitly requested immediate application
after the target environment and paths were already known.

### 5. Install project-local integration

- Add or replace exactly one `specspine:begin` / `specspine:end` managed block
  in each approved persistent instruction file.
- Preserve all content outside the managed block.
- Keep the bootstrap short: entry point, authority semantics, consultation
  trigger, conflict rule, and generated-skill pointer.
- Prefer a supported project-local skill location.
- Render every runtime binding field with resolved paths and detected native
  terminology. Keep the skill self-contained and consumer-only.
- Generate product-specific metadata only when supported.
- If project-local skills are unsupported, put detailed adapter instructions in
  the target environment's native local instruction surface instead.
- Use a global installation only with explicit approval, a project-unique name,
  and a project-root guard.

### 6. Verify

Check that:

- the bootstrap points to the existing SpecSpine index;
- the generated skill points to the same root;
- the bootstrap `$skill` name, generated frontmatter name, install directory,
  and product metadata agree;
- every runtime binding field has a concrete or explicit `not applicable`
  value and no `{{...}}` placeholder remains;
- referenced local workflow entries and format sources exist;
- managed markers occur once and are balanced;
- generated artifacts retain their ownership marker;
- the generated skill passes an available native skill validator;
- user-authored instructions remain unchanged outside the block;
- a second run would update rather than duplicate owned artifacts;
- no third-party skill or downstream artifact was modified.

Finally, perform a read-only standalone dry-run using only the persistent
instruction, generated skill, SpecSpine, and a representative downstream
request. Confirm that a fresh agent can identify the native workflow entry,
work-item identifier, artifact destination, context insertion, traceability
rule, and conflict route without guessing. Do not execute framework commands or
write downstream artifacts during this verification.

### 7. Report

Report created and modified files, the selected agent and SDD mapping, any
fallback used, and unresolved integration choices. State that regeneration is
required after material framework or agent-workflow changes.

## Refresh and removal

On refresh, rediscover the environment and show a new proposal. Replace only
the managed bootstrap and generated artifacts. If an owned artifact has lost
its ownership marker or contains apparent user edits, show the divergence and
ask before overwriting it.

On explicit removal, remove only the managed block and generated artifacts
identified by the integration. Never delete an entire user-owned instruction
file merely because the remaining file would be empty; report it for the user
to decide.

## Restrictions

Never:

- make downstream SDD artifacts an architectural authority;
- treat `Observed` or `Inferred` claims as accepted intent;
- silently resolve a SpecSpine conflict or open question;
- modify installed or vendored third-party skills;
- create a project-local skill in an unsupported or guessed location;
- duplicate detailed adapter rules across several instruction surfaces;
- hide uncertainty about detected paths, formats, or framework behavior.
