# Scenario: initial brownfield survey

## Initial repository

```text
README.md
AGENTS.md
package.json
apps/web/
apps/api/
apps/worker/
packages/database/
packages/documents/
docker-compose.yml
```

No `<spine-root>/` directory exists. Persistent project instructions require
all SpecSpine documentation to be in English.

## User request

```text
Create a SpecSpine for this repository.
```

## Expected behavior

The skill should:

- inspect high-value repository signals before deep internals;
- identify major runtime components and responsibilities;
- create `<spine-root>/README.md`;
- honor the configured SpecSpine documentation language;
- create a small set of top-level specification nodes;
- distinguish observed facts from inferred architecture;
- record incomplete coverage and open questions;
- avoid mirroring every directory;
- avoid modifying source code.

## Failure indicators

- one specification is created per source directory;
- the first inspected module is documented exhaustively;
- inference is presented as accepted architecture;
- the result claims complete coverage;
- implementation details dominate the specifications.
