Feature: End-to-end IWE specification lifecycle
  The complete skill line is judged as one coherent workflow.

  Scenario: Map, specify, verify, implement, and re-verify a brownfield export
    Given preparation "unsafe-user-export"
    When the operator asks:
      """
      Perform the full workflow in this order:
      1. Use $iwe-spec-map to map the existing user export endpoint as evidence.
      2. Use $iwe-spec-specify to record this accepted requirement in the right
         owner: exported users must never contain password hashes.
      3. Use $iwe-spec-verify to compare that requirement with the code.
      4. Use $iwe-spec-implement in conform mode to resolve the finding and add
         focused tests.
      5. Use $iwe-spec-verify again and report the final status.
      Keep evidence and accepted intent distinct throughout.
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
    When the operator asks:
      """
      Use $iwe-spec-verify to establish the current inactive-login finding. Then
      use $iwe-spec-implement in conform mode to repair it without changing the
      accepted specification. Finally use $iwe-spec-verify again and summarize
      the before/after evidence.
      """
    Then the AI judge verifies:
      """
      The initial report exposes the real divergence, implementation and tests
      resolve it, the accepted specification is unchanged, and the final report
      closes the original finding with concrete evidence.
      """
