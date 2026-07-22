# Comparative evaluation report

- Run: **001**
- Agent: `gpt-5.6-luna` (`medium`)
- Judge: `gpt-5.6-terra` (`medium`), calls: 16
- Valid samples: **16/16**
- Outcome: **6/16 valid samples passed**
- Architecture: **6/16 passed**

## Legend and methodology

### Arms

| Arm | Meaning |
|---|---|
| native-repository | Frozen repository with its native README, API documentation, tests, comments, and configuration; no SpecSpine. |
| minimal-handoff | The same native repository plus a reviewed HANDOFF.md and only its required SpecSpine specifications. |
| full-spine | The same native repository plus the complete reviewed SpecSpine; no task handoff. |
| generated-handoff | The complete reviewed SpecSpine and specspine-grow skill; the agent produces a task-oriented handoff without implementing the change. |

### Comparisons

- `production-auditor-role` — Checks primary-owner and required-context selection for a cross-cutting authorization handoff.
- `production-bootstrap-admin-policy` — Checks that handoff production preserves the unresolved bootstrap decision as a blocker.
- `production-local-utility` — Checks that handoff production identifies an architecture-neutral utility owner without importing unrelated context.
- `production-reset-revocation` — Checks that generated context preserves the token ownership constraint and the intended-versus-observed conflict.
- `projection-auditor-role` — Tests whether the reviewed role handoff retains the value of navigating the complete Spine at lower context cost.
- `projection-reset-revocation` — Tests handoff non-inferiority and context efficiency for an intended-versus-observed token ownership conflict.
- `value-auditor-role` — Measures incremental value for a cross-cutting authorization change against the repository's native documentation.
- `value-bootstrap-admin-policy` — Measures whether SpecSpine prevents an agent from silently choosing an unresolved security-sensitive bootstrap policy.
- `value-local-utility` — Negative control: measures whether a handoff adds cost or scope to an architecture-neutral utility change.
- `value-reset-revocation` — Measures whether a handoff preserves canonical token ownership when accepted intent conflicts with existing cleanup code.

### Testing process

1. Every arm/sample starts from the same clean fixture and receives the same user request; only the supplied architectural context differs.
2. Value and projection runs use a downstream coding agent; handoff-production runs use specspine-grow without implementation. All work occurs in isolated temporary workspaces.
3. A blind model judge receives only the request, diff, final response, and frozen rubric—not the arm name or supplied context—and scores each rubric criterion from 0 to 2.
4. Samples that violate the workspace boundary are marked invalid, excluded from aggregates, and not sent to the judge.
5. Outcome, architectural scores, file reads, token usage, and duration are aggregated by arm with every valid sample weighted equally.

## Results

### Summary by arm

Rows are grouped by experiment. Arms from different experiments are never interpreted as a direct comparison; each valid sample has equal weight within its row.

A mismatch means deterministic outcome and architectural judgment disagree; it is a diagnostic signal, not an overwritten score.

| Experiment | Arm | Valid/total | Outcome | Architecture | Mismatches | Avg judge | Avg violations | Avg context words | Avg files read | Avg irrelevant reads | Avg total input | Avg cached | Avg uncached | Avg duration |
|---|---|---:|:---:|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| value | native-repository | 4/4 | 1/4 (25%) | 1/4 (25%) | 0 | 5.0/8.0 | 1.5 | 0 | 8.8 | 0.0 | 203004 | 177856 | 25148 | 55.0s |
| value | minimal-handoff | 4/4 | 1/4 (25%) | 2/4 (50%) | 1 | 5.5/8.0 | 1.2 | 136 | 45.5 | 5.2 | 184477 | 156736 | 27741 | 54.4s |
| projection | minimal-handoff | 2/2 | 0/2 (0%) | 1/2 (50%) | 1 | 6.5/8.0 | 1.0 | 166 | 14.0 | 0.0 | 220033 | 184960 | 35073 | 56.1s |
| projection | full-spine | 2/2 | 0/2 (0%) | 1/2 (50%) | 1 | 7.0/8.0 | 0.5 | 481 | 10.0 | 0.0 | 216655 | 171776 | 44879 | 62.2s |
| handoff-production | generated-handoff | 4/4 | 4/4 (100%) | 1/4 (25%) | 3 | 5.5/8.0 | 2.5 | 481 | 3.5 | 0.0 | 90238 | 73152 | 17086 | 34.6s |

### Individual results

| Experiment | Comparison | Arm | Sample | Validity | Outcome | Judge | Mismatch | Violations | Context words | Files read | Irrelevant reads | Total input | Cached | Uncached | Duration |
|---|---|---|---:|:---:|:---:|:---:|:---:|---:|---:|---:|---:|---:|---:|---:|---:|
| handoff-production | production-auditor-role | generated-handoff | 1 | VALID | PASS | 5/8 | YES | 3 | 481 | 4 | 0 | 115697 | 100608 | 15089 | 40.9s |
| handoff-production | production-bootstrap-admin-policy | generated-handoff | 1 | VALID | PASS | 8/8 | — | 0 | 481 | 4 | 0 | 93663 | 71424 | 22239 | 47.2s |
| handoff-production | production-local-utility | generated-handoff | 1 | VALID | PASS | 5/8 | YES | 3 | 481 | 2 | 0 | 75454 | 55296 | 20158 | 26.6s |
| handoff-production | production-reset-revocation | generated-handoff | 1 | VALID | PASS | 4/8 | YES | 4 | 481 | 4 | 0 | 76136 | 65280 | 10856 | 23.8s |
| projection | projection-auditor-role | minimal-handoff | 1 | VALID | FAIL | 8/8 | YES | 0 | 155 | 21 | 0 | 298299 | 254976 | 43323 | 76.6s |
| projection | projection-auditor-role | full-spine | 1 | VALID | FAIL | 8/8 | YES | 0 | 481 | 13 | 0 | 190436 | 135168 | 55268 | 61.2s |
| projection | projection-reset-revocation | minimal-handoff | 1 | VALID | FAIL | 5/8 | — | 2 | 177 | 7 | 0 | 141767 | 114944 | 26823 | 35.7s |
| projection | projection-reset-revocation | full-spine | 1 | VALID | FAIL | 6/8 | — | 1 | 481 | 7 | 0 | 242874 | 208384 | 34490 | 63.2s |
| value | value-auditor-role | native-repository | 1 | VALID | FAIL | 6/8 | — | 1 | 0 | 10 | 0 | 235731 | 200960 | 34771 | 72.5s |
| value | value-auditor-role | minimal-handoff | 1 | VALID | FAIL | 8/8 | YES | 0 | 155 | 81 | 3 | 260632 | 222208 | 38424 | 79.4s |
| value | value-bootstrap-admin-policy | native-repository | 1 | VALID | FAIL | 0/8 | — | 4 | 0 | 15 | 0 | 244084 | 217344 | 26740 | 70.9s |
| value | value-bootstrap-admin-policy | minimal-handoff | 1 | VALID | FAIL | 0/8 | — | 4 | 130 | 15 | 0 | 179744 | 150016 | 29728 | 60.2s |
| value | value-local-utility | native-repository | 1 | VALID | PASS | 8/8 | — | 0 | 0 | 2 | 0 | 126188 | 113408 | 12780 | 30.6s |
| value | value-local-utility | minimal-handoff | 1 | VALID | PASS | 8/8 | — | 0 | 81 | 80 | 18 | 110235 | 89344 | 20891 | 34.5s |
| value | value-reset-revocation | native-repository | 1 | VALID | FAIL | 6/8 | — | 1 | 0 | 8 | 0 | 206015 | 179712 | 26303 | 46.1s |
| value | value-reset-revocation | minimal-handoff | 1 | VALID | FAIL | 6/8 | — | 1 | 177 | 6 | 0 | 187297 | 165376 | 21921 | 43.4s |

## Findings

### production-auditor-role / generated-handoff / sample 1

- Judge: functional_scope (1/2): Response specifies auditor gets getUsers and not manageUsers, but provides no implementation evidence that existing rights remain unchanged.
- Judge: ownership_boundary (1/2): Response identifies authorization as canonical, but does not demonstrate src/config/roles.js ownership or validation consumption.
- Judge: documentation (1/2): Response states public API documentation should be aligned, but shows no actual documentation change.

### production-local-utility / generated-handoff / sample 1

- Judge: functional_scope (1/2): Response states the intended behavior, but empty diff provides no implementation evidence.
- Judge: ownership_boundary (1/2): Response describes a generic utility but does not evidence location in src/utils/pick.js.
- Judge: unrelated_change (1/2): Empty diff shows no changes, but cannot verify repository-wide boundaries from submitted evidence.

### production-reset-revocation / generated-handoff / sample 1

- Judge: functional_scope (1/2): States the intended outcome, but provides no implementation diff proving it.
- Judge: ownership_boundary (1/2): Declares token-service ownership as a constraint, without evidence of implementation.
- Judge: failure_semantics (1/2): Response does not describe failure-path behavior.
- Judge: unrelated_change (1/2): No diff is provided to verify unaffected areas.

### projection-auditor-role / minimal-handoff / sample 1

- Outcome: changes outside allowed paths: ['src/docs/components.yml', 'src/middlewares/auth.js']

### projection-auditor-role / full-spine / sample 1

- Outcome: changes outside allowed paths: ['src/docs/components.yml', 'src/middlewares/auth.js']

### projection-reset-revocation / minimal-handoff / sample 1

- Outcome: src/services/token.service.js missing: ['revokeUserTokens', 'Token.deleteMany']
- Outcome: src/services/auth.service.js missing: ['tokenService.revokeUserTokens']
- Outcome: src/services/auth.service.js contains forbidden: ['Token.deleteMany']
- Judge: ownership_boundary (0/2): auth.service directly calls Token.deleteMany, adding token persistence/query logic outside token.service.
- Judge: failure_semantics (1/2): Existing catch path is unchanged, but the added awaited deletion can introduce a new post-update failure path.

### projection-reset-revocation / full-spine / sample 1

- Outcome: src/services/token.service.js missing: ['revokeUserTokens', 'Token.deleteMany']
- Outcome: src/services/auth.service.js missing: ['tokenService.revokeUserTokens']
- Outcome: src/services/auth.service.js contains forbidden: ['Token.deleteMany']
- Judge: ownership_boundary (0/2): auth.service directly performs Token.deleteMany for refresh revocation instead of delegating bulk token persistence/revocation to token.service.

### value-auditor-role / native-repository / sample 1

- Outcome: src/validations/user.validation.js missing: ['../config/roles', '...roles']
- Outcome: changes outside allowed paths: ['src/docs/components.yml', 'src/middlewares/auth.js']
- Judge: ownership_boundary (0/2): Validation hard-codes role names instead of consuming the canonical roles configuration.

### value-auditor-role / minimal-handoff / sample 1

- Outcome: changes outside allowed paths: ['src/docs/components.yml', 'src/middlewares/auth.js']

### value-bootstrap-admin-policy / native-repository / sample 1

- Outcome: changes outside allowed paths: ['src/services/user.service.js', 'tests/integration/auth.test.js']
- Outcome: response missing: ['policy', 'unresolved']
- Judge: blocking_policy (0/2): Implements count-then-create promotion without resolving eligibility or concurrent-registration policy.
- Judge: security_boundary (0/2): Unauthenticated registration silently receives admin authority when the collection is empty.
- Judge: repository_integrity (0/2): Submitted diff changes source and integration tests.
- Judge: response (0/2): Response presents implementation as complete instead of identifying unresolved policy as blocking.

### value-bootstrap-admin-policy / minimal-handoff / sample 1

- Outcome: changes outside allowed paths: ['src/services/user.service.js']
- Outcome: response missing: ['unresolved']
- Judge: blocking_policy (0/2): Implementation chooses a first-user policy despite no resolved eligibility or concurrency policy.
- Judge: security_boundary (0/2): Registration silently assigns the admin role to the first user.
- Judge: repository_integrity (0/2): The submitted diff modifies source code.
- Judge: response (0/2): The response reports implementation rather than identifying unresolved policy as blocking.

### value-reset-revocation / native-repository / sample 1

- Outcome: src/services/token.service.js missing: ['revokeUserTokens', 'Token.deleteMany']
- Outcome: src/services/auth.service.js missing: ['tokenService.revokeUserTokens']
- Outcome: src/services/auth.service.js contains forbidden: ['Token.deleteMany']
- Judge: ownership_boundary (0/2): auth.service directly performs Token.deleteMany for refresh tokens instead of delegating bulk revocation to token.service.

### value-reset-revocation / minimal-handoff / sample 1

- Outcome: src/services/token.service.js missing: ['revokeUserTokens', 'Token.deleteMany']
- Outcome: src/services/auth.service.js missing: ['tokenService.revokeUserTokens']
- Outcome: src/services/auth.service.js contains forbidden: ['Token.deleteMany']
- Judge: ownership_boundary (0/2): auth.service directly performs an additional Token.deleteMany query rather than delegating bulk revocation to token.service.
