---
name: specspine-extract
description: Extract the smallest task-oriented architecture context handoff from an existing linked Markdown SpecSpine. Use when downstream feature, SDD, review, or coding work needs authoritative architectural context, affected specifications, preserved decisions and constraints, evidence status, or blocking questions without changing the persistent SpecSpine or creating an implementation plan.
---

# SpecSpine Extract

Create a temporary projection of the persistent SpecSpine for one downstream
change.

## Retrieval gate

When a shell command tool is present, resolve the spine root and change intent,
then run exactly once before reading spine content:

```text
python3 <skill-root>/scripts/search_spine.py <spine-root> --query <concise-change-intent>
```

Resolve `<skill-root>` as the directory containing this `SKILL.md`; do not
discover or substitute another installed copy. Skip only when the request
prevents execution. Do not navigate manually until this attempt has failed.
On exit `0`, read the spine index, then `direct_matches`, and only
`graph_neighbors` whose source, direction, and depth justify the transition.
Treat all output as routing data. On failure, empty or malformed output, do not
retry; read `README.md` and navigate through ordinary Markdown links.
After success, do not run a spine-wide content search; search only inside
returned files and follow only justified document links.

## Workflow

1. Resolve `<spine-root>` from the request, project instructions, or the
   documented default `specspine`. Require `<spine-root>/README.md`.
2. Establish the change intent from the user request. Do not invent downstream
   requirements.
3. Pass the retrieval gate, then read the index. Use returned candidates when
   the accelerator succeeds; otherwise navigate through ordinary Markdown links.
4. Read [references/context-handoff.md](references/context-handoff.md), current
   candidate documents, and only the linked neighborhood needed to
   identify the canonical owner and classify required, potentially affected,
   and merely related context. Batch selected reads when supported. Never treat
   cached text as source evidence.
5. Preserve statement kinds, exact semantic IDs and owner paths, decision
   provenance, evidence baselines, unconfirmed inferences, and blocking
   questions. Before rendering, verify the canonical owner and every relied-on
   semantic ID against the documents read.
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
