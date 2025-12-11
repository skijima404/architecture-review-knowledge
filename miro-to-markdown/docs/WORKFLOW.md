# Gherkin-Driven Development Workflow

This document defines the workflow for developing features in this repository using Gherkin specifications as contracts between human and GenAI.

## Workflow Overview

```
1. Request (Human)
   ↓
2. Gherkin Scenario (GenAI drafts, Human reviews)
   ↓
3. Approval (Human)
   ↓
4. Implementation (GenAI)
   ↓
5. Verification (GenAI runs tests, reports results)
   ↓
6. Done
```

---

## Step-by-Step Instructions

### Step 1: Request

Human describes the feature or change in natural language.

**Example:**
> "I want the export CLI to support a --verbose flag that shows detailed progress."

### Step 2: Gherkin Scenario

GenAI drafts Gherkin scenarios covering:
- Happy path
- Edge cases
- Error handling

**GenAI should:**
1. Create or update the appropriate `.feature` file in `docs/specs/`
2. Present the scenarios for review
3. Wait for approval before implementing

**Example output:**

```gherkin
Feature: Verbose Export Mode

  Scenario: Verbose flag shows detailed progress
    Given the --verbose flag is provided
    When I run the export CLI
    Then it should print each sticky note being processed
    And it should print connector processing details

  Scenario: Default mode shows minimal output
    Given no --verbose flag is provided
    When I run the export CLI
    Then it should show summary counts only
```

### Step 3: Approval

Human reviews and either:
- **Approves**: "OK, implement this"
- **Requests changes**: "Add a scenario for invalid board ID"
- **Rejects**: "Actually, I don't need this"

### Step 4: Implementation

GenAI implements the feature to satisfy all scenarios.

**GenAI should:**
1. List affected files before making changes
2. Implement changes
3. Ensure existing tests still pass
4. Report completion

### Step 5: Verification

GenAI verifies the implementation:
1. Run relevant tests
2. Run linter checks
3. Manual verification if needed
4. Report results

**If issues found:** Fix and re-verify.

### Step 6: Done

Human confirms completion. Gherkin file remains as living documentation.

---

## File Structure

```
docs/specs/
├── miro-export.feature       # Miro export functionality
├── diff-and-apply.feature    # Diff generation and application
├── markdown-generation.feature # Markdown file generation
└── {new-feature}.feature     # Add new features here
```

---

## Prompt Templates

### Request New Feature

```
I want to add [FEATURE DESCRIPTION].

Please:
1. Draft Gherkin scenarios in docs/specs/{feature}.feature
2. Show me the scenarios for review
3. Wait for my approval before implementing
```

### Request Change to Existing Feature

```
I want to change [EXISTING FEATURE] to [NEW BEHAVIOR].

Please:
1. Update the relevant Gherkin scenarios in docs/specs/
2. Show me the changes for review
3. Wait for my approval before implementing
```

### Bug Report

```
There's a bug: [DESCRIPTION]

Please:
1. Add a Gherkin scenario that describes the expected behavior
2. Verify the current implementation fails this scenario
3. Fix the implementation
4. Verify the scenario now passes
```

### Session Resume

```
I'm continuing work on miro-to-markdown.

Please:
1. Read docs/specs/*.feature to understand current specifications
2. Read TASKS.md for current status
3. Summarize what's implemented and what's pending
```

---

## Rules for GenAI

1. **Never implement without approved Gherkin scenarios**
   - Draft scenarios first
   - Wait for human approval

2. **Keep Gherkin files updated**
   - When implementation changes, update scenarios
   - Scenarios are the source of truth for behavior

3. **Report impact before changes**
   - List affected files
   - Explain what will change

4. **Verify after implementation**
   - Run tests
   - Check for linter errors
   - Confirm scenarios are satisfied

5. **Ask if uncertain**
   - If requirements are ambiguous, ask before drafting scenarios
   - If implementation approach is unclear, propose options

---

## Example Session

```
Human: I want to add a --format json option to export CLI that outputs JSON instead of YAML.

GenAI: I'll draft Gherkin scenarios for this feature.

[Creates/updates docs/specs/miro-export.feature]

Here are the scenarios:

  Scenario: JSON format output
    Given the --format json flag is provided
    When I run the export CLI
    Then the output file should be valid JSON
    And the file extension should be .json

  Scenario: Default format is YAML
    Given no --format flag is provided
    When I run the export CLI
    Then the output file should be YAML
    And the file extension should be .yaml

Do you approve these scenarios?
