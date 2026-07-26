# Information Handling Policy

- Version: 1.0
- Updated: 2026-07-26

## Allowed

- public-safe practitioner reasoning;
- generalized and anonymized technical cases;
- public disclosures, standards, and articles with source anchors;
- hypotheses that contain no customer-identifying or restricted detail.

## Prohibited

- customer names or uniquely identifying project details;
- credentials, secrets, tokens, or private endpoints;
- personal data;
- confidential, contract-restricted, or internally restricted information;
- copied source material whose license does not permit repository storage.

## Required Metadata

Every new Raw Note must declare:

```yaml
confidentiality: public_safe
```

If material cannot truthfully receive that classification, it must not be stored
in this repository.

## Generalization

Generalizing a case requires removing or abstracting organizations, people,
exact dates, system names, commercial terms, and unique operational details.
Generalization must not change the technical mechanism being preserved.
