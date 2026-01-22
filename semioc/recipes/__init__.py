# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Deterministic biomed recipes.

Recipes are small, versioned scoring functions. They are intended to be:

- explicit (formula, expected units, missing/outlier handling)
- deterministic (same inputs yield identical outputs)
- auditable (intermediate features are emitted alongside the score)
"""
