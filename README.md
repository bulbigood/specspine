# Specspine

Specspine is a strict vocabulary for durable software specifications stored in
an [IWE](https://iwe.md/) Markdown library.

IWE owns documents, stable keys, links, graph traversal, refactoring, and
schema validation. Specspine adds the software-specification semantics: owners,
completeness facets, accepted constraints, implementation evidence, open
questions, and verification criteria. It does not add a second graph, index, or
document lifecycle beside IWE.

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
| `iwe-spec-map` | Record boundary-significant implementation evidence without inventing intent. |
| `iwe-spec-specify` | Create or refine accepted requirements and architecture. |
| `iwe-spec-verify` | Compare implementation evidence with accepted specifications without editing specifications or code. |
| `iwe-spec-implement` | Bring implementation into conformance without weakening the specification. |

The workflows are independently installable and share the setup prerequisites
below. They can also be combined for Map → Specify → Verify → Implement →
Verify work.

## Setup

Complete this setup before using any Specspine workflow.

### 1. Install and initialize IWE

Install IWE by following the
[official installation guide](https://iwe.md/docs/getting-started/installation/).
IWE is the only Specspine runtime dependency.

From the workspace root, initialize an IWE project with `docs` as its Markdown
library:

```bash
iwe init --auto --library docs
```

The generated `.iwe/config.toml` must contain:

```toml
[library]
path = "docs"
```

A plain `iwe init` may set `path = ""`, which means the workspace root. That is
valid IWE configuration, but this guide uses `docs`. For an existing IWE
project, keep its configured `library.path`; every `specs/**` path below is
relative to that library. See the official
[`iwe init` reference](https://iwe.md/docs/cli/init/).

### 2. Add the Specspine template and schema binding

Append the following tables to `.iwe/config.toml`. Do not replace the generated
configuration or unrelated IWE settings.

```toml
[templates.specification]
key_template = "specs/{{slug}}"
document_template = """
---
specspine: 5
title: {{title}}
kind: component
summary: Describe the durable boundary contract.
facets:
  architecture: missing
  behavior: missing
  interfaces: missing
  data: missing
  failure: missing
  quality: missing
  verification: missing
coverage:
  external-boundary: open
blockers: []
implementation_freedom: contract-equivalent
---

# {{title}}

## Responsibility

{{body}}
"""

[schemas.specification]
match = "specs/**"
```

Create `.iwe/schemas/` and save the canonical
[Specspine document schema](shared/assets/iwe/schemas/specification.yaml) as
`.iwe/schemas/specification.yaml`. The complete recommended configuration is
available as [a reference](shared/assets/iwe/config.toml); merge it rather than
copying it over an existing config.

The template creates documents below `<library.path>/specs/`. The schema match
uses IWE document keys relative to `library.path`, so Markdown elsewhere in the
library remains ordinary IWE content.

### 3. Validate the workspace

```bash
iwe schema validate
```

The resulting canonical layout is:

```text
workspace/
├── .iwe/
│   ├── config.toml
│   └── schemas/specification.yaml
└── docs/
    └── specs/
```

### 4. Install the agent skills

Install the official IWE skill used by every Specspine workflow:

```bash
npx skills add iwe-org/skills --skill iwe-memory-system
```

Then install the Specspine workflows:

```bash
npx skills add bulbigood/specspine
```

To install one workflow explicitly:

```bash
npx skills add bulbigood/specspine --skill iwe-spec-map
```

`iwe-memory-system` is an agent instruction dependency, not an additional
runtime or storage layer. The workflow skills assume that this setup is already
complete; they do not install or repair IWE or Specspine configuration.

Create and inspect specifications through IWE:

```bash
iwe create --template specification --var title="Authentication" --strict
iwe tree
iwe schema validate
```

## Documentation

- [Core model](docs/01-core-model.md)
- [Usage and lifecycle](docs/02-usage-and-lifecycle.md)
- [Acceptance and reconstruction](docs/03-acceptance-and-reconstruction.md)
- [Format v5](docs/reference/format.md)
- [Semantics](docs/reference/semantics.md)
- [Conformance](docs/reference/conformance.md)
- [Glossary](docs/reference/glossary.md)

## License

MIT
