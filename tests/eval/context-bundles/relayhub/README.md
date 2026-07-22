# RelayHub Extract benchmark corpus

This bundle is the persistent large-document fixture for the existing
`extract-accelerated-handoff` A/B case. `full-spine/specspine/` contains 63
linked Markdown specifications for RelayHub, a multi-tenant integration SaaS.

The corpus was mapped and grown from
`hagopj13/node-express-boilerplate` at commit
`179ae84efec61b14206d0305d941daed6c6d07f9` on 2026-07-22. It deliberately
contains both observed starter-runtime facts and accepted intended architecture.
Only the SpecSpine is retained because Extract's source boundary excludes the
implementation repository.

The case manifest references `full-spine` through `initial_tree`. Do not embed a
second copy in JSON. Corpus edits automatically change the case fingerprint and
must preserve mechanical Spine health.
