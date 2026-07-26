# Traceability Registry

Last updated: 2026-07-26

| id | title | type | stage | status | primary_asset | updated_at |
|---|---|---|---|---|---|---|
| EP-001 | Knowledge Lifecycle and Trust Zones | enabler_proposal | approved | active | `docs/traceability/enabler-proposals/ep-001-knowledge-lifecycle-and-trust-zones.md` | 2026-07-26 |
| VS-001 | Raw to Curated Knowledge | value_stream | defined | active | `docs/traceability/value-streams/vs-001-raw-to-curated-knowledge.md` | 2026-07-26 |
| IS-001 | Raw Notes Foundation and Repository Remodel | implementation_spec | implemented | active | `docs/traceability/implementation-specs/is-001-raw-notes-foundation.md` | 2026-07-26 |

## Traceability Chain

```text
EP-001
  realized_by -> VS-001
    implemented_by -> IS-001
      governs -> schemas, policies, directory structure, and validation
```

## Status Definitions

- `active`: current product or operating truth.
- `superseded`: retained for history but replaced by another registered asset.
- `retired`: no longer implemented and not a compatibility target.
