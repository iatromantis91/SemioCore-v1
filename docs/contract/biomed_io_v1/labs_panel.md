# Contract: semiocore.biomed.labs_panel.v1

**Scope.** Canonical JSON payload for laboratory panels (point or same‑day measurements) used as inputs to biomedical recipes.

## Schema
- `$id`: `semiocore.biomed.labs_panel.v1`
- JSON Schema: `schemas/biomed_io_v1/labs_panel.schema.json`

## Normative fields
- `schema` (required): must equal the contract id.
- `provenance` (required):
  - `tool_version`: producing tool version.
  - `created_utc`: artifact creation time.
  - `input_hash`: deterministic input hash (for reproducibility/audit).
- `collected_utc` (required): collection timestamp (ISO 8601 string).
- `labs` (required): map `assay_id -> { value, unit }`.

Optional:
- `subject_id`: free subject identifier.

## Unit policy (Level C)
Inputs are validated strictly. Recipes define expected units; mismatches are **fail-fast**.

## Fixtures
- `fixtures/biomed_io_v1/levelc/labs_t0.json`
- `fixtures/biomed_io_v1/levelc/labs_t24.json`
- `fixtures/biomed_io_v1/levelc/labs_t72.json`
- `fixtures/biomed_io_v1/levelc/labs_t168.json`
