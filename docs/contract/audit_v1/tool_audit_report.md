# Tool audit report (v1)

**Schema id**: `semiocore.audit.tool_audit_report.v1`  \
**Schema path**: `schemas/audit_v1/tool_audit_report.schema.json`

## Purpose

This report audits an external scoring tool against SemioCore's deterministic
oracles using an intervention manifest.

The v1.3 implementation consumes `external_scores` referenced by the manifest
(score artifacts produced by the external tool) and compares them to scores
recomputed by SemioCore from the raw inputs.

For each recipe, the report includes:

- score-level comparisons (per timepoint, under an absolute tolerance);
- recovery metrics derived via `trajectory_comparator.v2` for both score sets;
- plasticity2 metrics derived from the corresponding recovery reports.

## Production

Generate a report with:

```bash
semioc audit run \
  --tool <name> \
  --manifest fixtures/biomed_io_v1/levelc/intervention_manifest.json \
  --contracts biomed_v1 \
  --tolerance-abs 0.0 \
  --emit-report out/tool_audit.json
```

The CLI also accepts the "literal" alias form:

```bash
semioc audit --tool <name> --manifest <path> --contracts biomed_v1 --emit-report out/tool_audit.json
```

## Notes

- Reports are deterministic by default (fixed timestamp epoch) unless
  `--realtime` is used.
- `--contracts` currently supports the built-in suite `biomed_v1`.
