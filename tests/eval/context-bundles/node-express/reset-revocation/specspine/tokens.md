# Tokens

Owns generation, persistence, verification, consumption, and bulk revocation of authentication tokens.

<!-- specspine:semantic-ids:begin -->
## Constraints

- **CON-token-ownership** — Token storage queries and token-type selection remain encapsulated by the token capability; authentication workflows call that capability instead of duplicating persistence queries.
<!-- specspine:semantic-ids:end -->
