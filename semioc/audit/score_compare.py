# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..util import sha256_c14n_json, stable_utc_now_iso


SCORE_COMPARE_SCHEMA_V1 = "semiocore.audit.score_compare_report.v1"


def _as_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _score_hash(score_artifact: Dict[str, Any]) -> str:
    return sha256_c14n_json(score_artifact)


def score_compare(
    *,
    tool_version: str,
    baseline: Dict[str, Any],
    candidate: Dict[str, Any],
    tolerance_abs: float,
    use_realtime: bool = False,
) -> Dict[str, Any]:
    """Compare two score artifacts under an absolute tolerance.

    This comparator is intentionally conservative: it does not attempt any unit
    conversion. It assumes both artifacts are already normalized and
    schema-valid.
    """

    if tolerance_abs < 0:
        raise ValueError("tolerance_abs must be >= 0")

    recipe = baseline.get("recipe") if isinstance(baseline, dict) else None
    if not isinstance(recipe, str) or not recipe:
        recipe = "unknown"

    base_score = _as_float(baseline.get("score")) if isinstance(baseline, dict) else None
    cand_score = _as_float(candidate.get("score")) if isinstance(candidate, dict) else None
    if base_score is None or cand_score is None:
        raise ValueError("Both artifacts must contain numeric 'score'")

    base_feat = baseline.get("features") if isinstance(baseline.get("features"), dict) else {}
    cand_feat = candidate.get("features") if isinstance(candidate.get("features"), dict) else {}

    keys = sorted(set(base_feat) | set(cand_feat))
    diffs: List[Dict[str, Any]] = []
    max_abs = 0.0
    for k in keys:
        a = _as_float(base_feat.get(k))
        b = _as_float(cand_feat.get(k))
        aa = None if a is None else float(a)
        bb = None if b is None else float(b)
        d = abs((aa or 0.0) - (bb or 0.0))
        max_abs = max(max_abs, d)
        diffs.append({"feature": k, "baseline": aa, "candidate": bb, "abs": float(d)})

    score_abs = abs(float(base_score) - float(cand_score))
    within = bool(score_abs <= tolerance_abs and max_abs <= tolerance_abs)

    evidence_hash = sha256_c14n_json(
        {
            "baseline": baseline,
            "candidate": candidate,
            "tolerance_abs": float(tolerance_abs),
            "comparator": "score_compare_v1",
        }
    )

    return {
        "schema": SCORE_COMPARE_SCHEMA_V1,
        "provenance": {
            "tool_version": tool_version,
            "created_utc": stable_utc_now_iso(use_realtime=use_realtime),
            "evidence_hash": evidence_hash,
        },
        "recipe": recipe,
        "baseline": {
            "score_hash": _score_hash(baseline),
            "score": float(base_score),
        },
        "candidate": {
            "score_hash": _score_hash(candidate),
            "score": float(cand_score),
        },
        "tolerance_abs": float(tolerance_abs),
        "diff": {
            "score_abs": float(score_abs),
            "features_max_abs": float(max_abs),
        },
        "within_tolerance": within,
        "feature_diffs": diffs,
    }
