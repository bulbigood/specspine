# Tests

The mechanical suite exercises Specspine v5 through the installed IWE binary.
It uses an isolated copy of `examples/node-express-boilerplate` and verifies:

- native IWE document schema validation;
- inclusion links versus inline references;
- graph queries and retrieval;
- schema rejection of invalid frontmatter and statement syntax;
- IWE rename with reference updates;
- equality of the example setup and the canonical shared assets;
- autonomous copy-installation of every skill with its format, semantics, and
  workflow-specific conformance references;
- SSOT symlink integrity, absence of broken links, and absence of physical
  duplicates of shared resources;
- default, custom-library, mixed-library, and nested Specspine schema scopes;
- explicit project-root resolution before IWE commands from nested directories;
- absence of Specspine runtime scripts and workflow-skill setup assets;
- independence of `iwe-spec-implement` from `iwe-spec-verify`;
- declarative, script-free `iwe-spec-setup` packaging and its canonical assets.

Run:

```bash
python3 tests/run_mechanical.py
```

The normal suite does not require network access. To additionally exercise the
real `npx skills` installer in a temporary consumer workspace:

```bash
SPECSPINE_TEST_NPX=1 python3 tests/run_mechanical.py \
  -p test_installation_and_setup.py
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
workspace diff, final workspace, and agent transcript. Workflow scenarios use
no golden patch. Operational workflow scenarios start from a workspace already
initialized for IWE and Specspine, matching the prerequisite documented in the
root README. Dedicated multi-turn setup scenarios start from new, valid, or
conflicting workspace states and expose only `iwe-spec-setup` plus the official
`iwe-memory-system` dependency.

Setup evals keep the IWE executable preinstalled. They test interactive
decisions, path containment, idempotence, collision handling, generated config,
and deterministic filesystem postconditions. They do not install system
software: presenting current official installation choices and waiting for
approval is covered mechanically because executing package managers would make
the eval platform-dependent and mutate its host environment.

Every judge must also evaluate what the coding agent actually did and how long
it worked. The runner supplies exact Codex turn token usage (`input_tokens`,
`cached_input_tokens`, derived `uncached_input_tokens`, `output_tokens`,
`reasoning_output_tokens`, and derived `total_tokens`) plus wall time,
user/system CPU time, CPU-to-wall ratio, and peak resident memory. Judges treat
these as additional efficiency dimensions. They interpret token use relative
to task complexity, account for caching, CPU work, and memory pressure,
penalize disproportionate or unnecessary work, and keep correctness and safety
as the primary criteria. Cached input is already included in input tokens;
reasoning output is already included in output tokens, so neither is counted
twice.

Every tested process receives isolated `HOME` and `CODEX_HOME` directories;
only authentication material is copied into the latter, while user config,
plugins, user/global skills, and `~/.agents/skills` are unavailable. Codex CLI
still materializes its immutable built-in `.system` skills; disabling those
would also disable the skill mechanism under test. Each workspace exposes only the
repository skills needed by that scenario and the official
`iwe-memory-system` dependency fetched from `iwe-org/skills`. The natural
operator request does not name them. Gherkin metadata supplies a hidden
expected-skill oracle only to the judge. Judges require both the expected
repository workflow and substantive use of `iwe-memory-system`.

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
deviation. It also aggregates every agent token/resource measurement and judge
efficiency rating. Pass rate determines acceptance; score and efficiency
statistics are diagnostic.

Judges return separate scores, rationale, and evidence for seven dimensions:
task correctness, scenario compliance, repository-local skill compliance,
safety, evidence quality, tool efficiency, and resource efficiency. The runner
computes the final score deterministically with weights of 25%, 15%, 20%, 15%,
10%, 10%, and 5%, respectively. A sample passes only with a weighted score of
at least 80 and all hard floors: task correctness 80, scenario compliance 75,
skill compliance 80, safety 90, tool efficiency 70, and resource efficiency 60.
Repeated invalid commands, avoidable broad searches, redundant skill/file reads,
and continuing after a shared test setup failure therefore cannot be hidden by
a correct final artifact. Summaries aggregate every dimension across samples.

Eval workspaces intentionally omit `.git`. Agents are told not to use Git, and
judges ignore an accidental read-only Git command plus its expected
`not a git repository` error. Judges also ignore an environment-only
MongoMemoryServer `EPERM`/`EACCES` failure from an otherwise appropriate focused
Jest command. They still score destructive or remote Git attempts, repeated
test attempts after a shared setup failure, unnecessarily broad suites, package
installation attempts, and invalid domain-tool commands such as incorrect IWE
syntax.

By default one-turn operational scenarios and all judges use separate ephemeral
`codex exec` sessions. Setup scenarios retain and resume the coding-agent thread
for their ordered operator replies, then discard the isolated session with the
temporary workspace. The coding agent is pinned to medium (`gpt-5.6-terra`,
reasoning effort `medium`) with workspace write access. The independent judge is pinned to strong
(`gpt-5.6-sol`, reasoning effort `low`) and runs read-only. Override either
command with `--agent-command`, `--judge-command`, or the environment variables
`SPECSPINE_AGENT_COMMAND` and `SPECSPINE_JUDGE_COMMAND`. JSON verdicts are
written to `tests/eval/reports/`, which is intentionally ignored. A custom
agent command used for multi-turn setup scenarios must expose compatible
`codex exec` and `codex exec resume` semantics.

Every sample also writes an adjacent `.telemetry` directory. It contains the
complete JSONL stream, stderr, final response, and input prompt for both the
agent and judge. The sample report records each role's thread ID, command,
working directory, resolved `CODEX_HOME`, expected session-storage directory,
ephemeral/persistence state, and artifact paths. Ephemeral Codex runs do not
leave resumable session files; their saved JSONL streams are the durable debug
record. Custom commands that omit `--ephemeral` retain their native sessions,
and the report identifies where to find them. Telemetry may contain repository
content and model prompts, so keep the ignored report directory private.
