# SemioCore contracts

This directory contains **normative** (human-readable) specifications for SemioCore contract artifacts.

- The machine-checkable source of truth is the corresponding JSON Schema in `schemas/`.
- Contract documents define field semantics, compatibility rules, and conformance expectations.
- Breaking changes require a new contract version (`*.v2`, `*.v3`, ...).

## Core contracts

- [semiocore.ast.v1](ast.v1.md)
- [semiocore.lang.v1](lang.v1.md)
- [semiocore.trace.v1](trace.v1.md)
- [semiocore.ctxscan.v1](ctxscan.v1.md)
- [semiocore.plasticity.v1](plasticity.v1.md)

## Biomedical I/O v1

- [biomed_io_v1/labs_panel](biomed_io_v1/labs_panel.md)
- [biomed_io_v1/wearable_timeseries](biomed_io_v1/wearable_timeseries.md)
- [biomed_io_v1/score](biomed_io_v1/score.md)
- [biomed_io_v1/intervention_manifest](biomed_io_v1/intervention_manifest.md)

## Biomedical Level C v1

- [biomed_levelc_v1/trajectory_comparator_v2](biomed_levelc_v1/trajectory_comparator_v2.md)
- [biomed_levelc_v1/recovery_report](biomed_levelc_v1/recovery_report.md)
- [biomed_levelc_v1/plasticity2_report](biomed_levelc_v1/plasticity2_report.md)
- [biomed_levelc_v1/recipes_index](biomed_levelc_v1/recipes_index.md)
- [biomed_levelc_v1/recovery_kinetics](biomed_levelc_v1/recovery_kinetics.md)
- [biomed_levelc_v1/coupling_index](biomed_levelc_v1/coupling_index.md)
- [biomed_levelc_v1/failure_conditions](biomed_levelc_v1/failure_conditions.md)

## Audit v1

- [audit_v1/score_compare_report](audit_v1/score_compare_report.md)
- [audit_v1/tool_audit_report](audit_v1/tool_audit_report.md)
