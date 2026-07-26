# Knowledge Promotion Policy

- Version: 1.0
- Updated: 2026-07-26

## Direction

Promotion is additive and traceable:

```text
Raw Note -> Candidate -> Curated Knowledge
```

Promotion does not require deleting or rewriting the upstream asset.

## Raw to Candidate

A Candidate must:

- have its own stable ID;
- declare `maturity: candidate` and `review_usage: prohibited`;
- reference at least one upstream Raw Note or Source ID;
- separate observation from inference;
- state open assumptions or uncertainties;
- express a bounded proposed knowledge unit.

## Candidate to Curated

Before promotion, verify:

- provenance and reasoning path are traceable;
- observation and cause are not asserted as equivalent without support;
- counterconditions or applicability boundaries are stated;
- validation probes or review questions are usable;
- applicable review phase or context is stated when relevant;
- duplicates and contradictions with existing Curated Knowledge were checked;
- the result is granular enough for a Production Review;
- information handling policy is satisfied.

The Curated asset must declare:

```yaml
maturity: curated
review_usage: allowed
derived_from:
  - <candidate-id>
```

## Corrections

Correct Raw Notes by appending a `Corrections` entry. If evidence reverses a
Candidate or Curated conclusion, create a traceable replacement or correction;
do not erase the earlier reasoning path.
