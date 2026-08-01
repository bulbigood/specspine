# Specspine

Specspine is a strict format for durable software specifications stored in an
[IWE](https://iwe.md/) Markdown library.

IWE owns documents, document keys, inclusion hierarchy, references, backlinks,
search, retrieval, rename/delete operations, and structural validation.
Specspine adds only the specification vocabulary: kinds, completeness facets,
normative statements, observations, open questions, and verification criteria.

## Requirements

- IWE 0.17 or newer
- a project-level `.iwe/config.toml`
- `.iwe/schemas/specification.yaml`
- specifications below the configured IWE library path (normally `specspine/`)

Copy the preset from `skills/specspine-doctor/assets/iwe`, then validate it:

```bash
iwe schema validate
iwe tree
```

Create documents through IWE:

```bash
iwe create --template specification --var title="Authentication"
```

## Link semantics

A Markdown link in its own paragraph is an IWE inclusion link. It makes the
current document a parent of the target and is the only Specspine hierarchy.
A link inside prose is an IWE reference and does not affect hierarchy.

Specspine has no generated indexes, manifest, directory hierarchy, link parser,
or document lifecycle scripts.

See [the v5 format](docs/reference/format.md) and
[semantics](docs/reference/semantics.md).

## License

MIT
