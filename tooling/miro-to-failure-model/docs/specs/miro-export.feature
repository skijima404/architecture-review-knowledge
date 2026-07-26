Feature: Miro Board Export
  Export Backcasting Map data from Miro board to intermediate YAML format.

  Background:
    Given a Miro board with Backcasting Map content
    And .env file contains valid MIRO_ACCESS_TOKEN and MIRO_BOARD_ID
    And config file specifies output settings

  # ============================================================
  # Node Type Detection
  # ============================================================

  Scenario: Red sticky notes are mapped to Success Criteria
    Given a red sticky note with title "Day 1 Operation Success"
    When I run the export CLI
    Then the YAML output should contain a success_criteria node
    And the node should have id prefix "sc-"

  Scenario: Light yellow sticky notes are mapped to Symptom
    Given a light yellow sticky note with title "Repeated delays"
    When I run the export CLI
    Then the YAML output should contain a symptom node
    And the node should have id prefix "rf-"

  Scenario: Light blue sticky notes are mapped to Root Cause
    Given a light blue sticky note with title "Unrealistic transition architecture"
    When I run the export CLI
    Then the YAML output should contain a root_cause node
    And the node should have id prefix "rc-"

  Scenario: Gray sticky notes are ignored
    Given a gray sticky note with title "Architecture Review"
    When I run the export CLI
    Then the YAML output should NOT contain this node

  Scenario: Header labels are excluded
    Given a sticky note with title "Success Criteria" (header label)
    When I run the export CLI
    Then the YAML output should NOT contain this node

  # ============================================================
  # Existing Node Matching
  # ============================================================

  Scenario: Miro node matches existing Markdown file by title
    Given an existing Markdown file "knowledge/curated/failure-model/root-causes/rc-006.md" with title "Unrealistic transition architecture"
    And a Miro sticky note with the same title
    When I run the export CLI
    Then the YAML node should have existing_match "rc-006"
    And the node id should be "rc-006"

  Scenario: New node gets generated ID
    Given a Miro sticky note with title "Brand New Root Cause"
    And no existing Markdown file matches this title
    When I run the export CLI
    Then the YAML node should have existing_match null
    And the node id should be a new generated ID (e.g., "rc-043")

  # ============================================================
  # Edge Detection (Connectors)
  # ============================================================

  Scenario: Connector from Root Cause to Symptom creates triggers edge
    Given a connector from a root_cause node to a symptom node
    When I run the export CLI
    Then the root_cause node should have "triggers" edge to the symptom
    And the symptom node should have "triggered_by" edge from the root_cause

  Scenario: Connector from Symptom to Success Criteria creates threatens edge
    Given a connector from a symptom node to a success_criteria node
    When I run the export CLI
    Then the symptom node should have "threatens" edge to the success_criteria
    And the success_criteria node should have "threatened_by" edge from the symptom

  Scenario: Connector between Root Causes uses X position for direction
    Given two root_cause nodes at different X positions
    And a connector between them
    When I run the export CLI
    Then if end_x > start_x, source has "leads_to" and target has "leads_from"
    And if end_x < start_x, source has "leads_from" and target has "leads_to"

  Scenario: Cross-type connectors ignore visual direction
    Given a connector drawn from symptom to root_cause (reversed visual direction)
    When I run the export CLI
    Then the edge should be normalized to root_cause.triggers → symptom
    And visual direction should be ignored for cross-type edges

  Scenario: Disconnected connectors generate warnings
    Given a connector that is not attached to sticky notes on both ends
    When I run the export CLI
    Then a warning should be recorded for this connector
    And no edge should be created

  # ============================================================
  # Phase Detection
  # ============================================================

  Scenario: Phase detected from X position relative to header shapes
    Given phase header shapes on the board: A, B-D, E, F, G, H
    And a root_cause sticky note positioned in the E column
    When I run the export CLI
    Then the node should have introduced_in_phase ["E"]

  Scenario: B-D phase is expanded to B, C, D
    Given a sticky note positioned in the B-D column
    When I run the export CLI
    Then the phase should be expanded to ["B", "C", "D"]

  Scenario: Phase field depends on node type
    Given a root_cause node in phase F
    And a symptom node in phase G
    When I run the export CLI
    Then root_cause should have "introduced_in_phase: [F]"
    And symptom should have "observed_in_phase: [G]"

  # ============================================================
  # Config-based Path Resolution
  # ============================================================

  Scenario: Export checks existing nodes in config base_path
    Given config.local.yaml with base_path "./test_output"
    And no files exist in test_output/
    When I run the export CLI
    Then all nodes should have existing_match null
    And it should NOT check repository root folders

  Scenario: Export uses repository root when base_path is ".."
    Given config.yaml with base_path ".."
    And existing files in the configured curated Failure Model directories
    When I run the export CLI
    Then nodes should be matched against repository root files
