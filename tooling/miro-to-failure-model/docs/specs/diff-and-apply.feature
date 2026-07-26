Feature: Diff Generation and Application
  Compare Miro export with existing Markdown files and apply changes.

  Background:
    Given a YAML export file at output/node_list.yaml
    And existing Markdown files in the configured base_path

  # ============================================================
  # Diff Generation
  # ============================================================

  Scenario: Detect added edges
    Given an existing Markdown file rc-001.md with triggers: []
    And the YAML export shows rc-001 has triggers: [rf-001]
    When I run the diff CLI
    Then the diff report should show rc-001.triggers +[rf-001]

  Scenario: Detect removed edges
    Given an existing Markdown file rc-001.md with triggers: [rf-001, rf-002]
    And the YAML export shows rc-001 has triggers: [rf-001]
    When I run the diff CLI
    Then the diff report should show rc-001.triggers -[rf-002]

  Scenario: Detect phase changes
    Given an existing Markdown file rc-001.md with introduced_in_phase: [D]
    And the YAML export shows rc-001 has introduced_in_phase: [E]
    When I run the diff CLI
    Then the diff report should show rc-001.introduced_in_phase [D] → [E]

  Scenario: No differences when in sync
    Given existing Markdown files match the YAML export exactly
    When I run the diff CLI
    Then it should report "No differences found"

  Scenario: Diff uses config base_path
    Given config.local.yaml with base_path "./test_output"
    When I run the diff CLI
    Then it should compare against files in test_output/
    And it should NOT compare against repository root files

  # ============================================================
  # Diff Application
  # ============================================================

  Scenario: Apply adds new edges to existing files
    Given a diff report with rc-001.triggers +[rf-001]
    When I run apply_diff
    Then rc-001.md should have triggers: ["[[rf-001]]"]

  Scenario: Apply removes edges from existing files
    Given a diff report with rc-001.triggers -[rf-002]
    And rc-001.md currently has triggers: ["[[rf-001]]", "[[rf-002]]"]
    When I run apply_diff
    Then rc-001.md should have triggers: ["[[rf-001]]"]

  Scenario: Apply updates phase fields
    Given a diff report with rc-001.introduced_in_phase [D] → [E]
    When I run apply_diff
    Then rc-001.md should have introduced_in_phase: [E]

  Scenario: Dry-run shows changes without modifying files
    Given a diff report with changes
    When I run apply_diff --dry-run
    Then it should show what would be changed
    And no files should be modified

  Scenario: Apply preserves body content
    Given rc-001.md with custom Description and Context sections
    When I run apply_diff with edge changes
    Then the body content should remain unchanged
    And only frontmatter should be updated

