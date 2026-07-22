# SpecSpine evaluation

The evaluation directory contains two independent harnesses:

- `run.py` checks SpecSpine skills against deterministic case manifests.
- `compare.py` compares architectural-context strategies on downstream coding
  tasks using narrow mechanical checks and an optional blind semantic judge.

The Python harnesses use only the standard library. The bundled adapter requires
the Codex CLI.

## Validation

```bash
python3 tests/eval/run.py --validate --audit
python3 tests/eval/compare.py --validate --list
python3 -m unittest discover -s tests/eval -p 'test_*.py'
```

The optional installed-package test requires npm execution:

```bash
SPECSPINE_RUN_NPX=1 python3 -m unittest discover -s tests/eval -p 'test_npx_install.py' -v
```

## Deterministic skill evaluation

List cases or run an explicitly selected case/category:

```bash
python3 tests/eval/run.py --list

python3 tests/eval/run.py \
  --category core \
  --agent-command "python3 $(pwd)/tests/eval/adapters/codex.py"
```

`--case` and `--category` are repeatable and may be combined. There is no
implicit run-all mode. Planned cases are never executed.

Categories are disjoint:

- `core`: 10 executable cases, 12 agent calls;
- `extended`: 3 executable cases, 4 agent calls;
- `planned`: 11 documented, non-executable cases.

The runner creates a clean temporary workspace per case, sends the prompt to the
adapter on stdin, and evaluates the resulting files. The adapter path must be
absolute because its current directory is the temporary workspace. Cases run
with concurrency 8 by default; use `--jobs N` to change it.

Workspaces are created under `~/.cache/specspine-eval/workspaces`, outside the
system temp directory. Override this with `SPECSPINE_EVAL_WORKSPACES_DIR`.

Failed workspaces are deleted unless `--keep-workspace` is set. Successful
workspaces are always deleted. The final terminal line reports how many selected
cases passed.

### Case manifests

`cases/*.json` defines the fixture, category, status, skill, prompt and
deterministic assertions. A manifest may instead define `stages`: agent stages
run their own prompt and assertions, while fixture stages model external
changes. A failing stage stops later stages; `final_assertions` still inspect the
state reached. Stage diagnostics are stored under
`.eval/stages/<number>-<id>/` inside the temporary workspace.

Supported assertion types:

- paths/content: `path_exists`, `path_absent`, `glob_count`, `glob_contains`,
  `file_contains`, `file_not_contains`;
- response: `response_contains`, `response_not_contains`;
- changes: `unchanged`, `changed_only`, `max_changed_files`;
- execution: `command_succeeds`;
- trace: `read_only`, `read_includes`, `max_files_read`;
- structure: `balanced_markers`, `no_template_placeholders`,
  `markdown_links_valid`, `semantic_ids_valid`, `spine_mechanical_valid`.

Trace assertions require the adapter to write `.eval/trace.json`. The bundled
Codex adapter derives a conservative read trace from CLI command events; broad
content searches may count every candidate file as read.

## Comparative evaluation

The recommended pilot pairing is `gpt-5.6-luna` at medium reasoning for the
downstream or handoff-producing agent and the independent `gpt-5.6-terra` at
medium reasoning for the blind judge. Keep this pairing fixed within a run.

Run comparisons through the Docker launcher. It builds content-addressed agent
and controller images once, reuses them on later runs, and creates a fresh
restricted agent container for every sample and judgment. Verify the complete
controller-to-agent path without making a model call:

```bash
tests/eval/docker/run-comparisons.sh --preflight
```

The harness separates three questions. Run the primary incremental-value
experiment with its manifest-defined sample counts (24 agent calls):

```bash
tests/eval/docker/run-comparisons.sh --experiment value
```

Run the smaller projection ablation only after changing handoff format or
selection (8 agent calls):

```bash
tests/eval/docker/run-comparisons.sh --experiment projection
```

Evaluate automatic handoff production independently (4 agent calls). The judge
scores semantic handoff quality in addition to deterministic reference checks:

```bash
tests/eval/docker/run-comparisons.sh --experiment handoff-production
```

Run the complete manifest-defined pilot (36 agent calls and up to 36 judge
calls; identical judge inputs reuse one judgment):

```bash
tests/eval/docker/run-comparisons.sh --all
```

Use a one-sample smoke run to verify live infrastructure at lower cost before
the pilot. It makes 16 agent calls but is insufficient for product conclusions:

```bash
tests/eval/docker/run-comparisons.sh --all --samples 1
```

Override the pinned run pairing explicitly when needed:

```bash
SPECSPINE_EVAL_AGENT_MODEL=gpt-5.6-luna \
SPECSPINE_EVAL_AGENT_REASONING=medium \
SPECSPINE_EVAL_JUDGE_MODEL=gpt-5.6-terra \
SPECSPINE_EVAL_JUDGE_REASONING=medium \
  tests/eval/docker/run-comparisons.sh --experiment value
```

`--experiment` and `--comparison` are repeatable and may be combined. `--all`
runs the complete 36-agent-call pilot budget. `--samples N` overrides the
manifest counts and is intended for smoke verification or deliberate
resampling, not for changing the recorded pilot design silently.

The value experiment has two arms:

1. `native-repository`: the frozen repository and all of its native README,
   Swagger documentation, tests, comments, and configuration; no SpecSpine.
2. `minimal-handoff`: the same repository plus a reviewed `HANDOFF.md` and only
   the required SpecSpine files.

The minimal arm must read `HANDOFF.md` and every supplied primary/required
specification before editing. Required protocol reads are verified from the
adapter trace, so the intervention does not depend on chance discovery of an
unfamiliar root file.

The projection experiment reuses the same task definitions and compares:

1. `full-spine`: native repository plus the complete reviewed Spine.
2. `minimal-handoff`: native repository plus the reviewed projection.

Handoff production supplies the full Spine and `specspine-grow`, prohibits
repository inspection outside the Spine, and evaluates the returned handoff
without running an implementation task.

The repository fixture is a hash-verified archive of
`hagopj13/node-express-boilerplate` commit
`179ae84efec61b14206d0305d941daed6c6d07f9`. It is downloaded once to
`~/.cache/specspine-eval/fixtures`; override this with
`SPECSPINE_EVAL_FIXTURES_DIR`. Agent workspaces do not require network access.

### Docker execution model

The launcher uses the host Docker daemon through its local Unix socket. This is
container-outside-of-container, not a nested daemon: the controller container
is trusted and can create sibling containers, while agent and judge containers
never receive the socket. Do not run an untrusted controller image.

Agent images are named from the SHA-256 of their Dockerfile, adapter, and
preflight script. An exact image is built and preflighted once, then reused.
Every model invocation still gets a new `--rm` container, read-only root
filesystem, dropped capabilities, `no-new-privileges`, resource limits, private
tmpfs home/runtime, and only the current workspace plus read-only authentication
mounted. Docker's default seccomp profile is disabled because it blocks the
unprivileged user namespace required by Codex's bundled `bwrap`; capabilities
remain dropped and `bwrap` supplies the stricter per-command filesystem and
network sandbox. The cached preflight executes both `bwrap` and a local
`codex sandbox` read/write probe with the evaluation permission profile; it
does not make a model call. Thus tools are cached but sample state is not.

Persistent launcher state lives in `.eval-runtime/` and is ignored by Git:
fixture archives, prepared workspaces, Docker preflight markers, and controller
home. Override authentication with `SPECSPINE_EVAL_AUTH_FILE`. The launcher
currently requires a local Unix Docker socket. Docker build or preflight
failures produce `environment_invalid` traces, invalidate the affected sample,
as do recognized command-sandbox failures even when Codex returns exit code 0;
they are never counted as product failures. Reports record the exact agent image
name and immutable image ID; mixed or missing metadata on valid Docker samples
invalidates a run.

For debugging only, the original host adapter remains available:

```bash
python3 tests/eval/compare.py \
  --experiment value \
  --agent-command "python3 $(pwd)/tests/eval/adapters/codex.py --model gpt-5.6-luna --reasoning-effort medium" \
  --judge-command "python3 $(pwd)/tests/eval/adapters/codex.py --model gpt-5.6-terra --reasoning-effort medium"
```

All agent runs finish before judging starts. A judge receives only the
submission type, request, diff, final response and matching frozen rubric; it
cannot see the arm or supplied context. Implementation and handoff production
use separate rubrics. The handoff judge is explicitly told that its required
empty diff is not missing implementation evidence. Each criterion is scored
`0` (violated), `1` (partial/unclear), or `2` (fully satisfied). Identical judge
inputs reuse one judgment.

Mechanical checks are limited to facts requiring no interpretation: command
success, syntax, workspace/read boundaries, required context consumption,
protected-context integrity, and tasks whose only safe outcome is no repository
change. Ownership, blocker meaning, relevance, documentation adequacy,
unrelated scope, and handoff quality belong to the blind judge. Exact response
wording is never a pass condition. Overall pass requires both layers; efficiency
metrics remain independent.

The bundled Codex adapter uses an isolated named permission profile: only the
current workspace is writable/readable beyond minimal operating-system files,
network access is disabled, user config and exec rules are ignored, and secret
environment variables are filtered. Every prompt also forbids leaving the
workspace. Commands containing external-path markers invalidate the sample;
invalid samples are excluded from aggregates and are not judged.
Tool subprocesses receive private HOME, temporary, Git, Python, pip, and XDG
cache/config directories in an ephemeral sibling runtime that is removed after
the agent exits and is not part of repository context. Login shells are
disabled, and inaccessible user-level PATH entries such as pyenv shims are
removed. When available, `node` and `rg` are copied into the permitted
ephemeral runtime so agents can run dependency-free checks and search without
access to user tool directories. Each invocation also receives a private
`CODEX_HOME` containing only a temporary copy of `auth.json`; model cache,
config, rules and memory are not shared between concurrent agents. `.eval` is reserved for evaluator output and
excluded from agent inspection except for requested skill and companion inputs;
commands that explicitly exclude `.eval` from searches remain valid.
The profile was verified with Codex CLI 0.144.4; strict config validation makes
older incompatible CLIs fail instead of silently weakening isolation.

Mechanical or semantic failures are benchmark results and do not cause a
non-zero process exit. Workspace-boundary violations, agent execution errors, missing/invalid
judge responses, and inconsistent observed model settings do. Agent and judge
concurrency default to 8; override them with `--jobs` and `--judge-jobs`.

### Run output

Each execution allocates the next numeric directory:

```text
comparison-runs/<run>/
├── comparison-results.md
├── comparison-results.json
└── artifacts/<comparison>/<arm>/sample-<n>/
```

Both reports are automatic. Use `--markdown-output` or `--json-output` only to
change their filenames, `--runs-dir` to change the parent directory, and
`--artifacts-dir` to rename the artifacts directory.

The Markdown report separates overall, mechanical, and semantic outcomes and
contains the legend, methodology, arm aggregates, individual results and
failure findings. The JSON report additionally preserves
structured prompts, responses, diffs, checks, hashes, read metrics, token usage,
model metadata and artifact paths.

Each sample artifact contains the prompt, response, diff, judge input and parsed
traces. Its `agent/` and, when judging is enabled, `judge/` directories preserve:

- unfiltered Codex `--json` event stream (`codex-events.jsonl`);
- Codex stderr and exact prompt;
- invocation arguments, exit status and duration;
- parsed trace and final response.

The raw stream includes every event exported by Codex CLI, potentially including
reasoning summaries, command output, file changes and tool calls. Hidden model
chain-of-thought and events omitted by Codex itself are unavailable.

See [HYPOTHESIS.md](HYPOTHESIS.md) for the experimental hypothesis and metrics.
