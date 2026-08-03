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

### 1. Install the agent skills

Install the official IWE skill used by every Specspine workflow:

```bash
npx skills add iwe-org/skills --skill iwe-memory-system
```

Then install Specspine, including its setup and workflow skills:

```bash
npx skills add bulbigood/specspine
```

To install one workflow explicitly, use `--skill`, for example:

```bash
npx skills add bulbigood/specspine --skill iwe-spec-map
```

`iwe-memory-system` is an agent instruction dependency, not an additional
runtime or storage layer. IWE remains the only Specspine runtime dependency.

### 2. Run the guided setup

From the workspace root, ask your agent:

> Use `$iwe-spec-setup` to guide me through installing IWE and configuring
> Specspine in this workspace.

The setup skill is an interactive, script-free guide. It first checks whether
IWE is available. If not, it reads the current official IWE installation
instructions, presents compatible options, and runs only the method selected
and approved by the user. You may also install IWE beforehand from the
[official installation guide](https://iwe.md/docs/getting-started/installation/).

The skill then asks:

1. Which directory inside the workspace should be the IWE Markdown library
   (`library.path`). It offers `docs` for a new workspace.
2. Which directory inside that library should contain Specspine documents. It
   offers `<library.path>/specs` and rejects paths outside the IWE library.

After confirmation it initializes IWE if needed, derives the template key and
schema match from the selected Specspine directory, merges only the Specspine
configuration, installs the canonical document schema, and runs
`iwe schema validate`. Existing settings or conflicting Specspine configuration
are not overwritten without approval.

The workflow skills assume that setup is complete; they do not install or
repair IWE or Specspine configuration.

<details>
<summary>Manual workspace setup if the setup skill is unavailable or fails</summary>

#### Install IWE manually

Follow the [official IWE installation guide](https://iwe.md/docs/getting-started/installation/)
and verify that `iwe --version` succeeds.

#### Initialize IWE manually

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
For all available `.iwe/config.toml` options, see the official
[IWE configuration reference](https://iwe.md/docs/configuration/).

#### Add the Specspine template and schema binding

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

This example places specifications in `<library.path>/specs/`. For another
directory strictly inside the IWE library, replace both `specs` prefixes with
that directory's path relative to `library.path`. For example,
`docs/architecture/specs/` with `library.path = "docs"` requires:

```toml
[templates.specification]
key_template = "architecture/specs/{{slug}}"

[schemas.specification]
match = "architecture/specs/**"
```

Create `.iwe/schemas/` and save the canonical
[Specspine document schema](shared/assets/iwe/schemas/specification.yaml) as
`.iwe/schemas/specification.yaml`. The complete recommended configuration is
available as [a reference](shared/assets/iwe/config.toml); merge it rather than
copying it over an existing config.

With the example values, the template creates documents below
`<library.path>/specs/`. Both template keys and schema matches are relative to
`library.path`, so Markdown elsewhere in the library remains ordinary IWE
content.

#### Validate the workspace

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

</details>

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
- [Semantic audit](docs/reference/audit.md)
- [IWE operational recipes](docs/reference/operations.md)
- [Glossary](docs/reference/glossary.md)

## License

MIT
