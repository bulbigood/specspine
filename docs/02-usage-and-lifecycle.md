# Usage and lifecycle

Initialize IWE with `docs` as the library, then use IWE for every document and graph operation:

``` bash
iwe init --auto --library docs
iwe create --template specification --var title="Authentication" --strict
iwe find --filter 'kind: component'
iwe retrieve -k specs/authentication --children --backlinks
iwe tree
iwe rename specs/authentication specs/identity
iwe delete specs/identity
iwe schema validate
```

Use `iwe extract`, `iwe inline`, and editor code actions to split or consolidate content. Do not edit links in bulk with Specspine-specific scripts.

An inclusion link is the only content of its paragraph. Inline links create references and backlinks. Inspect the graph with `iwe tree`, `iwe find`, and `iwe retrieve`; select only the neighborhood required by the task.
