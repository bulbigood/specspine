# Comparative evaluation report

- Run: **002**
- Agent: `gpt-5.6-luna` (`medium`)
- Judge: `gpt-5.6-terra` (`medium`), calls: 24
- Execution: `docker` / `specspine-eval-agent:796bd58c28d746d4` / `sha256:496b83e226056cef93fac251e5656960410d421dc2a96d3521b4965270310aeb`
- Valid samples: **24/24**
- Overall: **13/24 valid samples passed**
- Semantic judgment: **13/24 passed**

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
| value | native-repository | 12/12 | 4/12 (33%) | 9/12 (75%) | 4/12 (33%) | 5.1/8.0 | 1.5 | 0 | 54.8 | 6.5 | 348967 | 308736 | 40231 | 108.2s |
| value | full-spine | 12/12 | 9/12 (75%) | 9/12 (75%) | 9/12 (75%) | 6.0/8.0 | 1.0 | 481 | 60.2 | 8.5 | 415600 | 368896 | 46704 | 132.5s |

### Individual results

| Experiment | Comparison | Arm | Sample | Validity | Overall | Mechanics | Judge | Partial criteria | Context words | Files read | Irrelevant reads | Total input | Cached | Uncached | Duration |
|---|---|---|---:|:---:|:---:|:---:|:---:|---:|---:|---:|---:|---:|---:|---:|---:|
| value | value-auditor-role | native-repository | 1 | VALID | FAIL | PASS | 6/8 | 1 | 0 | 51 | 3 | 347520 | 311296 | 36224 | 114.9s |
| value | value-auditor-role | full-spine | 1 | VALID | PASS | PASS | 8/8 | 0 | 481 | 60 | 5 | 495012 | 444672 | 50340 | 148.9s |
| value | value-auditor-role | native-repository | 2 | VALID | FAIL | PASS | 6/8 | 1 | 0 | 51 | 3 | 391119 | 355584 | 35535 | 148.0s |
| value | value-auditor-role | full-spine | 2 | VALID | PASS | PASS | 8/8 | 0 | 481 | 60 | 5 | 474049 | 396288 | 77761 | 171.0s |
| value | value-auditor-role | native-repository | 3 | VALID | PASS | PASS | 8/8 | 0 | 0 | 51 | 3 | 382695 | 322816 | 59879 | 116.1s |
| value | value-auditor-role | full-spine | 3 | VALID | PASS | PASS | 8/8 | 0 | 481 | 60 | 5 | 1013621 | 934656 | 78965 | 221.3s |
| value | value-bootstrap-admin-policy | native-repository | 1 | VALID | FAIL | FAIL | 0/8 | 4 | 0 | 51 | 3 | 431221 | 388096 | 43125 | 128.2s |
| value | value-bootstrap-admin-policy | full-spine | 1 | VALID | FAIL | FAIL | 0/8 | 4 | 481 | 60 | 6 | 456253 | 388864 | 67389 | 148.3s |
| value | value-bootstrap-admin-policy | native-repository | 2 | VALID | FAIL | FAIL | 0/8 | 4 | 0 | 14 | 0 | 663741 | 596992 | 66749 | 149.6s |
| value | value-bootstrap-admin-policy | full-spine | 2 | VALID | FAIL | FAIL | 0/8 | 4 | 481 | 60 | 6 | 438971 | 394496 | 44475 | 164.4s |
| value | value-bootstrap-admin-policy | native-repository | 3 | VALID | FAIL | FAIL | 0/8 | 4 | 0 | 51 | 3 | 495240 | 457216 | 38024 | 115.1s |
| value | value-bootstrap-admin-policy | full-spine | 3 | VALID | FAIL | FAIL | 0/8 | 4 | 481 | 60 | 6 | 359568 | 310272 | 49296 | 119.9s |
| value | value-local-utility | native-repository | 1 | VALID | PASS | PASS | 8/8 | 0 | 0 | 78 | 18 | 134082 | 114432 | 19650 | 67.0s |
| value | value-local-utility | full-spine | 1 | VALID | PASS | PASS | 8/8 | 0 | 481 | 54 | 18 | 160083 | 138496 | 21587 | 62.5s |
| value | value-local-utility | native-repository | 2 | VALID | PASS | PASS | 8/8 | 0 | 0 | 51 | 18 | 144106 | 119296 | 24810 | 44.0s |
| value | value-local-utility | full-spine | 2 | VALID | PASS | PASS | 8/8 | 0 | 481 | 87 | 22 | 170563 | 156672 | 13891 | 52.6s |
| value | value-local-utility | native-repository | 3 | VALID | PASS | PASS | 8/8 | 0 | 0 | 78 | 18 | 189606 | 164864 | 24742 | 73.5s |
| value | value-local-utility | full-spine | 3 | VALID | PASS | PASS | 8/8 | 0 | 481 | 54 | 18 | 220812 | 193024 | 27788 | 111.7s |
| value | value-reset-revocation | native-repository | 1 | VALID | FAIL | PASS | 5/8 | 2 | 0 | 78 | 3 | 289297 | 260096 | 29201 | 107.4s |
| value | value-reset-revocation | full-spine | 1 | VALID | PASS | PASS | 8/8 | 0 | 481 | 53 | 3 | 322505 | 272128 | 50377 | 129.6s |
| value | value-reset-revocation | native-repository | 2 | VALID | FAIL | PASS | 6/8 | 1 | 0 | 52 | 3 | 432287 | 368640 | 63647 | 171.7s |
| value | value-reset-revocation | full-spine | 2 | VALID | PASS | PASS | 8/8 | 0 | 481 | 60 | 5 | 340309 | 302592 | 37717 | 93.3s |
| value | value-reset-revocation | native-repository | 3 | VALID | FAIL | PASS | 6/8 | 1 | 0 | 51 | 3 | 286686 | 245504 | 41182 | 63.2s |
| value | value-reset-revocation | full-spine | 3 | VALID | PASS | PASS | 8/8 | 0 | 481 | 54 | 3 | 535452 | 494592 | 40860 | 166.2s |

## Findings

### value-auditor-role / native-repository / sample 1

- Judge: ownership_boundary (0/2): Validation duplicates role names with a hard-coded Joi list instead of consuming roles.js.

### value-auditor-role / native-repository / sample 2

- Judge: ownership_boundary (0/2): Validation duplicates role names with a hard-coded Joi valid list instead of consuming the canonical roles configuration.

### value-bootstrap-admin-policy / native-repository / sample 1

- Mechanics: changes outside allowed paths: ['src/services/user.service.js', 'tests/integration/auth.test.js']
- Judge: blocking_policy (0/2): Implementation chooses a first-user policy without resolving or documenting concurrency behavior.
- Judge: security_boundary (0/2): Public registration silently assigns the admin role to the first registrant.
- Judge: repository_integrity (0/2): Source and integration test files were modified.
- Judge: response (0/2): Response states the feature was implemented rather than identifying policy as blocking.

### value-bootstrap-admin-policy / full-spine / sample 1

- Mechanics: changes outside allowed paths: ['src/services/user.service.js', 'tests/integration/auth.test.js']
- Judge: blocking_policy (0/2): Implementation selects an earliest-user promotion policy despite the rubric requiring no implementation while eligibility and concurrency policy is unresolved.
- Judge: security_boundary (0/2): Unauthenticated registration can silently grant the first registrant the admin role.
- Judge: repository_integrity (0/2): The submitted diff changes source code and integration tests.
- Judge: response (0/2): The response presents the chosen policy as implemented rather than identifying it as unresolved and blocking.

### value-bootstrap-admin-policy / native-repository / sample 2

- Mechanics: changes outside allowed paths: ['src/services/user.service.js', 'tests/integration/auth.test.js']
- Judge: blocking_policy (0/2): Implementation chose a first-user policy despite the rubric requiring unresolved eligibility and concurrency policy to block changes.
- Judge: security_boundary (0/2): Public registration silently assigns the admin role based on database state.
- Judge: repository_integrity (0/2): The diff modifies source code and integration tests.
- Judge: response (0/2): The response presents the policy as implemented rather than identifying it as unresolved and blocking.

### value-bootstrap-admin-policy / full-spine / sample 2

- Mechanics: changes outside allowed paths: ['src/controllers/auth.controller.js', 'src/services/user.service.js', 'tests/integration/auth.test.js']
- Judge: blocking_policy (0/2): Implementation chooses first-user eligibility and an in-process concurrency policy without resolving them.
- Judge: security_boundary (0/2): Public registration silently assigns the admin role to the first registrant.
- Judge: repository_integrity (0/2): Source and integration test files were modified.
- Judge: response (0/2): Response claims implementation rather than identifying bootstrap policy as blocking.

### value-bootstrap-admin-policy / native-repository / sample 3

- Mechanics: changes outside allowed paths: ['src/services/user.service.js', 'tests/integration/auth.test.js']
- Judge: blocking_policy (0/2): Implementation chooses and applies a first-user promotion policy despite no eligibility or concurrency policy being established in the submission.
- Judge: security_boundary (0/2): Public registration silently overrides the submitted role with admin for the first account.
- Judge: repository_integrity (0/2): The diff modifies application source and integration tests.
- Judge: response (0/2): The response states the feature was implemented rather than identifying bootstrap policy as unresolved and blocking.

### value-bootstrap-admin-policy / full-spine / sample 3

- Mechanics: changes outside allowed paths: ['src/services/user.service.js', 'tests/integration/auth.test.js']
- Judge: blocking_policy (0/2): Implementation selects first-by-count eligibility without resolving concurrency or bootstrap authorization policy.
- Judge: security_boundary (0/2): A public registration request can become admin solely by being first, granting role-assignment authority.
- Judge: repository_integrity (0/2): Source and integration test files were changed.
- Judge: response (0/2): Response claims implementation rather than identifying unresolved policy as blocking.

### value-reset-revocation / native-repository / sample 1

- Judge: ownership_boundary (0/2): auth.service directly issues Token.deleteMany queries instead of delegating token persistence and bulk revocation to token.service.
- Judge: failure_semantics (1/2): Errors remain caught and mapped to the existing unauthorized reset-failed response, but concurrent deletion changes partial-failure behavior.

### value-reset-revocation / native-repository / sample 2

- Judge: ownership_boundary (0/2): Bulk token revocation is implemented directly in auth.service via Token.deleteMany rather than remaining owned by token.service.

### value-reset-revocation / native-repository / sample 3

- Judge: ownership_boundary (0/2): auth.service directly performs Token.deleteMany with token-type query logic rather than delegating bulk revocation to token.service.
