# Acceptance and reconstruction

The workspace Specspine schema gate proves format conformance. Semantic
readiness additionally requires:

- an empty `blockers` list;
- every applicable facet to be `complete` or `not-applicable`;
- every blocker ID to name an `OQ-*` statement in the same owner;
- every semantic ID to be unique within its owner;
- every exhaustive external boundary to have a valid owner-local `CON-*` basis;
- every registered asset path and verification target to be safe and resolvable;
- every complete verification facet to have owner-local verification support;
- completeness claims to agree with the document's actual accepted content.

The IWE schema enforces kind-dependent facet applicability, exhaustive-basis shape, and safe asset-path shape. Cross-statement and filesystem conditions remain native-IWE semantic audit checks. Do not add a second Markdown parser or lifecycle engine to enforce them.

Ask an applicable IWE skill for the owner and task-relevant graph neighborhood
needed to reconstruct the boundary. Describe the required relationships and
result, not commands, flags, traversal mechanics, or budgets.

Verification criteria describe observable outcomes without prescribing private implementation details. Verifying conformance still requires comparing those criteria and other normative claims with implementation evidence. Schema validity alone does not prove implementation conformance.
