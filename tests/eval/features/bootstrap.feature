Feature: Bootstrap Specspine skills in existing workspaces
  Bootstrap decisions are judged semantically and protected by deterministic
  filesystem postconditions.

  Scenario: Initialize the fallback without widening docs scope
    Given preparation "bootstrap-existing-docs"
    And skills "iwe-spec-specify"
    When the operator asks:
      """
      Record an accepted requirement that password-reset links expire after one
      use. Keep the existing specification files and do not index unrelated
      project documentation.
      """
    Then the AI judge verifies:
      """
      The agent recognizes that IWE is not initialized, loads the bootstrap
      protocol, configures the library at docs/specs, preserves existing files,
      installs the bundled schema and template without widening scope to docs,
      and records a valid focused requirement in the canonical owner.
      """

  Scenario: Honor an existing custom IWE library path
    Given preparation "bootstrap-custom-library"
    And skills "iwe-spec-specify"
    When the operator asks:
      """
      In the existing Authentication specification, record an accepted
      requirement that password-reset links expire after one use. Use the
      project's existing specification setup.
      """
    Then the AI judge verifies:
      """
      The existing knowledge library remains authoritative. The agent does not
      create docs/specs or migrate documents, and adds a valid focused claim to
      the canonical authentication owner through IWE.
      """

  Scenario: Repair a partial IWE directory conservatively
    Given preparation "bootstrap-partial-iwe"
    And skills "iwe-spec-specify"
    When the operator asks:
      """
      Record an accepted requirement that password-reset links expire after one
      use. Preserve everything already present in the project's IWE setup.
      """
    Then the AI judge verifies:
      """
      The agent loads the bootstrap protocol, preserves the partial .iwe
      directory, creates only the missing config from bundled assets, retains
      docs/specs as the library, validates it, and records the requirement.
      """

  Scenario: Scope Specspine inside a mixed IWE library
    Given preparation "bootstrap-mixed-library"
    And skills "iwe-spec-specify"
    When the operator asks:
      """
      Create an authentication specification in the existing knowledge library
      and record that invalid credentials must not disclose account existence.
      Keep unrelated notes outside the specification scope.
      """
    Then the AI judge verifies:
      """
      The agent preserves the ordinary note and existing library.path, installs
      the bundled Specspine assets, scopes both new keys and schema matching to
      specspine/**, creates a valid owner through IWE, and does not validate the
      unrelated note as Specspine.
      """

  Scenario: Stop for an existing configuration collision
    Given preparation "bootstrap-config-collision"
    And skills "iwe-spec-specify"
    When the operator asks:
      """
      Add an accepted authentication requirement that password-reset links
      expire after one use. Do not replace owner-specific project conventions
      without checking with me.
      """
    Then the AI judge verifies:
      """
      The agent detects that the same-named specification template differs from
      the bundled template, explains the collision, asks before changing it,
      and leaves the entire workspace unchanged while awaiting an answer.
      """

  Scenario: Ask once when several IWE roots are plausible
    Given preparation "bootstrap-ambiguous-roots"
    And skills "iwe-spec-specify"
    When the operator asks:
      """
      Add an accepted authentication requirement for the packages in this
      workspace. First make sure you are using the correct project root.
      """
    And the operator replies:
      """
      Use package-a. Record there that invalid credentials must not disclose
      whether an account exists.
      """
    Then the AI judge verifies:
      """
      The agent identifies package-a and package-b as plausible independent IWE
      roots and asks which root owns the task without changing the workspace.
      After the answer it uses package-a without asking again, repairs only that
      package's missing Specspine setup, records a valid focused requirement,
      and leaves package-b unchanged.
      """

  Scenario: Offer IWE installation without acting before approval
    Given preparation "bootstrap-missing-iwe"
    And skills "iwe-spec-specify"
    And skill setup "missing-iwe-cli"
    When the operator asks:
      """
      Add an accepted authentication requirement that password-reset links
      expire after one use.
      """
    Then the AI judge verifies:
      """
      The agent detects that the iwe executable is unavailable, explains that
      the latest IWE CLI is required, offers to install it, and asks where
      specifications should live with docs/specs as the default. It neither
      installs software nor changes the workspace before approval.
      """
