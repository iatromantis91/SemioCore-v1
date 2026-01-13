# Contract: semiocore.biomed.wearable_timeseries.v1

**Scope.** Canonical JSON payload for wearable-derived time series windows used as inputs to biomedical recipes and coupling metrics.

## Schema
- `$id`: `semiocore.biomed.wearable_timeseries.v1`
- JSON Schema: `schemas/biomed_io_v1/wearable_timeseries.schema.json`

## Normative fields
- `schema` (required): must equal the contract id.
- `provenance` (required):
  - `tool_version`, `created_utc`, `input_hash`.
- `window` (required):
  - `start_utc`, `end_utc`: ISO 8601 strings.
  - `epoch_s`: sampling epoch in seconds.
  - `n_obs`: number of observations.

## Channel representation
Exactly one of the following is required:
- `channels_map`: map `channel_id -> { unit, values }`, where `values` is an array of numbers.
- `channels_list`: list form with the same information, using objects `{ name, unit, values }`.

## Unit policy (Level C)
Recipes define expected units; mismatches are **fail-fast**.

## Fixtures
- `fixtures/biomed_io_v1/levelc/wearable_t0.json`
- `fixtures/biomed_io_v1/levelc/wearable_t24.json`
- `fixtures/biomed_io_v1/levelc/wearable_t72.json`
- `fixtures/biomed_io_v1/levelc/wearable_t168.json`
