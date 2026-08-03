Feature: Deterministic P1 operational safeguards
  The workflows select owners, evidence, closure, and IWE commands deliberately.

  Scenario: Reuse the authentication owner for password reset evidence
    Given preparation "baseline"
    And skills "iwe-spec-map"
    When the operator asks:
      """
      Map the current password-reset token and email flow. Test whether it belongs
      in an existing owner before considering a new specification document.
      Preserve the distinction between accepted intent and implementation evidence.
      """
    Then the AI judge verifies:
      """
      Authentication is refined as the canonical owner and no password-reset
      owner is created. The response explains the refine-versus-expand owner test,
      records only useful exception-layer evidence, does not invent accepted
      intent, uses bounded non-deprecated IWE discovery and retrieval, and schema
      validation succeeds.
      """

  Scenario: Evidence does not advance partial facets
    Given preparation "evidence-only-partial-facets"
    And skills "iwe-spec-map"
    When the operator asks:
      """
      Deepen the current password-reset implementation evidence in Authentication.
      Do not turn observed code into accepted requirements.
      """
    Then the AI judge verifies:
      """
      Useful OBS or INF evidence may be updated, but Authentication behavior and
      verification facets remain partial because evidence alone cannot advance
      them. No normative claim is invented, bounded current IWE commands are used,
      and schema validation succeeds.
      """

  Scenario: Refresh removes a stale current-state observation
    Given preparation "stale-password-reset-observation"
    And skills "iwe-spec-map"
    When the operator asks:
      """
      Refresh the password-reset email evidence against the current repository.
      Keep the document as a current-state map rather than an append-only history.
      """
    Then the AI judge verifies:
      """
      The false SendGrid observation is removed or corrected to the current SMTP
      and nodemailer implementation, inspection metadata records refresh, no
      contradictory current OBS claims remain, accepted intent and facets are
      unchanged, and validation succeeds.
      """

  Scenario: Aggregate mixed implementation freedom through governing context
    Given preparation "mixed-implementation-freedom"
    And skills "iwe-spec-verify"
    When the operator asks:
      """
      Verify the existing valid-credentials login behavior and state the effective
      implementation freedom across its governing specification closure.
      Do not modify the workspace.
      """
    Then the AI judge verifies:
      """
      The bounded closure includes Authentication and its governing API architecture
      parent for an explicit reason. Effective implementation freedom is reported as
      architecture-constrained and API architecture is named as the constraint.
      The compact report contains scope, findings, checks, and verdict, and no file
      changes occur.
      """

  Scenario: Disambiguate overlapping authentication owners
    Given preparation "ambiguous-authentication-owner"
    And skills "iwe-spec-verify"
    When the operator asks:
      """
      Verify the login valid-credentials contract. There are similarly named
      authentication documents, so identify the governing owner before checking it.
      """
    Then the AI judge verifies:
      """
      Bounded fuzzy or lexical discovery distinguishes Authentication, which owns
      login execution and REQ-valid-credentials, from Authentication policy, which
      only owns terminology. The closure includes or excludes each candidate for a
      stated reason, uses current non-deprecated IWE flags and hard budgets, and the
      read-only verdict is evidence-backed.
      """

  Scenario: Reject an escaping normative asset during audit
    Given preparation "escaping-asset"
    And skills "iwe-spec-audit"
    When the operator asks:
      """
      Audit Authentication for format and semantic readiness without repairing it.
      """
    Then the AI judge verifies:
      """
      The schema or semantic audit rejects ../../outside-auth.yaml as an escaping,
      non-workspace-relative asset path, reports Authentication not ready, clearly
      distinguishes the failed schema gate from further safe checks, and changes no
      files.
      """

  Scenario: Treat rename as an external address migration
    Given preparation "rename-external-identity"
    And skills "iwe-spec-specify"
    When the operator asks:
      """
      Rename the Authentication owner to identity-access using IWE. Preserve its
      accepted meaning and owner-local statement IDs, update the supplied external
      spec-link catalog, and report the address migration. Do not change application
      code.
      """
    Then the AI judge verifies:
      """
      The workflow uses iwe rename, the owner key becomes specs/identity-access,
      IWE-managed links remain valid, REQ-valid-credentials is unchanged, and
      external-spec-links.txt is migrated to the new key. The response treats this
      as an address migration rather than an immutable identity, validates the
      resulting schema, and leaves application code unchanged.
      """
