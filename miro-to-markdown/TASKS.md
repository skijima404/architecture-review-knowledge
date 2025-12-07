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
- [ ] Spec: Define relationship extraction rules (position/connector)
- [ ] Implement edge detection (triggers, threatens, leads_to, etc.)
- [ ] Test with real board data

### 3.4 TOGAF Phase Detection (TBD)
- [ ] Discuss: How phases are represented on Miro board
- [ ] Determine feasibility and approach
- [ ] Implement if viable

### 3.5 Markdown Generation
- [ ] Integrate with `write_node` from Phase 1
- [ ] End-to-end test: Miro → Markdown

---

## Phase 4: Documentation & Polish

- [ ] Complete `miro-to-markdown/README.md`
- [ ] Add usage examples
- [ ] ADR if major decisions are made

