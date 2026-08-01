# Usage and lifecycle

Use IWE for every document operation:

```bash
iwe create --template specification --var title="Authentication"
iwe find --filter 'kind: component'
iwe retrieve -k authentication --children --backlinks
iwe tree
iwe rename authentication identity
iwe delete identity
iwe schema validate
```

Use `iwe extract`, `iwe inline`, and editor code actions to split or consolidate
content. Do not edit links in bulk with Specspine scripts.

An inclusion link placed on its own line creates parent/child structure. Inline
links create references and backlinks. Inspect them with `iwe tree`,
`iwe find --included-by`, `--references`, and `--referenced-by`.
