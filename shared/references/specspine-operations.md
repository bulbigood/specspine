# Specspine IWE operations

Specspine workflows use the installed IWE CLI as their only search, graph, and refactoring runtime. The recipes below target IWE 0.18 and later CLIs that expose the same flags.

## Compatibility gate

From the resolved IWE project root, run once per workflow:

``` bash
iwe --version
iwe find --help
iwe retrieve --help
```

Require `find` to expose `--fuzzy`, `--lexical`, `--limit`, `--max-tokens`, and `--max-document-tokens`. Require `retrieve` to expose the four `--expand-*` flags plus `--limit`, `--max-documents`, `--max-tokens`, and `--max-document-tokens`. If a required feature is absent, stop and report an IWE compatibility failure. Do not guess an old positional or depth syntax.

Run help again only after an option rejection or a deprecation warning. Switch to the installed syntax once and do not repeat a rejected form.

## Bounded discovery

Use fuzzy search for a title or key and lexical search for body concepts. Never use deprecated positional search.

``` bash
iwe find --fuzzy '<title-or-key>' --limit 8 -f json
iwe find --lexical '<concept terms>' --limit 8 \
  --add-fields 'body=$content' --max-tokens 4000 \
  --max-document-tokens 1000 -f json
```

Combine `--fuzzy` and `--lexical` only when both rankings materially help. Increase a limit or token budget only after the bounded result demonstrates that a required candidate was clipped. Record the reason for the increase.

## Task-bounded closure

Start with the selected canonical owner. Add graph directions deliberately:

- `--expand-included-by 1` for governing parent context;
- `--expand-includes 1` only for child responsibilities plausibly affected;
- `--expand-references 1` when a normative claim depends on referenced owners;
- `--expand-referenced-by 1` only for impact analysis of consumers.

A representative maximum closure is:

``` bash
iwe retrieve -k <owner-key> --expand-included-by 1 \
  --expand-includes 1 --expand-references 1 --expand-referenced-by 1 \
  --limit 1 --max-documents 12 --max-tokens 8000 \
  --max-document-tokens 2000 -f markdown
```

Omit irrelevant expansion flags rather than retrieving every direction by default. A truncated result is not relationally closed. When IWE reports truncation, list the omitted or clipped context and either justify a bounded second retrieval or report the uncertainty.

For every selected closure, name:

1. the seed owner;
2. each governing parent included and why;
3. each referenced or referencing owner included and why;
4. plausible candidates deliberately excluded;
5. any budget or truncation uncertainty.

## Writes

Use IWE structural commands for graph-aware changes: `create`, `rename`, `delete`, `extract`, and `inline`. Use `update` for frontmatter. Run the exact command's help before a destructive or unfamiliar operation, use its preview mode when available, and validate the affected owners after each write batch.
