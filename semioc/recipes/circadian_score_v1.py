# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base import QCReport, ScoreResult, clamp, mean, pearson, safe_float


RECIPE_ID = "circadian_score_v1"

EXPECTED_UNITS: Dict[str, str] = {
    "hr": "bpm",
    "hrv_rmssd": "ms",
    "steps": "count",
    "sleep_minutes": "min",
}


def _series_map(wearable: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Normalize the wearable 'series' payload into a dict.

    The I/O schema admits both:
      - list-of-series: [{name, unit, values}, ...]
      - dict-of-series: {"hr": {unit, values}, ...}

    This helper makes the recipe tolerant to both, while keeping the units gate
    strict at the loader layer.
    """

    out: Dict[str, Dict[str, Any]] = {}
    series = wearable.get("series")

    if isinstance(series, list):
        for s in series or []:
            if not isinstance(s, dict):
                continue
            name = s.get("name")
            if isinstance(name, str):
                out[name] = dict(s)
        return out

    if isinstance(series, dict):
        for name, s in series.items():
            if isinstance(name, str) and isinstance(s, dict):
                out[name] = {"name": name, **dict(s)}
        return out

    return out


def _values(s: Dict[str, Any]) -> List[float]:
    vals = s.get("values", []) or []
    out: List[float] = []
    for v in vals:
        fv = safe_float(v)
        if fv is not None:
            out.append(float(fv))
    return out


def run(wearable_timeseries: Dict[str, Any]) -> ScoreResult:
    """Compute a deterministic circadian disruption proxy in [0, 1].

    This recipe is intentionally conservative: it emits its intermediate
    features (means/totals and simple coupling proxy) so downstream steps can
    audit exactly what drove the score.
    """

    qc = QCReport()
    m = _series_map(wearable_timeseries)

    features: Dict[str, float] = {}

    hr_vals: Optional[List[float]] = None
    hrv_vals: Optional[List[float]] = None
    steps_vals: Optional[List[float]] = None
    sleep_vals: Optional[List[float]] = None

    if "hr" in m:
        hr_vals = _values(m["hr"])
    else:
        qc.missing.append("hr")

    if "hrv_rmssd" in m:
        hrv_vals = _values(m["hrv_rmssd"])
    else:
        qc.missing.append("hrv_rmssd")

    if "steps" in m:
        steps_vals = _values(m["steps"])
    else:
        qc.missing.append("steps")

    if "sleep_minutes" in m:
        sleep_vals = _values(m["sleep_minutes"])
    else:
        qc.missing.append("sleep_minutes")

    mean_hr = mean(hr_vals) if hr_vals else None
    mean_hrv = mean(hrv_vals) if hrv_vals else None
    total_steps = sum(steps_vals) if steps_vals else None
    total_sleep = sum(sleep_vals) if sleep_vals else None

    if mean_hr is not None:
        features["mean_hr_bpm"] = float(mean_hr)
        if mean_hr <= 0:
            qc.outliers.append("mean_hr_bpm")
    if mean_hrv is not None:
        features["mean_hrv_rmssd_ms"] = float(mean_hrv)
        if mean_hrv < 0:
            qc.outliers.append("mean_hrv_rmssd_ms")
    if total_steps is not None:
        features["total_steps"] = float(total_steps)
        if total_steps < 0:
            qc.outliers.append("total_steps")
    if total_sleep is not None:
        features["total_sleep_min"] = float(total_sleep)
        if total_sleep < 0:
            qc.outliers.append("total_sleep_min")

    coupling = None
    if hr_vals and steps_vals:
        n = min(len(hr_vals), len(steps_vals))
        coupling = pearson(hr_vals[:n], steps_vals[:n])
        if coupling is not None:
            features["hr_steps_coupling"] = float(coupling)

    parts: Dict[str, float] = {}
    weights: Dict[str, float] = {}

    if mean_hr is not None and mean_hr > 0:
        parts["hr_risk"] = clamp((mean_hr - 55.0) / 45.0, 0.0, 1.0)
        weights["hr_risk"] = 0.25

    if mean_hrv is not None and mean_hrv >= 0:
        # Low HRV -> higher risk
        parts["hrv_risk"] = clamp((40.0 - mean_hrv) / 40.0, 0.0, 1.0)
        weights["hrv_risk"] = 0.25

    if total_sleep is not None and total_sleep >= 0:
        # Less than 7h/day -> higher risk. More than 7h does not add risk here.
        parts["sleep_risk"] = clamp((420.0 - total_sleep) / 300.0, 0.0, 1.0)
        weights["sleep_risk"] = 0.25

    if total_steps is not None and total_steps >= 0:
        # Low activity -> higher risk
        parts["activity_risk"] = clamp((8000.0 - total_steps) / 8000.0, 0.0, 1.0)
        weights["activity_risk"] = 0.25

    if not parts:
        qc.notes.append("No usable series; score defaulted to 0.0")
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
