# Architecture Review Knowledge

This repository manages the lifecycle of reusable Architecture Review
Knowledge.

It began as a Failure Model vault. The Failure Model remains an active curated
knowledge product, while the repository now also preserves the public-safe raw
material and provisional reasoning from which future knowledge is developed.

## Product Model

```text
Raw Notes
  -> Candidates
  -> Curated Knowledge
       -> Failure Model
       -> Review Lenses (future)
```

Trust is determined by knowledge zone and policy, not by repository membership.
Production Architecture Review uses Curated Knowledge only.

## Repository Structure

```text
knowledge/
  raw-notes/       # Unverified material; Production use prohibited
  candidates/      # Structured provisional knowledge; Production use prohibited
  curated/
    failure-model/
      success-criteria/
      symptoms/
      root-causes/
    review-lenses/
  sources/         # Public-safe evidence metadata and anchors

schemas/           # Canonical, tool-independent knowledge contracts
policies/          # Retrieval, promotion, and information-handling rules
tooling/           # Replaceable adapters and authoring tools
docs/traceability/ # Current product direction and implementation rationale
docs/adr/          # Historical architecture decisions
generated/         # Generated exports; not canonical knowledge
legacy/            # Retired implementations and historical operational assets
```

## Add a Raw Note

1. Read `policies/information-handling-policy.md`.
2. Copy `schemas/raw-note-template.md`.
3. Assign a stable `rn-YYYYMMDD-NNN` ID.
4. Save the note under `knowledge/raw-notes/`.
5. Preserve later corrections in the `Corrections` section.

Raw Notes may contain observations, practitioner reasoning, hypotheses, and open
questions. They must declare `review_usage: prohibited`.

## Failure Model

The curated Failure Model contains:

- Success Criteria (`sc-*`)
- Symptoms (`rf-*`; historical prefix retained)
- Root Causes (`rc-*`)

Relationships use the canonical causal vocabulary:

- `triggers` / `triggered_by`
- `threatens` / `threatened_by`
- `leads_to` / `leads_from`

The canonical node contract is
`schemas/failure-model/node-spec.md`.

## Miro Conversion

`tooling/miro-to-failure-model/` converts a Miro Backcasting Map into Failure
Model Markdown and supports diff/apply workflows.

MCP and RAG are not part of the current product baseline. Either may be
introduced later as a replaceable adapter through a new traceability decision.

## Current Product Truth

Start with:

- `AGENTS.md`
- `docs/traceability/registry.md`
- `docs/traceability/enabler-proposals/ep-001-knowledge-lifecycle-and-trust-zones.md`
- `docs/traceability/value-streams/vs-001-raw-to-curated-knowledge.md`
- `docs/traceability/implementation-specs/is-001-raw-notes-foundation.md`
- `policies/retrieval-policy.md`

## Validation

```bash
python3 scripts/validate_repository.py

cd tooling/miro-to-failure-model
python -m pytest
```

## License

See [LICENSE.md](LICENSE.md).
