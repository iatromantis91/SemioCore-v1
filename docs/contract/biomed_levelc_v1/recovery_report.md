# Contract: semiocore.biomed.recovery_report.v1

**Scope.** Level C comparator v2 output: compares a baseline score artifact against post-baseline score artifacts and emits recovery metrics.

## Schema
- `$id`: `semiocore.biomed.recovery_report.v1`
- JSON Schema: `schemas/biomed_levelc_v1/recovery_report.schema.json`

## Semantics
- Baseline is identified by `baseline_label` (default `t0`).
- Each post artifact produces a delta trajectory with deterministic evidence hashing.

## Goldens
See `expected/biomed_levelc_v1/recovery/...`.
