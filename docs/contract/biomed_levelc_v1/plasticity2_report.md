# Contract: semiocore.biomed.plasticity2_report.v1

**Scope.** Plasticity v2 report derived from a recovery report.

## Schema
- `$id`: `semiocore.biomed.plasticity2_report.v1`
- JSON Schema: `schemas/biomed_levelc_v1/plasticity2_report.schema.json`

## Semantics
The report summarizes trajectory behavior into a compact signature σ(t)=⟨D,T,R,C⟩:
- **D**: delta magnitude summary.
- **T**: time-to-recovery summary.
- **R**: stability/area-under-curve style summary.
- **C**: coupling summary.

## Goldens
See `expected/biomed_levelc_v1/plasticity2/...`.
