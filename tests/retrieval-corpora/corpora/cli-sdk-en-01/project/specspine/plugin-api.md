# Plugin API

## Responsibility

This specification owns plugin discovery, activation, and extension contracts.

## Discovery

Plugins are found through explicit manifest paths and the user plugin
directory. Directory entries are sorted before loading. Duplicate plugin IDs
are rejected; an explicit manifest does not silently shadow an installed
plugin.

## Compatibility

Every manifest declares an API range. The host compares that range with the
plugin API version before loading code. Minor additions are backward
compatible; a major API mismatch disables the plugin and returns a structured
diagnostic. Plugins may register commands, migration readers, and renderers,
but cannot intercept credentials or lease operations.

<!-- specspine:semantic-ids:begin -->
## Decisions

- **DEC-plugin-api-range** — Compatibility is negotiated from the declared API
  range before plugin code is loaded.
<!-- specspine:semantic-ids:end -->

## Relationships

- [Command dispatch](command-dispatch.md)
- [Release compatibility](release-compatibility.md)
- [Error contract](error-contract.md)
