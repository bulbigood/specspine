# Development

The executable format contract is the IWE configuration and document schema in `shared/assets/iwe`. The `iwe-spec-setup` skill packages those canonical assets for one-time workspace initialization, while installed workflow skills contain only their task instructions and semantic references. The README keeps the same setup as a manual fallback.

Run:

``` bash
python3 tests/run_mechanical.py
```

The tests exercise the `docs` IWE library, default and nested library-relative schema scopes, inclusion and reference semantics, document creation and refactoring, autonomous skill packaging, and both setup paths documented in the README.

IWE is the only runtime, parser, graph, and document-lifecycle implementation. Do not add Specspine scripts, a second Markdown parser, generated indexes, or a parallel relationship model. Extend the IWE document schema first and adopt new native IWE relationship semantics as they become available.
