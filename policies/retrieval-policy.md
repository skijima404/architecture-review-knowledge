# Retrieval Policy

- Version: 1.0
- Updated: 2026-07-26
- Scope: Architecture Review Knowledge

## Principle

Repository membership is not evidence of review eligibility. Retrieval must
apply a named profile and trust-zone rules before relevance ranking.

## Profiles

### Production

Purpose: support an Architecture Review or a review deliverable.

Allowed by default:

- `knowledge/curated/failure-model/success-criteria/*.md`
- `knowledge/curated/failure-model/symptoms/*.md`
- `knowledge/curated/failure-model/root-causes/*.md`
- future Curated assets with both `maturity: curated` and
  `review_usage: allowed`

Always prohibited:

- `knowledge/raw-notes/**`
- `knowledge/candidates/**`
- `generated/**`
- `legacy/**`
- templates, examples, tests, and fixtures

The current Failure Model is allowed through the explicit legacy-curated
compatibility rule in IS-001. Missing maturity metadata outside those exact
directories must never default to Curated.

### Curation

Purpose: extract, compare, validate, and promote knowledge.

Allowed:

- Raw Notes
- Candidates
- Curated Knowledge
- Sources
- schemas and policies

Results must preserve asset IDs and trust-zone labels. Curation output is not
automatically eligible for Production.

### Research

Purpose: investigate sources, disclosures, practitioner reasoning, and open
hypotheses.

Raw and Source material may be used. Responses must identify unverified claims
and must not present them as Curated Knowledge.

## Selection Order

1. Apply profile and path allowlist.
2. Apply metadata requirements.
3. Resolve stable-ID relations and source anchors.
4. Rank the remaining material for relevance.

Semantic or vector similarity, if introduced later, may perform step 4 only. It
must not decide trust or review eligibility.

## Response Contract

Production use must identify the Curated asset IDs supporting material claims.
When a legacy Failure Model asset lacks formal maturity metadata, identify it as
`legacy-curated` until it has passed explicit content review.
