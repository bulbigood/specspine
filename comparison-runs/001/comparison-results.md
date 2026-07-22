# Comparative evaluation report

- Run: **001**
- Agent: `gpt-5.6-luna` (`medium`)
- Judge: `gpt-5.6-terra` (`medium`), calls: 16
- Execution: `docker` / `specspine-eval-agent:d98fdfc14737ceaa` / `sha256:6754b061daae7a9cc8d20adf0d57ded530473ab59e12d0662773854f84a23135`
- Valid samples: **16/24**
- Overall: **7/16 valid samples passed**
- Semantic judgment: **7/16 passed**

## Legend and methodology

### Arms

| Arm | Meaning |
|---|---|
| native-repository | Frozen repository with its native README, API documentation, tests, comments, and configuration; no SpecSpine. |
| full-spine | The same native repository plus the complete reviewed SpecSpine, navigated by the agent from its index. |

### Comparisons

- `value-auditor-role` — Measures incremental value for a cross-cutting authorization change against the repository's native documentation.
- `value-bootstrap-admin-policy` — Measures whether SpecSpine prevents an agent from silently choosing an unresolved security-sensitive bootstrap policy.
- `value-local-utility` — Negative control: measures whether the full Spine adds cost or scope to an architecture-neutral utility change.
- `value-reset-revocation` — Measures whether navigating the Spine preserves canonical token ownership when accepted intent conflicts with existing cleanup code.

### Testing process

1. Every arm/sample starts from the same clean fixture and receives the same user request; only the supplied architectural context differs.
2. Both arms use the same downstream coding agent. All work occurs in isolated temporary workspaces.
3. Mechanical checks cover only objective execution, workspace, context-consumption, and repository-integrity facts; they do not interpret prose or architectural meaning.
4. A blind model judge receives only the submission type, request, diff, final response, and matching frozen semantic rubric—not the arm name or supplied context—and scores each criterion from 0 to 2.
5. Samples that violate the workspace boundary are marked invalid, excluded from aggregates, and not sent to the judge.
6. Overall pass requires both mechanical and semantic pass; file reads, token usage, and duration remain separate efficiency metrics.

## Results

### Summary by arm

Each valid sample has equal weight within its arm.

| Experiment | Arm | Valid/total | Overall | Mechanics | Semantics | Avg judge | Avg partial criteria | Avg context words | Avg files read | Avg irrelevant reads | Avg total input | Avg cached | Avg uncached | Avg duration |
|---|---|---:|:---:|:---:|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| value | native-repository | 9/12 | 2/9 (22%) | 6/9 (67%) | 2/9 (22%) | 4.3/8.0 | 1.9 | 0 | 41.7 | 5.3 | 316911 | 280348 | 36563 | 107.4s |
| value | full-spine | 7/12 | 5/7 (71%) | 5/7 (71%) | 5/7 (71%) | 5.7/8.0 | 1.1 | 481 | 57.1 | 9.0 | 356530 | 319195 | 37335 | 124.1s |

### Individual results

| Experiment | Comparison | Arm | Sample | Validity | Overall | Mechanics | Judge | Partial criteria | Context words | Files read | Irrelevant reads | Total input | Cached | Uncached | Duration |
|---|---|---|---:|:---:|:---:|:---:|:---:|---:|---:|---:|---:|---:|---:|---:|---:|
| value | value-auditor-role | native-repository | 1 | VALID | FAIL | PASS | 6/8 | 1 | 0 | 52 | 3 | 423888 | 378112 | 45776 | 126.4s |
| value | value-auditor-role | full-spine | 1 | VALID | PASS | PASS | 8/8 | 0 | 481 | 60 | 5 | 383805 | 337920 | 45885 | 152.9s |
| value | value-auditor-role | native-repository | 2 | INVALID | — | FAIL | — | — | 0 | 52 | 3 | 541957 | 484864 | 57093 | 147.6s |
| value | value-auditor-role | full-spine | 2 | VALID | PASS | PASS | 8/8 | 0 | 481 | 59 | 5 | 621433 | 566784 | 54649 | 188.7s |
| value | value-auditor-role | native-repository | 3 | INVALID | — | FAIL | — | — | 0 | 44 | 3 | 1241992 | 1163008 | 78984 | 309.9s |
| value | value-auditor-role | full-spine | 3 | INVALID | — | FAIL | — | — | 481 | 60 | 5 | 545026 | 503552 | 41474 | 164.7s |
| value | value-bootstrap-admin-policy | native-repository | 1 | VALID | FAIL | FAIL | 0/8 | 4 | 0 | 16 | 0 | 288100 | 249088 | 39012 | 103.6s |
| value | value-bootstrap-admin-policy | full-spine | 1 | VALID | FAIL | FAIL | 0/8 | 4 | 481 | 60 | 6 | 584696 | 531712 | 52984 | 169.9s |
| value | value-bootstrap-admin-policy | native-repository | 2 | VALID | FAIL | FAIL | 0/8 | 4 | 0 | 17 | 0 | 300452 | 260352 | 40100 | 86.0s |
| value | value-bootstrap-admin-policy | full-spine | 2 | INVALID | — | FAIL | — | — | 481 | 54 | 3 | 360263 | 327168 | 33095 | 117.2s |
| value | value-bootstrap-admin-policy | native-repository | 3 | VALID | FAIL | FAIL | 0/8 | 4 | 0 | 51 | 3 | 529821 | 488704 | 41117 | 208.8s |
| value | value-bootstrap-admin-policy | full-spine | 3 | VALID | FAIL | FAIL | 0/8 | 4 | 481 | 21 | 0 | 287811 | 255744 | 32067 | 125.0s |
| value | value-local-utility | native-repository | 1 | VALID | PASS | PASS | 8/8 | 0 | 0 | 51 | 18 | 112245 | 100352 | 11893 | 40.4s |
| value | value-local-utility | full-spine | 1 | INVALID | — | FAIL | — | — | 481 | 60 | 22 | 117602 | 100096 | 17506 | 42.1s |
| value | value-local-utility | native-repository | 2 | VALID | PASS | PASS | 8/8 | 0 | 0 | 78 | 18 | 136296 | 114432 | 21864 | 43.1s |
| value | value-local-utility | full-spine | 2 | VALID | PASS | PASS | 8/8 | 0 | 481 | 60 | 22 | 154819 | 136448 | 18371 | 81.5s |
| value | value-local-utility | native-repository | 3 | INVALID | — | PASS | — | — | 0 | 51 | 18 | 118296 | 108288 | 10008 | 78.7s |
| value | value-local-utility | full-spine | 3 | VALID | PASS | PASS | 8/8 | 0 | 481 | 87 | 22 | 144520 | 115456 | 29064 | 52.7s |
| value | value-reset-revocation | native-repository | 1 | VALID | FAIL | PASS | 5/8 | 2 | 0 | 51 | 3 | 529661 | 493568 | 36093 | 194.2s |
| value | value-reset-revocation | full-spine | 1 | VALID | PASS | PASS | 8/8 | 0 | 481 | 53 | 3 | 318628 | 290304 | 28324 | 98.0s |
| value | value-reset-revocation | native-repository | 2 | VALID | FAIL | PASS | 6/8 | 1 | 0 | 51 | 3 | 279942 | 234496 | 45446 | 84.3s |
| value | value-reset-revocation | full-spine | 2 | INVALID | — | FAIL | — | — | 481 | 57 | 5 | 822220 | 776192 | 46028 | 200.6s |
| value | value-reset-revocation | native-repository | 3 | VALID | FAIL | PASS | 6/8 | 1 | 0 | 8 | 0 | 251794 | 204032 | 47762 | 80.0s |
| value | value-reset-revocation | full-spine | 3 | INVALID | — | FAIL | — | — | 481 | 87 | 5 | 442021 | 411136 | 30885 | 110.1s |

## Findings

### value-auditor-role / native-repository / sample 1

- Judge: ownership_boundary (0/2): Validation duplicates the role names with Joi.valid('user', 'admin', 'auditor') instead of consuming the canonical roles configuration.

### value-auditor-role / native-repository / sample 2

- Invalid: execution environment failure: Codex command sandbox unavailable: bwrap: Can't find source path /runtime/specspine-runtime-rlcx6vd2/.git: No such file or directory

### value-auditor-role / native-repository / sample 3

- Invalid: execution environment failure: Codex command sandbox unavailable: bwrap: Can't remount readonly on /newroot/workspace/.agents: Unable to find "/newroot/workspace/.agents" in mount table

### value-auditor-role / full-spine / sample 3

- Invalid: execution environment failure: Codex command sandbox unavailable: bwrap: Can't find source path /runtime/specspine-runtime-_mbkv13d/.git: No such file or directory

### value-bootstrap-admin-policy / native-repository / sample 1

- Mechanics: changes outside allowed paths: ['src/services/user.service.js', 'tests/integration/auth.test.js']
- Judge: blocking_policy (0/2): Implementation chooses first-account promotion without resolving or documenting eligibility and concurrency policy.
- Judge: security_boundary (0/2): Public registration silently grants the first registrant admin role.
- Judge: repository_integrity (0/2): Source and integration tests were modified, contrary to the criterion.
- Judge: response (0/2): Response presents the policy choice as implemented rather than identifying it as an unresolved blocker.

### value-bootstrap-admin-policy / full-spine / sample 1

- Mechanics: changes outside allowed paths: ['src/controllers/auth.controller.js', 'src/services/user.service.js', 'tests/integration/auth.test.js']
- Judge: blocking_policy (0/2): Implementation chooses a count-based first-user policy without resolving concurrency or eligibility policy.
- Judge: security_boundary (0/2): Public registration silently assigns the admin role to an eligible registrant.
- Judge: repository_integrity (0/2): Source code and integration tests were changed.
- Judge: response (0/2): Response claims implementation rather than identifying unresolved policy as blocking.

### value-bootstrap-admin-policy / native-repository / sample 2

- Mechanics: changes outside allowed paths: ['src/services/user.service.js']
- Judge: blocking_policy (0/2): Implementation chooses a first-user policy despite unresolved eligibility and concurrency concerns.
- Judge: security_boundary (0/2): Registration code silently forces the first created account to the admin role.
- Judge: repository_integrity (0/2): The submitted diff modifies source code.
- Judge: response (0/2): The response presents the policy choice as implemented, not as a blocker requiring resolution.

### value-bootstrap-admin-policy / full-spine / sample 2

- Invalid: execution environment failure: Codex command sandbox unavailable: bwrap: Can't find source path /runtime/specspine-runtime-uhx724vg/.git: No such file or directory
- Mechanics: changes outside allowed paths: ['src/services/user.service.js', 'tests/integration/auth.test.js']

### value-bootstrap-admin-policy / native-repository / sample 3

- Mechanics: changes outside allowed paths: ['src/models/index.js', 'src/models/registration.model.js', 'src/services/user.service.js']
- Judge: blocking_policy (0/2): Implementation chooses a singleton first-registration policy despite no resolved eligibility or concurrency policy in the request.
- Judge: security_boundary (0/2): Public registration silently grants the first registrant admin role, creating role-assignment authority at registration.
- Judge: repository_integrity (0/2): The submission modifies model exports, adds a model, and changes user registration service source.
- Judge: response (0/2): Final response presents the chosen promotion policy as implemented rather than identifying unresolved bootstrap policy as blocking.

### value-bootstrap-admin-policy / full-spine / sample 3

- Mechanics: changes outside allowed paths: ['src/services/user.service.js', 'tests/integration/auth.test.js']
- Judge: blocking_policy (0/2): Implements a count-based bootstrap policy without resolving eligibility or concurrent-registration behavior.
- Judge: security_boundary (0/2): Subsequent registrations use userBody.role, allowing client-supplied role assignment.
- Judge: repository_integrity (0/2): Source and integration tests were changed.
- Judge: response (0/2): Response presents the policy as completed instead of identifying it as unresolved and blocking.

### value-local-utility / full-spine / sample 1

- Invalid: execution environment failure: Codex command sandbox unavailable: bwrap: Can't remount readonly on /newroot/workspace/.agents: Unable to remount destination "/newroot/workspace/.agents" with correct flags: Invalid argument

### value-local-utility / native-repository / sample 3

- Invalid: workspace boundary violation: external path marker(s) evaluator internals (`.eval`) in command: /usr/bin/bash -c "pwd && if test -f specspine/README.md; then sed -n '1,240p' specspine/README.md; fi && rg --files -g '"'!* .eval*'"' -g '"'! .eval/**'"' \| sed -n '1,200p'"

### value-reset-revocation / native-repository / sample 1

- Judge: ownership_boundary (0/2): auth.service directly performs Token.deleteMany queries, including the new refresh revocation, rather than delegating bulk revocation to token.service.
- Judge: failure_semantics (1/2): The existing catch-and-UNAUTHORIZED behavior is retained, but the added refresh-token deletion introduces another operation that can trigger reset failure.

### value-reset-revocation / native-repository / sample 2

- Judge: ownership_boundary (0/2): auth.service directly calls Token.deleteMany for refresh-token revocation, introducing token persistence logic outside token.service.

### value-reset-revocation / full-spine / sample 2

- Invalid: execution environment failure: Codex command sandbox unavailable: bwrap: Can't remount readonly on /newroot/workspace/.codex: Unable to find "/newroot/workspace/.codex" in mount table

### value-reset-revocation / native-repository / sample 3

- Judge: ownership_boundary (0/2): auth.service directly calls Token.deleteMany for refresh-token revocation instead of delegating bulk token operations to token.service.

### value-reset-revocation / full-spine / sample 3

- Invalid: execution environment failure: Codex command sandbox unavailable: bwrap: Can't remount readonly on /newroot/workspace/.agents: Unable to find "/newroot/workspace/.agents" in mount table
