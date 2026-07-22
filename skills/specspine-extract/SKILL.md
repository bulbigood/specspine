---
name: specspine-extract
description: Extract the smallest task-oriented architecture context handoff from an existing linked Markdown SpecSpine. Use when downstream feature, SDD, review, or coding work needs authoritative architectural context, affected specifications, preserved decisions and constraints, evidence status, or blocking questions without changing the persistent SpecSpine or creating an implementation plan.
---

# SpecSpine Extract

Runtime contract: SpecSpine v1.

Create a temporary projection of the persistent SpecSpine for one downstream
change. Read [references/context-handoff.md](references/context-handoff.md)
before extracting.

## Workflow

1. Resolve `<spine-root>` from the request, project instructions, or the
   documented default `specspine`. Require `<spine-root>/README.md`.
2. Establish the change intent from the user request. Do not invent downstream
   requirements.
3. Read the index, the canonical owner, and only the linked neighborhood needed
   to classify required, potentially affected, and merely related context.
4. Preserve statement kinds, semantic IDs, decision provenance, evidence
   baselines, unconfirmed inferences, and blocking questions.
5. Render the smallest useful handoff using the bundled contract.
6. Return it in the response by default. Write a file only when the user
   explicitly requests a location; never store it inside the persistent
   SpecSpine unless explicitly requested.

## Source boundary

Use only the current request and files inside `<spine-root>` as project
architecture sources. Inspect project-specific code, configuration, tests,
documentation, tools, or external systems only when the user explicitly
authorizes them. Authorized external evidence remains `Observed` or `Inferred`
unless the user separately accepts it as intent.

## Restrictions

Never modify the SpecSpine, implementation, or downstream artifacts while
extracting. Never add acceptance criteria, tasks, ordering, implementation
filenames, test scenarios, estimates, release scope, or implementation status.
Never silently answer blocking questions, promote inference, claim code/spec
conformance, or treat extraction readiness as implementation readiness.
