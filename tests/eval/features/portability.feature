Feature: IWE specification skills outside a web-service stack
  The skills are exercised against a small Python filesystem tool so evaluation
  is not limited to Node, HTTP, authentication, or database boundaries.

  Scenario: Map a Python file-indexing boundary without inventing intent
    Given fixture "python-file-indexer"
    Given preparation "baseline"
    And skills "iwe-spec-map"
    When the operator asks:
      """
      Inspect how the indexer currently reads files and writes its index. Record
      only boundary-significant evidence, keep implementation observations
      separate from accepted behavior, and do not invent new requirements.
      """
    Then the AI judge verifies:
      """
      The existing Indexing owner receives useful OBS or INF evidence about its
      filesystem boundary without turning code into accepted intent. Inspection
      metadata is honest, the schema remains valid, and no parallel graph or
      generated inventory is introduced.
      """
