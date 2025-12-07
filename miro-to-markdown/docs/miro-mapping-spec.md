# Miro → Markdown Mapping Specification

This document defines the mapping rules for converting Miro board elements to Backcasting Markdown nodes.

---

## 1. Node Type Mapping (Color-based)

Sticky notes are mapped to node types based on their `fillColor` attribute.

| Miro `fillColor` | Node Type | ID Prefix | Notes |
|------------------|-----------|-----------|-------|
| `red` | `success_criteria` | `sc-` | Success Criteria |
| `light_yellow` | `symptom` | `rf-` | Symptom (Risk Factor) |
| `light_blue` | `root_cause` | `rc-` | Root Cause |
| `gray` | _(ignored)_ | — | Memos, notes, not a node |
| _(other)_ | _(ignored)_ | — | Unrecognized colors are skipped |

### 1.1 Implementation Notes

```python
COLOR_TO_NODE_TYPE = {
    "red": "success_criteria",
    "light_yellow": "symptom", 
    "light_blue": "root_cause",
}

IGNORED_COLORS = {"gray"}

def get_node_type(fill_color: str) -> str | None:
    """Return node type for a color, or None if ignored."""
    if fill_color in IGNORED_COLORS:
        return None
    return COLOR_TO_NODE_TYPE.get(fill_color)
```

---

## 2. Field Extraction from Sticky Note

### 2.1 Direct Mapping

| Markdown Field | Miro Source | Notes |
|----------------|-------------|-------|
| `title` | `data.content` | HTML tags stripped |
| `type` | Derived from `style.fillColor` | See §1 |
| `id` | Generated or matched | `{prefix}-{seq}` format |
| `tags` | `[type]` | At minimum, the node type |

### 2.2 Example: Miro Sticky Note → Frontmatter

**Miro API Response:**
```json
{
  "id": "3458764517454286230",
  "type": "sticky_note",
  "data": {
    "content": "<p>Design-induced operational risk</p>"
  },
  "style": {
    "fillColor": "light_yellow"
  }
}
```

**Generated Markdown Frontmatter:**
```yaml
---
id: rf-004
title: Design-induced operational risk
type: symptom
tags: [symptom]
---
```

---

## 3. Edge Type Extraction (Phase 3.3 — TBD)

Relationships between nodes will be extracted in a separate phase.

Possible approaches:
1. **Miro Connectors** — If lines connect sticky notes
2. **Spatial Proximity** — Nodes in the same frame/area
3. **Manual Input** — Relationships entered separately

| Edge Type | Direction | Notes |
|-----------|-----------|-------|
| `triggers` | RC → SYM, SYM → SYM | Root cause triggers symptom |
| `threatens` | SYM → SC | Symptom threatens success criteria |
| `triggered_by` | SYM → RC | Reverse of triggers |
| `threatened_by` | SC → SYM | Reverse of threatens |
| `leads_to` | RC → RC | Root cause chain |
| `leads_from` | RC → RC | Reverse of leads_to |

---

## 4. TOGAF Phase Detection (Phase 3.4 — TBD)

Phase information (`introduced_in_phase`, `observed_in_phase`, `reviewable_in_phase`) extraction is pending.

Possible approaches:
1. **Swimlanes / Frames** — Nodes placed in phase-labeled areas
2. **Tags on Miro** — Phase tags attached to sticky notes
3. **Manual Input** — Phases entered separately after generation

---

## 5. ID Generation Strategy

### 5.1 New Nodes

For nodes not matching existing files:
- Generate sequential IDs: `rc-042`, `rf-013`, `sc-008`
- Check existing files to avoid collisions

### 5.2 Matching Existing Nodes

When a sticky note matches an existing Markdown file:
- Match by `title` (fuzzy matching may be needed)
- Preserve existing `id`
- Update relationships if changed

---

## 6. Processing Pipeline

```
Miro Board
    │
    ▼
[1] Fetch all sticky notes (GET /v2/boards/{id}/items)
    │
    ▼
[2] Filter by fillColor (red, light_yellow, light_blue)
    │
    ▼
[3] Map to node type
    │
    ▼
[4] Extract title (strip HTML)
    │
    ▼
[5] Generate/match ID
    │
    ▼
[6] Extract edges (TBD - Phase 3.3)
    │
    ▼
[7] Extract phases (TBD - Phase 3.4)
    │
    ▼
[8] Generate Markdown via write_node()
```

---

## 7. Edge Extraction (Phase 3.3)

### 7.1 Connector Data Structure

Miro connectors reference sticky notes by their `miro_id`:

```json
{
  "id": "3458764651489083035",
  "startItem": { "id": "3458764651489083046" },
  "endItem": { "id": "3458764651489083047" },
  "style": { "strokeStyle": "normal" }
}
```

### 7.2 Edge Processing Flow

1. Fetch all connectors from board
2. For each connector, extract `startItem.id` → `endItem.id`
3. Map `miro_id` to `node_id` using node_list
4. Add edges to YAML per sticky note
5. Merge edges when generating Markdown (for duplicate titles)

### 7.3 Disconnected Connector Handling

Connectors without proper connections are flagged for manual review:

| Pattern | Detection |
|---------|-----------|
| `startItem` missing | Connector start not attached to sticky note |
| `endItem` missing | Connector end not attached to sticky note |
| Both missing | Floating line (likely orphaned) |

**Output:**
- Terminal: Warning list with connector IDs
- YAML: `_warnings.disconnected_connectors` section

Example:
```yaml
_warnings:
  disconnected_connectors:
    - connector_id: "3458764651489083035"
      start_connected: false
      end_connected: false
      reason: "Both ends disconnected"
```

### 7.4 Edge Type Determination (TBD)

How to determine edge type (triggers, threatens, leads_to):
- **Option A**: By node types (RC→SYM = triggers, SYM→SC = threatens)
- **Option B**: By connector style/color
- **Option C**: Manual specification

---

## 8. Open Questions

1. **Edge type determination**: How to distinguish triggers vs threatens vs leads_to?
2. **Phase representation**: How are TOGAF phases represented on the board?
3. **Duplicate handling**: When merging edges, how to handle conflicts?

