# SemioCore

Current release: **v1.3.3** (2026-01-13)

SemioCore is a reproducibility-first toolkit for **semiotic auditing**: it makes biomedical interpretation regimes explicit, executable, and comparable under versioned, machine-verifiable contracts.

This repository provides two working surfaces:

1. **Paper demo surface (DSL + conformance fixtures)**: minimal artifacts used to reproduce reference experiments.
2. **Biomedical surface (Level C)**: deterministic biomedical recipes + strict I/O validation + comparator v2 + plasticity v2 + audit reports.

The biomedical surface supports bioinformatics-style workflows where the objective is to audit measurement pipelines and study stability, recovery, and plasticity of domain-bounded signals under explicit regimes.

## Scope and non-clinical use

SemioCore emits **regime-level artifacts** (scores, recovery/plasticity reports, and audit reports) intended for research, methodological auditing, and reproducibility.

- Outputs are not framed as biological age estimates, disease diagnoses, or medical risk classifications.
- Any biomedical or clinical interpretation requires independent validation outside SemioCore and remains the responsibility of the user.

## Deterministic JSON and evidence hashing

SemioCore normalizes JSON outputs prior to emission and canonical hashing to support cross-platform reproducibility.

- Floats are quantized (configurable via `SEMIOC_JSON_FLOAT_NDIGITS`, default: 12).
- `-0.0` is canonicalized to `0.0`.

This ensures that the same inputs and contracts yield identical persisted artifacts and stable SHA-256 evidence hashes across operating systems.

## Cite SemioCore

SemioCore releases are intended to be archived on Zenodo. For reproducible citation, use the Zenodo DOI minted for the exact version tag used (e.g., v1.3.3). The repository includes `CITATION.cff` for automated citation metadata.

### BibTeX (template)

```bibtex
@software{huerta_castillo_semiocore,
  author  = {Huerta Castillo, Israel},
  title   = {SemioCore},
  url     = {https://github.com/iatromantis91/SemioCore-v1},
  date    = {2026-01-13},
  doi     = {https://doi.org/10.5281/zenodo.18237327}
}
```

## Requirements

- Python 3.11+

## Install

From the repository root:

```bash
python -m pip install -e .
```

## Run the test suite

```bash
pytest -q
```

## CLI

```bash
python -m semioc --help
python -m semioc biomed --help
python -m semioc audit --help
```

## Biomedical quickstart (fixtures + golden outputs)

The repository includes this fixtures and golden outputs:

- Inputs:
  - `fixtures/biomed_io_v1/levelc/labs_t*.json`
  - `fixtures/biomed_io_v1/levelc/wearable_t*.json`
- Goldens:
  - `expected/biomed_levelc_v1/score/...`
  - `expected/biomed_levelc_v1/recovery/...`
  - `expected/biomed_levelc_v1/plasticity2/...`
  - `expected/biomed_levelc_v1/audit/...`

Generate a score artifact (recipe-specific):

```bash
python -m semioc biomed score \
  --recipe inflammation_score_v1 \
  --input fixtures/biomed_io_v1/levelc/labs_t0.json \
  --emit-score out/inflammation.t0.score.json
```

Compute recovery report (comparator v2):

```bash
python -m semioc biomed compare \
  --baseline-label t0 \
  --baseline-score expected/biomed_levelc_v1/score/inflammation_score_v1/t0.score.json \
  --post t24=expected/biomed_levelc_v1/score/inflammation_score_v1/t24.score.json \
  --post t72=expected/biomed_levelc_v1/score/inflammation_score_v1/t72.score.json \
  --post t168=expected/biomed_levelc_v1/score/inflammation_score_v1/t168.score.json \
  --emit-report out/inflammation.recovery.json
```

Compute plasticity v2 report:

```bash
python -m semioc biomed plasticity2 \
  --recovery-report out/inflammation.recovery.json \
  --emit-report out/inflammation.plasticity2.json
```

Audit score equivalence under tolerance:

```bash
python -m semioc audit score-compare \
  --baseline expected/biomed_levelc_v1/score/inflammation_score_v1/t0.score.json \
  --candidate expected/biomed_levelc_v1/score/inflammation_score_v1/t0.score.json \
  --tolerance-abs 0.0 \
  --emit-report out/inflammation.audit.json
```

List available recipes (optionally emit a recipes index artifact):

```bash
python -m semioc biomed recipes
python -m semioc biomed recipes --emit-index out/recipes_index.json
```

## Contract registry validation

The repository maintains a strict registry of contracts (schemas + docs + fixtures):

```bash
python -m semioc contracts validate
```

## Paper demo surface

The paper demo is kept as a reproducibility baseline and can be executed:

```bash
make paper-demo
```
