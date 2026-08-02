# Development

The executable format contract is the IWE configuration and document schema in `shared/assets/iwe`. The README exposes those canonical setup assets, while installed workflow skills contain only their task instructions and semantic references.

Run:

``` bash
python3 tests/run_mechanical.py
```

The tests exercise the `docs` IWE library, the scoped `specs/**` schema, inclusion and reference semantics, document creation and refactoring, skill packaging, and the manual setup contract documented in the README.

IWE is the only runtime, parser, graph, and document-lifecycle implementation. Do not add Specspine scripts, a second Markdown parser, generated indexes, or a parallel relationship model. Extend the IWE document schema first and adopt new native IWE relationship semantics as they become available.
