# Contract: semiocore.biomed.trajectory_comparator.v2

**Scope.** Descriptor contract for the Level‑C trajectory comparator (V2). It formalizes the supported timepoints and the primary derived metrics used by downstream modules.

## Schema
- `$id`: `semiocore.biomed.trajectory_comparator.v2`
- JSON Schema: `schemas/biomed_levelc_v1/trajectory_comparator_v2.schema.json`

## Fixture
- `semioc/contracts/trajectory_comparator.v2.json`

## Operational semantics
- Input: `semiocore.biomed.score.v1` artifacts at canonical timepoints.
- Output: `semiocore.biomed.recovery_report.v1` (see its contract).
- Determinism: comparator behavior is pure w.r.t. inputs; no stochastic components.
