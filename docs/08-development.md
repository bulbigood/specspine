# Development

The executable contract is the IWE preset in
`skills/specspine-doctor/assets/iwe`. It is packaged with Doctor.

Run:

```bash
python3 tests/run_mechanical.py
```

The tests install the preset into an isolated copy of
`examples/node-express-boilerplate`, then exercise IWE schema validation,
inclusion hierarchy, references, creation, and rename behavior.

Do not add a second Markdown parser or graph implementation. Extend the IWE
document schema first. Add custom code only for a requirement that IWE cannot
express and that remains important after simplifying the format.
