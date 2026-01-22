# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

from ..util import sha256_c14n_json, stable_utc_now_iso
from ..recipes.base import pearson


RECOVERY_SCHEMA_V1 = "semiocore.biomed.recovery_report.v1"
PLASTICITY2_SCHEMA_V1 = "semiocore.biomed.plasticity2_report.v1"


_T_LABEL_RE = re.compile(r"^t(?P<hours>\d+)$")


def parse_time_label(label: str) -> float:
    """Parse a compact time label into hours.

    The Level C fixtures use labels like: t0, t24, t72, t168.
    """

    m = _T_LABEL_RE.match(label.strip())
    if not m:
        raise ValueError(f"Invalid time label '{label}'. Expected 't<Hours>' (e.g. t24).")
    return float(m.group("hours"))


def _as_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _features_vector(features: Dict[str, Any], keys: Iterable[str]) -> List[float]:
    out: List[float] = []
    for k in keys:
        v = _as_float(features.get(k))
        if v is None:
            out.append(0.0)
        else:
            out.append(float(v))
    return out


def _coupling_features(a: Dict[str, Any], b: Dict[str, Any]) -> Optional[float]:
    """Feature coupling proxy.

    Uses Pearson correlation over the intersection of feature keys.
    Returns null if the intersection is too small or degenerate.
    """

    fa = a.get("features") if isinstance(a, dict) else None
    fb = b.get("features") if isinstance(b, dict) else None
    if not isinstance(fa, dict) or not isinstance(fb, dict):
        return None

    keys = sorted(set(fa) & set(fb))
    if len(keys) < 2:
        return None

    xa = _features_vector(fa, keys)
    xb = _features_vector(fb, keys)
    return pearson(xa, xb)


@dataclass(frozen=True)
class SigmaPoint:
    """σ(t) = ⟨D, T, R, C⟩.

    - D: divergence proxy (absolute score delta vs baseline)
    - T: time (hours)
    - R: recovery proxy (1 - D / D_peak)
    - C: coupling proxy (feature correlation vs baseline)
    """

    label: str
    hours: float
    score_hash: str
    score: float
    D: float
    T: float
    R: float
    C: Optional[float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "hours": float(self.hours),
            "score_hash": self.score_hash,
            "score": float(self.score),
            "D": float(self.D),
            "T": float(self.T),
            "R": float(self.R),
            "C": None if self.C is None else float(self.C),
        }


def _score_hash(score_artifact: Dict[str, Any]) -> str:
    return sha256_c14n_json(score_artifact)


def _evidence_hash(*objs: Dict[str, Any]) -> str:
    """Hash evidence deterministically.

    Evidence hashes are meant to support auditing: if the input artifacts change,
    the report's evidence hash changes as well.
    """

    return sha256_c14n_json({"evidence": list(objs)})


def compare_v2(
    *,
    tool_version: str,
    baseline_label: str,
    baseline_score: Dict[str, Any],
    posts: List[Tuple[str, Dict[str, Any]]],
    use_realtime: bool = False,
) -> Dict[str, Any]:
    """Comparator v2.

    Produces a recovery report with σ(t) points for each post.
    """

    if not isinstance(baseline_score, dict):
        raise TypeError("baseline_score must be a dict")

    recipe = baseline_score.get("recipe")
    if not isinstance(recipe, str) or not recipe:
        raise ValueError("Baseline score artifact missing 'recipe'")

    base_hours = parse_time_label(baseline_label)
    base_score = _as_float(baseline_score.get("score"))
    if base_score is None:
        raise ValueError("Baseline score artifact missing numeric 'score'")

    baseline_h = _score_hash(baseline_score)

    # Prepare post points sorted by time.
    points_raw: List[Tuple[str, float, Dict[str, Any]]] = []
    for label, art in posts:
        if not isinstance(label, str) or not label:
            raise ValueError("Post label must be a non-empty string")
        if not isinstance(art, dict):
            raise TypeError("Post score artifact must be a dict")
        if art.get("recipe") != recipe:
            raise ValueError(f"Recipe mismatch in post '{label}': expected '{recipe}'")
        h = parse_time_label(label)
        points_raw.append((label, h, art))

    points_raw.sort(key=lambda t: t[1])

    # Divergence proxy: absolute score delta.
    Ds: List[float] = []
    for _, _, art in points_raw:
        s = _as_float(art.get("score"))
        if s is None:
            raise ValueError("Post score artifact missing numeric 'score'")
        Ds.append(abs(float(s) - float(base_score)))

    D_peak = max(Ds) if Ds else 0.0
    if Ds:
        i_peak = min(i for i, d in enumerate(Ds) if d == D_peak)
        t_peak_hours = float(points_raw[i_peak][1])
    else:
        t_peak_hours = float(base_hours)

    # Recovery threshold: 80% recovery = D <= 0.2 * D_peak.
    t_recover_80 = None
    if D_peak == 0.0:
        t_recover_80 = float(base_hours)
    else:
        thr = 0.2 * D_peak
        for (label, h, art), d in zip(points_raw, Ds):
            if h >= t_peak_hours and d <= thr:
                t_recover_80 = float(h)
                break

    sigma_points: List[SigmaPoint] = []
    for (label, h, art), d in zip(points_raw, Ds):
        s = float(_as_float(art.get("score")) or 0.0)
        r = 1.0 if D_peak == 0.0 else max(0.0, min(1.0, 1.0 - (d / D_peak)))
        c = _coupling_features(baseline_score, art)
        sigma_points.append(
            SigmaPoint(
                label=label,
                hours=float(h),
                score_hash=_score_hash(art),
                score=float(s),
                D=float(d),
                T=float(h),
                R=float(r),
                C=c,
            )
        )

    evidence_hash = _evidence_hash(baseline_score, *[a for _, _, a in points_raw])

    return {
        "schema": RECOVERY_SCHEMA_V1,
        "provenance": {
            "tool_version": tool_version,
            "created_utc": stable_utc_now_iso(use_realtime=use_realtime),
            "evidence_hash": evidence_hash,
        },
        "recipe": recipe,
        "baseline": {
            "label": baseline_label,
            "hours": float(base_hours),
            "score_hash": baseline_h,
            "score": float(base_score),
        },
        "sigma": [p.to_dict() for p in sigma_points],
        "metrics": {
            "D_peak": float(D_peak),
            "t_peak_hours": float(t_peak_hours),
            "t_recover_80_hours": None if t_recover_80 is None else float(t_recover_80),
        },
    }


def _auc_trapezoid(points: List[Tuple[float, float]]) -> float:
    if len(points) < 2:
        return 0.0
    pts = sorted(points, key=lambda t: t[0])
    auc = 0.0
    for (t0, y0), (t1, y1) in zip(pts[:-1], pts[1:]):
        dt = float(t1 - t0)
        auc += dt * (float(y0) + float(y1)) / 2.0
    return float(auc)


def plasticity_v2(
    *,
    tool_version: str,
    recovery_report: Dict[str, Any],
    use_realtime: bool = False,
) -> Dict[str, Any]:
    """Summarize a recovery report into a plasticity2 report."""

    if not isinstance(recovery_report, dict):
        raise TypeError("recovery_report must be a dict")
    if recovery_report.get("schema") != RECOVERY_SCHEMA_V1:
        raise ValueError("Unexpected recovery report schema")

    recipe = recovery_report.get("recipe")
    if not isinstance(recipe, str) or not recipe:
        raise ValueError("Recovery report missing 'recipe'")

    sigma = recovery_report.get("sigma")
    if not isinstance(sigma, list):
        raise ValueError("Recovery report missing 'sigma'")

    # Metrics from recovery
    m = recovery_report.get("metrics") if isinstance(recovery_report.get("metrics"), dict) else {}
    D_peak = float(m.get("D_peak") or 0.0)
    t_peak_hours = float(m.get("t_peak_hours") or 0.0)
    t_recover_80 = m.get("t_recover_80_hours")
    t_recover_80_hours = None if t_recover_80 is None else float(t_recover_80)

    # AUC over D(t) (include baseline at D=0).
    base = recovery_report.get("baseline") if isinstance(recovery_report.get("baseline"), dict) else {}
    base_h = float(base.get("hours") or 0.0)
    points: List[Tuple[float, float]] = [(base_h, 0.0)]

    Rs: List[float] = []
    Cs: List[float] = []
    for row in sigma:
        if not isinstance(row, dict):
            continue
        h = _as_float(row.get("hours"))
        d = _as_float(row.get("D"))
        r = _as_float(row.get("R"))
        c = _as_float(row.get("C"))
        if h is not None and d is not None:
            points.append((float(h), float(d)))
        if r is not None:
            Rs.append(float(r))
        if c is not None:
            Cs.append(float(c))

    auc_D = _auc_trapezoid(points)
    mean_R = sum(Rs) / len(Rs) if Rs else 0.0
    mean_C = (sum(Cs) / len(Cs)) if Cs else None

    evidence_hash = str(recovery_report.get("provenance", {}).get("evidence_hash"))

    return {
        "schema": PLASTICITY2_SCHEMA_V1,
        "provenance": {
            "tool_version": tool_version,
            "created_utc": stable_utc_now_iso(use_realtime=use_realtime),
            "evidence_hash": evidence_hash,
        },
        "recipe": recipe,
        "sigma": [
            {
                "label": str(row.get("label")),
                "hours": float(row.get("hours")),
                "D": float(row.get("D")),
                "T": float(row.get("T")),
                "R": float(row.get("R")),
                "C": None if row.get("C") is None else float(row.get("C")),
            }
            for row in sigma
            if isinstance(row, dict)
        ],
        "metrics": {
            "D_peak": float(D_peak),
            "t_peak_hours": float(t_peak_hours),
            "t_recover_80_hours": t_recover_80_hours,
            "auc_D": float(auc_D),
            "mean_R": float(mean_R),
            "mean_C": None if mean_C is None else float(mean_C),
        },
    }
