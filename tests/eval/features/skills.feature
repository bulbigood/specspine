Feature: IWE specification skills on a brownfield service
  The skills are exercised against isolated copies of node-express-boilerplate.
  Outcomes are accepted only by an independent AI judge.

  Scenario: Map password-reset evidence without inventing intent
    Given preparation "baseline"
    And skills "iwe-spec-map"
    When the operator asks:
      """
      Please document what the service currently does during password reset,
      including where email delivery crosses the system boundary. Keep observed
      behavior separate from accepted product requirements.
      """
    Then the AI judge verifies:
      """
      Authentication owns useful OBS/INF evidence for password reset and email.
      No new normative intent was inferred from code. IWE structure and schema
      remain valid, and no generated hierarchy or index was introduced.
      """

  Scenario: Specify an accepted authentication requirement
    Given preparation "baseline"
    And skills "iwe-spec-specify"
    When the operator asks:
      """
      We have accepted a new requirement: login for an inactive user must fail
      without revealing whether the account exists. Document the requirement
      in the right place and describe how it will be verified. Do not implement it.
      """
    Then the AI judge verifies:
      """
      The accepted requirement and verification criterion are in the canonical
      authentication owner, use valid statement identifiers, and are not copied
      elsewhere. Application code is unchanged and IWE validation succeeds.
      """

  Scenario: Specify with an owner-local identifier collision
    Given preparation "owner-local-id-collision"
    And skills "iwe-spec-specify"
    When the operator asks:
      """
      We have accepted that inactive users must receive the same generic login
      rejection as invalid credentials. Document this authentication requirement
      with a focused verification criterion. Do not implement it or disturb
      requirements belonging to another part of the system.
      """
    Then the AI judge verifies:
      """
      Authentication owns REQ-login-policy and a focused valid VER claim. User
      management retains its distinct REQ-login-policy unchanged, proving that
      statement identifiers were treated as owner-local rather than globally
      unique. No claim was copied between owners, application code is unchanged,
      and IWE schema validation succeeds.
      """

  Scenario: Map a cross-owner registration flow without duplicate claims
    Given preparation "cross-owner-registration"
    And skills "iwe-spec-map"
    When the operator asks:
      """
      Please deepen the documentation of the existing public registration flow.
      The flow crosses authentication and user management, so put each confirmed
      fact where it naturally belongs without duplication. Keep observations
      separate from interpretation and do not invent product requirements.
      """
    Then the AI judge verifies:
      """
      Useful registration evidence is divided by canonical ownership rather
      than duplicated: authentication owns its public request/token behavior
      and user management owns identity creation or persistence behavior.
      OBS claims contain confirmed facts, any INF claims are interpretations,
      both touched owners have honest deepen inspection metadata, no normative
      intent was invented, the existing hierarchy is unchanged, and schema
      validation succeeds.
      """

  Scenario: Verify missing behavior without editing
    Given preparation "missing-inactive-login"
    And skills "iwe-spec-verify"
    When the operator asks:
      """
      Check whether inactive-user login behavior matches the accepted
      specification. Return a conformance report supported by evidence.
      """
    Then the AI judge verifies:
      """
      The report identifies the inactive-user requirement as missing (or gives
      an equally well-supported nonconformance), cites the owner and claim, and
      distinguishes authority from evidence. No workspace file was modified.
      """

  Scenario: Verify an uncovered integration under an open boundary
    Given preparation "open-audit-webhook"
    And skills "iwe-spec-verify"
    When the operator asks:
      """
      Review authentication for external interactions, including the login audit
      webhook. Return an evidence-backed conformance report without changing
      the project.
      """
    Then the AI judge verifies:
      """
      The audit webhook is reported as uncovered-boundary, not conflicting,
      because it is not governed by normative claims. The report explicitly
      records that the governing Authentication owner has non-exhaustive/open
      external-boundary coverage, includes concrete code evidence and
      confidence, and no workspace file was modified.
      """

  Scenario: Implement additive missing behavior
    Given preparation "missing-inactive-login"
    And skills "iwe-spec-implement"
    When the operator asks:
      """
      Implement the missing inactive-user login requirement without removing
      existing behavior. Add focused tests and verify the result.
      """
    Then the AI judge verifies:
      """
      Inactive users can no longer log in and the response does not disclose
      account existence. Focused tests cover the behavior. Specifications were
      not weakened, unrelated behavior was preserved, and the final result is
      conformant to the relevant claims.
      """

  Scenario: Conform mode removes explicitly forbidden behavior
    Given preparation "forbidden-registration"
    And skills "iwe-spec-implement"
    When the operator asks:
      """
      Bring public registration into line with the accepted authentication
      specification. Add or update focused tests as needed.
      """
    Then the AI judge verifies:
      """
      The public registration behavior forbidden by the normative claim is no
      longer reachable. The removal is coherent across routing and tests,
      unrelated authentication behavior remains, and the specification was not
      edited to excuse the implementation.
      """

  Scenario: Closed-boundary mode removes an uncovered external integration
    Given preparation "uncovered-audit-webhook"
    And skills "iwe-spec-implement"
    When the operator asks:
      """
      The accepted documentation says its list of external authentication
      behavior is complete. Remove external behavior that falls outside that
      list, then verify the result again.
      """
    Then the AI judge verifies:
      """
      The synthetic audit webhook and its dead path are removed because the
      governing owner explicitly has exhaustive external-boundary coverage.
      Documented authentication behavior remains intact, tests are appropriate,
      and the specification was not weakened.
      """

  Scenario: Closed-boundary mode preserves an integration under open coverage
    Given preparation "open-audit-webhook"
    And skills "iwe-spec-implement"
    When the operator asks:
      """
      Reconcile the login audit webhook with the accepted authentication
      specification. Preserve behavior unless the accepted specification gives
      a sound basis for removing it, and report the final verification status.
      """
    Then the AI judge verifies:
      """
      The synthetic audit webhook and its call path remain unchanged because
      Authentication declares open, not exhaustive, external-boundary coverage
      and no normative claim forbids the interaction. It is reported as
      uncovered-boundary or unverified rather than conflicting; specifications
      are not weakened, no unnecessary tests or implementation edits are made,
      and final schema validation succeeds.
      """
