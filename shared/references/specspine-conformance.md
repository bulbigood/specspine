# Specspine conformance

Conformance is evaluated against the task-bounded Specspine graph closure retrieved through IWE. The closure includes the relevant owners, their accepted claims, governing boundary declarations, and registered normative assets.

Schema validity is a prerequisite, not proof of implementation conformance.

## Finding classes

- `conforming`: available evidence satisfies the applicable accepted claim.
- `missing`: an accepted claim requires observable behavior that is absent.
- `conflicting`: concrete implementation behavior violates an explicit normative claim, invariant, constraint, decision, or verification criterion.
- `uncovered-boundary`: an external interaction exists but is not governed by the retrieved accepted boundary.
- `ambiguous`: accepted intent is internally inconsistent or insufficient to determine the required behavior, including a materially blocking open question.
- `runtime-unverified`: the claim needs runtime evidence and that evidence has not been established.

Each finding identifies its owner, applicable semantic ID or normative asset, expectation, evidence, runtime status, and confidence. A finding without an applicable claim may be `uncovered-boundary`; it is not automatically a conflict.

## Implementation freedom

Aggregate a retrieved closure to `architecture-constrained` when any applicable governing owner declares it; otherwise use `contract-equivalent`. Name each owner that introduces the stricter constraint. Conformance never weakens an owner's declared implementation freedom during aggregation.

## External-boundary coverage

External interactions include network calls, persistence, files, queues, processes, platform APIs, and other effects beyond an owner's private logic.

`coverage.external-boundary: open` means the owner does not claim to enumerate every permitted external interaction. An interaction omitted from an open boundary is `uncovered-boundary`; silence is not a prohibition.

`coverage.external-boundary: exhaustive` means unmentioned external interactions are outside that owner's accepted boundary. It is valid only with an owner-local `coverage.basis` resolving to a `CON-*` statement that explicitly declares the enumerated external boundary complete. Treat an interaction as outside the accepted boundary only when every governing owner needed for that interaction is exhaustive with a valid basis, or an explicit normative claim independently prohibits it.

## Change and removal authority

Implementation may be added or changed to satisfy an accepted claim. Existing behavior may be removed only when at least one of these conditions supplies positive authority:

- an explicit normative claim forbids it;
- an invariant, constraint, or accepted decision excludes it;
- every governing external boundary is exhaustive with a valid basis and the behavior falls outside it;
- a normative verification criterion establishes that the behavior fails the accepted contract.

Absence from the specification is not removal authority. Preserve or report uncovered behavior when no positive authority exists. When accepted intent is insufficient or contradictory, report `ambiguous` instead of choosing a new product or architecture decision.

## Evidence

Use the smallest evidence set that can establish the claim: a concrete static trace, a focused test, runtime observation, or a registered asset. Record environment limitations explicitly. Do not convert supporting evidence into accepted intent.
