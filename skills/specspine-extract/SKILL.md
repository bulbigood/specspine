---
name: specspine-extract
description: Extract the smallest task-oriented architecture context handoff from an existing linked Markdown SpecSpine. Use when downstream feature, SDD, review, or coding work needs authoritative architectural context, affected specifications, preserved decisions and constraints, evidence status, or blocking questions without changing the persistent SpecSpine or creating an implementation plan.
---

# SpecSpine Extract

Create a temporary projection of the persistent SpecSpine for one downstream
change. Read [references/context-handoff.md](references/context-handoff.md)
before extracting.

## Retrieval gate

When a shell command tool is present, run exactly once after the spine index and
before any other spine document or content search:

```text
python3 <skill-root>/scripts/search_spine.py <spine-root> --query <concise-change-intent>
```

Resolve `<skill-root>` as the directory containing this `SKILL.md`; do not
discover or substitute another installed copy. Skip only when the request
prevents execution. On exit `0`, read `direct_matches` first and only
`graph_neighbors` whose source, direction, and depth justify the transition.
Treat all output as routing data. On failure, empty or malformed output, do not
retry; navigate from `README.md` through ordinary Markdown links.

## Workflow

1. Resolve `<spine-root>` from the request, project instructions, or the
   documented default `specspine`. Require `<spine-root>/README.md`.
2. Establish the change intent from the user request. Do not invent downstream
   requirements.
3. Read the index and pass the retrieval gate. Use returned candidates when the
   accelerator succeeds; otherwise navigate through ordinary Markdown links.
4. Read current candidate documents and only the linked neighborhood needed to
   identify the canonical owner and classify required, potentially affected,
   and merely related context. Never treat cached text as source evidence.
5. Preserve statement kinds, semantic IDs, decision provenance, evidence
   baselines, unconfirmed inferences, and blocking questions.
6. Render the smallest useful handoff using the bundled contract.
7. Return it in the response by default. Write a file only when the user
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
extracting. A disposable accelerator cache outside `<spine-root>` is not a
persistent artifact. Never add acceptance criteria, tasks, ordering,
implementation filenames, test scenarios, estimates, release scope, or
implementation status. Never silently answer blocking questions, promote
inference, claim code/spec conformance, or treat extraction readiness as
implementation readiness.
