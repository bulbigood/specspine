# Development

The executable format contract is the IWE configuration and document schema in
`shared/assets/iwe`. The `iwe-spec-setup` skill packages those canonical assets
for one-time workspace initialization, while installed workflow skills contain
only task instructions and semantic references. Each workflow discovers an
available IWE-capable skill and describes the result it needs; that skill owns
project discovery, retrieval, graph traversal, document operations, validation,
CLI or tool selection, compatibility handling, and resource budgets.
`iwe-spec-audit` applies cross-statement and filesystem checks to data returned
through that boundary without adding a parser or runtime.

Run:

``` bash
python3 tests/run_mechanical.py
```

The tests exercise the `docs` IWE library, default and nested library-relative
schema scopes, inclusion and reference semantics, kind-dependent facets,
exhaustive-boundary basis, asset constraints, semantic-audit inputs, capability
discovery and delegation, owner reuse, evidence-only facet safety, document
creation and refactoring, autonomous skill packaging, and setup outcomes.

IWE is the only runtime, parser, graph, and document-lifecycle implementation. Do not add Specspine scripts, a second Markdown parser, generated indexes, or a parallel relationship model. Extend the IWE document schema first and adopt new native IWE relationship semantics as they become available.
