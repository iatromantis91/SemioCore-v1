# Contract: semiocore.audit.score_compare_report.v1

**Scope.** Audit report for score artifact equivalence under a configurable tolerance.

## Schema
- `$id`: `semiocore.audit.score_compare_report.v1`
- JSON Schema: `schemas/audit_v1/score_compare_report.schema.json`

## Semantics
- The comparator reports per-field deltas and a pass/fail decision under `tolerance_abs`.
- Evidence is hashed deterministically to enable regression and audit trails.

## Goldens
See `expected/biomed_levelc_v1/audit/...`.
