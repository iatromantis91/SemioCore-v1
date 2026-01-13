# Contract: semiocore.biomed.intervention_manifest.v1

**Scope.** Minimal manifest to describe a controlled perturbation window and the timepoints used for Level‑C pipelines (score → compare → plasticity2 → audit).

This contract is intentionally **path-based**: it links timepoints to input files (labs panel / wearable time series) and, optionally, to externally-produced score artifacts. The goal is reproducibility and separation between raw signals and derived artifacts.

## Schema
- `$id`: `semiocore.biomed.intervention_manifest.v1`
- JSON Schema: `schemas/biomed_io_v1/intervention_manifest.schema.json`

## Fields
### Top-level
- `schema` (required): must equal the contract id.
- `subject_id` (optional): free identifier.
- `perturbation` (optional): structured description of the perturbation (e.g. sleep restriction, training load, cold exposure).
- `baseline` (required): the baseline timepoint.
- `posts` (required): one or more post timepoints.

### Timepoint object (`baseline` and items in `posts`)
- `label` (required): e.g. `t0`, `t24`, `t72`, `t168`.
- `offset_hours` (optional): numeric offset relative to baseline.
- `labs_ref` (optional): path to a `semiocore.biomed.labs_panel.v1` JSON.
- `wearable_ref` (optional): path to a `semiocore.biomed.wearable_timeseries.v1` JSON.
- `external_scores` (optional): mapping `recipe_id -> path` pointing to `semiocore.biomed.score.v1` artifacts.

## Notes
- The manifest **does not** prescribe how inputs are scored; it only binds file references to timepoints.
- `external_scores` is useful when auditing a third‑party tool or when reusing precomputed score artifacts.
