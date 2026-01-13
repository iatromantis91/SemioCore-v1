# SemioCore Design Principles and Scope

## 0. Purpose

SemioCore is a domain-specific, declarative language and toolchain for **machine-verifiable regimes of biomedical interpretation and decision**. It is designed to make **interpretive dynamics** measurable, reproducible, and auditable in laboratory bioinformatics workflows.

SemioCore's contribution is not statistical modeling or prediction, but the formalization and measurement of **regimes of interpretation**: how signals become meaningful under explicit, versioned contracts.

## 1. What SemioCore Measures

SemioCore measures **semiodynamics** as the dynamics of interpretive stability under a fixed regime:

- stability of partitions / categorical interpretants (`partition_stability`)
- sensitivity to noise / regime brittleness (`noise_sensitivity`)
- controlled indeterminacy as a legitimate outcome (`indeterminacy_rate`)
- coherence loss in internal regime parameters (`coherence_loss`)

SemioCore does **not** measure "age" directly. It measures the dynamics of regime application to biomedical signals. Ageing can be operationalized as **loss of semiotic plasticity** under fixed interpretive conditions.

## 2. What SemioCore Is Not

SemioCore is not:
- a general-purpose programming language
- a statistical platform
- a machine learning framework
- an ontology system
- a clinical diagnostic device
- a dashboard/visualization suite

SemioCore complements these tools by operating at a different layer: **interpretive infrastructure**.

## 3. Design Invariants

### 3.1 Explicitness
If a rule is not in a contract, it does not exist.

### 3.2 Determinism
Given the same inputs and contracts, SemioCore must produce deterministic artifacts:
- deterministic AST emission (`--emit-ast`)
- deterministic language manifest emission (`--emit-lang`)
- deterministic reports (e.g., plasticity report)

Contract artifacts must not include volatile fields (timestamps, hostnames, random IDs).

### 3.3 Machine-verifiable contracts
Contracts are:
- versioned (`contract_id`)
- documented (`docs/contract/*.md`)
- validated by JSON Schema (`schemas/*.schema.json`)
- grounded in golden fixtures (`expected/*`)

### 3.4 Replayability
SemioCore supports replay: the same interpretive regime can be re-applied to the same or different signals to test stability, drift, and regime brittleness.

### 3.5 Separation of concerns
- Biomarkers are signals (inputs).
- SemioCore formalizes interpretation regimes (contracts).
- Semiodynamics is the measured dynamic of interpretation under control.

## 4. Canonical Position on Biomarkers

SemioCore does not replace biomarkers.
It turns biomarkers into experimental semiotic objects by making the interpretive regime explicit, executable, and auditable.

This enables laboratory study of ageing as dynamics of biological meaning under controlled conditions with computational reproducibility.

## 5. Exclusions

### 5.1 No statistical/ML features
No regressions, p-values, embeddings, clustering, neural models, or predictive optimization.

### 5.2 No clinical claims
No outputs framed as biological age, disease diagnosis, or medical risk classification.
SemioCore outputs are regime-level and interpretation-level, not clinical verdicts.

### 5.3 No biomarker hardcoding
No biomarker-specific primitives in the core.
Biomarkers enter as signals; SemioCore remains neutral to biomarker fashions.

### 5.4 No implicit intelligence
No hidden heuristics, "smart defaults", or undocumented inference.

### 5.5 No breaking changes without versioning
Breaking changes require `v2` contracts. No silent semantic changes.

### 5.6 No "all-in-one" platform
No GUI, dashboards, or notebooks as core.
SemioCore produces artifacts; other tools consume them.

### 5.7 No causal promises
SemioCore supports diagnostic description of interpretive regimes, not causal explanation.

### 5.8 No opaque metrics
Every metric must be explainable from trace evidence.
If a metric cannot be justified with the trace in hand, it does not belong.

### 5.9 No ad hoc per-experiment forks of the core
Experiments adapt to contracts. Contracts evolve by versioning, not by patching the core.

### 5.10 Correctness over feature breadth
Determinism, trace-auditability, and contract stability take precedence over expanding scope.

## 6. Contract Discipline (Audit Loop)

Any change that affects contract artifacts MUST follow this loop:

1) justify the intent and scope (issue/PR description)
2) update schema(s) if needed (`schemas/*`)
3) update golden fixtures (`expected/*`)
4) update docs (`docs/contract/*.md`)
5) ensure tests pass (`pytest`)
6) run registry validation (`python -m semioc contracts validate`)

Golden fixtures act as the regression oracle: if fixtures change, the change must be intentional and documented.

## 7. Versioning Policy (SemVer + Contracts)

- Patch: internal changes that do not affect contract artifacts
- Minor: additive, backward-compatible extensions (optional fields, clarifications) with fixtures/docs updates
- Major: breaking changes in contract semantics or schema incompatibility (requires `*.v2` contracts)

## 8. Acceptance Criteria for New Features

A feature proposal must answer:

1) Does it increase explicitness and auditability of interpretation regimes?
2) Can it be expressed as a contract + schema + fixture + docs?
3) Does it preserve determinism and replayability?
4) Does it avoid competing with R/ML/statistics tooling?
5) Does it respect the separation signal / interpretation / dynamics?

If any answer is "no", the feature should be rejected or redesigned.

## 9. Objective

SemioCore's objective is to enable laboratory bioinformatics to:
- define interpretive regimes explicitly,
- replay them reproducibly,
- and measure interpretive stability (semiodynamics) as a first-class experimental object.
