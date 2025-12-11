# Epic: Backcasting MCP & Miro-to-Markdown Pipeline

This document describes the product vision and Epic Hypothesis Statement for the **Miro-to-Markdown** and **Backcasting MCP** work inside the `architecture-review-knowledge` repository.

The goal is to reliably convert visual Backcasting Maps (in Miro) into structured Markdown nodes, and expose those nodes via a local MCP interface so AI tools (Cursor, ChatGPT, etc.) can read, navigate, and co-edit the architecture review knowledge base.

---

## 1. Problem & Context

Today, Backcasting Maps are primarily maintained as Miro boards:

- The **causal structure** (Success Criteria → Symptoms → Root Causes) lives in a visual diagram.
- The **explanatory text** and architecture reasoning live in separate Markdown files.
- Synchronization between Miro and Markdown is **manual, error-prone, and time-consuming**.
- AI assistants can easily read Markdown, but **cannot reliably reconstruct structure** from PDFs, screenshots, or `.rtb` exports.

As a result:

- Updating Backcasting Maps requires **double maintenance** (Miro + Markdown).
- Root Cause–to–Success Criteria chains are not consistently available for **AI-assisted explanation, review, and training use cases**.
- The architecture review repository is harder to reuse as a **teachable, navigable knowledge base**.

---

## 2. Epic Hypothesis Statement

**Epic Name**  
Backcasting MCP & Miro-to-Markdown Pipeline

**Hypothesis**  
If we provide a local Backcasting MCP server and a Miro-to-Markdown conversion pipeline that can:

- Read existing Backcasting nodes from the `architecture-review-knowledge` repo,
- Generate new nodes from templates in a consistent Markdown format,
- And return causal chains from Root Cause to Success Criteria on demand,

then:

- AI tools (Cursor, ChatGPT, etc.) will be able to **reliably navigate, explain, and co-edit** the Backcasting knowledge,
- And we will **reduce the cognitive and operational cost** of maintaining Backcasting Maps,  
  while **increasing reuse** of the same knowledge across architecture reviews, workshops, and training scenarios.

We will know this is true when:

- We can generate or update Backcasting nodes from AI (via MCP) **without breaking** the expected Markdown/graph conventions.
- We can ask AI to **explain a root cause in context**, and it automatically pulls the correct RC→SYM→SC chain from the MCP.
- The same Backcasting knowledge is reused in **at least 2–3 different contexts**:
  - Architecture review reports
  - Training / skill assessment scenarios
  - Presentation / blog content

---

## 3. Scope (In / Out)

### In Scope (for this Epic)

- **Local Backcasting MCP interface**:
  - `get_template(node_type)` to fetch Markdown templates.
  - `get_node(id)` to read existing nodes.
  - `write_node(id, markdown, path)` to create/update nodes.
  - `get_chain_from_root(root_id, max_depth?)` to traverse RC→SC chains.

- **Miro-to-Markdown tooling**:
  - Read node-like items from Miro (via MCP / API / SDK).
  - Map sticky-note color / tags / position to:
    - `type: success_criteria | symptom | root_cause`
    - `observed_in_phase`, `introduced_in_phase` (where feasible).
  - Emit Markdown that conforms to `backcasting-map-spec.md`.

- **Developer-facing documentation**:
  - `docs/backcasting-mcp-spec.md` as the source of truth for the MCP interface.
  - A minimal `README` for the `miro-to-markdown` directory.

### Out of Scope (for this Epic)

- Full bidirectional sync between Miro and Markdown (round-trip editing).
- Rich visualization or UI beyond what Miro and existing tools already provide.
- Large-scale production hardening (multi-user concurrency, authZ, etc.).

These may become follow-up Epics once the basic pipeline is proven useful.

---

## 4. Users & Primary Use Cases

**Primary users**

- The repository owner (EA / architect) using AI tools as a **thinking partner**.
- Facilitators of Backcasting workshops who want to **move from Miro to reusable Markdown** quickly.
- Future trainees / participants consuming the Backcasting knowledge through AI-assisted explanations.

**Key use cases**

1. **Read existing Backcasting nodes via MCP**  
   - From Cursor or ChatGPT, fetch a node by ID and ask for:
     - Explanation
     - Refactoring of text
     - Translation (JP/EN) while preserving structure.

2. **Create new Root Cause or Symptom nodes from templates**  
   - Get a template for `root_cause` or `symptom`.
   - Fill in fields using AI+human co-editing.
   - Save as a new Markdown node, preserving consistency with existing IDs and relationships.

3. **Traverse RC→SC chains for explanation**  
   - Starting from `rc-XXX`, fetch the chain to SC.
   - Ask AI to explain:
     - How this root cause leads to visible symptoms.
     - Which success criteria are threatened and why.
   - Use the explanation in:
     - Architecture review reports
     - Training material
     - Workshop debriefs.

---

## 5. Leading Indicators & Success Criteria

**Leading indicators**

- MCP tools are successfully called from at least one AI client (Cursor / ChatGPT) during day-to-day work.
- New Backcasting nodes are created or edited via MCP, not only manual file editing.
- The RC→SC chain API becomes the **default way** to get context for a root cause explanation.

**Success criteria (for this Epic)**

- ✅ Can read any existing Backcasting node by ID via MCP.  
- ✅ Can generate a new node from a template and persist it as Markdown via MCP.  
- ✅ Can obtain an RC→SYM→SC chain for at least one realistic Backcasting scenario.  
- ✅ Epic is documented well enough that the same tools can be reused or extended in:
  - Other repos,
  - Or future Epics (e.g., SC→RC traversal, phase summaries, Miro round-trip).

---

## 6. Non-Goals / Guardrails

- This Epic does **not** attempt to:
  - Replace Miro as the primary **visual** authoring tool.
  - Implement a full graph database or query language on top of the Markdown.
  - Introduce complex configuration or heavy dependencies that make local usage difficult.

- Guardrails:
  - Keep the local MCP server **simple enough** to run inside a devcontainer or local Python environment.
  - Prefer **plain files + simple conventions** over sophisticated infrastructure.
  - Ensure that any AI-facing interface (MCP tools, JSON shapes) is **stable and documented** in this folder.

---
