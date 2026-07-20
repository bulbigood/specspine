# Scenario: adapt SpecSpine to an existing SDD workflow

## Initial project

`architecture/README.md` is an existing SpecSpine index. Project instructions
declare `architecture` as `<spine-root>`. The repository contains an installed
SDD framework with local manifests, instructions, templates, and a native
workflow. Its feature artifacts use framework-specific paths and names.

## User request

```text
Initialize SpecSpine integration for this agent and its current SDD framework.
```

## Expected behavior

The skill should:

- use `architecture` rather than the default root;
- inspect the agent and SDD integration metadata but not source code or feature
  contents;
- identify native downstream terms and paths only when supported by evidence;
- show the bootstrap, compact binding path, complete runtime binding, and open
  decisions before writing;
- bind the exact native workflow entry, downstream stage, artifact paths,
  work-item naming rule, format source, context insertion point, traceability
  rule, and conflict destination;
- generate a compact binding that carries minimal relevant SpecSpine context
  into the native SDD stage without generating another skill;
- keep canonical SpecSpine filenames and format unchanged;
- preserve exact claims through ordinary paths and semantic IDs when present;
- leave installed third-party skills untouched.

## Failure indicators

- the original SDD skill is copied, fused, patched, or replaced;
- a project-local integration skill or product metadata is generated;
- framework conventions are guessed from a directory name alone;
- a required runtime field is delegated to vague free-form mapping;
- the binding contains an unresolved `{{...}}` placeholder;
- feature specifications become the architectural source of truth;
- SpecSpine documents are converted into the framework's format;
- the skill claims a maintained compatibility guarantee;
- changes are applied before approval.
