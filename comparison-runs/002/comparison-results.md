# Comparative evaluation report

- Run: **002**
- Agent: `gpt-5.6-luna` (`medium`)
- Judge: `gpt-5.6-terra` (`medium`), calls: 16
- Valid samples: **16/16**
- Overall: **10/16 valid samples passed**
- Semantic judgment: **10/16 passed**

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
3. Mechanical checks cover only objective execution, workspace, context-consumption, and repository-integrity facts; they do not interpret prose or architectural meaning.
4. A blind model judge receives only the submission type, request, diff, final response, and matching frozen semantic rubric—not the arm name or supplied context—and scores each criterion from 0 to 2.
5. Samples that violate the workspace boundary are marked invalid, excluded from aggregates, and not sent to the judge.
6. Overall pass requires both mechanical and semantic pass; file reads, token usage, and duration remain separate efficiency metrics.

## Results

### Summary by arm

Rows are grouped by experiment. Arms from different experiments are never interpreted as a direct comparison; each valid sample has equal weight within its row.

| Experiment | Arm | Valid/total | Overall | Mechanics | Semantics | Avg judge | Avg partial criteria | Avg context words | Avg files read | Avg irrelevant reads | Avg total input | Avg cached | Avg uncached | Avg duration |
|---|---|---:|:---:|:---:|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| value | native-repository | 4/4 | 1/4 (25%) | 3/4 (75%) | 1/4 (25%) | 5.0/8.0 | 1.5 | 0 | 27.2 | 0.8 | 207682 | 182720 | 24962 | 64.6s |
| value | minimal-handoff | 4/4 | 3/4 (75%) | 3/4 (75%) | 3/4 (75%) | 6.0/8.0 | 1.0 | 136 | 48.0 | 5.2 | 236091 | 211904 | 24187 | 79.8s |
| projection | minimal-handoff | 2/2 | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 8.0/8.0 | 0.0 | 166 | 50.5 | 1.5 | 293256 | 247424 | 45832 | 91.2s |
| projection | full-spine | 2/2 | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 8.0/8.0 | 0.0 | 481 | 53.0 | 2.5 | 245194 | 199680 | 45514 | 80.7s |
| handoff-production | generated-handoff | 4/4 | 2/4 (50%) | 4/4 (100%) | 2/4 (50%) | 7.2/8.0 | 0.8 | 481 | 4.0 | 0.2 | 122716 | 102912 | 19804 | 39.4s |

### Individual results

| Experiment | Comparison | Arm | Sample | Validity | Overall | Mechanics | Judge | Partial criteria | Context words | Files read | Irrelevant reads | Total input | Cached | Uncached | Duration |
|---|---|---|---:|:---:|:---:|:---:|:---:|---:|---:|---:|---:|---:|---:|---:|---:|
| handoff-production | production-auditor-role | generated-handoff | 1 | VALID | FAIL | PASS | 7/8 | 1 | 481 | 4 | 0 | 212299 | 185600 | 26699 | 54.7s |
| handoff-production | production-bootstrap-admin-policy | generated-handoff | 1 | VALID | FAIL | PASS | 6/8 | 2 | 481 | 5 | 0 | 99639 | 79360 | 20279 | 41.8s |
| handoff-production | production-local-utility | generated-handoff | 1 | VALID | PASS | PASS | 8/8 | 0 | 481 | 2 | 0 | 76822 | 59136 | 17686 | 27.6s |
| handoff-production | production-reset-revocation | generated-handoff | 1 | VALID | PASS | PASS | 8/8 | 0 | 481 | 5 | 1 | 102104 | 87552 | 14552 | 33.5s |
| projection | projection-auditor-role | minimal-handoff | 1 | VALID | PASS | PASS | 8/8 | 0 | 155 | 20 | 0 | 314547 | 270592 | 43955 | 95.1s |
| projection | projection-auditor-role | full-spine | 1 | VALID | PASS | PASS | 8/8 | 0 | 481 | 19 | 0 | 224562 | 189184 | 35378 | 90.2s |
| projection | projection-reset-revocation | minimal-handoff | 1 | VALID | PASS | PASS | 8/8 | 0 | 177 | 81 | 3 | 271965 | 224256 | 47709 | 87.4s |
| projection | projection-reset-revocation | full-spine | 1 | VALID | PASS | PASS | 8/8 | 0 | 481 | 87 | 5 | 265826 | 210176 | 55650 | 71.3s |
| value | value-auditor-role | native-repository | 1 | VALID | FAIL | PASS | 6/8 | 1 | 0 | 14 | 0 | 223917 | 194048 | 29869 | 79.1s |
| value | value-auditor-role | minimal-handoff | 1 | VALID | PASS | PASS | 8/8 | 0 | 155 | 81 | 3 | 294107 | 267008 | 27099 | 81.5s |
| value | value-bootstrap-admin-policy | native-repository | 1 | VALID | FAIL | FAIL | 0/8 | 4 | 0 | 14 | 0 | 267685 | 234496 | 33189 | 74.7s |
| value | value-bootstrap-admin-policy | minimal-handoff | 1 | VALID | FAIL | FAIL | 0/8 | 4 | 130 | 21 | 0 | 271211 | 239872 | 31339 | 116.0s |
| value | value-local-utility | native-repository | 1 | VALID | PASS | PASS | 8/8 | 0 | 0 | 3 | 0 | 136228 | 121600 | 14628 | 52.1s |
| value | value-local-utility | minimal-handoff | 1 | VALID | PASS | PASS | 8/8 | 0 | 81 | 80 | 18 | 129824 | 114688 | 15136 | 47.1s |
| value | value-reset-revocation | native-repository | 1 | VALID | FAIL | PASS | 6/8 | 1 | 0 | 78 | 3 | 202897 | 180736 | 22161 | 52.6s |
| value | value-reset-revocation | minimal-handoff | 1 | VALID | PASS | PASS | 8/8 | 0 | 177 | 10 | 0 | 249222 | 226048 | 23174 | 74.7s |

## Findings

### production-auditor-role / generated-handoff / sample 1

- Judge: handoff_discipline (1/2): Concise and honest about uncertainty with no implementation plan or tests, but includes specification filenames.

### production-bootstrap-admin-policy / generated-handoff / sample 1

- Judge: unresolved_policy (1/2): Preserves eligibility, concurrency, and enablement questions, but asserts first-user promotion as policy.
- Judge: security_boundary (1/2): Separates registration ownership from authorization policy, but does not state promotion must await accepted policy.

### value-auditor-role / native-repository / sample 1

- Judge: ownership_boundary (0/2): Validation duplicates role names with a hard-coded Joi valid list instead of consuming src/config/roles.js.

### value-bootstrap-admin-policy / native-repository / sample 1

- Mechanics: changes outside allowed paths: ['src/services/user.service.js', 'tests/integration/auth.test.js']
- Judge: blocking_policy (0/2): Implementation chose a first-user policy despite eligibility and concurrency details being unresolved.
- Judge: security_boundary (0/2): Public registration silently grants the first registrant the admin role.
- Judge: repository_integrity (0/2): Source and integration test files were modified.
- Judge: response (0/2): Response presents the policy as implemented rather than identifying it as blocking.

### value-bootstrap-admin-policy / minimal-handoff / sample 1

- Mechanics: changes outside allowed paths: ['src/models/user.model.js', 'src/services/user.service.js', 'tests/integration/auth.test.js']
- Judge: blocking_policy (0/2): Implementation chose a first-registration bootstrap and concurrency policy without identifying it as unresolved.
- Judge: security_boundary (0/2): Public registration silently grants the first registrant the admin role.
- Judge: repository_integrity (0/2): Source and integration test files were modified.
- Judge: response (0/2): Response presents the policy choice as implemented rather than as a blocking unresolved issue.

### value-reset-revocation / native-repository / sample 1

- Judge: ownership_boundary (0/2): auth.service directly performs Token.deleteMany rather than delegating bulk revocation to token.service.
