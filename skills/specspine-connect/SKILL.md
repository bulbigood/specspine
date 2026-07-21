---
name: specspine-connect
description: Bootstrap or refresh an ultralight project-local connection between an existing SpecSpine, persistent agent instructions, and an optional SDD framework. Use to advertise the SpecSpine entry point, generate a compact downstream binding, repair or remove a prior integration, or adapt architecture context to native project workflows without generating another skill.
---

# SpecSpine Connect

Runtime contract: SpecSpine v1.

Install one small always-visible discovery block and, only when an SDD workflow
exists, one lazily read project binding. Generate no project-local skill.

## Resources

- Read [references/integration-contract.md](references/integration-contract.md)
  before proposing or changing an integration.
- Use [assets/templates/agent-bootstrap.md](assets/templates/agent-bootstrap.md)
  for persistent project instructions.
- Use [assets/templates/project-binding.md](assets/templates/project-binding.md)
  only for a detected SDD workflow.

## Scope

Declare the SpecSpine entry point in project instructions; bind minimal context
to a detected native SDD workflow; refresh it; or explicitly remove only owned
integration artifacts. Do not edit specifications, code, tests, downstream
artifacts, third-party skills, or global agent configuration.

## Discovery boundary

Inspect only applicable persistent instructions and SDD integration metadata.
Do not inspect implementation, tests, features, or unrelated documentation
unless authorized, and do not execute framework commands during discovery.

## Workflow

### 1. Resolve the spine

Resolve `<spine-root>` from the user, applicable project instructions, existing
integration, or `specspine`, in that order. Require
`<spine-root>/README.md`; do not create it.

### 2. Discover persistent instructions and SDD

Identify the persistent instruction surface. If an SDD framework exists,
establish from evidence:

- native workflow entry and downstream stage;
- artifact paths and work-item naming rule;
- format source and context insertion point;
- traceability rule and conflict destination.

Require only the framework and native workflow entry for a binding. Treat all
other mapping fields as optional capabilities.

Do not discover project-local skill conventions because this integration does
not generate a skill. If several instruction surfaces or frameworks are
plausible, ask which target to adapt.

Resolve the SpecSpine documentation language only from an explicit choice in
the current request or an existing managed bootstrap. Otherwise ask the user
which language to use before writing the integration; do not infer it from the
conversation, repository, or existing specification prose.

### 3. Derive minimal artifacts

Always derive one managed bootstrap. Add a project binding only for a detected
SDD workflow; default it to root `.specspine-integration.md`. Preserve canonical
SpecSpine names and formats. Resolve fields from evidence and omit unknown
options. If the framework or native entry is unknown, install only the
bootstrap.

### 4. Determine changes

Before writing, show:

```text
SpecSpine integration plan

Spine root:
- path

Persistent instruction:
- path and evidence

Documentation language:
- explicit language

SDD framework:
- framework and evidence, or none

Create:
- binding path, or none

Modify:
- persistent instruction path

Runtime binding:
- resolved fields and omitted capabilities, or none

Open decisions:
- unresolved choices, or none
```

Treat an explicit connect, install, refresh, or removal request as authorization
once the target paths are unambiguous. Show this impact summary, then apply it
without redundant confirmation. Stop only when selecting among plausible
instruction surfaces or frameworks, overwriting apparent user edits, or making
a choice the request did not decide.

### 5. Install

- Add or replace one balanced `specspine:begin` / `specspine:end` block.
- Preserve all content outside the managed block.
- Render the resolved index, documentation language, and optional binding path.
- For SDD, render the required core and only discovered optional fields.
- For a generic agent, create no binding or other generated artifact.
- Keep integration artifacts outside `<spine-root>`.

### 6. Verify

Check that:

- bootstrap and binding, when present, point to the same index;
- the bootstrap declares the explicitly selected documentation language;
- no unresolved `{{...}}` placeholder remains;
- referenced workflow entries and format sources exist;
- managed markers occur once and are balanced;
- user content outside the block is unchanged;
- a second run would update rather than duplicate artifacts;
- no skill or downstream artifact changed.

Perform a read-only trace using only persistent instructions, the optional
binding, SpecSpine, and a representative downstream request. When a fresh-agent
facility is available, use it; otherwise trace the discovery path directly and
report that independent verification was not run.

### 7. Report

Report modified and created files, detected mapping, whether a binding was
needed, and unresolved choices. State that refresh is required after material
agent-instruction or SDD convention changes.

## Refresh and removal

Refresh by rediscovering conventions and replacing only the managed block and
owned binding. If the binding lost its ownership marker or contains apparent
user edits, show the divergence and ask before overwriting it.

On explicit removal, remove only the managed block and owned binding. Never
delete a user-owned instruction file merely because it becomes empty.

## Restrictions

Never:

- generate or install a project-local or global skill;
- make downstream artifacts architectural authority;
- treat observations or inferences as accepted intent;
- resolve SpecSpine conflicts or open questions;
- guess framework commands, paths, formats, or naming rules;
- duplicate detailed binding rules across instruction surfaces;
- claim framework compatibility or code/spec conformance.
