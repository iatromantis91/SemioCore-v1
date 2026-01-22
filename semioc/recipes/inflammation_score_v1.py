# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
from __future__ import annotations

from typing import Any, Dict, Tuple

from .base import QCReport, ScoreResult, clamp, safe_float


RECIPE_ID = "inflammation_score_v1"

# Expected lab units (fail-fast is handled at I/O layer).
EXPECTED_UNITS: Dict[str, str] = {
    "crp": "mg/L",
    "neutrophils": "10^9/L",
    "lymphocytes": "10^9/L",
}


def _labs_to_map(labs_panel: Dict[str, Any]) -> Dict[str, Tuple[float, str]]:
    out: Dict[str, Tuple[float, str]] = {}
    for row in labs_panel.get("labs", []) or []:
        name = row.get("name")
        val = safe_float(row.get("value"))
        unit = row.get("unit")
        if isinstance(name, str) and isinstance(unit, str) and val is not None:
            out[name] = (val, unit)
    return out


def run(labs_panel: Dict[str, Any]) -> ScoreResult:
    """Compute a deterministic inflammation proxy score in [0, 1]."""

    qc = QCReport()
    labs = _labs_to_map(labs_panel)

    features: Dict[str, float] = {}

    crp = labs.get("crp", (None, ""))[0] if "crp" in labs else None
    if crp is None:
        qc.missing.append("crp")
    else:
        if crp < 0:
            qc.outliers.append("crp")
        features["crp_mg_L"] = float(crp)

    neut = labs.get("neutrophils", (None, ""))[0] if "neutrophils" in labs else None
    lymph = labs.get("lymphocytes", (None, ""))[0] if "lymphocytes" in labs else None
    nlr = None
    if neut is None:
        qc.missing.append("neutrophils")
    if lymph is None:
        qc.missing.append("lymphocytes")
    if neut is not None and lymph is not None:
        if neut < 0 or lymph <= 0:
            qc.outliers.append("nlr")
        else:
            nlr = neut / lymph
            features["nlr"] = float(nlr)

    # Map to risk components
    parts: Dict[str, float] = {}
    weights: Dict[str, float] = {}
    if crp is not None and crp >= 0:
        parts["crp_risk"] = clamp(crp / 10.0, 0.0, 1.0)
        weights["crp_risk"] = 0.6
    if nlr is not None:
        parts["nlr_risk"] = clamp((nlr - 1.0) / 4.0, 0.0, 1.0)
        weights["nlr_risk"] = 0.4

    if not parts:
        qc.notes.append("No usable biomarkers; score defaulted to 0.0")
        score = 0.0
    else:
        wsum = sum(weights.values())
        score = sum(parts[k] * weights[k] for k in parts) / wsum

    features.update({k: float(v) for k, v in parts.items()})
    return ScoreResult(
        recipe=RECIPE_ID,
        score=float(score),
        features=features,
        qc=qc,
        details={
            "weights": weights,
            "expected_units": EXPECTED_UNITS,
        },
    )
