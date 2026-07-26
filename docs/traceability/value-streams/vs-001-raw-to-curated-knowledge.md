---
id: VS-001
type: value_stream
title: Raw to Curated Knowledge
status: active
enabled_by:
  - EP-001
implemented_by:
  - IS-001
---

# Raw to Curated Knowledge

## Value

Preserve practitioner insight quickly, then turn selected material into
review-safe, reusable Architecture Review Knowledge without losing provenance.

## Flow

```text
Public-safe observation, reasoning, case, or source
  -> Raw Note
  -> Candidate extraction
  -> provenance, countercondition, and relation validation
  -> Curated Knowledge Product
  -> Production Architecture Review
  -> new observation or correction
  -> Raw Note
```

## Stage Contracts

### Raw Note

- Optimized for capture speed and reasoning preservation.
- May be incomplete, contradictory, or incorrect.
- Has a stable ID.
- Is prohibited in Production Review.
- Is corrected by append-only `Corrections` entries.

### Candidate

- Expresses one or more structured provisional conclusions.
- References its upstream Raw Notes or Sources with stable IDs.
- Is prohibited in Production Review.
- May propose a Review Lens, Root Cause, relation, countercondition, probe, or
  change to an existing Curated asset.

### Curated Knowledge

- Has passed the applicable promotion gates.
- Has explicit review usage permission.
- Is suitable for a defined Architecture Review purpose.
- Preserves upstream provenance.

### Production Review

- Uses a production retrieval profile.
- Receives Curated assets only.
- Does not infer approval from repository membership or semantic similarity.

## Feedback

Production observations do not directly rewrite Curated Knowledge. They enter as
new Raw Notes or Corrections and follow the same promotion flow.

## Measures

- Raw Notes can be added without schema friction.
- Every promoted asset can identify its upstream material.
- Production retrieval contains no Raw or Candidate assets.
- Existing Failure Model relations remain valid after repository migration.
