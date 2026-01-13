# Changelog
All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [Unreleased]

## [1.3.3] - 2026-01-13
### Fixed
- Tool audit report emission is now normalized for cross-platform golden stability (float quantization and -0.0 canonicalization applied before writing JSON).

## [1.3.2] - 2026-01-13
### Added
- Repository hygiene and release metadata: .editorconfig, .gitattributes, GitHub issue/PR templates, and CI workflow.
### Changed
- Documentation and release text normalized to an impersonal, research-oriented style; clarified non-clinical scope and determinism guarantees.
### Fixed
- Removed accidental non-source artifacts from the repository archive (test temporary directory).

## [1.3.1] - 2026-01-11
### Fixed
- Reproducible JSON artifacts across platforms by normalizing JSON before emission and hashing: float quantization (configurable) and -0.0 → 0.0 canonicalization.

## [1.3.0] - 2026-01-10
### Added
- Biomedical I/O v1 schemas (labs_panel, wearable_timeseries) with strict validation and unit gating.
- Deterministic biomedical recipes (inflammation_score_v1, metabolic_score_v1, circadian_score_v1) with QC.
- Level C comparator v2 producing recovery_report artifacts with stable evidence hashing.
- Plasticity v2 report (AUC + mean coupling) derived from recovery reports (σ(t)=⟨D,T,R,C⟩).
- Audit comparator for score artifacts (score-compare) with tolerance control and evidence hash.
- Level C fixtures (t0/t24/t72/t168) and golden outputs (score/recovery/plasticity2/audit).
- CLI integration: `semioc biomed ...` and `semioc audit ...` commands.

### Changed
- Wearable schema accepts both list and dict encodings for `series`, normalized by the loader and recipes.

### Fixed
- Repository root detection and strict unit fail-fast behavior in biomedical loading pipeline.

## [1.2.0] - 2026-01-04
### Added
- First biomedical contracts library (biomed_v1) implementing reproducible interpretive regimes over normalized biomedical proxy channels:
  - inflammation_proxy
  - metabolic_risk
  - circadian_disruption
  - frailty_phenotype
  - qc_regime
  - trajectory_comparator
- Contract schemas and documentation for each biomedical contract.
- Fixtures and golden expected traces for reproducibility.
- Reference biomedical world fixture (`biomed_world_v1.json`).

### Testing
- All tests pass locally: `python -m pytest -q` (18 passed).

### Notes
- These contracts are a DSL layer for reproducible regimes over proxy/normalized channels; they are not biomarker discovery, biological age estimation, or clinical diagnostic tools. Biological/clinical interpretation requires independent validation outside SemioCore.

## [1.1.0] - 2026-01-02
### Added
- `semioc parse` emits `semiocore.ast.v1` (deterministic JSON).
- `semioc parse --emit-lang` emits `semiocore.lang.v1`.
- Golden conformance fixtures for AST/lang manifests.

### Changed
- Hardened `trace.v1` and `ctxscan.v1` schemas (required top-level structure and minimum constraints).
- Stabilized `program_file` as a repo-relative POSIX path for deterministic parsing artifacts.
- CLI help now shows the package VERSION.

### Compatibility
- Backward compatible with v1.x (SemVer minor release).

### Contracts
- `semiocore.ast.v1`
- `semiocore.lang.v1`

## [1.0.1] - 2026-01-01
### Added
- Normative v1 contract documents for `semiocore.trace.v1` and `semiocore.ctxscan.v1`.
- Cross-platform CI matrix (Ubuntu/Windows/macOS) for Python 3.11–3.13.

### Changed
- CI installs test dependencies via `pyproject.toml` extras (declarative install).

### Fixed
- Cross-platform conformance hashing stability (path normalization / stable views) for trace/ctxscan artifacts.

## [1.0.0] - 2025-12-30
- Initial stable release.
