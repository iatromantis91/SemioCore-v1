# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
from __future__ import annotations

from typing import Any, Dict, Tuple

from .base import QCReport, ScoreResult, clamp, safe_float


RECIPE_ID = "metabolic_score_v1"

EXPECTED_UNITS: Dict[str, str] = {
    "fasting_glucose": "mg/dL",
    "hba1c": "%",
    "triglycerides": "mg/dL",
    "hdl": "mg/dL",
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
    """Compute a deterministic metabolic risk proxy in [0, 1]."""

    qc = QCReport()
    labs = _labs_to_map(labs_panel)

    features: Dict[str, float] = {}

    glucose = labs.get("fasting_glucose", (None, ""))[0] if "fasting_glucose" in labs else None
    hba1c = labs.get("hba1c", (None, ""))[0] if "hba1c" in labs else None
    tg = labs.get("triglycerides", (None, ""))[0] if "triglycerides" in labs else None
    hdl = labs.get("hdl", (None, ""))[0] if "hdl" in labs else None

    for k, v in [("fasting_glucose", glucose), ("hba1c", hba1c), ("triglycerides", tg), ("hdl", hdl)]:
        if v is None:
            qc.missing.append(k)
        elif v < 0:
            qc.outliers.append(k)
        else:
            features[k] = float(v)

    ratio = None
    if tg is not None and hdl is not None:
        if hdl <= 0:
            qc.outliers.append("tg_hdl_ratio")
        else:
            ratio = tg / hdl
            features["tg_hdl_ratio"] = float(ratio)
    else:
        qc.missing.append("tg_hdl_ratio")

    parts: Dict[str, float] = {}
    weights: Dict[str, float] = {}

    if glucose is not None and glucose >= 0:
        # 80 mg/dL ~ low; 150 mg/dL ~ high
        parts["glucose_risk"] = clamp((glucose - 80.0) / 70.0, 0.0, 1.0)
        weights["glucose_risk"] = 0.4

    if hba1c is not None and hba1c >= 0:
        # 5.0% ~ low; 7.5% ~ high
        parts["hba1c_risk"] = clamp((hba1c - 5.0) / 2.5, 0.0, 1.0)
        weights["hba1c_risk"] = 0.4

    if ratio is not None:
        # 1.5 ~ low; 4.5 ~ high
        parts["tg_hdl_risk"] = clamp((ratio - 1.5) / 3.0, 0.0, 1.0)
        weights["tg_hdl_risk"] = 0.2

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
