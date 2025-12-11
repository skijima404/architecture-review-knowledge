# Miro-to-Markdown: Task List

## Phase 1: Backcasting MCP Server (Local Read/Write)

### Setup
- [x] Create `src/` directory structure
- [x] Initialize Python project (pyproject.toml or requirements.txt)
- [x] Add `python-frontmatter` dependency

### MCP Tools
- [x] Implement `get_template(node_type)`
  - Return Markdown template from `templates/{node_type}.md`
  - Include `frontmatter_schema` and `_links`
- [x] Implement `get_node(id)`
  - Parse frontmatter from `{type_folder}/{id}.md`
  - Return `backcasting_node` resource
- [x] Implement `write_node(id, markdown, path)`
  - Write Markdown to disk
  - Validate frontmatter structure
  - Return updated `backcasting_node` resource

### Testing
- [x] Unit tests for frontmatter parsing
- [x] Integration test: read existing rc-001, rf-001, sc-001

---

## Phase 2: Chain Traversal

- [x] Implement `get_chain_from_root(root_id, max_depth?)`
  - Traverse `triggers` → `threatens` relationships
  - Return `backcasting_chain` resource
- [x] Integration test with realistic RC→SYM→SC path

---

## Phase 3: Miro Integration

### 3.1 Spike: API Evaluation
- [x] Evaluate Miro REST API vs Miro MCP → REST API採用
- [x] Verify API connection and sticky note retrieval

### 3.2 Sticky Note → Node Type Mapping
- [x] Spec: Define mapping rules (color/text → RC/SYM/SC)
- [x] Implement `map_sticky_to_node_type()`
- [x] Test with real board data

### 3.3 Edge Type Extraction (Relationships)
- [x] Spec: Define relationship extraction rules (position/connector)
  - Connectors reference sticky notes by miro_id
  - Edge type determined by node type + X position direction
  - Warnings for disconnected/unknown connectors
- [x] Implement edge detection (triggers, threatens, leads_to, etc.)
- [x] Test with real board data
- [x] Implement comparison script (compare_edges.py)
- [x] Debug and fix edge direction issues

### 3.4 TOGAF Phase Detection
- [x] Determine approach: Shape-based phase headers (A, B-D, E, F, G, H)
- [x] Implement phase detection from X position
- [x] Phase field mapping: introduced_in_phase (RC), observed_in_phase (SYM/SC)
- [x] B-D expansion to ["B", "C", "D"]

### 3.5 Markdown Generation
- [x] Implement `generate_cli.py` for new file generation
- [x] Implement `diff_cli.py` for diff report
- [x] Implement `apply_diff.py` for updating existing files
- [x] Config-based output path (`config.yaml`, `config.local.yaml`)
- [x] End-to-end test: Miro → YAML → Markdown

---

## Phase 4: Documentation & Polish

- [x] Complete `miro-to-markdown/README.md`
- [x] Document Miro board rules (`docs/miro-board-rules.md`)
- [x] Update `.cursor/rules` with language policy
- [ ] Add usage examples (optional)
- [ ] ADR if major decisions are made (optional)

---

## Completed: 2024-12-11

All core functionality implemented:
- Miro → YAML export with node type, edges, and phase detection
- Diff generation and application for existing files
- New Markdown file generation
- Configurable output paths for testing vs production
