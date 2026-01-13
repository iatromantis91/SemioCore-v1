# Contract: semiocore.biomed.failure_conditions.v1

**Scope.** Descriptor contract for explicit failure / invalidity conditions in Level‑C pipelines. The purpose is to prevent silent success on out‑of‑spec inputs.

## Schema
- `$id`: `semiocore.biomed.failure_conditions.v1`
- JSON Schema: `schemas/biomed_levelc_v1/failure_conditions.schema.json`

## Fixture
- `semioc/contracts/failure_conditions.v1.json`

## Notes
Failure conditions are intended to be surfaced in QC blocks and in audit reports.
