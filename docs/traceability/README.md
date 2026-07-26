# Traceability Space

This directory is the source of current truth for the product direction,
value streams, and implementation framing of Architecture Review Knowledge.

It preserves why the repository exists, why its trust zones are structured as
they are, and which implementation choices are current. It is separate from the
knowledge assets themselves:

- Product traceability explains repository and capability changes.
- Knowledge provenance connects Source, Raw Note, Candidate, and Curated assets.

## Structure

- `registry.md`: stable index and current status of traceability assets.
- `enabler-proposals/`: cross-cutting product and operating decisions.
- `value-streams/`: durable end-to-end flows.
- `implementation-specs/`: bounded implementation contracts and acceptance
  criteria.

Historical ADRs remain under `docs/adr/`. They record why earlier approaches
were adopted or abandoned but do not override the current assets here.

## Update Rule

Update this space when a change:

- changes the repository's product boundary;
- changes trust, retrieval, or promotion behavior;
- restructures canonical knowledge;
- adds or removes a major adapter such as MCP or RAG;
- would otherwise be difficult to understand from the resulting files alone.
