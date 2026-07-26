---
id: IS-001
type: implementation_spec
title: Raw Notes Foundation and Repository Remodel
status: implemented
implements:
  - EP-001
  - VS-001
---

# Raw Notes Foundation and Repository Remodel

## Scope

1. Establish repository-local product traceability and operating rules.
2. Add a minimal Raw Note schema and trust-zone policies.
3. Reorganize the existing Failure Model as Curated Knowledge.
4. Separate Miro conversion tooling from canonical knowledge contracts.
5. Remove the obsolete MCP implementation and its tests/specification.
6. Remove RAG and MCP from the current product baseline.
7. Preserve existing Failure Model content, IDs, and relations.
8. Remove tracked virtual environments, caches, and stale generated tool output.

## Target Structure

```text
knowledge/
  raw-notes/
    practitioner-reasoning/
    solution-lenses/
    generic-cases/
    disclosures/
  candidates/
  curated/
    failure-model/
      success-criteria/
      symptoms/
      root-causes/
    review-lenses/
  sources/

schemas/
  raw-note-template.md
  failure-model/

policies/
tooling/
  miro-to-failure-model/
docs/
  traceability/
  adr/
generated/
legacy/
```

## Migration Map

| Previous path | Current path |
|---|---|
| `success_criteria/` | `knowledge/curated/failure-model/success-criteria/` |
| `symptom/` | `knowledge/curated/failure-model/symptoms/` |
| `root_cause/` | `knowledge/curated/failure-model/root-causes/` |
| `templates/` | `schemas/failure-model/templates/` |
| `miro-to-markdown/` | `tooling/miro-to-failure-model/` |
| `export/` | `generated/failure-model-exports/` |
| `deprecated/` | `legacy/deprecated/` |

## Compatibility

Existing Failure Model assets are legacy-curated assets. During migration they
remain production-eligible only when all of these conditions hold:

- the asset is directly under one of the three canonical Failure Model
  directories;
- `type`, ID prefix, and filename are consistent;
- the file is not in Raw, Candidate, Generated, or Legacy zones.

New knowledge product types must declare `maturity: curated` and
`review_usage: allowed`. Existing Failure Model assets are not bulk-certified by
adding those fields without content review.

## Out of Scope

- Candidate extraction automation.
- Curated Review Lens implementation.
- RAG, vector stores, or semantic indexing.
- MCP replacement.
- bulk content quality certification of existing Failure Model nodes.

## Acceptance Criteria

- Product direction is traceable from EP-001 through VS-001 to IS-001.
- A Raw Note can be created from the canonical template.
- Raw and Candidate paths are prohibited by the production retrieval policy.
- Existing Failure Model IDs are unique and their Wikilink targets exist.
- Miro conversion reads and writes the new Failure Model paths.
- No MCP implementation, MCP-specific tests, or active MCP specification remain.
- Tool tests and repository structural checks pass.

## Implementation Result

Completed: 2026-07-26

- Product traceability is established from EP-001 through VS-001 to IS-001.
- Raw, Candidate, Curated, and Source trust zones are present.
- All 59 existing Failure Model nodes were moved without content changes; their
  pre- and post-migration Git blob hashes match.
- Canonical Failure Model contracts were moved out of the tool implementation.
- The legacy MCP implementation, MCP-specific tests, and active MCP
  specification were removed.
- The tracked, platform-specific virtual environment and stale generated Miro
  output were removed.
- The Miro tool resolves the new repository root and canonical directories.
- Miro tool tests pass: 40 passed.
- Repository validation passes for IDs, filenames, types, links, trust-zone
  restrictions, and required contracts.
