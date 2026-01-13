# Contract: semiocore.biomed.score.v1

**Scope.** Canonical score artifact produced by a biomedical recipe.

## Schema
- `$id`: `semiocore.biomed.score.v1`
- JSON Schema: `schemas/biomed_io_v1/score.schema.json`

## Normative fields
- `schema` (required): must equal the contract id.
- `provenance` (required):
  - `tool_version`, `created_utc`, `input_hash`.
- `input_schema` (required): input contract id that was scored (e.g. `semiocore.biomed.labs_panel.v1`).
- `recipe` (required): recipe identifier (e.g. `inflammation_score_v1`).
- `score` (required): primary scalar used for comparisons.
- `features` (required): free-form object (feature map) produced by the recipe. The canonical convention is `name -> number`.
- `qc` (required): structured QC object (recipe-defined).

Optional:
- `details`, `extra`: additional structured payloads.

## Goldens
See `expected/biomed_levelc_v1/score/...`.
