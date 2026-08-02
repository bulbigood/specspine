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

> **Operator authorization is required.** Run commands that execute AI-agent
> scenarios **only when the operator explicitly requests an AI evaluation in
> the current task**. A general request to run tests does not grant that
> authorization. If the operator has not explicitly requested AI-agent tests,
> ask for permission and wait for approval before running them. Mechanical
> tests and `tests/eval/run.py --list` do not launch AI agents and do not
> require this approval.

Executable Gherkin scenarios in `eval/features/` exercise every `iwe-spec-*`
skill and two end-to-end workflows against isolated copies of
`examples/node-express-boilerplate`. The runner invokes one coding agent and a
separate read-only AI judge. The judge evaluates the request, semantic rubric,
workspace diff, final workspace, and agent transcript; no golden patch or
mechanical assertion decides whether a scenario passes.

Every judge must also evaluate what the coding agent actually did and how long
it worked. The runner supplies wall time, user/system CPU time, CPU-to-wall
ratio, and peak resident memory for the agent process. Judges treat these as
additional efficiency dimensions: they account for CPU work and memory
pressure when interpreting a long duration, penalize disproportionate or
unnecessary work, and keep correctness and safety as the primary criteria.

Judges assume the tested agents are sufficiently capable to complete the
scenario at a high quality bar. They evaluate whether an agent used available
tools as efficiently as reasonably possible and made the decisions required by
both the scenario and every explicitly required repository-local skill. Judges
read those skills from `.agents/skills/` and check their substantive workflow,
guardrails, and decision rules. They do not evaluate compliance with skills or
instructions that are not contained in this repository, and they do not reward
accidental success that bypasses a required skill procedure or decision.

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

Run several independent samples per scenario and accept a scenario by pass
rate:

```bash
python3 tests/eval/run.py --samples 5 --min-pass-rate 0.8
```

The worker limit applies to all `scenario × sample` tasks together. Every run
gets a timestamped directory under `tests/eval/reports/`, so later runs do not
overwrite earlier samples. `summary.json` contains per-scenario and overall
pass rate plus score mean, median, minimum, maximum, and population standard
deviation. It also aggregates agent resource measurements and judge efficiency
ratings. Pass rate determines acceptance; score and efficiency statistics are
diagnostic.

By default both roles use separate ephemeral `codex exec` sessions. The coding
agent is pinned to medium (`gpt-5.6-terra`, reasoning effort `medium`) with
workspace write access. The independent judge is pinned to strong
(`gpt-5.6-sol`, reasoning effort `low`) and runs read-only. Override either
command with `--agent-command`, `--judge-command`, or the environment variables
`SPECSPINE_AGENT_COMMAND` and `SPECSPINE_JUDGE_COMMAND`. JSON verdicts are
written to `tests/eval/reports/`, which is intentionally ignored.
