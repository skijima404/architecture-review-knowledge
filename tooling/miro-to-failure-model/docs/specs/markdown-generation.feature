Feature: Markdown File Generation
  Generate new Markdown files from Miro export for nodes without existing files.

  Background:
    Given a YAML export file at output/node_list.yaml
    And config file specifies output folders

  # ============================================================
  # New File Generation
  # ============================================================

  Scenario: Generate new file for node without existing match
    Given a YAML node with existing_match null and id "rc-043"
    When I run the generate CLI
    Then a new file should be created at {base_path}/knowledge/curated/failure-model/root-causes/rc-043.md

  Scenario: Skip nodes with existing match
    Given a YAML node with existing_match "rc-006"
    When I run the generate CLI
    Then no new file should be created for this node
    And it should be listed as skipped

  Scenario: Generated file has correct frontmatter structure
    Given a new root_cause node with:
      | id | rc-043 |
      | title | New Root Cause |
      | introduced_in_phase | [E] |
      | triggers | [rf-001, rf-002] |
      | leads_to | [rc-005] |
    When I run the generate CLI
    Then the generated file should have:
      """
      ---
      id: rc-043
      title: New Root Cause
      type: root_cause
      introduced_in_phase:
        - E
      reviewable_in_phase: []
      leads_from: []
      triggers:
        - "[[rf-001]]"
        - "[[rf-002]]"
      leads_to:
        - "[[rc-005]]"
      tags: [root_cause]
      ---
      """

  Scenario: Generated file has body template
    Given a new root_cause node
    When I run the generate CLI
    Then the generated file should have body sections:
      | ## Description |
      | ## Context |
      | ## Impact |
      | ## Preventive Measures |
    And each section should contain "TBD"

  Scenario: Edge miro_ids are converted to node_ids
    Given a YAML node with edges containing miro_ids
    When I run the generate CLI
    Then the generated file should have edges with node_ids (e.g., [[rc-001]])
    And miro_ids should not appear in the output

  # ============================================================
  # Output Path Configuration
  # ============================================================

  Scenario: Generate uses base_path from config
    Given config.local.yaml with base_path "./test_output"
    When I run the generate CLI
    Then files should be created in tooling/miro-to-failure-model/test_output/
    And NOT in repository root

  Scenario: Generate uses repository root when base_path is ".."
    Given config.yaml with base_path ".."
    When I run the generate CLI
    Then files should be created in repository root folders

  Scenario: Folder names are configurable
    Given config with folders:
      | success_criteria | sc |
      | symptom | sym |
      | root_cause | rc |
    When I run the generate CLI
    Then root_cause files should be created in {base_path}/rc/

  # ============================================================
  # Dry Run
  # ============================================================

  Scenario: Dry-run shows what would be created
    Given nodes that would generate new files
    When I run generate CLI --dry-run
    Then it should list files that would be created
    And no files should actually be created

  Scenario: Dry-run shows skipped nodes
    Given nodes with existing matches
    When I run generate CLI --dry-run
    Then it should list skipped nodes
