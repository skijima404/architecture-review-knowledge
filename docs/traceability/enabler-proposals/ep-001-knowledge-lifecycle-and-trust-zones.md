---
id: EP-001
type: enabler_proposal
title: Knowledge Lifecycle and Trust Zones
status: approved
decision_date: 2026-07-26
realized_by:
  - VS-001
implemented_by:
  - IS-001
---

# Knowledge Lifecycle and Trust Zones

## Problem

The repository began as a Failure Model vault containing Success Criteria,
Symptoms, and Root Causes. It now needs to preserve the reasoning material from
which reusable Architecture Review Knowledge is developed.

Unverified notes can contain duplicate, contradictory, incomplete, or incorrect
claims. Keeping them in a separate repository would weaken provenance, while
mixing them into the production knowledge surface would weaken trust.

The previous RAG and MCP direction was designed when model context windows were
small. Those implementations are not a compatibility target for the expanded
product.

## Product Decision

This repository is the lifecycle store for reusable Architecture Review
Knowledge.

The Failure Model is the first curated knowledge product, not the complete
product boundary.

Raw, Candidate, Curated, and Source assets remain in the same repository but are
separated by directories, metadata, validation, and retrieval profiles.

```text
Same repository
  does not imply
Same retrieval surface
```

Production Review uses Curated Knowledge only. Raw Notes and Candidates may be
used only by explicit curation or research workflows.

## Current Capability Baseline

Included:

- Raw Note capture.
- Candidate and Curated trust-zone boundaries.
- Failure Model authoring and maintenance.
- Miro-to-Failure-Model conversion.
- deterministic policies and validation.

Not included:

- RAG or vector indexing.
- MCP interfaces.
- automatic AI promotion.
- automatic semantic ranking.

RAG and MCP may be introduced later as replaceable adapters after a new
traceability decision defines their current purpose.

## Information Boundary

The repository must not contain customer-identifying, confidential, personal,
or restricted information. Only public-safe practitioner reasoning,
generalized cases, and source anchors are allowed.

## Consequences

- Repository structure follows knowledge maturity before individual tooling.
- Tools depend on canonical schemas and policies; schemas do not depend on tools.
- Legacy MCP code can be removed without preserving compatibility.
- Existing Failure Model IDs and relations remain stable through migration.
- Raw capture remains deliberately lightweight.
