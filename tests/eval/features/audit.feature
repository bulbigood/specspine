Feature: Read-only Specspine semantic audit
  The audit skill checks cross-statement and filesystem invariants through IWE.

  Scenario: Report semantic readiness defects without editing
    Given preparation "semantic-audit-defects"
    And skills "iwe-spec-audit"
    When the operator asks:
      """
      Audit the authentication specification for format and semantic readiness.
      Report concrete problems and their evidence, but do not repair anything.
      """
    Then the AI judge verifies:
      """
      The report identifies the title/H1 mismatch, duplicate owner-local
      requirement identifier, unresolved blocking question, and missing asset.
      It distinguishes schema validity from semantic readiness, reports the
      authentication owner as invalid or not ready, states the inspected scope,
      and leaves every workspace file unchanged.
      """
