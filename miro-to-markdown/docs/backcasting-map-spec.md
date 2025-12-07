# Backcasting Map Node Specification (Markdown v0)

This document defines the **Markdown node specification** for Backcasting Map nodes (Success Criteria / Symptom / Root Cause) used in the `architecture-review-knowledge` repository.

Goals:
- Clarify the target Markdown format when converting Backcasting Maps created in Miro into node files
- Fix the output requirements for automation tools (Miro → Markdown / LangChain chains, etc.)
- Separate the responsibilities between what is generated automatically and what is edited/augmented by humans + GenAI
- **Align Markdown frontmatter relationship names with the GraphDB edge labels** to reduce cognitive overhead

---

## 1. Node Types

Backcasting Map nodes are classified into the following three types:

- `success_criteria`  – Desired outcomes / target states
- `symptom`           – Surface-level symptoms (formerly: Risk Factor). IDs may still use the `rf-` prefix
- `root_cause`        – Structural root causes

### 1.1 Relationship between `id` and `type`

- `id` is the identifier of a node and is treated as a **label that may include historical naming**
  - Examples: `sc-002`, `rf-004`, `rc-006`
- `type` is the **single source of truth** for the node type
  - Example: if `type: symptom`, then the node is treated as a Symptom even when `id: rf-004`
- Automation tools **MUST NOT infer `type` from the `id` prefix**

---

## 2. Common Structure (frontmatter & body)

All node files share the following basic structure:

```markdown
---
id: <string>                # Required: unique ID
title: <string>             # Required: node title (English or Japanese)
type: success_criteria | symptom | root_cause

# Phase-related fields
observed_in_phase: ["E","F"]      # Generally required: phases where this node is observed/validated
introduced_in_phase: ["B","C"]   # Generally required: phases where this node is introduced (if not applicable, use an empty array or omit)
reviewable_in_phase: ["D","E"]   # Optional: phases where this node is reviewable (e.g., gate reviews)

tags: [string]              # Type tag + additional tags
---

## Description
(Explanation of the node itself)
```

- The frontmatter represents **structural information**
- The body contains **meaning / context / impact / measures** and other narrative elements

---

## 3. Success Criteria Node Specification

### 3.1 Frontmatter

```yaml
---
id: sc-002
title: Compliance with Architecture Principles
type: success_criteria

threatened_by:
  - "[[rf-010]]"        # rf-xxx (Symptom) or rc-xxx (Root Cause)
related_success_criteria:
  - "[[sc-006]]"        # Optional: sc-xxx that are related or affected

observed_in_phase: ["E","F"]
introduced_in_phase: ["B","C"]
reviewable_in_phase: ["D","E","F"]

tags: [success_criteria]
---
```

Field definitions:

- `id` (required) – Recommended format: `sc-XXX`
- `title` (required) – Title of the success criteria
- `type` (required) – Always `success_criteria`
- `threatened_by` (optional) – Links to Symptom / Root Cause nodes that threaten this success criteria
  - Example: `"[[rf-010]]"`
- `related_success_criteria` (optional) – Links to related or affected Success Criteria (`sc-xxx`)
- `observed_in_phase` / `introduced_in_phase` (generally required)
  - Phases (e.g., TOGAF phases) where this success criteria is observed or introduced
- `reviewable_in_phase` (optional)
  - Phases where this success criteria is reviewable (e.g., as part of gate reviews)
- `tags` (optional) – Should contain at least `success_criteria`

### 3.2 Body Sections

```markdown
## Description
The system is designed and implemented in compliance with the architecture principles. Design decisions are consistent and aligned with the overall direction of the enterprise.

## Rationale
Compliance with principles is essential to reduce design variability and person-dependence, and to ensure overall consistency. It also contributes to adaptability to change and higher reusability.
```

- `Description` – What the success criteria means
- `Rationale` – Why it is important / what value it protects

---

## 4. Symptom Node Specification

A Symptom represents an undesirable state or a sign of risk that is visible at the surface.

### 4.1 Frontmatter

```yaml
---
id: rf-004
title: Design-induced operational risk
type: symptom

observed_in_phase:
  - G
  - H

# Relationships (aligned with Graph edge labels)
triggered_by:
  - "[[rc-023]]"        # Upstream Root Causes (rc-xxx)
  - "[[rf-001]]"        # Upstream Symptoms (rf-xxx) that precede or cause this symptom (optional)

triggers: []
  # Optional: downstream Symptoms (rf-xxx) if this symptom leads to other symptoms

threatens:
  - "[[sc-006]]"        # Success Criteria (sc-xxx) endangered by this symptom

tags: [symptom]
---
```

Field definitions:

- `id` (required) – Historically in the form `rf-XXX`, but `type: symptom` is the truth
- `type` (required) – `symptom`
- `observed_in_phase` (generally required) – Phases where this symptom is observed
- `triggered_by` (optional) – Links to upstream Root Cause or Symptom nodes that trigger this symptom
  - Example: `"[[rc-023]]"` or `"[[rf-001]]"`
- `triggers` (optional) – Links to downstream Symptom nodes (`rf-xxx`) that this symptom triggers
- `threatens` (optional) – Links to Success Criteria nodes (`sc-xxx`) that are endangered by this symptom
- `tags` (optional) – Should contain at least `symptom`

> Note: `threatened_by` (on the Success Criteria side) and `threatens` (on the Symptom side) **do not both have to be populated**.
> The primary relationship for data entry is `threatened_by` on Success Criteria; `threatens` can be derived or maintained for convenience and for causal traversal.

### 4.2 Body Sections

```markdown
## Description
Operational incidents and errors occur not because of operator skill issues, but because operational aspects were not considered in the design phase.

## Context
Typical patterns include lack of knowledge due to non-standard configurations, missing automation/reproducibility of runbooks, insufficient observability, and fragile synchronization design. Many of these issues could have been avoided if the operations team had been involved during the design phase.

## Severity
TBD
```

- `Description` – Explanation of the symptom itself
- `Context` – Typical patterns and background in which this symptom appears
- `Severity` – Severity assessment (may later be promoted into a frontmatter field)

---

## 5. Root Cause Node Specification

A Root Cause represents a structural cause or a mistaken assumption.

### 5.1 Frontmatter

```yaml
---
id: rc-006
title: Unrealistic transition architecture
type: root_cause

introduced_in_phase:
  - F
reviewable_in_phase:
  - F

# Relationships (aligned with Graph edge labels)
leads_from:
  - "[[rc-013]]"          # Upstream Root Causes (`rc-xxx`) — symmetric with `leads_to`

triggers:
  - "[[rf-001]]"          # Downstream Symptoms (`rf-xxx`)

leads_to: []
  # Optional: downstream Root Causes (`rc-xxx`) reached from this cause

tags: [root_cause]
---
```

Field definitions:

- `type` (required) – `root_cause`
- `introduced_in_phase` (generally required) – Phases in the system lifecycle where this cause was introduced
- `reviewable_in_phase` (optional) – Phases where this cause can be reviewed
- `leads_from` (optional) – Links to upstream Root Cause nodes (`rc-xxx`) — symmetric with `leads_to`
- `triggers` (optional) – Links to downstream Symptom nodes (`rf-xxx`) that this cause triggers
- `leads_to` (optional) – Links to downstream Root Cause nodes (`rc-xxx`) reached from this cause
- `tags` (optional) – Should contain at least `root_cause`

> Note: For Root Causes, `leads_to` / `leads_from` represent the forward and reverse chains between RC nodes. Using a symmetric verb pair makes bidirectional traversal intuitive.

### 5.2 Body Sections

```markdown
## Description
The transition architecture responsible for migrating from the current system to the new system is designed without considering feasibility or constraints of the existing environment.

## Context
There is insufficient understanding of the baseline architecture (e.g., spaghetti code with complex dependencies), and the transition architecture is defined based on severely incorrect assumptions.
In addition, there is a lack of understanding of solution composition and staged rollout (e.g., staging environments, phased deployment), resulting in missing intermediate stages and workarounds in the design.

## Impact
Cutover procedures become unrealistic, leading to infeasible cutover or failure of the migration plan.

## Preventive Measures
TBD
```

---

## 6. Division of Responsibilities: Auto-generation (Step 3) vs Human + GenAI Editing (Step 4)

### 6.1 Step 3: Fields that the Miro → Markdown converter should aim to populate

- Common
  - `id`                – Either matched with existing files or newly assigned
  - `title`             – From Miro node label
  - `type`              – From Miro node type (color / shape / prefix, etc.)
  - `tags`              – At minimum, the node `type`
- Success Criteria
  - `threatened_by`
- Symptom
  - `observed_in_phase` (depending on Miro expression rules)
  - `triggered_by`
  - `triggers`
  - `threatens`
- Root Cause
  - `introduced_in_phase` / `reviewable_in_phase` (depending on Miro expression rules)
  - `leads_from`
  - `triggers`
  - `leads_to`

### 6.2 Step 4: Fields/sections to be edited by humans + GenAI after Markdown generation

- Body content
  - `## Description`
  - `## Rationale` / `## Context` / `## Impact` / `## Severity` / `## Preventive Measures`, etc.
- Evaluation / status fields (to be added when needed)
  - e.g., `status`, `severity`, `last_reviewed_at`, `approved_by`, etc.

---

## 7. Notes for Future Extensions

- Assuming import into a GraphDB or a GenAI memory structure, the relationship fields in frontmatter can be mapped directly to edges
- Miro-side expression rules (colors / prefixes / tags / swimlanes, etc.) will be defined separately in `docs/backcasting-map-miro-rules.md`
- Any LangChain-based conversion pipeline should treat this frontmatter specification as its success criteria
- The relationship field names in this spec (`triggers`, `triggered_by`, `threatens`, `threatened_by`, `leads_to`) are intentionally aligned with the causal edge labels defined for Graph representations to minimize cognitive load and rename overhead.
