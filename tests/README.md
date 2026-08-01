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

## AI-judged skill evaluations

Executable Gherkin scenarios in `eval/features/` exercise every `iwe-spec-*`
skill and two end-to-end workflows against isolated copies of
`examples/node-express-boilerplate`. The runner invokes one coding agent and a
separate read-only AI judge. The judge evaluates the request, semantic rubric,
workspace diff, final workspace, and agent transcript; no golden patch or
mechanical assertion decides whether a scenario passes.

List scenarios:

```bash
python3 tests/eval/run.py --list
```

Run one scenario:

```bash
python3 tests/eval/run.py --scenario "Map password-reset"
```

Run the full skill line:

```bash
python3 tests/eval/run.py
```

Each parallel scenario receives its own temporary workspace, agent process,
judge process, and report file. AI scenarios run with 10 workers by default;
use `--jobs` to override that limit and `--exclude-scenario` to omit a
previously completed case. The runner installs the fixture's locked Node.js
dependencies once when needed and shares the dependency tree between
isolated workspaces. Jest uses a separate in-memory MongoDB process, so it does
not require Docker or a system MongoDB service.

By default both roles use separate ephemeral `codex exec` sessions. The judge
is pinned to the strong configuration (`gpt-5.6-sol`, reasoning effort `low`)
and runs read-only. Override either command with `--agent-command`,
`--judge-command`, or the environment variables `SPECSPINE_AGENT_COMMAND` and
`SPECSPINE_JUDGE_COMMAND`. JSON verdicts are written to
`tests/eval/reports/`, which is intentionally ignored.
