# SpecSpine evaluation

The evaluation directory contains two independent harnesses:

- `run.py` checks SpecSpine skills against deterministic case manifests.
- `compare.py` compares architectural-context strategies on downstream coding
  tasks using deterministic checks and an optional blind model judge.

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

Run all comparisons with repeated samples:

```bash
python3 tests/eval/compare.py \
  --all \
  --samples 5 \
  --agent-command "python3 $(pwd)/tests/eval/adapters/codex.py --model gpt-5.6-luna --reasoning-effort medium" \
  --judge-command "python3 $(pwd)/tests/eval/adapters/codex.py --model gpt-5.6-terra --reasoning-effort medium"
```

Use repeatable `--comparison ID` instead of `--all` to select scenarios. The
four current scenarios are `blocking-question`, `cross-cutting-change`,
`intended-observed-conflict`, and `local-change`.

Every sample uses the same frozen fixture and request across four arms, ordered
from least to most supplied context:

1. `repository-only`: repository and request; no architecture files.
2. `architecture-document`: repository, request, and one monolithic
   `ARCHITECTURE.md`.
3. `minimal-handoff`: repository, request, task-specific `HANDOFF.md`, and only
   the SpecSpine files referenced by it.
4. `full-spine`: repository, request, and the complete SpecSpine graph,
   including deliberately unrelated specifications.

All agent runs finish before judging starts. A judge receives only the request,
diff, final response and frozen rubric; it cannot see the arm or supplied
context. Each rubric criterion is scored `0` (violated), `1` (partial/unclear),
or `2` (fully satisfied). Identical judge inputs reuse one judgment.

The bundled Codex adapter uses an isolated named permission profile: only the
current workspace is writable/readable beyond minimal operating-system files,
network access is disabled, user config and exec rules are ignored, and secret
environment variables are filtered. Every prompt also forbids leaving the
workspace. Commands containing external-path markers invalidate the sample;
invalid samples are excluded from aggregates and are not judged.
The profile was verified with Codex CLI 0.144.4; strict config validation makes
older incompatible CLIs fail instead of silently weakening isolation.

Deterministic failures are benchmark results and do not cause a non-zero process
exit. Workspace-boundary violations, agent execution errors, missing/invalid
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

The Markdown report contains the legend, methodology, arm aggregates,
individual results and failure findings. The JSON report additionally preserves
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
