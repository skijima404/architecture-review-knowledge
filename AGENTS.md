# Repository Operating Rules

## Product Boundary

This repository manages the lifecycle of reusable Architecture Review Knowledge.
The Failure Model is one curated knowledge product within that lifecycle.

The canonical product direction and change rationale are under
`docs/traceability/`. Historical ADRs explain previous decisions but are not the
source of current operating truth.

## Primary References

Read these before making structural or knowledge-lifecycle changes:

1. `docs/traceability/README.md`
2. `docs/traceability/registry.md`
3. `docs/traceability/enabler-proposals/ep-001-knowledge-lifecycle-and-trust-zones.md`
4. `docs/traceability/value-streams/vs-001-raw-to-curated-knowledge.md`
5. `docs/traceability/implementation-specs/is-001-raw-notes-foundation.md`
6. `policies/retrieval-policy.md`
7. `policies/promotion-policy.md`
8. `policies/information-handling-policy.md`
9. `schemas/raw-note-template.md`
10. `schemas/failure-model/node-spec.md`

## Trust Zones

- `knowledge/raw-notes/`: unverified material; prohibited in Production Review.
- `knowledge/candidates/`: structured but unapproved knowledge; prohibited in
  Production Review.
- `knowledge/curated/`: approved knowledge products and the only default source
  for Production Review.
- `knowledge/sources/`: evidence metadata and source anchors; use for
  verification, not as an automatic review conclusion.

Never treat repository membership as permission for Production Review use.
Apply `policies/retrieval-policy.md`.

## Raw Notes

- Preserve observations, practitioner reasoning, hypotheses, and open questions.
- Do not silently rewrite a Raw Note when later evidence changes its meaning.
  Append a `Corrections` entry.
- Do not store customer-identifying, confidential, personal, or restricted
  information.
- Use a stable Raw Note ID and the template in `schemas/raw-note-template.md`.

## Tooling Boundary

Tooling is an adapter around repository contracts. It must not define the
canonical knowledge schema inside its own implementation directory.

RAG and MCP are not part of the current product baseline. Introduce either only
through a new traceability decision and implementation specification.

## Change Rules

- Preserve stable IDs and causal relations during moves.
- Update traceability assets for structurally important changes.
- Keep generated exports under `generated/` and historical implementations under
  `legacy/`.
- Validate IDs, metadata, links, retrieval-zone boundaries, and relevant tests
  before completing a change.
