# Miro Board Expression Rules for Backcasting Map

This document defines how Backcasting Map elements should be represented in Miro for automatic conversion to Markdown.

**Audience**: Board creators (humans) who design and maintain Backcasting Maps in Miro.

---

## 1. Sticky Note Colors → Node Types

| Sticky Note Color | Node Type | ID Prefix |
|-------------------|-----------|-----------|
| **Red** | Success Criteria | `sc-` |
| **Light Yellow** | Symptom | `rf-` |
| **Light Blue** | Root Cause | `rc-` |
| **Gray** | _(Ignored)_ | — |

- Gray sticky notes are used for labels, headers, or annotations and are excluded from conversion.
- Header labels like "Success Criteria", "Symptom", "Root Cause" are automatically excluded.

---

## 2. Connectors → Relationships (Edges)

Relationships between nodes are represented by **connectors (lines)** in Miro.

### 2.1 Cross-Type Connections

For connections between **different node types**, the edge type is automatically inferred based on the natural causal flow:

| From Type | To Type | Edge Type |
|-----------|---------|-----------|
| Root Cause | Symptom | `triggers` |
| Symptom | Success Criteria | `threatens` |

> **Note**: You don't need to worry about the visual direction of the connector. The system automatically normalizes to the causal direction (cause → effect).

### 2.2 Same-Type Connections

For connections between the **same node type** (e.g., RC → RC), the direction is determined by X-axis position:

| Direction | Edge Type |
|-----------|-----------|
| Left → Right (forward) | `leads_to` |
| Right → Left (backward) | `leads_from` |

### 2.3 Important: Attach Connectors Properly

- Connectors **must be attached to sticky notes on both ends**.
- Disconnected connectors are reported as warnings and excluded from conversion.
- Make sure the connector endpoint snaps to the sticky note edge.

---

## 3. Phase Detection (TOGAF Phases)

TOGAF phases are determined by the **X-axis position** of sticky notes relative to phase header shapes.

### 3.1 Phase Header Shapes

Create **Shape elements** at the top of the board with the following labels:

| Shape Label | Phases in Markdown |
|-------------|-------------------|
| `A` | A |
| `B-D` | B, C, D |
| `E` | E |
| `F` | F |
| `G` | G |
| `H` | H |

- `B-D` is automatically expanded to `["B", "C", "D"]` in Markdown.
- Phase headers should be placed **horizontally** at the top of the board.
- The system calculates column boundaries based on the position and width of each shape.

### 3.2 Phase Field Mapping

| Node Type | Markdown Field |
|-----------|----------------|
| Root Cause | `introduced_in_phase` |
| Symptom | `observed_in_phase` |
| Success Criteria | `observed_in_phase` |

---

## 4. Board Layout Guidelines

```
┌─────────────────────────────────────────────────────────────────┐
│  [A]     [B-D]     [E]      [F]      [G]      [H]              │  ← Phase Headers (Shapes)
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🔵 RC   🔵 RC     🔵 RC    🔵 RC    🟡 SYM ──► 🔴 SC           │  ← Nodes & Connectors
│    │       │         │        │        ▲                       │
│    └───────┴─────────┴────────┴────────┘                       │
│         (leads_to / leads_from)    (triggers)   (threatens)    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Legend:
  🔴 Red = Success Criteria (SC)
  🟡 Yellow = Symptom (SYM)
  🔵 Blue = Root Cause (RC)
  ─► = Connector (direction auto-detected)
```

### Key Points

1. **Place nodes within the appropriate phase column** (X-axis determines phase)
2. **Use connectors to define relationships** between nodes
3. **Y-axis is for visual organization only** — it does not affect conversion
4. **Keep titles concise and consistent** — they are used for matching with existing Markdown files

---

## 5. Checklist Before Running Conversion

- [ ] All sticky notes use the correct colors (Red/Yellow/Blue)
- [ ] All connectors are attached to sticky notes on both ends
- [ ] Phase header shapes (A, B-D, E, F, G, H) are in place
- [ ] No duplicate sticky notes with identical titles (or they will be merged)
- [ ] Gray notes are only used for non-node content (labels, annotations)

