from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def safe_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


@dataclass
class QCReport:
    missing: List[str] = field(default_factory=list)
    outliers: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def ok(self) -> bool:
        return (not self.missing) and (not self.outliers)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok(),
            "missing": list(self.missing),
            "outliers": list(self.outliers),
            "notes": list(self.notes),
        }


@dataclass
class ScoreResult:
    recipe: str
    score: float
    features: Dict[str, float]
    qc: QCReport
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recipe": self.recipe,
            "score": float(self.score),
            "features": {k: float(v) for k, v in self.features.items()},
            "qc": self.qc.to_dict(),
            "details": self.details,
        }


def mean(xs: Iterable[float]) -> Optional[float]:
    ys = list(xs)
    if not ys:
        return None
    return sum(ys) / len(ys)


def stdev(xs: Iterable[float]) -> Optional[float]:
    ys = list(xs)
    if len(ys) < 2:
        return None
    m = sum(ys) / len(ys)
    var = sum((x - m) ** 2 for x in ys) / (len(ys) - 1)
    return var ** 0.5


def pearson(x: List[float], y: List[float]) -> Optional[float]:
    if len(x) != len(y) or len(x) < 2:
        return None
    mx = sum(x) / len(x)
    my = sum(y) / len(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    denx = sum((a - mx) ** 2 for a in x) ** 0.5
    deny = sum((b - my) ** 2 for b in y) ** 0.5
    if denx == 0.0 or deny == 0.0:
        return None
    return num / (denx * deny)
