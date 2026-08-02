# Core model

Each Specspine document is one canonical specification owner. Its IWE key is its stable identity. Frontmatter declares its kind, completeness, boundary coverage, and verification metadata. Markdown owns the durable contract.

Source code owns implementation reality. A specification owns accepted intent. `OBS-*` statements record confirmed evidence and `INF-*` statements record unconfirmed interpretations without promoting either to accepted intent.

## Ownership

Create a separate owner only for an independently useful responsibility, lifecycle, or external boundary. Assign each claim to one owner and connect related owners instead of copying claims between them. Statement IDs are local to their owner; `<IWE key, semantic ID>` is the stable address.

## Graph

Specspine uses relationships native to IWE:

- a link that is the only content of its paragraph is an inclusion edge and expresses structure;
- a link embedded in prose is a reference edge and expresses a non-structural dependency.

A document may have multiple inclusion parents. Directories carry no semantic meaning. Specspine does not duplicate IWE relationships in frontmatter, manifests, or generated indexes. New relationship capabilities should build on IWE's native model rather than introduce a parallel graph.
