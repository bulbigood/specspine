# Configuration resolution

## Responsibility

This specification owns how effective configuration is selected.

## Precedence

Sources are applied from lowest to highest priority: built-in defaults,
configuration file, selected profile, environment variables, then command-line
flags. An explicit `null` in a higher layer unsets an inherited optional value;
an empty string remains a value. Unknown keys fail validation after all layers
are merged.

Secrets are represented by references and resolved only after precedence is
complete. Diagnostic output may name a winning source but must not print its
secret value.

<!-- specspine:semantic-ids:begin -->
## Constraints

- **CON-config-explicit-unset** — A higher-priority explicit null removes an
  inherited optional setting instead of revealing the lower value.
<!-- specspine:semantic-ids:end -->

## Relationships

- [Profile inheritance](profile-inheritance.md)
- [Credential store](credential-store.md)
- [Command dispatch](command-dispatch.md)
