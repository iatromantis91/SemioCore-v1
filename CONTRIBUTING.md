# Contributing to SemioCore

Contributions are welcome, subject to the constraints below. The project applies strict requirements to preserve determinism, auditability, and contract stability.

Background and design invariants: [MANIFESTO.md](MANIFESTO.md).

---

## 1. Scope and Non-Goals

SemioCore is **out of scope** for:
- statistics platforms (regressions, p-values, modeling toolkits)
- ML frameworks (embeddings, neural models, predictive optimization)
- clinical diagnostic tooling (biological age, disease diagnosis, medical risk classification)
- GUI/dashboard applications
- biomarker libraries (hardcoded biomarker primitives)

Rule of thumb: if a capability is better implemented in R/Python/Stan or a dedicated ML stack, it should not be implemented in SemioCore.

---

## 2. Core Principles

Accepted changes must preserve:

1) **Explicitness:** If a rule is not in a contract, it does not exist.  
2) **Determinism:** Same inputs + same contracts → identical artifacts.  
3) **Machine-verifiable contracts:** versioned IDs, JSON Schema validation, docs, and fixtures.  
4) **Replayability:** regimes must be re-applicable and comparable over time and traces.  
5) **Separation of concerns:** signals are inputs; SemioCore formalizes interpretation regimes; semiodynamics is the measured dynamic.

---

## 3. Local Setup

```bash
git clone <REPO_URL>
cd <REPO_DIR>
python -m venv .venv
source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -e ".[test]"
```

Run tests and contract validation:

```bash
pytest -q
python -m semioc contracts validate
```

## 4. Golden fixtures

If a change modifies emitted artifacts, regenerate goldens and re-run tests:

```bash
python tools/regenerate_goldens.py
pytest -q
```
