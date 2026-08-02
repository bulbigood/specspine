Feature: Interactive Specspine workspace setup
  The dedicated setup skill is evaluated independently from the operational
  specification workflows. IWE is preinstalled in every scenario.

  Scenario: Configure a new workspace with a nested custom scope
    Given preparation "setup-new-custom-scope"
    And skills "iwe-spec-setup"
    When the operator asks:
      """
      Set up Specspine in this project. Guide me through every directory choice
      before changing the workspace.
      """
    And the operator replies:
      """
      Use the current working directory as the workspace root.
      """
    And the operator replies:
      """
      Store all IWE-managed Markdown in knowledge.
      """
    And the operator replies:
      """
      Store Specspine documents in knowledge/architecture/specs.
      """
    And the operator replies:
      """
      The resolved paths and derived key prefix are correct. Apply the setup.
      """
    Then the AI judge verifies:
      """
      The agent follows the setup skill as a linear conversation, initializes
      IWE only after the workspace and library decisions, and does not install
      software because IWE is already available. The resulting library.path is
      knowledge, the specification template uses
      architecture/specs/{{slug}}, the schema match is
      architecture/specs/**, the canonical schema is installed, unrelated
      project files are preserved, and IWE schema validation succeeds.
      """

  Scenario: Reject a specification directory outside the IWE library
    Given preparation "setup-new-contained-scope"
    And skills "iwe-spec-setup"
    When the operator asks:
      """
      Set up Specspine here and ask me where its files should live.
      """
    And the operator replies:
      """
      Use the current working directory as the workspace root.
      """
    And the operator replies:
      """
      Use docs as the IWE Markdown library.
      """
    And the operator replies:
      """
      Put the Specspine files in specs at the workspace root.
      """
    And the operator replies:
      """
      Use docs/specs instead.
      """
    And the operator replies:
      """
      The corrected paths are right. Apply the setup.
      """
    Then the AI judge verifies:
      """
      The agent rejects workspace/specs because it is outside the selected docs
      library, explains the containment requirement, accepts the corrected
      docs/specs path, and does not install Specspine configuration before final
      confirmation. The final template and schema are scoped to specs/** inside
      docs, no workspace-root specs directory is created, and validation passes.
      """

  Scenario: Leave an existing valid setup unchanged
    Given preparation "setup-existing-workspace"
    And skills "iwe-spec-setup"
    When the operator asks:
      """
      Check and complete the Specspine setup in this existing project without
      rewriting configuration that is already correct.
      """
    Then the AI judge verifies:
      """
      The agent recognizes the existing template, schema binding, and schema as
      identical canonical setup, preserves every workspace file byte-for-byte,
      performs no installation or normalization, takes the existing-valid
      fast path without asking the operator to reconfirm unchanged paths, and
      reports successful IWE validation.
      """

  Scenario: Stop before replacing conflicting Specspine configuration
    Given preparation "setup-config-collision"
    And skills "iwe-spec-setup"
    When the operator asks:
      """
      Set up Specspine in this existing project, but do not overwrite any
      project-specific configuration conflict without separate approval.
      """
    And the operator replies:
      """
      Keep the current docs library.
      """
    And the operator replies:
      """
      Use docs/specs for Specspine documents.
      """
    And the operator replies:
      """
      The paths are correct. Inspect the setup, but stop if replacement would
      be required.
      """
    Then the AI judge verifies:
      """
      The agent detects the differing specification template, shows or clearly
      explains the conflict, requests separate replacement approval, and leaves
      the entire workspace unchanged. It does not treat path confirmation as
      permission to overwrite project-specific configuration.
      """
