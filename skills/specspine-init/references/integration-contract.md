# SpecSpine integration contract

This reference defines the boundary between the architectural source of truth,
the persistent discovery instruction, and a generated downstream adapter.

## Contents

- [Artifact roles](#artifact-roles)
- [Authority semantics](#authority-semantics)
- [Bootstrap contract](#bootstrap-contract)
- [Generated skill contract](#generated-skill-contract)
- [Framework mapping](#framework-mapping)
- [Discovery and fallbacks](#discovery-and-fallbacks)
- [Ownership and regeneration](#ownership-and-regeneration)

## Artifact roles

| Artifact | Role | Persistence |
|---|---|---|
| `<spine-root>/README.md` | Entry into canonical architectural claims | Long-lived |
| Linked SpecSpine documents | Architectural responsibilities, boundaries, decisions, constraints, observations, inferences, and questions | Long-lived |
| Persistent agent instruction | Always-visible discovery bridge | Generated project configuration |
| Project integration skill | Detailed consumer workflow and SDD mapping | Regenerable project configuration |
| Feature specs, plans, tasks, code, and tests | Downstream change and implementation artifacts | Owned downstream |

The bootstrap and generated skill are not part of the architectural source of
truth. Do not place them under `<spine-root>`.

## Authority semantics

SpecSpine is the canonical location for architectural claims, but not every
claim has equal authority:

- `Decisions` and `Constraints` express accepted intent;
- `Observed` records repository evidence, not required intent;
- `Inferred` remains unconfirmed;
- `Open questions` remain unresolved and may block downstream work.

Downstream artifacts may refine a change but must not silently replace accepted
architecture. Preserve disagreement between implementation evidence and intent.
Do not claim that documented intent is implemented.

## Bootstrap contract

Keep the persistent block small enough to load on every agent turn. It must
contain only:

1. the resolved SpecSpine index path;
2. when an agent must consult it;
3. the distinction between normative intent and non-normative evidence;
4. the rule to preserve conflicts;
5. the generated integration skill name or native fallback pointer.

Use exactly one managed region per instruction file:

```markdown
<!-- specspine:begin -->
...
<!-- specspine:end -->
```

Do not put framework commands, directory maps, long explanations, or copied
SpecSpine content in this block.

## Generated skill contract

The generated project skill must be thin and self-contained. Include:

- a trigger description covering planning, specification, implementation, and
  review work in the project;
- a project-root guard when the skill is not project-local;
- the resolved SpecSpine entry point;
- the authority semantics above;
- the rule to read only the smallest relevant linked context;
- the detected framework and exact native workflow entry;
- the downstream stage, artifact paths, work-item naming rule, format source,
  and context insertion point;
- traceability through ordinary specification paths and semantic IDs when
  present;
- an explicit destination for conflicts and blocking questions;
- a consumer-only boundary: do not edit SpecSpine unless explicitly requested
  through an appropriate maintenance workflow.

Do not copy the complete SDD framework skill. Refer to its native workflow and
add only the bridge rules that it lacks.

## Framework mapping

Record every runtime binding field. Use a concrete value supported by inspected
integration metadata or explicit `not applicable`; never leave the field
implicit:

| Required field | Example answer |
|---|---|
| Framework | Framework name, or `not applicable — generic coding agent` |
| Native workflow entry | Skill, command, or applicable instruction file |
| Downstream stage | Change proposal creation |
| Artifact paths | Framework-native change path pattern |
| Work-item naming rule | Lowercase kebab-case identifier derived from intent |
| Format source | Template, schema, or instruction path |
| Context insertion point | Named document section or workflow input |
| Traceability rule | Relative specification path plus semantic ID label |
| Conflict destination | Named artifact section or blocking user response |

Use native names and formats downstream. Do not rename or transform canonical
SpecSpine documents to match them.

If a required convention cannot be established confidently, keep it as an open
decision in the proposal and do not install. Never guess a command, path, or
file format, and never emit unresolved template placeholders.

## Discovery and fallbacks

Use the narrowest sufficient inspection:

1. applicable root-level agent instructions;
2. existing project-local skill or rule directories;
3. SDD manifests, instructions, templates, and command definitions;
4. explicitly authorized external or global skill metadata.

The presence of a directory name alone is weak evidence. Prefer an applicable
instruction, manifest, or template that demonstrates the convention.

If local skills are unsupported:

1. keep the minimal discovery block in the persistent instruction;
2. put detailed integration rules in a supported native project-rule surface;
3. if no such surface exists, expand the managed block only as much as needed
   and report the fallback.

Do not install globally merely to avoid this fallback.

## Ownership and regeneration

The integration owns only:

- text between its managed bootstrap markers;
- generated files explicitly named in the approved proposal and carrying a
  `Generated by specspine-init` ownership marker.

Make installation idempotent. Refresh by rediscovering current conventions and
regenerating owned artifacts. Do not maintain a permanent compatibility matrix;
the generated adapter is a snapshot of the inspected environment.

Do not overwrite apparent user edits silently. Do not delete user-owned files
or directories during removal.
