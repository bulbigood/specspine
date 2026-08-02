# Specspine

Specspine is a strict format for durable software specifications stored in an
[IWE](https://iwe.md/) Markdown library.

IWE owns documents, document keys, inclusion hierarchy, references, backlinks,
search, retrieval, rename/delete operations, and structural validation.
Specspine adds only the specification vocabulary: kinds, completeness facets,
normative statements, observations, open questions, and verification criteria.

## Install

Install all skills and select the ones needed by your agent:

```bash
npx skills add bulbigood/specspine
```

Or install one workflow explicitly:

```bash
npx skills add bulbigood/specspine -s iwe-spec-map
```

The workflows are independent. In particular, `iwe-spec-implement` does not
require `iwe-spec-verify`. Every workflow uses the official
`iwe-memory-system` skill for IWE operations; when it is unavailable, the agent
is instructed to obtain it through the environment's skill installer.

Specspine requires the latest `iwe` CLI. Installing a skill does not install
the CLI. When `iwe` is absent, the agent must offer to install it and ask where
specifications should live; `docs/specs` is the default. Installation and
workspace changes require operator approval. If installed CLI syntax differs,
the agent consults `iwe --help` rather than assuming a version-specific flag.

## Workspace bootstrap

Each installed skill includes the Specspine config template and document
schema. The agent loads its bootstrap protocol only when IWE or the Specspine
configuration is missing, incomplete, or conflicting.

| Workspace state | Behavior |
| --- | --- |
| No `iwe` executable | Offer to install it and ask for the specification directory, defaulting to `docs/specs` |
| No `.iwe/` project | Preview and initialize IWE with the selected path, then merge the bundled template and schema |
| Existing IWE with another `library.path` | Keep and use that configured path unless the operator explicitly requests another |
| Existing `docs/` without IWE | Scope IWE to `docs/specs`, not all of `docs` |
| Existing `docs/specs` | Preserve its name and contents; never rename it for installation or a trial |
| `.iwe/` exists without `config.toml` | Preserve the directory and create only the missing config from bundled assets |
| Existing library contains unrelated notes | Keep those notes and bind new Specspine documents below `specspine/` within the configured library |
| Several IWE roots are plausible | Ask once which project root owns the task; the resulting config preserves that choice for later runs |

The normal new-project layout is:

```text
workspace/
├── .iwe/
│   ├── config.toml
│   └── schemas/specification.yaml
└── docs/specs/
```

For manual setup, copy the canonical preset:

```bash
mkdir -p .iwe
cp -R /path/to/specspine/presets/iwe/. .iwe/
```

If the project already has `.iwe/config.toml`, merge the `[library]`,
`[templates.specification]`, and `[schemas.specification]` settings instead of
overwriting its configuration. In a mixed existing library, use
`key_template = "specspine/{{slug}}"` and `match = "specspine/**"` so unrelated
notes are not validated as Specspine. Then validate it:

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
