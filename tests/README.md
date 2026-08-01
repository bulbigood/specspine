# Tests

The mechanical suite exercises Specspine v5 through the installed IWE binary.
It uses an isolated copy of `examples/node-express-boilerplate` and verifies:

- native IWE document schema validation;
- inclusion links versus inline references;
- graph queries and retrieval;
- schema rejection of invalid frontmatter and statement syntax;
- IWE rename with reference updates;
- equality of the example schema and the canonical shared preset.

Run:

```bash
python3 tests/run_mechanical.py
```
