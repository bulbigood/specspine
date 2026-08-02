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

The workflows are independently installable and self-contained. They can also
be combined for Map → Specify → Verify → Implement → Verify work.

## Setup

Install IWE by following the
[official installation guide](https://iwe.md/docs/getting-started/installation/).
Specspine has no other runtime dependency.

Initialize IWE from the workspace root and use `docs` as its library:

```bash
iwe init --auto --library docs
```

See the official [`iwe init` reference](https://iwe.md/docs/cli/init/) for
initialization modes and configuration behavior.

This creates `.iwe/config.toml` with:

```toml
[library]
path = "docs"
```

Then choose the Specspine workflows to install:

```bash
npx skills add bulbigood/specspine
```

To install one workflow explicitly:

```bash
npx skills add bulbigood/specspine --skill iwe-spec-map
```

Skill installation only installs the workflow and its bundled Specspine schema
assets; it cannot execute a workspace setup hook. On first use, a workflow adds
the missing Specspine template and schema binding to the existing IWE project.
The binding is scoped to `specs/**`, so ordinary files elsewhere under `docs`
remain normal IWE documents.

Each workflow uses the official `iwe-memory-system` skill as its agent-facing
guide to IWE. This is a skill dependency, not an additional runtime or storage
layer; IWE remains the only executable dependency and graph implementation.

The resulting layout is:

```text
workspace/
├── .iwe/
│   ├── config.toml
│   └── schemas/specification.yaml
└── docs/
    └── specs/
```

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
