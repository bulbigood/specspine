# Core model

Each IWE document is one canonical specification owner. Its IWE key is its
stable identity. Frontmatter declares its Specspine kind, completeness and
verification metadata. Markdown owns the durable contract.

Source code owns implementation reality. A specification owns accepted intent.
`OBS-*` statements record relevant evidence without turning it into intent.

## Graph

Specspine uses the two relationships native to IWE:

- a link in its own paragraph is an inclusion edge and expresses structure;
- a link embedded in prose is a reference edge and expresses a conceptual
  dependency without changing structure.

A document may have multiple inclusion parents. Directories carry no semantic
meaning.
