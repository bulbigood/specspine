Feature: End-to-end IWE specification lifecycle
  The complete skill line is judged as one coherent workflow.

  Scenario: Map, specify, verify, implement, and re-verify a brownfield export
    Given preparation "unsafe-user-export"
    And skills "iwe-spec-map,iwe-spec-specify,iwe-spec-verify,iwe-spec-implement"
    When the operator asks:
      """
      First document the existing user export behavior. Then record this accepted
      requirement in the right place: exported users must never contain password
      hashes. Check the implementation against it, resolve any mismatch with
      focused tests, and verify the result again. Keep observed behavior and
      accepted intent distinct throughout.
      """
    Then the AI judge verifies:
      """
      All five phases are evidenced. Mapping records the pre-existing endpoint
      without inventing intent; specification adds one canonical normative
      requirement; initial verification detects the password-hash exposure;
      implementation fixes it with a focused test; final verification finds no
      remaining conflict for that claim. IWE validation succeeds and unrelated
      behavior is preserved.
      """

  Scenario: Verify before and after an implementation-only repair
    Given preparation "missing-inactive-login"
    And skills "iwe-spec-verify,iwe-spec-implement"
    When the operator asks:
      """
      Establish the current inactive-login mismatch, repair the implementation
      without changing the accepted specification, then verify again and
      summarize the before-and-after evidence.
      """
    Then the AI judge verifies:
      """
      The initial report exposes the real divergence, implementation and tests
      resolve it, the accepted specification is unchanged, and the final report
      closes the original finding with concrete evidence.
      """
