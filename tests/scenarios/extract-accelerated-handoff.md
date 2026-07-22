# Scenario: extract a minimal handoff through accelerated retrieval

## Existing specification

RelayHub has a 63-document SpecSpine for a multi-tenant integration platform.
Its dense graph separates connector contracts, provider quota coordination,
durable step attempts, retry policy, background scheduling, and idempotent
business effects. Several unrelated areas use the same operational vocabulary.

## User request

```text
Prepare the smallest architecture context handoff for downstream work that will
change retry policy so a connector action can retry after provider throttling
without duplicating business effects. Use only the SpecSpine as architecture
authority and do not modify project files.
```

## Expected behavior

The skill should attempt accelerated retrieval, read the current Markdown
owners, and distinguish retry policy from provider quota coordination,
scheduling mechanics, attempt state, and idempotency. The handoff should retain
the relevant semantic constraints while excluding unrelated billing, identity,
and operations areas.

## Failure indicators

- the retrieval accelerator is not attempted despite being available;
- execution retry policy is not identified as the primary owner;
- rate-limit, scheduling, or idempotency boundaries are lost;
- routing output is treated as architecture authority without reading Markdown;
- unrelated documents dominate the handoff;
- project files are modified or an implementation plan is produced.
