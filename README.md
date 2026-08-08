# Specspine

**Durable boundary contracts and architectural ownership for AI-assisted
software development.**

Specspine preserves accepted, durable intent as a graph of canonical
specification owners and their boundary contracts. Source code owns internal
mechanisms and current implementation reality; Specspine owns what the system is
expected to mean and do. It neither mirrors the source tree nor assumes that the
implementation conforms to the specification.

A sufficiently specified area can be understood or independently reimplemented
from its normative closure, then checked with implementation-independent
verification criteria. This gives humans and coding agents a stable source of
architectural intent instead of asking them to reconstruct it from whichever
code happens to exist today.

## Principles

- One IWE document is the canonical owner of one durable software boundary.
- Accepted intent and observed implementation evidence remain distinct.
- A link-only paragraph is structural inclusion; an inline link is a
  non-structural reference.
- Directories organize files but carry no architectural meaning.
- Specspine follows IWE's native relationship model as it evolves instead of
  maintaining parallel relationship metadata.

## Workflows

| Skill | Purpose |
| --- | --- |
| **🚀 BOOTSTRAP** | — |
| `iwe-spec-setup` | Initialize or repair the one-time Specspine workspace configuration. |
| **🎯 CORE** | — |
| `iwe-spec-specify` | Create or refine accepted requirements and architecture. |
| `iwe-spec-map` | Record boundary-significant implementation evidence without inventing intent. |
| `iwe-spec-implement` | Bring implementation into conformance without weakening the specification. |
| **🛠️ SUPPORT** | — |
| `iwe-spec-audit` | Audit format conformance and semantic readiness without changing files. |
| `iwe-spec-verify` | Compare implementation evidence with accepted specifications without editing specifications or code. |

## Setup

Complete this setup before using any Specspine workflow.

Install Specspine, including its setup and workflow skills:

```bash
npx skills add bulbigood/specspine
```

To install one workflow explicitly, use `--skill`, for example:

```bash
npx skills add bulbigood/specspine --skill iwe-spec-map
```

Specspine does not require a particular external skill. Before a workflow uses
IWE, the agent discovers an available skill whose declared capability covers
IWE and delegates all project discovery, retrieval, graph traversal, document
operations, validation, compatibility handling, and resource budgeting to it.
The Specspine skill describes only the domain result it needs. If the agent has
no IWE-capable skill, the workflow reports the missing capability and stops.

Run the guided setup from the workspace root:

> Use `$iwe-spec-setup` to configure Specspine in this IWE workspace.

The setup skill finds an applicable IWE-capable skill and gives it the desired
workspace outcome and bundled Specspine assets. The IWE skill owns installation
guidance, project initialization, configuration operations, and validation.

The setup establishes:

1. the intended IWE workspace and Markdown library;
2. a Specspine directory strictly inside that library;
3. matching library-relative template and schema prefixes;
4. the canonical Specspine schema and a valid final workspace.

It reuses explicit values already supplied by the user, asks only for unresolved
or consequential choices, preserves unrelated settings, and does not overwrite
conflicting Specspine configuration without approval.

The workflow skills assume that setup is complete; they do not install or
repair IWE or Specspine configuration.

## Documentation

- [Core model](docs/01-core-model.md)
- [Usage and lifecycle](docs/02-usage-and-lifecycle.md)
- [Acceptance and reconstruction](docs/03-acceptance-and-reconstruction.md)
- [Format v5](docs/reference/format.md)
- [Semantics](docs/reference/semantics.md)
- [Conformance](docs/reference/conformance.md)
- [Semantic audit](docs/reference/audit.md)
- [Glossary](docs/reference/glossary.md)

## License

MIT
