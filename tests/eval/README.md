# SpecSpine evaluation

The directory contains two independent harnesses:

- `run.py` checks SpecSpine skills against deterministic case manifests;
- Docker comparisons measure whether navigating a SpecSpine documentation graph
  improves downstream coding outcomes over a normally documented repository.

The Python harnesses use only the standard library. Live runs require Docker,
the Codex CLI bundled in the agent image, and Codex authentication.

## Validation

```bash
python3 tests/eval/run.py --validate --audit
python3 -m unittest discover -s tests/eval -p 'test_*.py'
tests/eval/docker/run-comparisons.sh --validate --list
tests/eval/docker/run-comparisons.sh --preflight
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
implicit run-all mode. Planned cases are never executed. Categories are
disjoint: `core` has 10 executable cases, `extended` has 3, and `planned` has
11 documented non-executable cases.

Each case gets a clean temporary workspace. Cases run with concurrency 8 by
default; change it with `--jobs N`. Workspaces default to
`~/.cache/specspine-eval/workspaces`; override with
`SPECSPINE_EVAL_WORKSPACES_DIR`. Failed workspaces are retained only with
`--keep-workspace`.

Case manifests in `cases/*.json` define fixtures, prompts and deterministic
assertions. A manifest may instead define ordered `stages`; agent stages run a
prompt and assertions, while fixture stages model external changes.

Supported assertions:

- paths/content: `path_exists`, `path_absent`, `glob_count`, `glob_contains`,
  `file_contains`, `file_not_contains`;
- response: `response_contains`, `response_not_contains`;
- changes: `unchanged`, `changed_only`, `max_changed_files`;
- execution: `command_succeeds`;
- trace: `read_only`, `read_includes`, `max_files_read`;
- structure: `balanced_markers`, `no_template_placeholders`,
  `markdown_links_valid`, `semantic_ids_valid`, `spine_mechanical_valid`.

Trace assertions require `.eval/trace.json`. The Codex adapter conservatively
infers reads from completed command events; repository-wide content searches
may count every candidate file as read.

## Comparative evaluation

Comparisons have one experiment, `value`, and four task classes:

- `local-utility`: architecture-neutral negative control;
- `auditor-role`: cross-cutting authorization vocabulary;
- `reset-revocation`: accepted token ownership versus existing code;
- `bootstrap-admin-policy`: unresolved security-sensitive policy.

Every task compares exactly two arms:

1. `native-repository`: the frozen repository with its native documentation,
   tests, comments and configuration, without SpecSpine;
2. `full-spine`: the identical repository plus the complete reviewed Spine.

The downstream prompt is byte-identical. When `specspine/README.md` exists, the
agent must read it and navigate the documentation graph itself. No task-specific
context is preselected and no external context tool is involved.

The default pilot uses three samples per arm: 4 tasks × 2 arms × 3 samples = 24
agent calls and up to 24 blind-judge calls. First run the cheaper smoke:

```bash
tests/eval/docker/run-comparisons.sh --all --samples 1
```

Then run the manifest-defined pilot:

```bash
tests/eval/docker/run-comparisons.sh --all
```

Individual selections are repeatable:

```bash
tests/eval/docker/run-comparisons.sh \
  --comparison value-auditor-role \
  --comparison value-reset-revocation

tests/eval/docker/run-comparisons.sh --experiment value
```

### Models

Defaults are `gpt-5.6-luna` at medium reasoning for the agent and
`gpt-5.6-terra` at medium reasoning for the independent judge. Keep a pairing
fixed within a run. Override it with environment variables:

```bash
SPECSPINE_EVAL_AGENT_MODEL=gpt-5.6-luna \
SPECSPINE_EVAL_AGENT_REASONING=medium \
SPECSPINE_EVAL_JUDGE_MODEL=gpt-5.6-terra \
SPECSPINE_EVAL_JUDGE_REASONING=medium \
  tests/eval/docker/run-comparisons.sh --all --samples 1
```

Set `SPECSPINE_EVAL_NO_JUDGE=1` to omit judging. Override the authentication
file with `SPECSPINE_EVAL_AUTH_FILE`.

### Launcher arguments

`run-comparisons.sh` is the only supported comparison entry point. It forwards
all comparison arguments unchanged to the controller:

- discovery: `--list`, `--validate`;
- selection: repeatable `--comparison ID`, repeatable `--experiment value`, or
  `--all`;
- execution: `--samples N`, `--jobs N`, `--judge-jobs N`, `--keep-workspace`;
- output: `--runs-dir PATH`, `--artifacts-dir NAME`,
  `--json-output NAME`, `--markdown-output NAME`;
- advanced adapter override: `--agent-command COMMAND`,
  `--judge-command COMMAND`.

Both `--option value` and argparse's `--option=value` form are preserved. The
advanced command overrides execute inside the Docker controller and therefore
must reference tools and paths available there. Direct `compare.py` execution
is rejected to prevent accidental host runs.

### Docker execution model

The trusted controller uses the host's local Unix Docker socket to create
sibling agent containers. Agent and judge containers never receive the socket.
Each model invocation gets a fresh `--rm` container with a read-only root,
dropped capabilities, `no-new-privileges`, CPU/RAM/PID limits, private tmpfs
home/runtime, one writable workspace, and read-only authentication.

Docker's default seccomp profile is disabled because Codex's bundled `bwrap`
needs an unprivileged user namespace. Capabilities remain dropped and `bwrap`
provides the stricter per-command filesystem and network sandbox. The adapter
materializes Codex's protected `.git`, `.agents`, and `.codex` mountpoints for
the lifetime of each invocation, then removes empty placeholders. Preflight
executes `bwrap` and 12 concurrent local `codex sandbox` read/write probes with
the exact evaluation permission profile; it makes no model call:

```bash
tests/eval/docker/run-comparisons.sh --preflight
```

Agent images are named from the SHA-256 of their Dockerfile, adapter and
preflight inputs. Exact images and successful preflight markers are reused;
sample containers and runtime state are not. Persistent caches live in
`.eval-runtime/` and are ignored by Git.

Recognized sandbox/build/preflight failures populate `environment_errors`, mark
the sample invalid, exclude it from aggregates and prevent judging. Reports
record the exact image name and immutable image ID.

### Evaluation and output

Mechanical checks cover executable behavior, syntax, required Spine-index
consumption and context integrity. Architecture, ownership, blockers and
unrelated scope are scored by a blind judge that receives only the request,
diff, final response and frozen rubric. Overall pass requires both layers;
read counts, tokens, duration and cost remain independent efficiency metrics.

Each run allocates the next numeric directory:

```text
comparison-runs/<run>/
├── comparison-results.md
├── comparison-results.json
└── artifacts/<comparison>/<arm>/sample-<n>/
```

Reports preserve prompts, responses, diffs, checks, hashes, read metrics, token
usage, model metadata and artifact paths. Per-sample agent/judge directories
also contain the raw Codex JSONL stream, stderr, invocation metadata and trace.

See [HYPOTHESIS.md](HYPOTHESIS.md) for the experimental claim and thresholds.
