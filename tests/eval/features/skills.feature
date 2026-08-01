Feature: IWE specification skills on a brownfield service
  The skills are exercised against isolated copies of node-express-boilerplate.
  Outcomes are accepted only by an independent AI judge.

  Scenario: Map password-reset evidence without inventing intent
    Given preparation "baseline"
    When the operator asks:
      """
      Use $iwe-spec-map to deepen the authentication specification around the
      password-reset flow. Record what the repository proves, including its
      email boundary, without turning implementation behavior into requirements.
      """
    Then the AI judge verifies:
      """
      Authentication owns useful OBS/INF evidence for password reset and email.
      No new normative intent was inferred from code. IWE structure and schema
      remain valid, and no generated hierarchy or index was introduced.
      """

  Scenario: Specify an accepted authentication requirement
    Given preparation "baseline"
    When the operator asks:
      """
      Use $iwe-spec-specify. We have accepted this requirement: login for an
      inactive user must fail without revealing whether the account exists.
      Add it to the correct canonical specification with a verification
      criterion. Do not implement it.
      """
    Then the AI judge verifies:
      """
      The accepted requirement and verification criterion are in the canonical
      authentication owner, use valid statement identifiers, and are not copied
      elsewhere. Application code is unchanged and IWE validation succeeds.
      """

  Scenario: Verify missing behavior without editing
    Given preparation "missing-inactive-login"
    When the operator asks:
      """
      Use $iwe-spec-verify to check inactive-user login behavior against the
      accepted specifications. Return a conformance report with evidence.
      """
    Then the AI judge verifies:
      """
      The report identifies the inactive-user requirement as missing (or gives
      an equally well-supported nonconformance), cites the owner and claim, and
      distinguishes authority from evidence. No workspace file was modified.
      """

  Scenario: Implement additive missing behavior
    Given preparation "missing-inactive-login"
    When the operator asks:
      """
      Use $iwe-spec-implement in additive mode to satisfy the accepted
      inactive-user login requirement. Add focused tests and verify the result.
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
    When the operator asks:
      """
      Use $iwe-spec-implement in conform mode to reconcile public registration
      with the accepted authentication specification. Add or update tests.
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
    When the operator asks:
      """
      Use $iwe-spec-implement in closed-boundary mode for authentication. Remove
      external behavior excluded by its exhaustive boundary, then verify again.
      """
    Then the AI judge verifies:
      """
      The synthetic audit webhook and its dead path are removed because the
      governing owner explicitly has exhaustive external-boundary coverage.
      Documented authentication behavior remains intact, tests are appropriate,
      and the specification was not weakened.
      """
