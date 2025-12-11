# Backcasting MCP Specification

This document defines the local **Backcasting MCP** interface used by the `miro-to-markdown` tools.  
It provides a simple CRUD-style interface for reading and writing Backcasting nodes.

The MCP server is responsible for:

- Reading and writing **Backcasting nodes** (Markdown files) in the `architecture-review-knowledge` repository.
- Providing **templates** for new nodes.
- Returning **causal chains** from Root Cause (RC) to Success Criteria (SC), using the Backcasting relationships defined in `backcasting-map-spec.md`.

Miro access (via Miro MCP or REST API) is explicitly **out of scope** for this spec.  
This spec only covers the *local* Backcasting MCP.

---

## 1. Resource Overview

The Backcasting MCP exposes the following logical resource types:

- `backcasting_template`  
  - Templates for each node type (`root_cause`, `symptom`, `success_criteria`).

- `backcasting_node`  
  - A single Backcasting node (one Markdown file), including parsed frontmatter and raw Markdown.

- `backcasting_chain`  
  - A causal chain starting from a Root Cause node and rolling up to one or more Success Criteria.

These resources are addressed using a simple URI scheme:

- Templates  
  - `backcasting://templates/{node_type}`  
  - `node_type ∈ {root_cause, symptom, success_criteria}`

- Nodes  
  - `backcasting://nodes/{id}`  
  - `id` is the logical node ID, e.g. `rc-006`, `rf-004`, `sc-002`.

- Chains (Root → SC direction)  
  - `backcasting://chains/from-root/{root_id}`  
  - `root_id` is a `root_cause` node ID, e.g. `rc-006`.

These URIs are **logical identifiers** used in MCP responses.  
The MCP implementation is free to map them to local filesystem paths or other internal structures.

---

## 2. Data Models

### 2.1 Backcasting Template

A template describes how to create a new node of a given type.

```jsonc
{
  "type": "backcasting_template",
  "node_type": "root_cause", // or "symptom" | "success_criteria"

  "frontmatter_schema": {
    "required": ["id", "title", "type"],
    "optional": [
      "observed_in_phase",
      "introduced_in_phase",
      "reviewable_in_phase",
      "triggered_by",
      "triggers",
      "leads_from",
      "leads_to",
      "threatens",
      "threatened_by",
      "tags"
    ]
  },

  "markdown": "---\n"
  + "id: rc-xxx\n"
  + "title: \n"
  + "type: root_cause\n"
  + "introduced_in_phase: []\n"
  + "reviewable_in_phase: []\n"
  + "leads_from: []\n"
  + "triggers: []\n"
  + "leads_to: []\n"
  + "tags: [root_cause]\n"
  + "---\n\n"
  + "## Description\n\n"
  + "## Context\n\n"
  + "## Impact\n\n"
  + "## Preventive Measures\n"
}
```

Notes:

- `frontmatter_schema` is a lightweight description so the LLM knows **which keys to fill**.
- `markdown` is a ready-to-use template that can be edited and written as a new node.

---

### 2.2 Backcasting Node

A `backcasting_node` represents one Markdown file in the repository.

```jsonc
{
  "type": "backcasting_node",
  "id": "rc-006",
  "title": "Unrealistic transition architecture",
  "node_type": "root_cause", // or "symptom" | "success_criteria"

  "phase": {
    "observed_in_phase": [],
    "introduced_in_phase": ["F"],
    "reviewable_in_phase": ["F"]
  },

  "relations": {
    // Backcasting / roll-up relationships, aligned with ADR-0002 / ADR-0004
    "leads_from": ["rc-013"],            // upstream root causes (for RC nodes)
    "triggered_by": [],                  // upstream root causes or symptoms (for Symptom nodes)
    "triggers": ["rf-001"],              // downstream symptoms
    "leads_to": [],                      // downstream root causes
    "threatens": [],                     // (for Symptom) downstream success criteria
    "threatened_by": [],                 // (for SC) upstream symptoms
    "tags": ["root_cause", "backcasting"]
  },

  "markdown": "---\n"
  + "id: rc-006\n"
  + "title: Unrealistic transition architecture\n"
  + "type: root_cause\n"
  + "introduced_in_phase:\n"
  + "  - F\n"
  + "reviewable_in_phase:\n"
  + "  - F\n"
  + "leads_from:\n"
  + "  - \"[[rc-013]]\"\n"
  + "triggers:\n"
  + "  - \"[[rf-001]]\"\n"
  + "leads_to: []\n"
  + "tags: [root_cause]\n"
  + "---\n\n"
  + "## Description\n..."
  ,

  "path": "root_cause/rc-006.md"
}
```

Notes:

- `markdown` is the raw file content (frontmatter + body).
- `path` is the relative file path within the repository. The MCP server is responsible for mapping `id` ⇄ `path`.

---

### 2.3 Backcasting Chain (Root → Success Criteria)

A `backcasting_chain` represents one or more causal paths starting from a root cause and ending at success criteria.

```jsonc
{
  "type": "backcasting_chain",
  "direction": "root_to_success_criteria",
  "root_id": "rc-006",

  "nodes": [
    { "id": "rc-006", "node_type": "root_cause", "title": "Unrealistic transition architecture" },
    { "id": "rf-001", "node_type": "symptom", "title": "Unstable cutover plan" },
    { "id": "sc-006", "node_type": "success_criteria", "title": "Smooth and reversible cutover" }
  ],

  // Optional explicit path information, useful if multiple paths exist
  "paths": [
    ["rc-006", "rf-001", "sc-006"]
  ]
}
```

Notes:

- v1 can return a **single representative path** in `paths`.  
  Later versions may support multiple paths and path ranking.

---

## 3. MCP Tools

This section describes the main MCP tools (operations) exposed by the Backcasting MCP server.  
Actual MCP wiring (e.g. `.mcp.json`, JSON-RPC method names) can be derived from this logical spec.

### 3.1 `get_template`

Return a template for creating a new node of a given type.

**Logical name**

- `backcasting.get_template`

**Request**

```jsonc
{
  "node_type": "root_cause" // or "symptom" | "success_criteria"
}
```

**Response**

- A `backcasting_template` resource as defined in §2.1.

```jsonc
{
  "type": "backcasting_template",
  "node_type": "root_cause",
  "frontmatter_schema": { "...": "..." },
  "markdown": "---\n...\n"
}
```

---

### 3.2 `get_node`

Fetch a single Backcasting node by ID.

**Logical name**

- `backcasting.get_node`

**Request**

```jsonc
{
  "id": "rc-006"
}
```

**Response**

- A `backcasting_node` resource as defined in §2.2.

```jsonc
{
  "type": "backcasting_node",
  "id": "rc-006",
  "title": "Unrealistic transition architecture",
  "node_type": "root_cause",
  "phase": { "...": "..." },
  "relations": { "...": "..." },
  "markdown": "---\n...\n",
  "path": "root_cause/rc-006.md"
}
```

---

### 3.3 `write_node`

Create or update a Backcasting node on disk.

**Logical name**

- `backcasting.write_node`

**Request**

```jsonc
{
  "id": "rc-006",
  "markdown": "---\n...\n",
  "path": "root_cause/rc-006.md"
}
```

- `id`  
  - Logical node ID, must match the `id` in the frontmatter.
- `markdown`  
  - Full file contents (frontmatter + body).
- `path`  
  - Relative path where the file should be written.  
    The server MAY override this based on internal mapping rules.

**Response**

```jsonc
{
  "type": "backcasting_node",
  "id": "rc-006",
  "title": "Unrealistic transition architecture",
  "node_type": "root_cause",
  "phase": { "...": "..." },
  "relations": { "...": "..." },
  "markdown": "---\n...\n",
  "path": "root_cause/rc-006.md"
}
```

Notes:

- The server is responsible for:
  - Writing the file to disk.
  - Re-parsing the frontmatter to populate `phase` and `relations`.
  - Returning the canonical `path`.

---

### 3.4 `get_chain_from_root`

Return a causal chain starting from a Root Cause and rolling up to one or more Success Criteria.

**Logical name**

- `backcasting.get_chain_from_root`

**Request**

```jsonc
{
  "root_id": "rc-006",
  "max_depth": 5,          // optional
  "include_markdown": false // optional; v1 default = false
}
```

- `root_id`  
  - ID of the starting `root_cause`.
- `max_depth`  
  - Optional limit for traversal depth (default may be reasonable, e.g. 5).
- `include_markdown`  
  - If `true`, the server MAY include `markdown` for nodes in the chain.  
    v1 can ignore this or keep it `false` by default.

**Response**

- A `backcasting_chain` resource as defined in §2.3.

```jsonc
{
  "type": "backcasting_chain",
  "direction": "root_to_success_criteria",
  "root_id": "rc-006",
  "nodes": [
    { "id": "rc-006", "node_type": "root_cause", "title": "Unrealistic transition architecture" },
    { "id": "rf-001", "node_type": "symptom", "title": "Unstable cutover plan" },
    { "id": "sc-006", "node_type": "success_criteria", "title": "Smooth and reversible cutover" }
  ],
  "paths": [
    ["rc-006", "rf-001", "sc-006"]
  ]
}
```

---

## 4. Typical Workflows

Typical usage patterns for the Backcasting MCP tools:

1. **Create a new Root Cause node**
   - Call `get_template(node_type="root_cause")` to get a blank template.
   - Fill in frontmatter/body using the template.
   - Call `write_node(id, markdown, path)` to persist.

2. **Explain a Root Cause with context**
   - Call `get_node(id="rc-006")` to read the node.
   - Call `get_chain_from_root(root_id="rc-006")` to get the causal chain.
   - Use the `nodes` and `paths` in the chain to generate explanation text.

3. **Traverse from RC to SC for review**
   - Call `get_chain_from_root(root_id="rc-XXX")`.
   - Optionally fetch each node via `get_node(id)` for detailed content.

---

## 5. Future Extensions (Non-blocking for v1)

The following ideas are explicitly **out of scope for v1**, but the model is designed to allow them later:

- `backcasting://boards/{board_id}`  
  - Explicit grouping of nodes into logical boards or scenarios.

- `backcasting://chains/from-success/{sc_id}`  
  - The reverse direction (SC → RF → RC) which may fan out heavily.

- Phase-centric summaries:
  - e.g. `backcasting://summaries/by-phase/F` returning all nodes observed/introduced in phase F.

- Miro-linked metadata:
  - Add `miro_id` / `miro_board_id` to `backcasting_node` for round-trip mapping.

---

This spec should be treated as the **source of truth** for implementing the local Backcasting MCP server and for wiring MCP tools in AI clients.
